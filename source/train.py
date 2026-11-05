"""CloudRacer Original GUI — policy gradient REINFORCE com PyTorch.
Treinamento headless no SageMaker (CPU); avaliações e artefatos em /opt/ml/model.
O ambiente é gerado pelo simulador (não é um dataset supervisionado).
"""
import argparse
import csv
import json
import math
import os
from pathlib import Path
import random
import statistics

import torch
from torch import nn
from torch.distributions import Normal
from racer_env import (CarRacingEnv, CX, CY, RX, RY, TRACK_WIDTH)
from viewer import create_viewer


class Policy(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(10, 32), nn.Tanh(),
                                 nn.Linear(32, 24), nn.Tanh(), nn.Linear(24, 2))
        self.log_std = nn.Parameter(torch.tensor([-0.50, -0.75]))

    def act(self, state, stochastic=True):
        inp = torch.tensor(state, dtype=torch.float32)
        mu = self.net(inp)
        dist = Normal(mu, self.log_std.exp())
        raw = dist.sample() if stochastic else mu
        action = [float(torch.tanh(raw[0]).item()),
                  float(torch.sigmoid(raw[1]).item())]
        return action, (dist.log_prob(raw).sum() if stochastic else None)


def episode(policy, max_steps, stochastic, phase=0.0, record=False):
    env = CarRacingEnv(max_steps=max_steps, start_phase=phase)
    s = env.reset()
    trajectory = [env.snapshot(s[:7])] if record else None
    logprobs, rewards = [], []
    for _ in range(max_steps):
        a, logprob = policy.act(s, stochastic=stochastic)
        s, reward, done, info = env.step(a)
        rewards.append(reward)
        if stochastic:
            logprobs.append(logprob)
        if record:
            trajectory.append(env.snapshot(s[:7]))
        if done:
            break
    return {'reward': sum(rewards), 'rewards': rewards, 'logprobs': logprobs,
            'info': info, 'trajectory': trajectory}


def reinforce(policy, optimizer, rollouts, gamma=0.985):
    terms = []
    all_returns = []
    for run in rollouts:
        ret, rev = 0.0, []
        for value in reversed(run['rewards']):
            ret = value + gamma * ret
            rev.append(ret)
        rets = list(reversed(rev))
        all_returns.extend(rets)
        terms.append((run['logprobs'], rets))
    mu = statistics.fmean(all_returns)
    std = max(1.0, statistics.pstdev(all_returns))
    loss_terms = [-(lp * ((r - mu) / std)) for logprobs, values in terms
                  for lp, r in zip(logprobs, values)]
    loss = torch.stack(loss_terms).mean()
    optimizer.zero_grad()
    loss.backward()
    nn.utils.clip_grad_norm_(policy.parameters(), 1.0)
    optimizer.step()
    return float(loss.detach())


def evaluate(policy, max_steps, n=3):
    vals = [episode(policy, max_steps, False, phase=d)['reward']
            for d in (0.0, 0.36, 0.72)[:n]]
    return round(statistics.fmean(vals), 3)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--episodes', type=int, default=100)
    p.add_argument('--max-steps', type=int, default=350)
    p.add_argument('--seed', type=int, default=42)
    p.add_argument('--learning-rate', type=float, default=0.002)
    p.add_argument('--eval-every', type=int, default=10)
    p.add_argument('--output-dir', default=os.environ.get('SM_MODEL_DIR', './outputs'))
    args, _ = p.parse_known_args()  # nomes especiais de hyperparams pertencem ao SageMaker
    if not 1 <= args.episodes <= 2000 or not 30 <= args.max_steps <= 2000:
        p.error('episodes entre 1-2000 e max-steps entre 30-2000')
    torch.set_num_threads(2)
    random.seed(args.seed)
    torch.manual_seed(args.seed)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    policy = Policy()
    optimizer = torch.optim.Adam(policy.parameters(), lr=args.learning_rate)
    baseline_run = episode(policy, args.max_steps, False, record=True)
    baseline_mean = evaluate(policy, args.max_steps)
    rows = []
    best = -float('inf')
    best_checkpoint = None
    for i in range(1, args.episodes + 1):
        runs = [episode(policy, args.max_steps, True) for _ in range(3)]
        loss = reinforce(policy, optimizer, runs)
        mean_reward = statistics.fmean(r['reward'] for r in runs)
        crashes = sum(int(r['info']['crashed']) for r in runs)
        print(f'episode={i} metric_train_reward={mean_reward:.4f} '
              f'metric_loss={loss:.5f} crashes={crashes}/3', flush=True)
        row = {'episodio': i, 'recompensa_treino': round(mean_reward, 3),
               'recompensa_avaliacao': '', 'colisoes_3_episodios': crashes,
               'loss': round(loss, 5)}
        if i % args.eval_every == 0 or i == args.episodes:
            ev = evaluate(policy, args.max_steps)
            row['recompensa_avaliacao'] = ev
            print(f'episode={i} metric_eval_reward={ev:.4f}', flush=True)
            if ev > best:
                best = ev
                best_checkpoint = {k: v.detach().clone() for k, v in policy.state_dict().items()}
        rows.append(row)
    torch.save(policy.state_dict(), out / 'last_policy.pt')
    if best_checkpoint is not None:
        policy.load_state_dict(best_checkpoint)
    torch.save(policy.state_dict(), out / 'best_policy.pt')
    final_run = episode(policy, args.max_steps, False, record=True)
    final_mean = evaluate(policy, args.max_steps)
    summary = {
        'algoritmo': 'REINFORCE (policy gradient; rede neural PyTorch)',
        'origem_ambiente': 'Ambiente didático contínuo inspirado no contrato do neural_network (não clone do Pygame)',
        'pista': 'oval 2D parametrizado', 'observacoes': 10, 'sensores': 7,
        'acoes': ['steering', 'throttle'], 'seed': args.seed,
        'episodios_treino': args.episodes, 'max_passos': args.max_steps,
        'recompensa_media_antes_3_partidas': baseline_mean,
        'recompensa_media_depois_3_partidas': final_mean,
        'recompensa_melhor_checkpoint': best,
        'antes': {'recompensa': round(baseline_run['reward'], 3), **baseline_run['info']},
        'depois': {'recompensa': round(final_run['reward'], 3), **final_run['info']},
        'nota': 'Não há garantia de melhora ou voltas completas em cada treinamento.'
    }
    with (out / 'metrics.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    (out / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    (out / 'viewer.html').write_text(create_viewer(summary, rows, baseline_run['trajectory'],
                                                  final_run['trajectory']), encoding='utf-8')
    print('metric_eval_reward=' + str(final_mean), flush=True)
    print('results_saved=' + str(out), flush=True)


if __name__ == '__main__':
    main()

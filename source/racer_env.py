"""CloudRacer Original GUI: ambiente 2D contínuo independente, sem pygame.
Adaptação didática inspirada no contrato público de sensores do projeto
akshaybhandare/neural_network (MIT); não contém o código do repositório.
"""
import math

ANGLES = (-90, -55, -25, 0, 25, 55, 90)
CX, CY, RX, RY = 430.0, 285.0, 262.0, 172.0
TRACK_WIDTH = 110.0
MAX_SPEED = 8.0


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def center_angle(x, y):
    return math.atan2((y - CY) / RY, (x - CX) / RX)


def tangent(theta):
    return math.atan2(RY * math.cos(theta), -RX * math.sin(theta))


def signed_distance(x, y):
    """Distância aproximada ao centro da pista elíptica (não a uma borda)."""
    dx, dy = x - CX, y - CY
    f = (dx / RX) ** 2 + (dy / RY) ** 2 - 1.0
    g = math.hypot(2 * dx / (RX * RX), 2 * dy / (RY * RY))
    return f / max(g, 1e-9)


class CarRacingEnv:
    """Observação = 7 sensores, velocidade, erro angular, deslocamento lateral.
    Ação = steer e throttle, ambos contínuos. Sem dependência de bibliotecas externas.
    """
    def __init__(self, max_steps=360, start_phase=0.0):
        self.max_steps = max_steps
        self.start_phase = start_phase
        self.reset()

    def reset(self, phase=None):
        theta = self.start_phase if phase is None else phase
        self.x = CX + RX * math.cos(theta)
        self.y = CY + RY * math.sin(theta)
        self.angle = tangent(theta)
        self.speed = 2.7
        self.prev_theta = theta
        self.total_phase = 0.0
        self.steps = 0
        self.crashed = False
        return self.observe()

    def on_track(self, x, y):
        return abs(signed_distance(x, y)) <= TRACK_WIDTH / 2

    def sensors(self):
        result = []
        for deg in ANGLES:
            ang = self.angle + math.radians(deg)
            ux, uy = math.cos(ang), math.sin(ang)
            length = 176.0
            for dist in range(8, 177, 8):
                if not self.on_track(self.x + dist * ux, self.y + dist * uy):
                    length = float(dist)
                    break
            result.append(round(length / 176.0, 5))
        return result

    def observe(self):
        phase = center_angle(self.x, self.y)
        err = wrap(tangent(phase) - self.angle)
        off = signed_distance(self.x, self.y)
        return self.sensors() + [self.speed / MAX_SPEED,
                                 clamp(err / math.pi, -1, 1),
                                 clamp(off / (TRACK_WIDTH / 2), -1, 1)]

    def step(self, action):
        steer, throttle = (clamp(float(action[0]), -1, 1),
                           clamp(float(action[1]), 0, 1))
        self.speed = clamp(self.speed * 0.981 + 0.31 * throttle, 0, MAX_SPEED)
        self.angle += 0.058 * steer * (self.speed / 6.0)
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        self.steps += 1
        theta = center_angle(self.x, self.y)
        delta = wrap(theta - self.prev_theta)
        self.total_phase += delta
        self.prev_theta = theta
        progress = max(-0.3, min(delta, 0.3))
        self.crashed = not self.on_track(self.x, self.y)
        completed = self.total_phase >= 2 * math.pi
        truncated = self.steps >= self.max_steps
        # Recompensa de progresso e de centralização + penalidade de colisão.
        reward = 55.0 * progress - 0.012 * abs(signed_distance(self.x, self.y)) - 0.06
        if progress < 0:
            reward += 30.0 * progress
        if self.crashed:
            reward -= 14
        if completed:
            reward += 40
        return self.observe(), float(reward), bool(self.crashed or completed or truncated), {
            'crashed': self.crashed,
            'lap_completed': bool(completed),
            'steps': self.steps,
            'phase': self.total_phase,
            'distance_to_center': round(float(signed_distance(self.x, self.y)), 2),
        }

    def snapshot(self, readings=None):
        return [round(self.x, 2), round(self.y, 2), round(self.angle, 3),
                round(self.speed, 2), readings or self.sensors()]

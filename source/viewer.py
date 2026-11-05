"""Página HTML independente, gerada a partir das trajetórias reais do experimento."""
import json
from racer_env import CX, CY, RX, RY, TRACK_WIDTH


def create_viewer(summary, rows, before, after):
    data = json.dumps({'summary': summary, 'metrics': rows, 'before': before,
                       'after': after, 'track': [CX, CY, RX, RY, TRACK_WIDTH]},
                      separators=(',', ':'), ensure_ascii=False).replace('</', '<\\/')
    html = r'''<!doctype html><html lang="pt-br"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>CloudRacer AI — Avaliação</title>
<style>body{margin:0;background:#08111f;color:#e9eff9;font:15px system-ui,sans-serif}
main{max-width:1120px;padding:24px;margin:auto}h1{font-size:30px;margin-bottom:8px}
small,p{color:#b0bccc}.panel{background:#122139;border:1px solid #2d4261;border-radius:15px;padding:16px;margin:15px 0}
canvas{display:block;width:100%;height:auto;background:#071524;border-radius:10px}
.controls{display:flex;flex-wrap:wrap;align-items:center;gap:14px;margin:12px 0}
button,select,input{accent-color:#55d3e3;color:#f0f4fa;background:#1b3452;border:1px solid #497194;border-radius:9px;padding:9px}
button{cursor:pointer}input[type=range]{flex:1;min-width:180px}strong{color:#ffffff}
.cards{display:flex;flex-wrap:wrap;gap:10px}.stat{flex:1;min-width:180px;padding:12px;background:#1c304e;border-radius:10px}
.stat span{display:block;color:#bacce1;font-size:12px}.stat b{font-size:22px}
</style></head><body><main><h1>🏎️ CloudRacer AI — corrida 2D</h1>
<p>Rede neural treinada por <strong>REINFORCE</strong> no SageMaker. Os trajetos são gravações das avaliações e não uma simulação inventada.</p>
<div class="cards"><div class="stat"><span>Recompensa média antes (3 corridas)</span><b id="beforeReward"></b></div>
<div class="stat"><span>Recompensa média depois (3 corridas)</span><b id="afterReward"></b></div>
<div class="stat"><span>Episódios de treinamento</span><b id="episodes"></b></div></div>
<section class="panel"><div class="controls"><label>Trajetória <select id="mode"><option value="before">Antes do treinamento</option><option value="after" selected>Depois do treinamento</option></select></label>
<button id="play">▶ Reproduzir</button><button id="reset">↩ Reiniciar</button><label>Velocidade <select id="speed"><option value="1">1x</option><option value="3" selected>3x</option><option value="6">6x</option></select></label></div>
<canvas id="track" width="860" height="570"></canvas><div class="controls"><span id="frame"></span><input id="seek" type="range" min="0" max="1" value="0" /></div>
<p>Linhas verdes: sensores de distância. Faixa cinza: área transitável. Ponto dourado: carro.</p></section>
<section class="panel"><h2>Curva de treinamento</h2><canvas id="chart" width="860" height="260"></canvas>
<p>Recompensa de treinamento (linha azul) e avaliações periódicas (pontos dourados). O desempenho depende da semente, dos episódios e do algoritmo.</p></section>
<section class="panel"><h2>Resumo de execução</h2><pre id="summary" style="white-space:pre-wrap;overflow-wrap:anywhere"></pre></section>
</main><script id="payload" type="application/json">__DATA__</script>
<script>
const D=JSON.parse(document.getElementById('payload').textContent);
const $=id=>document.getElementById(id);
$('beforeReward').textContent=D.summary.recompensa_media_antes_3_partidas;
$('afterReward').textContent=D.summary.recompensa_media_depois_3_partidas;
$('episodes').textContent=D.summary.episodios_treino;
$('summary').textContent=JSON.stringify(D.summary,null,2);
const ctx=$('track').getContext('2d'), c=$('chart').getContext('2d');
let frame=0, running=false;
function trajectory(){return D[$('mode').value] || [];}
function road(){
 const [cx,cy,rx,ry,w]=D.track;
 ctx.lineWidth=w;ctx.strokeStyle='#637584';ctx.beginPath();ctx.ellipse(cx,cy,rx,ry,0,0,Math.PI*2);ctx.stroke();
 ctx.lineWidth=2;ctx.strokeStyle='#dce4e8';ctx.setLineDash([16,16]);ctx.beginPath();ctx.ellipse(cx,cy,rx,ry,0,0,Math.PI*2);ctx.stroke();ctx.setLineDash([]);
 ctx.beginPath();ctx.ellipse(cx,cy,rx+0.5*w,ry+0.5*w,0,0,Math.PI*2);ctx.strokeStyle='#8ad8af';ctx.lineWidth=2;ctx.stroke();
 ctx.beginPath();ctx.ellipse(cx,cy,rx-0.5*w,ry-0.5*w,0,0,Math.PI*2);ctx.stroke();
}
function draw(){
 const t=trajectory();if(!t.length)return;
 frame=Math.max(0,Math.min(frame,t.length-1)); $('seek').max=t.length-1; $('seek').value=frame;
 $('frame').textContent=`Quadro ${frame+1} / ${t.length}`;
 ctx.fillStyle='#0b2530';ctx.fillRect(0,0,860,570);road();
 ctx.beginPath();ctx.strokeStyle=$('mode').value==='before'?'#ff886e':'#78e1f7';ctx.lineWidth=3;
 for(let i=0;i<=frame;i++){const pt=t[i]; if(i===0)ctx.moveTo(pt[0],pt[1]);else ctx.lineTo(pt[0],pt[1]);}ctx.stroke();
 const [x,y,ang,vel,sensors]=t[frame];
 const angles=[-90,-55,-25,0,25,55,90];
 angles.forEach((a,i)=>{const theta=ang+a*Math.PI/180,len=sensors[i]*176;
 ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(x+Math.cos(theta)*len,y+Math.sin(theta)*len);
 ctx.strokeStyle='rgba(125,255,153,.70)';ctx.lineWidth=1.5;ctx.stroke();});
 ctx.save();ctx.translate(x,y);ctx.rotate(ang);ctx.fillStyle='#ffcc54';ctx.fillRect(-15,-8,30,16);
 ctx.fillStyle='#1b2635';ctx.fillRect(0,-7,8,14);ctx.restore();
 ctx.fillStyle='#dbe8fb';ctx.font='16px sans-serif';ctx.fillText(`Velocidade ${vel.toFixed(1)} px/quadro`,24,29);
}
function plot(){ const w=860,h=260,p=36,r=D.metrics;const series=r.map(v=>Number(v.recompensa_treino));
 const evals=r.filter(v=>v.recompensa_avaliacao!==''&&v.recompensa_avaliacao!==null);
 const all=series.concat(evals.map(v=>Number(v.recompensa_avaliacao)));let mn=Math.min(...all),mx=Math.max(...all);if(mx<=mn){mx+=1;mn-=1}
 const xx=i=>p+(w-2*p)*i/Math.max(1,r.length-1),yy=v=>h-p-(h-2*p)*(v-mn)/(mx-mn);
 c.fillStyle='#0b2530';c.fillRect(0,0,w,h);c.strokeStyle='#50647b';c.lineWidth=1;
 for(let k=0;k<5;k++){const y=p+k*(h-2*p)/4;c.beginPath();c.moveTo(p,y);c.lineTo(w-p,y);c.stroke();}
 c.strokeStyle='#55cde9';c.lineWidth=2;c.beginPath();series.forEach((v,i)=>i?c.lineTo(xx(i),yy(v)):c.moveTo(xx(i),yy(v)));c.stroke();
 c.fillStyle='#ffce63';evals.forEach(e=>{const i=Number(e.episodio)-1;c.beginPath();c.arc(xx(i),yy(Number(e.recompensa_avaliacao)),4,0,Math.PI*2);c.fill()});
 c.font='12px sans-serif';c.fillStyle='#c3d3e7';c.fillText(mx.toFixed(1),3,p);c.fillText(mn.toFixed(1),3,h-p);
}
$('play').onclick=()=>{running=!running;$('play').textContent=running?'Ⅱ Pausar':'▶ Reproduzir'};
$('reset').onclick=()=>{frame=0;running=false;$('play').textContent='▶ Reproduzir';draw()};
$('mode').onchange=()=>{frame=0;draw()};$('seek').oninput=()=>{frame=Number($('seek').value);draw()};
let n=0;function loop(){if(running){n++;if(n%2===0){frame+=Number($('speed').value);if(frame>=trajectory().length){frame=trajectory().length-1;running=false;$('play').textContent='▶ Reproduzir';}draw();}}requestAnimationFrame(loop)}
plot();draw();requestAnimationFrame(loop);
</script></body></html>'''
    return html.replace('__DATA__', data)

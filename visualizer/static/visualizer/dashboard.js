(() => {
  const behavior = JSON.parse(document.getElementById("behavior-data").textContent);
  const triggers = JSON.parse(document.getElementById("trigger-data").textContent);
  const colors = ["#2d6a4f", "#e76f51", "#457b9d", "#a7c957", "#8e6c88", "#e9c46a"];

  function setupSelect(id, items, draw) {
    const select = document.getElementById(id);
    items.forEach((item, i) => select.add(new Option(item.name, i)));
    select.addEventListener("change", () => draw(items[Number(select.value)]));
    if (items.length) draw(items[0]); else select.disabled = true;
  }

  function canvasContext(id) {
    const canvas = document.getElementById(id);
    const ratio = window.devicePixelRatio || 1;
    const box = canvas.getBoundingClientRect();
    canvas.width = box.width * ratio; canvas.height = box.height * ratio;
    const ctx = canvas.getContext("2d"); ctx.scale(ratio, ratio);
    return {ctx, width:box.width, height:box.height};
  }

  function axes(ctx, width, height, maxY, yLabel) {
    const p = {l:50,r:16,t:15,b:34}; ctx.strokeStyle="#dcd9cf"; ctx.fillStyle="#788079"; ctx.font="11px system-ui";
    for (let i=0;i<=4;i++) { const y=p.t+(height-p.t-p.b)*i/4; ctx.beginPath();ctx.moveTo(p.l,y);ctx.lineTo(width-p.r,y);ctx.stroke(); const value=maxY*(1-i/4);ctx.fillText(value.toFixed(1),7,y+4); }
    ctx.fillText(yLabel,p.l,height-8); return p;
  }

  function drawBehavior(session) {
    const metrics = document.getElementById("behavior-metrics");
    metrics.innerHTML = `<span><strong>${session.trial_count}</strong> trials</span><span><strong>${session.makes}</strong> made</span><span><strong>${session.misses}</strong> missed</span><span><strong>${session.average_reaction_time ?? "—"}s</strong> avg response</span>`;
    const {ctx,width,height}=canvasContext("behavior-chart"); const values=session.trials.map(t=>t.reaction_time||0); const max=Math.max(...values,1); const p=axes(ctx,width,height,max,"Trial number →"); const plotW=width-p.l-p.r, plotH=height-p.t-p.b;
    session.trials.forEach((trial,i)=>{ const x=p.l+(i+.5)*plotW/session.trials.length; const y=p.t+plotH-(trial.reaction_time||0)*plotH/max; ctx.fillStyle=trial.made?"#2d6a4f":"#e76f51";ctx.beginPath();ctx.arc(x,y,4.5,0,Math.PI*2);ctx.fill(); });
  }

  function drawTriggers(session) {
    document.getElementById("trigger-metrics").innerHTML=`<span><strong>${session.event_count}</strong> events</span><span><strong>${session.duration}s</strong> duration</span><span><strong>${Object.keys(session.code_counts).length}</strong> marker codes</span>`;
    const codes=Object.keys(session.code_counts), {ctx,width,height}=canvasContext("trigger-chart"), p={l:50,r:18,t:18,b:34}, plotW=width-p.l-p.r, plotH=height-p.t-p.b;
    ctx.strokeStyle="#dcd9cf";ctx.beginPath();ctx.moveTo(p.l,p.t+plotH);ctx.lineTo(width-p.r,p.t+plotH);ctx.stroke();ctx.fillStyle="#788079";ctx.font="11px system-ui";ctx.fillText("0s",p.l,height-9);ctx.fillText(`${session.duration}s`,width-p.r-38,height-9);
    session.events.forEach(event=>{ const x=p.l+(event.time/session.duration)*plotW, index=codes.indexOf(event.code), y=p.t+12+index*Math.max(12,(plotH-20)/Math.max(codes.length,1));ctx.strokeStyle=colors[index%colors.length]+"99";ctx.beginPath();ctx.moveTo(x,p.t+plotH);ctx.lineTo(x,y);ctx.stroke();ctx.fillStyle=colors[index%colors.length];ctx.beginPath();ctx.arc(x,y,3,0,Math.PI*2);ctx.fill(); });
    document.getElementById("code-legend").innerHTML=codes.map((code,i)=>`<span style="--dot:${colors[i%colors.length]}">Code ${code} · ${session.code_counts[code]}</span>`).join("");
  }

  setupSelect("behavior-session", behavior, drawBehavior); setupSelect("trigger-session", triggers, drawTriggers);
  let timer; window.addEventListener("resize",()=>{clearTimeout(timer);timer=setTimeout(()=>{ const b=document.getElementById("behavior-session"),t=document.getElementById("trigger-session");if(behavior.length)drawBehavior(behavior[+b.value]);if(triggers.length)drawTriggers(triggers[+t.value]);},120)});
})();

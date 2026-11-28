"use strict";

window.MirrorMaterial = (() => {
  const preferenceKey = "liusterko-material";
  const changeEvent = "mirror-material-change";
  const labels = Object.freeze({
    kahlia: "Кахля",
    vytynanka: "Витинанка",
    klyny: "Клини"
  });
  const hex = /^#(?:[a-f\d]{3,4}|[a-f\d]{6}|[a-f\d]{8})$/i;

  function keyFor(value) {
    const id = value === "kahlja" ? "kahlia" : value;
    return typeof id === "string" && Object.hasOwn(labels, id) ? id : null;
  }

  function read(key, field) {
    try {
      const raw = window.localStorage.getItem(key);
      if (raw == null) return null;
      return keyFor(field ? JSON.parse(raw)?.[field] : raw);
    } catch {
      return null;
    }
  }

  function previousSelection() {
    return read(preferenceKey) ||
      read("liusterko-mirror-3", "hand") ||
      read("liusterko-studio-v2", "theme") ||
      read("liusterko-interface-v1", "theme") ||
      read("люстерко-тема") ||
      "kahlia";
  }

  let active = previousSelection();
  document.documentElement.dataset.mirrorMaterial = active;

  function apply(id) {
    if (id === active) return;
    const previous = active;
    active = id;
    document.documentElement.dataset.mirrorMaterial = id;
    window.dispatchEvent(new CustomEvent(changeEvent, {detail: {theme: id, previous}}));
  }

  function set(value) {
    const id = keyFor(value);
    if (!id) return false;
    try { window.localStorage.setItem(preferenceKey, id); } catch {}
    apply(id);
    return true;
  }

  window.addEventListener("storage", event => {
    if (event.key !== preferenceKey && event.key !== null) return;
    apply(keyFor(event.newValue) || previousSelection());
  });

  function label(theme = active) { return labels[keyFor(theme)] || ""; }
  function get() { return active; }

  function mast() { return window.Hand.wordmark(active); }

  function petal(color, size = 18) {
    return window.Hand.petal(active, typeof color === "string" && hex.test(color) ? color : null, size);
  }

  // Selection is a paper slip, a pool of glaze or a tilted plane underneath the actual control.
  function choice(color, width = 92, height = 32) {
    const pigment = typeof color === "string" && hex.test(color) ? color : undefined;
    return window.Hand.patch(active, pigment, width, height);
  }

  // The host supplies its measured stage. No synthetic stage or timer runs here.
  function waiting(phase) {
    if (!Number.isInteger(phase) || phase < 1 || phase > 5) return "";
    return window.Hand.art(active, "waiting", phase);
  }

  // Decorative time-based reveal, not a percentage of backend work. Completion comes from the host.
  function reveal(host, {startedAt=Date.now(), expectedSeconds=180, complete=false}={}) {
    const theme=active;
    host.innerHTML=window.Hand.art(theme,'building');
    const svg=host.querySelector('svg'), reduced=window.matchMedia?.('(prefers-reduced-motion: reduce)');
    const cuts=[...svg.querySelectorAll('.vt-pr')];
    const lines=[...svg.querySelectorAll('.sh')];
    const pigments=[...svg.querySelectorAll('.shar.zhov path,.shar.zel path,.pl,.pol')];
    const planes=[...svg.querySelectorAll('.kl-ch')];
    const fold=svg.querySelector('.vt-p');
    const clamp=x=>Math.max(0,Math.min(1,x));
    const part=(p,i,n,from=0,to=.88)=>clamp((p-from-i/Math.max(1,n-1)*(to-from))/.12);
    for(const path of lines){path.setAttribute('pathLength','1');path.style.strokeDasharray='1';}
    let frame=0,last=-Infinity,stopped=false;
    function draw(now){
      if(stopped||!host.isConnected)return;
      if(now-last>=250){
        last=now;
        const seconds=Math.max(0,(Date.now()-startedAt)/1000);
        const p=complete||reduced?.matches?1:1-Math.exp(-seconds/Math.max(30,expectedSeconds));
        host.dataset.reveal=String(p);
        cuts.forEach((path,i)=>{const t=part(p,i,cuts.length,.02,.87);path.style.opacity=t;path.style.transform='scale('+(.12+.88*t)+')';});
        if(fold)fold.style.transform='scaleX('+(.06+.94*Math.sqrt(p))+')';
        lines.forEach((path,i)=>{path.style.strokeDashoffset=1-part(p,i,lines.length,0,.72);});
        pigments.forEach((path,i)=>{path.style.opacity=part(p,i,pigments.length,.12,.88);});
        planes.forEach((path,i)=>{const t=part(p,i,planes.length,0,.88);path.style.opacity=t;path.style.transform='translate(calc(var(--dx, 0px) * '+(1-t)+'),calc(var(--dy, 0px) * '+(1-t)+'))';});
      }
      if(!complete)frame=requestAnimationFrame(draw);
    }
    draw(0);
    return {host,theme,startedAt,stop(){stopped=true;cancelAnimationFrame(frame);}};
  }

  function error() { return window.Hand.art(active, "error"); }

  function seal(colors, worn = false, size = 64) {
    const pigments = Array.isArray(colors) ? colors.filter(c => typeof c === "string" && hex.test(c)) : [];
    if (!pigments.length) return "";
    return window.Hand.seal(active, pigments, worn === true, size);
  }

  return Object.freeze({get, set, labels, label, mast, petal, choice, waiting, reveal, error, seal, changeEvent});
})();

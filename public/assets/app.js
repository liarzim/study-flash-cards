/* Study Flash Cards: static study app. Topics live in /topics/<id>/topic.json */
(() => {
'use strict';
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const shuffle = a => { for (let i=a.length-1;i>0;i--){ const j=Math.floor(Math.random()*(i+1)); [a[i],a[j]]=[a[j],a[i]]; } return a; };
const IMG = '__img';

let index = null, topic = null, cards = [];
const cfg = { front:IMG, back:'name', mode:'flip', groups:new Set() };
let queue = [], pos = 0, good = 0, bad = 0, missed = [];

/* ---------- data ---------- */
async function getJSON(url){ const r = await fetch(url, {cache:'no-cache'}); if (!r.ok) throw new Error(url); return r.json(); }
const imgURL = (t, path) => `topics/${t}/${path}`;

/* ---------- routing: #<topic-id> ---------- */
async function route(){
  const id = decodeURIComponent(location.hash.slice(1));
  if (!id){ showHome(); return; }
  try { await openTopic(id); } catch { location.hash = ''; }
}
window.addEventListener('hashchange', route);

/* ---------- home ---------- */
async function showHome(){
  $('#v-home').hidden = false; $('#v-study').hidden = true; document.title = 'Study Flash Cards';
  if (!index){
    try { index = await getJSON('topics/index.json'); }
    catch { $('#home-status').textContent = 'לא ניתן לטעון את רשימת הנושאים'; return; }
  }
  const list = index.topics || [];
  $('#home-status').textContent = `${list.length} נושאים`;
  const el = $('#topics');
  if (!list.length){ el.innerHTML = '<div class="empty">עדיין אין נושאים.</div>'; return; }
  el.innerHTML = list.map(t => `
    <a class="topic" href="#${encodeURIComponent(t.id)}">
      <div class="cover">${(t.covers||[]).map(c=>`<img src="${esc(imgURL(t.id,c))}" alt="" loading="lazy">`).join('') || '<span class="big muted">Aa</span>'}</div>
      <div class="body"><h3>${esc(t.title)}</h3>
        ${t.subtitle?`<span class="muted" style="font-size:.9rem">${esc(t.subtitle)}</span>`:''}
        <span class="muted mono" style="font-size:.85rem">${t.count||0} כרטיסיות · ${(t.groups||[]).length} קבוצות</span>
        <div class="chips">${(t.groups||[]).map(g=>`<span class="chip">${esc(g)}</span>`).join('')}</div></div>
    </a>`).join('');
}

/* ---------- topic setup ---------- */
function fieldOpts(){
  const o = [];
  if (cards.some(c => c.image)) o.push({k:IMG, l:topic.imageLabel || 'תמונה'});
  for (const f of topic.fields) o.push({k:f.key, l:f.label});
  if (topic.groups?.length) o.push({k:'group', l:topic.groupLabel || 'קבוצה'});
  return o;
}
const valOf = (c,k) => k===IMG ? c.image : k==='group' ? c.group : c.values?.[k];
const labelOf = k => fieldOpts().find(o => o.k===k)?.l || k;

async function openTopic(id){
  if (!topic || topic.id !== id){ topic = await getJSON(`topics/${encodeURIComponent(id)}/topic.json`); cards = topic.cards || []; }
  $('#v-home').hidden = true; $('#v-study').hidden = false; window.scrollTo(0,0);
  document.title = `${topic.title} · Study Flash Cards`;
  $('#s-title').textContent = topic.title; $('#s-sub').textContent = topic.subtitle || '';
  $('#s-eyebrow').textContent = `${cards.length} כרטיסיות`;
  $('#s-setup').hidden = false; $('#s-run').hidden = true;
  const opts = fieldOpts();
  const fill = (sel, def) => { sel.innerHTML = opts.map(o=>`<option value="${esc(o.k)}">${esc(o.l)}</option>`).join(''); sel.value = def; };
  fill($('#s-front'), opts[0].k); fill($('#s-back'), (opts.find(o=>o.k!==opts[0].k) || opts[0]).k);
  cfg.groups = new Set(topic.groups || []);
  renderGroups(); updateCount();
}
function renderGroups(){
  const el = $('#s-groups'); el.innerHTML = '';
  if (!topic.groups?.length){ el.innerHTML = '<span class="muted">אין קבוצות בנושא זה</span>'; return; }
  for (const g of topic.groups){
    const b = document.createElement('button'); b.className = 'chip' + (cfg.groups.has(g) ? ' on' : ''); b.textContent = g; b.setAttribute('aria-pressed', cfg.groups.has(g));
    b.onclick = () => { cfg.groups.has(g) ? cfg.groups.delete(g) : cfg.groups.add(g); renderGroups(); updateCount(); };
    el.appendChild(b);
  }
}
const pool = () => cards.filter(c => (!topic.groups?.length || cfg.groups.has(c.group)) && valOf(c,cfg.front) && valOf(c,cfg.back));
function updateCount(){
  cfg.front = $('#s-front').value; cfg.back = $('#s-back').value;
  const n = pool().length;
  $('#s-count').textContent = cfg.front===cfg.back ? 'בחרו שדות שונים לשאלה ולתשובה' : `${n} כרטיסיות בסבב`;
  $('#b-start').disabled = !n || cfg.front===cfg.back;
}
$('#s-front').onchange = updateCount; $('#s-back').onchange = updateCount;
const setMode = m => { cfg.mode = m; $('#m-flip').setAttribute('aria-pressed', m==='flip'); $('#m-mcq').setAttribute('aria-pressed', m==='mcq'); };
$('#m-flip').onclick = () => setMode('flip'); $('#m-mcq').onclick = () => setMode('mcq');

/* ---------- running a round ---------- */
$('#b-start').onclick = () => startRound(pool(), $('#s-shuffle').checked);
$('#b-setup').onclick = () => { $('#s-run').hidden = true; $('#s-setup').hidden = false; };
$('#b-reshuffle').onclick = () => { queue = queue.slice(0,pos).concat(shuffle(queue.slice(pos))); showCard(); };
$('#b-retry').onclick = () => startRound(missed.slice(), true);
$('#b-again').onclick = () => startRound(pool(), true);

function startRound(list, doShuffle){
  queue = doShuffle ? shuffle(list.slice()) : list.slice(); pos = 0; good = 0; bad = 0; missed = [];
  $('#s-setup').hidden = true; $('#s-run').hidden = false; $('#run-done').hidden = true;
  $('#run-flip').hidden = cfg.mode !== 'flip'; $('#run-mcq').hidden = cfg.mode !== 'mcq';
  showCard();
}
function visual(card){
  const box = document.createElement('div'); box.className = 'plate';
  const i = new Image(); i.src = imgURL(topic.id, card.image); i.alt = topic.imageLabel || 'תמונה'; i.decoding = 'async';
  box.appendChild(i); return box;
}
function fillFace(el, c, k, extras){
  el.innerHTML = `<span class="tag chip">${esc(labelOf(k))}</span>`;
  if (k===IMG) el.appendChild(visual(c));
  else { const t = document.createElement('div'); t.className = 'big'; t.textContent = valOf(c,k); el.appendChild(t); }
  if (extras){
    const parts = fieldOpts().filter(o => o.k!==cfg.front && o.k!==cfg.back && o.k!==IMG).map(o => valOf(c,o.k)).filter(Boolean);
    if (parts.length){ const x = document.createElement('div'); x.className = 'extra'; x.innerHTML = parts.map(p=>`<span class="chip">${esc(p)}</span>`).join(''); el.appendChild(x); }
    if (c.credit){ const cr = document.createElement('div'); cr.className = 'credit'; cr.textContent = c.credit; el.appendChild(cr); }
  }
}
function updateBar(){
  $('#r-pos').textContent = `${Math.min(pos+1, queue.length)} / ${queue.length}`;
  $('#r-bar').style.width = (pos/queue.length*100) + '%';
  $('#live-score').innerHTML = `<span class="good-t">✓ ${good}</span><span class="bad-t">✗ ${bad}</span>`;
}
function showCard(){
  if (pos >= queue.length) return finish();
  updateBar(); const c = queue[pos];
  if (cfg.mode === 'flip'){
    $('#card').classList.remove('flipped'); fillFace($('#f-front'), c, cfg.front, false);
    setTimeout(() => fillFace($('#f-back'), c, cfg.back, true), 200);
    return;
  }
  fillFace($('#q-front'), c, cfg.front, false);
  const right = valOf(c, cfg.back), seen = new Set([right]), others = [];
  for (const x of shuffle(cards.slice())){ const v = valOf(x, cfg.back); if (!v || seen.has(v)) continue; seen.add(v); others.push(v); if (others.length===3) break; }
  const opts = shuffle([right, ...others]), el = $('#q-opts'); el.innerHTML = ''; $('#b-next').hidden = true;
  opts.forEach(o => {
    const b = document.createElement('button'); b.className = 'opt';
    if (cfg.back === IMG) b.appendChild(visual({image:o})); else b.textContent = o;
    b.onclick = () => {
      const ok = o === right; ok ? good++ : (bad++, missed.push(c));
      el.querySelectorAll('.opt').forEach((x,i) => { x.disabled = true; if (opts[i]===right) x.classList.add('right'); });
      if (!ok) b.classList.add('wrong');
      $('#b-next').hidden = false; $('#b-next').focus(); updateBar();
    };
    el.appendChild(b);
  });
}
const flip = () => $('#card').classList.toggle('flipped');
$('#card').onclick = flip; $('#b-flip').onclick = flip;
$('#card').onkeydown = e => { if (e.key===' ' || e.key==='Enter'){ e.preventDefault(); flip(); } };
$('#b-yes').onclick = () => { good++; pos++; showCard(); };
$('#b-no').onclick = () => { bad++; missed.push(queue[pos]); pos++; showCard(); };
$('#b-next').onclick = () => { pos++; showCard(); };
function finish(){
  $('#r-bar').style.width = '100%'; $('#r-pos').textContent = `${queue.length} / ${queue.length}`;
  $('#run-flip').hidden = true; $('#run-mcq').hidden = true; $('#run-done').hidden = false;
  $('#d-good').textContent = `ידעתי: ${good}`; $('#d-bad').textContent = `לא ידעתי: ${bad}`;
  $('#b-retry').hidden = !missed.length;
}
document.addEventListener('keydown', e => {
  if ($('#v-study').hidden || $('#s-run').hidden || cfg.mode!=='flip' || $('#run-flip').hidden || /INPUT|SELECT/.test(e.target.tagName)) return;
  if (e.key==='ArrowLeft') $('#b-yes').click(); else if (e.key==='ArrowRight') $('#b-no').click();
});

route();
})();

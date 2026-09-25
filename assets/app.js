/* Educational drawing state is deliberately separate from electrical topology. */
'use strict';
const $ = id => document.getElementById(id);
const NS = 'http://www.w3.org/2000/svg';
let components = [], byId = new Map(), selected = null, connecting = false, start = null;
let draft = {schema_version: 'sld-educational-draft/1', educational_only: true, instances: [], connections: []};
const text = (tag, value, cls) => {const e = document.createElement(tag); e.textContent = value; if(cls)e.className=cls; return e;};
const svg = (tag, attrs={}) => {const e=document.createElementNS(NS,tag); for(const [k,v] of Object.entries(attrs))e.setAttribute(k,String(v)); return e;};
const say = value => {$('status').textContent=value;};
const label = c => c.label || c.display_label || c.type.replaceAll('_',' ').toLowerCase();
const key = c => c.id || c.type;
const preview = c => c.preview || `assets/previews/${c.type}.svg`;
function renderCards(){
  const query=$('search').value.trim().toLowerCase();
  const matches=components.filter(c=>`${label(c)} ${c.type} ${c.description||''}`.toLowerCase().includes(query));
  $('cards').replaceChildren(); $('count').textContent=`${matches.length} / ${components.length} components`; $('empty').hidden=!!matches.length;
  for(const c of matches){
    const card=text('article','','card');const img=document.createElement('img');img.src=preview(c);img.alt=`${label(c)} research preview`;img.className='preview';img.loading='lazy';card.append(img,text('span','RESEARCH / NOT APPROVED','badge'),text('h3',label(c)),text('div',c.type,'type'));
    const details=document.createElement('details');details.append(text('summary','Source & details'));
    details.append(text('p','PowSyBl · ConvergenceLibrary · MPL-2.0. Not approved for engineering use.'));
    details.append(text('p',`${(c.anchorPoints||c.anchors||[]).length} graphical anchors. Electrical terminal mapping requires separate review.`));
    if(!(c.subComponents||[]).length)details.append(text('p','Renderer primitive: illustrative preview, no standalone upstream SVG.'));
    const source=document.createElement('a');source.href='https://github.com/powsybl/powsybl-diagram/tree/952186b5b34d1e4e472a04fb663b3654b54e3022/single-line-diagram/single-line-diagram-core/src/main/resources/ConvergenceLibrary';source.textContent='Original source ↗';source.target='_blank';source.rel='noopener noreferrer';details.append(source);card.append(details);
    const add=text('button','+ Add to draft');add.type='button';add.dataset.component=key(c);add.addEventListener('click',()=>addPart(c));card.append(add);$('cards').append(card);
  }
}
function addPart(c){if(draft.instances.length>=200){say('Draft limit: 200 parts.');return;}const n=draft.instances.length;const item={id:crypto.randomUUID(),component_id:key(c),x:100+(n%7)*125,y:100+(Math.floor(n/7)%4)*115};draft.instances.push(item);selected=item.id;renderCanvas();say(`Added ${label(c)}. Select it to move or connect.`);}
function choose(id){
  selected=id;
  if(connecting){if(start&&start!==id){const exists=draft.connections.some(e=>[e.from,e.to].includes(start)&&[e.from,e.to].includes(id));if(!exists&&draft.connections.length<400)draft.connections.push({from:start,to:id,kind:'illustrative-centre-link'});start=null;say('Illustrative link added. Crossings are not junctions.');}else{start=id;say('Choose another part to connect its graphical centre.');}}
  renderCanvas();
}
function renderCanvas(){
  const canvas=$('canvas');canvas.replaceChildren();
  canvas.append(svg('rect',{width:1000,height:560,fill:'#f5f5f5'}));
  const caption=svg('text',{x:16,y:24,fill:'#555','font-size':12});caption.textContent='EDUCATIONAL DRAFT / RATINGS UNKNOWN / CENTRE LINKS ONLY';canvas.append(caption);
  for(const e of draft.connections){const a=draft.instances.find(n=>n.id===e.from),b=draft.instances.find(n=>n.id===e.to);canvas.append(svg('line',{x1:a.x,y1:a.y,x2:b.x,y2:b.y,stroke:'#333','stroke-width':2,'stroke-dasharray':'5 4'}));}
  for(const n of draft.instances){const c=byId.get(n.component_id);const group=svg('g',{transform:`translate(${n.x},${n.y})`,tabindex:0,role:'button','aria-label':`${label(c)}, select part`,class:`instance${selected===n.id?' selected':''}`,'data-instance':n.id});group.append(svg('rect',{x:-42,y:-40,width:84,height:80,fill:'#fff',stroke:'#aaa',rx:4}));group.append(svg('image',{href:preview(c),x:-30,y:-33,width:60,height:56}));const title=svg('text',{x:0,y:32,'text-anchor':'middle','font-size':8,fill:'#111'});title.textContent=label(c).slice(0,20);group.append(title);group.addEventListener('click',()=>choose(n.id));group.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose(n.id);}});canvas.append(group);}
}
function move(dx,dy){const n=draft.instances.find(n=>n.id===selected);if(!n){say('Select a part first.');return;}n.x=Math.max(48,Math.min(952,n.x+dx));n.y=Math.max(75,Math.min(510,n.y+dy));renderCanvas();say('Part moved.');}
function remove(){if(!selected)return;draft.instances=draft.instances.filter(n=>n.id!==selected);draft.connections=draft.connections.filter(e=>e.from!==selected&&e.to!==selected);selected=null;start=null;renderCanvas();say('Selected part and its links removed.');}
function validateDraft(value){
  if(!value||typeof value!=='object'||value.schema_version!=='sld-educational-draft/1'||value.educational_only!==true)throw Error('Expected an SLD educational draft, version 1.');
  if(!Array.isArray(value.instances)||value.instances.length>200||!Array.isArray(value.connections)||value.connections.length>400)throw Error('Invalid draft size.');
  const ids=new Set();const instances=value.instances.map(n=>{if(!n||typeof n.id!=='string'||!/^[a-zA-Z0-9_-]{1,80}$/.test(n.id)||ids.has(n.id)||!byId.has(n.component_id)||!Number.isFinite(n.x)||!Number.isFinite(n.y)||n.x<48||n.x>952||n.y<75||n.y>510)throw Error('Invalid or duplicate part, component or position.');ids.add(n.id);return{id:n.id,component_id:n.component_id,x:n.x,y:n.y};});
  const pairs=new Set();const connections=value.connections.map(e=>{if(!e||!ids.has(e.from)||!ids.has(e.to)||e.from===e.to||e.kind!=='illustrative-centre-link')throw Error('Invalid connection.');const pair=[e.from,e.to].sort().join('|');if(pairs.has(pair))throw Error('Duplicate connection.');pairs.add(pair);return{from:e.from,to:e.to,kind:e.kind};});
  return{schema_version:'sld-educational-draft/1',educational_only:true,instances,connections};
}
function download(data,name,type){const url=URL.createObjectURL(new Blob([data],{type}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
async function exportSVG(){
  const copy=$('canvas').cloneNode(true);copy.setAttribute('xmlns',NS);copy.setAttribute('width','1000');copy.setAttribute('height','560');
  for(const img of copy.querySelectorAll('image')){const url=new URL(img.getAttribute('href'),location.href);if(url.origin!==location.origin)throw Error('External preview rejected.');const response=await fetch(url);if(!response.ok)throw Error('Preview unavailable.');const bytes=new Uint8Array(await response.arrayBuffer());let binary='';for(const b of bytes)binary+=String.fromCharCode(b);img.setAttribute('href','data:image/svg+xml;base64,'+btoa(binary));}
  copy.querySelectorAll('[tabindex]').forEach(e=>{e.removeAttribute('tabindex');e.removeAttribute('role');e.removeAttribute('class');});download(new XMLSerializer().serializeToString(copy),'sld-educational-draft.svg','image/svg+xml');say('Exported a self-contained educational SVG.');
}
$('search').addEventListener('input',renderCards);
$('connect').addEventListener('click',()=>{connecting=!connecting;start=null;$('connect').setAttribute('aria-pressed',String(connecting));say(connecting?'Select two parts. Links are illustrative, not electrical terminals.':'Selection mode.');});
for(const [id,dx,dy] of [['move-left',-10,0],['move-up',0,-10],['move-down',0,10],['move-right',10,0]])$(id).addEventListener('click',()=>move(dx,dy));
$('delete').addEventListener('click',remove);
$('clear').addEventListener('click',()=>{draft.instances=[];draft.connections=[];selected=null;start=null;renderCanvas();say('Draft cleared.');});
$('export').addEventListener('click',()=>{download(JSON.stringify(draft,null,2),'sld-educational-draft.json','application/json');say('Exported educational draft JSON.');});
$('export-svg').addEventListener('click',()=>exportSVG().catch(e=>say(`Export failed: ${e.message}`)));
$('import').addEventListener('change',async e=>{try{const file=e.target.files[0];if(!file)return;if(file.size>1_000_000)throw Error('Maximum file size is 1 MB.');draft=validateDraft(JSON.parse(await file.text()));selected=null;start=null;renderCanvas();say(`Imported ${draft.instances.length} parts. Unknown extra fields were discarded.`);}catch(err){say(`Import rejected: ${err.message}`);}finally{e.target.value='';}});
document.addEventListener('keydown',e=>{if(['INPUT','TEXTAREA','SELECT','BUTTON'].includes(e.target.tagName)||e.target.isContentEditable)return;const offsets={ArrowLeft:[-10,0],ArrowRight:[10,0],ArrowUp:[0,-10],ArrowDown:[0,10]};if(offsets[e.key]&&selected){e.preventDefault();move(...offsets[e.key]);}if(e.key==='Delete')remove();});
fetch('data/library.json').then(r=>{if(!r.ok)throw Error('Library request failed.');return r.json();}).then(data=>{components=data.components||data.symbols||[];if(!components.length)throw Error('Library contains no components.');byId=new Map(components.map(c=>[key(c),c]));renderCards();renderCanvas();}).catch(e=>{$('count').textContent='Library unavailable';say(`${e.message} Please try again later.`);});

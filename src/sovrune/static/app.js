const fallback=[
  {office:'Signal',status:'complete',summary:'Company state assembled from sourced evidence.'},
  {office:'Strategy',status:'complete',summary:'Proposal conversion is the binding constraint.'},
  {office:'Opportunity',status:'complete',summary:'A 6-point conversion gap is the highest leverage.'},
  {office:'Product',status:'complete',summary:'Test a reliable 48-hour follow-up workflow.'},
  {office:'Engineering',status:'waiting',summary:'Implementation awaits an isolated branch.'},
  {office:'Approval',status:'human',summary:'External writes require a human.'},
  {office:'Outcome',status:'scheduled',summary:'Measurement window is scheduled.'}
];
const box=document.querySelector('#loopNodes');
function paint(steps){box.innerHTML=steps.map((s,i)=>`<div class="node ${i===0?'active':''}" data-i="${i}"><span class="pulse"></span><strong>${s.office}</strong><b>${s.status}</b><p>${s.summary}</p></div>`).join('');let n=0;const reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;if(reduce){document.querySelectorAll('.node').forEach(x=>x.classList.add('complete'));return}setInterval(()=>{const nodes=[...document.querySelectorAll('.node')];nodes.forEach((x,i)=>{x.classList.toggle('active',i===n);x.classList.toggle('complete',i<n)});n=(n+1)%nodes.length},1250)}
fetch('/api/loop').then(r=>r.json()).then(x=>paint(x.steps)).catch(()=>paint(fallback));
document.querySelector('#copy').addEventListener('click',async e=>{await navigator.clipboard.writeText('git clone https://github.com/Sovrune/sovrune\ncd sovrune\ndocker compose up --build');e.target.textContent='Copied'});

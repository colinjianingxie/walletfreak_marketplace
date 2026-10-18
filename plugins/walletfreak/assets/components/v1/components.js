'use strict';
// Shared by the public gallery and the offline local dashboard. No requests or code evaluation.
(() => {
  const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const text=(value)=>typeof value==='string'&&value.trim()&&value.length<=120;
  function exact(object,keys){return object&&typeof object==='object'&&!Array.isArray(object)&&Object.keys(object).length===keys.length&&keys.every(k=>Object.hasOwn(object,k));}
  function validate(layout,catalog){
    if(!exact(layout,['version','title','theme','density','blocks'])||layout.version!==1||!text(layout.title)||!catalog.themes.includes(layout.theme)||!catalog.densities.includes(layout.density)||!Array.isArray(layout.blocks)||!layout.blocks.length||layout.blocks.length>12)throw new Error('Invalid or unsupported dashboard layout.');
    const ids=new Set();
    for(const b of layout.blocks){
      const component=catalog.components.find(c=>c.id===b?.component);
      if(!exact(b,['id','component','source','title'])||!text(b.title)||typeof b.id!=='string'||!/^[a-z][a-z0-9-]{0,39}$/.test(b.id)||ids.has(b.id)||!component?.sources.includes(b.source))throw new Error('Unknown component, duplicate ID or invalid source.');
      ids.add(b.id);
    }
    return layout;
  }
  const value=(row,key)=>`${key==='balance'&&row.approximate?'≈ ':''}${esc(row[key]===null||row[key]===undefined||row[key]===''?'—':row[key])}`;
  const columns={
    'wallet.cards':[['name','Card'],['owner','Owner'],['notes','Details'],['reported_on','Reported']],
    'wallet.programs':[['name','Program'],['balance','Balance'],['status','Status'],['notes','Notes'],['reported_on','Reported']],
    'wallet.benefits':[['name','Benefit'],['remaining','Remaining'],['expires_on','Expires'],['notes','Restrictions']]
  };
  function sources(item,data){const files=data['spending.references']||[];const names=(item.source_ids||[]).map(id=>files.find(f=>f.id===id)?.name).filter(Boolean);return names.length?`<small class="wf-source">Source: ${names.map(esc).join(' · ')}</small>`:'';}
  function payment(p){if(!p)return '<small>Payment card: to confirm</small>';return `<small>Pay with <strong>${esc(p.card)}</strong> · ${esc(p.reason)}</small>${(p.benefits||[]).map(b=>`<small>${esc(b.name)} · ${esc(b.status)} · ${esc(b.detail)}</small>`).join('')}`;}
  function componentHtml(block,data){
    const all=data[block.source]||[],rows=all.slice(0,100);
    if(!rows.length)return '<p class="wf-empty">Nothing here yet. Add wallet entries or ask your agent to publish findings.</p>';
    let html='';
    if(block.component==='metric-cards')html=`<div class="wf-metrics">${rows.map(r=>`<article><small>${esc(r.label)}</small><strong>${esc(r.value)}</strong><p>${esc(r.detail)}</p>${sources(r,data)}</article>`).join('')}</div>`;
    if(block.component==='findings')html=rows.map(r=>`<article class="wf-finding"><strong>${esc(r.label)}</strong><p>${esc(r.detail)}</p>${sources(r,data)}</article>`).join('');
    if(block.component==='reference-list')html=rows.map(r=>`<article class="wf-reference"><span class="wf-file">${esc(r.name?.split('.').pop()?.toUpperCase()||'FILE')}</span><div><strong>${esc(r.name)}</strong><small>${r.available===false?'File missing':'Local reference'}${Number.isFinite(r.bytes)?' · '+Math.ceil(r.bytes/1024)+' KB':''}</small></div></article>`).join('');
    if(block.component==='itinerary')html=`<ol class="wf-itinerary">${rows.map(r=>`<li><small>${esc(r.trip)} · ${esc(r.when)}</small><strong>${esc(r.title)}</strong><p>${esc(r.detail)}</p>${payment(r.payment)}</li>`).join('')}</ol>`;
    if(block.component==='data-table') {
      const cols=columns[block.source];
      html=`<div class="wf-table-scroll"><table><caption class="wf-sr-only">${esc(block.title)}</caption><thead><tr>${cols.map(([,label])=>`<th scope="col">${label}</th>`).join('')}</tr></thead><tbody>${rows.map(r=>`<tr>${cols.map(([key])=>`<td>${value(r,key)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
      html+=`<div class="wf-records">${rows.map(r=>`<article class="wf-record"><h4>${value(r,cols[0][0])}</h4><dl>${cols.slice(1).map(([key,label])=>`<div><dt>${label}</dt><dd>${value(r,key)}</dd></div>`).join('')}</dl></article>`).join('')}</div>`;
    }
    return html+(all.length>100?'<p class="wf-empty">Showing the first 100 entries. Open the full workspace view for more.</p>':'');
  }
  function render(target,layout,catalog,data){
    validate(layout,catalog);
    target.classList.add('wf-dashboard');target.dataset.theme=layout.theme;target.dataset.density=layout.density;
    target.innerHTML=`<h2 class="wf-title">${esc(layout.title)}</h2>${layout.blocks.map(b=>`<section class="wf-block" data-component="${esc(b.component)}" data-block="${esc(b.id)}"><h3>${esc(b.title)}</h3>${componentHtml(b,data)}</section>`).join('')}`;
  }
  window.WalletFreakComponents=Object.freeze({validate,render});
})();

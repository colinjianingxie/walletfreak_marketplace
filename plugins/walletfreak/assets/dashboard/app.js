'use strict';
const $ = selector => document.querySelector(selector);
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let state, activeId = '', brands = {}, cards = [], draft, draftRevision, dirty = false, stopped = false, assetCatalog = [], vaultState, pluginInventory, currentTab = 'wallet';
function notice(message, error = false) { $('#notice').textContent = message; $('#notice').className = error ? 'error' : ''; }
async function api(path, body) {
  const response = await fetch('/api/' + path, body === undefined ? {} : {method:'POST', headers:{'Content-Type':'application/json','X-WalletFreak':'1'}, body:JSON.stringify(body)});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Request failed.');
  return data;
}
async function act(path, body) {
  try { const result = await api(path, body); if (result.message) notice(result.message); await refresh(); return result; }
  catch (error) { notice(error.message, true); await refresh(); return null; }
}
function tab(name) { currentTab = name; if (name === 'spending') window.loadSpending(); if (name === 'plugins') loadPlugins(); if (name === 'credentials') refreshVault(); for (const item of document.querySelectorAll('[data-tab]')) item.setAttribute('aria-pressed', String(item.dataset.tab === name)); for (const panel of document.querySelectorAll('.panel')) panel.hidden = panel.id !== name; }
document.querySelectorAll('[data-tab]').forEach(button => button.addEventListener('click', () => tab(button.dataset.tab)));
$('#open-wallet').onclick = () => tab('wallet');
function trip() { return state?.trips.find(t => t.id === activeId); }
function logo(name) {
  if (typeof name !== 'string') return '';
  const aliases={'amex membership rewards':'amex-travel','chase ultimate rewards':'chase-travel','capital one miles':'capital-one-travel'};
  const match = aliases[name.toLowerCase()] || name.split('·')[0].trim().toLowerCase();
  const provider = state?.providers.find(p => p.id === match || p.name.toLowerCase() === match || p.programs.some(program => program.toLowerCase() === match || (p.name + ' ' + program).toLowerCase() === match || (program + ' points').toLowerCase() === match));
  const asset = brands[provider?.id];
  return asset?.path ? `<img src="/assets/${esc(asset.path)}" alt="">` : '';
}
function sourceLinks(sources = []) { return sources.map(source => `<a href="${esc(source.url)}" target="_blank" rel="noopener noreferrer">${esc(source.label)} ↗</a>`).join(' · '); }
function paymentView(option) {
  const p=option?.payment;
  if(!p)return '<div class="payment"><strong>Payment card: To confirm</strong><p>No benefit usage recorded.</p></div>';
  const labels={'planned':'Planned · not spent','used':'Already used','not-used':'Not used','conditional':'Conditional','unavailable':'Unavailable'};
  return `<div class="payment"><strong>Pay with: ${esc(p.card)}</strong><p>${esc(p.reason)}</p>${p.benefits?.length?`<ul>${p.benefits.map(b=>`<li><span class="benefit-state ${esc(b.status)}">${labels[b.status]}</span> <strong>${esc(b.name)}</strong> — ${esc(b.detail)}${b.recorded_at?` <small>Recorded ${esc(b.recorded_at)}</small>`:''}</li>`).join('')}</ul>`:'<p>No benefit usage recorded.</p>'}</div>`;
}
function itineraryItem(item, option) {
  const kind = option?.kind || 'other';
  const names = {flight:'Flight', hotel:'Stay', transport:'Getting around', lounge:'Lounge', other:'Plan'};
  return `<li class="itinerary-item ${kind}"><div class="itinerary-label">${names[kind]}<small>${esc(item.when || 'Schedule to confirm')}</small></div><article><div class="provider">${logo(option?.provider)}${esc(option?.provider || '')}</div><h4>${esc(item.title)}</h4><p>${esc(item.detail || option?.product || '')}</p>${option ? `<p class="price">${esc(option.price || 'Price unknown')}</p><span class="status ${esc(option.status)}">${esc(option.status)} at observation</span><p class="muted">${esc(option.terms || 'Confirm terms before booking.')}</p>${paymentView(option)}${sourceLinks(option.sources)}` : ''}</article></li>`;
}
function renderFindings() {
  const t = trip();
  $('#empty-results').hidden = !!t; $('#result-content').hidden = !t;
  if (!t) return;
  const f = t.findings;
  $('#brief').innerHTML = `<div class="brief"><h3>${esc(f.title)}</h3><p>${esc(f.summary || '')}</p><p class="muted">Research recorded ${esc(f.generated_at)}${f.illustrative ? ' · FICTIONAL DEMO — not live quotes' : ''}</p></div>`;
  const byId = new Map((f.options || []).map(o => [o.id, o]));
  const itinerary = f.itinerary || [];
  const linked = new Set(itinerary.map(i => i.option_id));
  $('#itinerary').innerHTML = itinerary.map(i => itineraryItem(i, byId.get(i.option_id))).join('') + t.selected.filter(id => !linked.has(id)).map(id => { const o = byId.get(id); return itineraryItem({title:o.title, when:'Your proposed selection', detail:o.product}, o); }).join('');
  if (!$('#itinerary').children.length) $('#itinerary').innerHTML = '<li class="muted">No itinerary supplied with these findings. Select options below to build a local comparison.</li>';
  const words = $('#search').value.toLowerCase().trim().split(/\s+/).filter(Boolean);
  const options = (f.options || []).filter(o => words.every(w=>JSON.stringify(o).toLowerCase().includes(w)) && (!$('#kind').value || o.kind === $('#kind').value) && (!$('#availability').value || o.status === $('#availability').value) && (!$('#shortlisted').checked || t.shortlist.includes(o.id)));
  $('#count').textContent = `${options.length} of ${(f.options || []).length} options · ${t.shortlist.length} shortlisted`;
  $('#options').innerHTML = options.length ? options.map(o => `<article class="option"><div class="provider">${logo(o.provider)}<span>${esc(o.provider)} · ${esc(o.kind)}</span></div><h3>${esc(o.title)}</h3><span class="status ${esc(o.status)}">${esc(o.status)} at observation</span><p class="price">${esc(o.price || 'Price unknown')}</p><p class="muted">${esc(o.program)} · Observed ${esc(o.observed_at || 'not recorded')}</p>${paymentView(o)}<label class="check"><input type="checkbox" data-shortlist="${esc(o.id)}" ${t.shortlist.includes(o.id)?'checked':''}> Add to shortlist</label><label class="check"><input type="checkbox" data-select="${esc(o.id)}" ${t.selected.includes(o.id)?'checked':''}> Include in my comparison</label><details><summary>Evidence & restrictions</summary><dl>${['search','product','terms','benefits','uncertainty','reproduce'].map(key=>`<dt>${esc(key)}</dt><dd>${esc(o[key] || 'Not recorded')}</dd>`).join('')}</dl>${sourceLinks(o.sources)}</details></article>`).join('') : '<p class="muted">No matching findings.</p>';
  const shortlisted = (f.options || []).filter(o=>t.shortlist.includes(o.id));
  $('#comparison').innerHTML = shortlisted.length ? `<table><thead><tr><th scope="col">Compare</th>${shortlisted.map(o=>`<th scope="col">${esc(o.title)}</th>`).join('')}</tr></thead><tbody>${['provider','price','status','payment','product','terms','benefits','uncertainty'].map(key=>`<tr><th scope="row">${esc(key==='payment'?'Card & benefits':key)}</th>${shortlisted.map(o=>`<td>${key==='payment'?paymentView(o):esc(o[key] || 'Not recorded')}</td>`).join('')}</tr>`).join('')}</tbody></table>` : '<p class="muted">Shortlist options to compare their prices, terms and benefits here.</p>';
  const totals = [...Object.entries(t.totals.cash).map(([c,v])=>`${c} ${v}`), ...Object.entries(t.totals.points).map(([p,v])=>`${v.toLocaleString()} ${p} points`)];
  $('#totals').innerHTML = `<strong>Selected items only: ${esc(totals.join(' + ') || 'No verified costs selected')}</strong><p>Partial subtotal, not a whole-trip price. Points programs and cash currencies remain separate. Conditional credits are excluded.</p>${t.totals.unknown.length ? `<p>Unpriced or unverified selections: ${esc(t.totals.unknown.join('; '))}</p>` : ''}`;
  $('#evidence').innerHTML = (f.research || []).map(i=>`<article><h4>${esc(i.title)}</h4><p>${esc(i.detail)}</p>${i.url ? sourceLinks([{label:'Official source',url:i.url}]) : ''}</article>`).join('');
  $('#gaps').innerHTML = (f.gaps || []).map(g=>`<li>${esc(g)}</li>`).join('');
}
function walletImage(section, row) {
  if (section !== 'cards') return logo(assetCatalog.find(a=>a.name===row.name)?.provider || row.name);
  const alias = {'capital one venture x;':'capital-one-venture-x-rewards-credit-card','american express platinum;':'american-express-platinum-card','hilton honors american express aspire':'hilton-honors-aspire-card-from-american-express'};
  const name=row.name.toLowerCase();
  const card = cards.find(c => c.name.toLowerCase() === name) || cards.find(c=>c.id === alias[Object.keys(alias).find(k=>name.startsWith(k))]);
  return card ? `<img class="card-art" src="/assets${esc(card.path)}" alt="${esc(card.name)} artwork">` : '<span class="card-placeholder" aria-hidden="true">▰</span>';
}
const assetKinds = {'credit':'Card credit / offer','certificate':'Free-night certificate','gift-card':'Gift card','travel-bank':'TravelBank / stored funds','travel-credit':'Airline / trip credit','companion':'Companion certificate','upgrade':'Upgrade award','lounge-pass':'Lounge visits / passes','membership':'Membership','voucher':'Voucher / award','cashback':'Cash-back balance','other':'Other asset'};
const columns = {
  cards: [['name','Card name'],['owner','Owner alias'],['reported_on','Reported on','date'],['notes','Card details','textarea']],
  programs: [['name','Loyalty program'],['balance','Points / miles'],['approximate','Approx.','checkbox'],['status','Elite status'],['preserve','Preserve','checkbox'],['owner','Owner alias'],['reported_on','Reported on','date'],['notes','Notes','textarea']],
  benefits: [['kind','Type','select'],['name','Asset name'],['remaining','Remaining / currency'],['owner','Owner alias'],['expires_on','Expires on','date'],['reported_on','Reported on','date'],['notes','Restrictions / period','textarea']]
};
function cell(section, index, row, [key,label,type='text']) {
  const attrs = `data-field="${key}" aria-label="${label} ${index+1}"`;
  if (type === 'textarea') return `<textarea ${attrs} maxlength="4000" rows="1">${esc(row[key] || '')}</textarea>`;
  if (type === 'select') return `<select ${attrs}>${Object.entries(assetKinds).map(([id,name])=>`<option value="${id}" ${row[key]===id?'selected':''}>${name}</option>`).join('')}</select>`;
  let extra = key === 'name' ? `required list="${section==='cards'?'card-names':section==='programs'?'program-names':'asset-names'}"` : '';
  if (key === 'balance') extra = 'inputmode="numeric" pattern="[0-9]{1,13}" maxlength="13"';
  return `<input ${attrs} type="${type}" ${type==='checkbox' ? (row[key]?'checked':'') : `value="${esc(row[key] || '')}"`} ${extra} ${type==='text'&&key!=='balance'?'maxlength="300"':''}>`;
}
function renderWallet() {
  for (const section of ['cards','programs','benefits']) {
    const cols=columns[section];
    $(`#wallet-${section}`).innerHTML = `<table class="wallet-sheet"><thead><tr><th scope="col">#</th><th scope="col">${section==='cards'?'Card':'Program'}</th>${cols.map(c=>`<th scope="col">${c[1]}</th>`).join('')}<th scope="col">Remove</th></tr></thead><tbody>${draft[section].map((row,index)=>`<tr data-section="${section}" data-index="${index}"><th scope="row">${index+1}</th><td class="wallet-image provider">${walletImage(section,row)}</td>${cols.map(c=>`<td>${cell(section,index,row,c)}</td>`).join('')}<td><button type="button" data-remove="${section}" data-index="${index}" class="quiet danger" aria-label="Remove ${section==='cards'?'card':section==='programs'?'program':'asset'} ${index+1}">×</button></td></tr>`).join('')}</tbody></table>${draft[section].length?'':`<p class="muted empty-sheet">No ${section==='programs'?'loyalty programs':section==='benefits'?'assets':section} added yet.</p>`}`;
  }
  $('#wallet-preferences').value = draft.preferences;
  filterWallet();walletStatus();
}
function filterWallet() {
  const words=$('#wallet-search').value.toLowerCase().trim().split(/\s+/).filter(Boolean);
  document.querySelectorAll('tr[data-section]').forEach(row=>{row.hidden=!words.every(word=>JSON.stringify(draft[row.dataset.section][Number(row.dataset.index)]).toLowerCase().includes(word));});
}
$('#wallet-search').oninput=filterWallet;
function walletStatus() {
  $('#wallet-status').textContent = dirty ? 'Unsaved changes' : 'Your saved wallet is up to date on this device.';
  $('#wallet-conflict').hidden = !dirty || state.wallet.revision === draftRevision;
  $('#legacy-profile').hidden = !state.legacy_profile || state.wallet.revision !== 'empty';
}
function loadWallet() {
  draft = structuredClone(state.wallet); draftRevision = draft.revision;
  delete draft.version; delete draft.revision; for(const row of draft.programs) row.notes ??= ''; dirty = false; renderWallet();
}
async function refresh() {
  if (stopped) return;
  try {
    const next = await api('state');
    const resultChanged = !state || JSON.stringify(state.trips) !== JSON.stringify(next.trips);
    state = next;
    $('#wallet-summary').innerHTML = `<span><strong>${state.wallet.cards.length}</strong> cards</span><span><strong>${state.wallet.programs.length}</strong> points programs</span><span><strong>${state.wallet.benefits.length}</strong> credits & assets</span><span><strong>${state.trips.length}</strong> itineraries</span>`;
    if (resultChanged) {
      if (!state.trips.some(t=>t.id===activeId)) activeId = state.trips[0]?.id || '';
      $('#trip-select').innerHTML = state.trips.length ? state.trips.map(t=>`<option value="${t.id}">${esc(t.findings.title)}</option>`).join('') : '<option value="">No saved results</option>';
      $('#trip-select').value = activeId; renderFindings();
    }
    if (!draft || (!dirty && draftRevision !== state.wallet.revision)) loadWallet(); else walletStatus();
    if(currentTab==='credentials') await refreshVault();
  } catch(error) { notice(error.message, true); }
}
$('#wallet-form').addEventListener('input', event => {
  const entry = event.target.closest('[data-section]');
  if (entry && event.target.dataset.field) {
    const row = draft[entry.dataset.section][Number(entry.dataset.index)];
    row[event.target.dataset.field] = event.target.type === 'checkbox' ? event.target.checked : event.target.value;
    if (event.target.dataset.field === 'name') {
      entry.querySelector('.wallet-image').innerHTML = walletImage(entry.dataset.section,row);
      if(entry.dataset.section==='benefits') { const template=assetCatalog.find(a=>a.name===row.name);if(template){row.kind=template.kind;entry.querySelector('[data-field=kind]').value=template.kind;} }
    }
  } else if (event.target.id === 'wallet-preferences') draft.preferences = event.target.value;
  dirty = true; walletStatus();
});
$('#wallet-form').addEventListener('click', event => {
  const button = event.target.closest('button');
  if (button?.dataset.add) {
    const section = button.dataset.add;
    const common = {name:'',owner:'',reported_on:''};
    draft[section].push(section === 'cards' ? {...common,notes:''} : section === 'programs' ? {...common,balance:'',status:'',approximate:false,preserve:false,notes:''} : {...common,kind:'credit',remaining:'',expires_on:'',notes:''});
    dirty = true; renderWallet(); $(`#wallet-${section} tbody tr:last-child [data-field=name]`).focus();
  } else if (button?.dataset.remove) {
    draft[button.dataset.remove].splice(Number(button.dataset.index),1); dirty = true; renderWallet();
  }
});
$('#wallet-form').addEventListener('keydown', event=>{
  if(event.key!=='Enter' || event.target.tagName==='TEXTAREA' || !event.target.dataset.field) return;
  event.preventDefault();const row=event.target.closest('tr'), table=row.closest('tbody');
  const rows=[...table.querySelectorAll('tr')].filter(r=>!r.hidden), index=rows.indexOf(row)+(event.shiftKey?-1:1);
  rows[index]?.querySelector(`[data-field="${event.target.dataset.field}"]`)?.focus();
});
$('#import-profile').onclick=async()=>{if(dirty&&!confirm('Discard unsaved edits and load the existing profile into this empty wallet?'))return;if(await act('import-profile',{expected_revision:draftRevision}))loadWallet();};
$('#wallet-form').onsubmit = async event => {
  event.preventDefault();
  const button = event.submitter; button.disabled = true;
  const sent = JSON.stringify(draft);
  try {
    const result = await api('wallet',{wallet:JSON.parse(sent),expected_revision:draftRevision});
    state.wallet = result.wallet;
    if (JSON.stringify(draft) === sent) loadWallet();
    else { draftRevision = result.wallet.revision; walletStatus(); }
    notice(result.message);
  } catch(error) { notice(error.message,true); await refresh(); }
  button.disabled = false;
};
$('#reload-wallet').onclick = () => { if (!dirty || confirm('Discard unsaved wallet edits and reload the saved wallet?')) loadWallet(); };
$('#delete-wallet').onclick = async () => {
  if (!confirm('Delete your saved personal wallet and discard unsaved wallet edits? Trip results and downloaded files will stay.')) return;
  if (await act('delete-wallet',{expected_revision:draftRevision})) loadWallet();
};
$('#trip-select').onchange = event => { activeId = event.target.value; renderFindings(); };
for (const id of ['search','kind','availability','shortlisted']) $('#'+id).addEventListener('input', renderFindings);
$('#options').addEventListener('change', async event => {
  const t = trip(), target = event.target, key = target.dataset.shortlist ? 'shortlist' : 'selected', id = target.dataset.shortlist || target.dataset.select;
  if (!t || !id) return;
  const body = {id:t.id,shortlist:[...t.shortlist],selected:[...t.selected],expected_revision:t.selection_revision};
  body[key] = target.checked ? [...body[key],id] : body[key].filter(i=>i!==id);
  await act('selection',body); renderFindings();
});
$('#export').onclick = () => { if (trip()) location.href = '/api/export/' + trip().id; };
$('#delete-results').onclick = async () => {
  const t = trip();
  if (t && confirm(`Delete “${t.findings.title}” from this device? Your wallet and downloaded copies will stay.`)) await act('delete-results',{id:t.id,expected_revision:t.revision});
};
$('#stop').onclick = async () => {
  if (!confirm('Close the local server? Saved results and your wallet stay on this device. Unsaved wallet edits will be lost.')) return;
  try { const result = await api('stop',{}); stopped = true; notice(result.message); } catch(error) { notice(error.message,true); }
};
window.addEventListener('beforeunload', event => { if (dirty && !stopped) { event.preventDefault(); event.returnValue = ''; } });
(async () => {
  try {
    const token = new URLSearchParams(location.hash.slice(1)).get('key');
    if (token) { await api('session',{token}); history.replaceState(null,'',location.pathname); }
    const loaded = await Promise.all(['/assets/brands.json','/assets/cards.json','/assets/wallet-assets.json'].map(path=>fetch(path).then(r=>r.json())));
    [brands,cards] = loaded; assetCatalog=loaded[2].items;
    $('#asset-names').innerHTML=assetCatalog.map(a=>`<option value="${esc(a.name)}"></option>`).join('');
    $('#asset-catalog').innerHTML=assetCatalog.map(a=>`<p><a href="${esc(a.url)}" target="_blank" rel="noopener noreferrer">${esc(a.name)} ↗</a> <span class="muted">${esc(a.note)}</span></p>`).join('');
    $('#card-names').innerHTML = cards.map(c=>`<option value="${esc(c.name)}"></option>`).join('');
    await refresh();
    $('#program-names').innerHTML = (state?.providers || []).flatMap(p=>p.programs).map(p=>`<option value="${esc(p)}"></option>`).join('');
    $('#provider-names').innerHTML=(state?.providers || []).map(p=>`<option value="${esc(p.name)}"></option>`).join('');
    setInterval(refresh,3000);
  } catch(error) { notice(error.message,true); }
})();

async function refreshVault() {
  try {const next=await api('vault');const changed=JSON.stringify(next)!==JSON.stringify(vaultState);vaultState=next;if(changed)renderVault();}catch(error){$('#vault-status').textContent=error.message;}
}
function renderVault() {
  const v=vaultState;
  $('#vault-status').textContent=!v.supported?'Vault dependency unavailable. Ask setup to install requirements-vault.txt.':v.unlocked?'Unlocked in this browser. Passwords are never shown or exported.':v.exists?'Vault locked.':'Create a master password to save sign-ins for any provider.';
  $('#vault-unlock').hidden=v.unlocked || !v.supported;$('#vault-open').hidden=!v.unlocked;$('#lock-vault').hidden=!v.unlocked;
  $('#unlock-vault').textContent=v.exists?'Unlock vault':'Create vault';
  if(!v.unlocked){$('#credential-form').reset();$('#credential-id').value='';return;}
  $('#vault-list').innerHTML=`<table><thead><tr><th>Provider</th><th>Label</th><th>Username</th><th>Password</th><th>Actions</th></tr></thead><tbody>${v.entries.map(e=>`<tr><td>${esc(e.provider)}</td><td>${esc(e.label)}</td><td>${esc(e.username)}</td><td>••••••••</td><td><button data-edit-credential="${e.id}" type="button">Replace</button> <button data-delete-credential="${e.id}" type="button">Delete</button></td></tr>`).join('')}</tbody></table>`;
}
$('#vault-unlock').onsubmit=async event=>{
  event.preventDefault();const password=$('#master-password').value;$('#master-password').value='';event.submitter.disabled=true;
  try{vaultState=await api('vault/'+(vaultState.exists?'unlock':'create'),{master_password:password});renderVault();}catch(error){$('#vault-status').textContent=error.message;}finally{event.submitter.disabled=false;}
};
$('#lock-vault').onclick=async()=>{try{vaultState=await api('vault/lock',{});renderVault();}catch(error){notice(error.message,true);}};
$('#credential-form').onsubmit=async event=>{
  event.preventDefault();event.submitter.disabled=true;
  const body={provider:$('#credential-provider').value,label:$('#credential-label').value,username:$('#credential-username').value,password:$('#credential-password').value,expected_revision:vaultState.revision};
  if($('#credential-id').value)body.id=$('#credential-id').value;
  $('#credential-password').value='';
  try{vaultState=await api('vault/save',body);$('#credential-form').reset();$('#credential-id').value='';renderVault();$('#vault-status').textContent='Sign-in saved in the encrypted vault.';}catch(error){$('#vault-status').textContent=error.message;}finally{event.submitter.disabled=false;}
};
$('#new-credential').onclick=()=>{$('#credential-form').reset();$('#credential-id').value='';};
$('#vault-list').onclick=async event=>{
  const button=event.target.closest('button');if(!button)return;
  const id=button.dataset.editCredential || button.dataset.deleteCredential;
  if(button.dataset.editCredential){const e=vaultState.entries.find(e=>e.id===id);for(const key of ['id','provider','label','username'])$('#credential-'+key).value=e[key];$('#credential-password').value='';$('#credential-password').focus();}
  else if(confirm('Delete this saved sign-in? The provider account will stay unchanged.')){try{vaultState=await api('vault/delete',{id,expected_revision:vaultState.revision});renderVault();}catch(error){$('#vault-status').textContent=error.message;}}
};
async function loadPlugins(){$('#plugin-note').textContent='Loading installed plugins…';try{pluginInventory=await api('plugins');renderPlugins();}catch(error){$('#plugin-note').textContent=error.message;}}
function renderPlugins(){
  if(!pluginInventory)return;const words=$('#skill-search').value.toLowerCase().trim().split(/\s+/).filter(Boolean);$('#plugin-note').textContent=pluginInventory.note;
  $('#plugin-list').innerHTML=pluginInventory.plugins.map(p=>{const skills=p.skills.filter(s=>words.every(w=>(p.name+' '+s.name+' '+s.description).toLowerCase().includes(w)));if(!skills.length&&words.length)return '';return `<section class="plugin"><div class="plugin-heading"><span class="plugin-symbol">${p.name==='walletfreak'?'<img src="/assets/mascot.png" alt="">':esc(p.name.slice(0,2).toUpperCase())}</span><div><h3>${esc(p.name)}</h3><small>${esc(p.version)} · ${p.enabled?'Enabled':'Disabled'} · ${p.skills.length} skills</small></div></div><div class="skill-grid">${skills.map(s=>`<details class="skill"><summary><strong>${esc(s.name)}</strong><span>${esc(s.description)}</span></summary><pre>${esc(s.content)}</pre></details>`).join('')}</div></section>`;}).join('');
}
$('#skill-search').oninput=renderPlugins;

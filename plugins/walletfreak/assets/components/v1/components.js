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
    'wallet.programs':[['owner','Person'],['account_label','Account'],['name','Program'],['balance','Balance'],['status','Status'],['notes','Notes'],['reported_on','Reported']],
    'wallet.benefits':[['name','Benefit'],['remaining','Remaining'],['expires_on','Expires'],['notes','Restrictions']]
  };
  function sources(item,data){const files=data['spending.references']||[];const names=(item.source_ids||[]).map(id=>files.find(f=>f.id===id)?.name).filter(Boolean);return names.length?`<small class="wf-source">Source: ${names.map(esc).join(' · ')}</small>`:'';}
  function paymentSummary(p){return p?`Pay with ${esc(p.card)}${p.benefits?.length?' · '+p.benefits.map(b=>esc(b.name)+': '+esc(b.status)).join(' · '):' · Benefits not recorded'}`:'Payment card: to confirm';}
  function payment(p){return p?`<p>${esc(p.reason)}</p>${(p.benefits||[]).map(b=>`<p>${esc(b.name)} · ${esc(b.status)} — ${esc(b.detail)}${b.recorded_at?' · Recorded '+esc(b.recorded_at):''}</p>`).join('')}`:'';}
  function stayLabel(r){if(!r.stay)return '';const n=(Date.parse(r.stay.check_out)-Date.parse(r.stay.check_in))/86400000;return `${esc(r.stay.check_in)} → ${esc(r.stay.check_out)} · ${Number.isFinite(n)?n:'?'} nights`;}
  function safeLink(url,label){try{const u=new URL(url);return u.protocol==='https:'&&!u.username&&!u.password?`<a href="${esc(u.href)}" target="_blank" rel="noopener noreferrer">${esc(label)} ↗</a>`:'';}catch{return '';}}
  function routeWarnings(rows){
    const warnings=[];let previous;
    for(const r of rows){
      if(r.stay){if(previous&&previous.trip===r.trip){if(r.stay.check_in<previous.stay.check_out)warnings.push('Overlapping stays: '+previous.title+' and '+r.title);else if(r.stay.check_in>previous.stay.check_out)warnings.push('Uncovered nights between '+previous.title+' and '+r.title);}previous=r;}
    }
    for(let i=1;i<rows.length;i++){const a=rows[i-1],b=rows[i];if(a.trip===b.trip&&a.place&&b.place&&!b.route&&(a.place.lat!==b.place.lat||a.place.lng!==b.place.lng))warnings.push('Transfer to confirm: '+a.place.label+' → '+b.place.label);}
    return warnings;
  }
  function tripHtml(rows){
    return `<div class="wf-trip">${routeWarnings(rows).length?`<aside class="wf-route-warning"><strong>Check the plan</strong><ul>${routeWarnings(rows).map(w=>`<li>${esc(w)}</li>`).join('')}</ul></aside>`:''}<div class="wf-trip-switch" role="group" aria-label="Trip view"><button type="button" data-trip-view="timeline" aria-pressed="true">Timeline</button><button type="button" data-trip-view="map" aria-pressed="false">Map</button></div><div class="wf-trip-columns"><ol class="wf-itinerary">${rows.map((r,i)=>`<li data-stop="${i}" tabindex="-1">${r.day?`<span class="wf-day">${esc(r.day)}</span>`:''}<small>${esc(r.trip||'')} ${esc(r.when)}</small><div class="wf-step-heading"><strong>${esc(r.title)}</strong><span class="wf-tag">${esc(r.booking_status||'proposed')}</span></div>${r.stay?`<p>${stayLabel(r)}</p>`:''}${r.route?`<small>${esc(r.route.mode)}${r.route.duration?' · '+esc(r.route.duration):' · Duration to confirm'}</small>`:''}${r.price?`<p class="wf-price">${esc(r.price)}</p>`:''}<small class="wf-payment">${paymentSummary(r.payment)}</small><div class="wf-step-actions">${r.place?`<button type="button" data-show-stop="${i}">Show on map</button>`:''}<details><summary>Details & evidence</summary><p>${esc(r.detail)}</p>${r.option_anchor&&/^#option-[0-9]+$/.test(r.option_anchor)?`<a href="${r.option_anchor}">View option</a>`:''}${payment(r.payment)}${r.terms?`<p>${esc(r.terms)}</p>`:''}${(r.sources||[]).map(s=>safeLink(s.url,s.label)).join(' · ')}${r.place?`<p>${esc(r.place.label)} · ${esc(r.place.confidence)} ${safeLink(r.place.source_url,'Location source')}</p>`:''}${r.route?.source_url?`<p>${safeLink(r.route.source_url,'Route source')}</p>`:''}</details></div></li>`).join('')}</ol><aside class="wf-route"><h4>Stays & route</h4><p class="wf-map-note">Schematic connections, not navigation directions.</p><div class="wf-route-diagram">${rows.map((r,i)=>`<button type="button" data-route-stop="${i}"><span class="wf-pin">${i+1}</span><span><strong>${esc(r.place?.label||r.title)}</strong><small>${r.stay?stayLabel(r):esc(r.when)}${r.place?' · '+esc(r.place.confidence):' · Location to confirm'}</small></span></button>`).join('')}</div><div class="wf-street-map" hidden aria-label="Street map of trip stops"></div><button type="button" class="wf-load-map">Load street map</button><p class="wf-map-note">Optional: contacts OpenStreetMap for tiles. Your wallet is never sent. The stop list works offline.</p><p class="wf-map-status" role="status"></p></aside></div></div>`;
  }
  function mountTrip(target,rows){
    let map,markers=[];
    const trip=target.querySelector('.wf-trip');if(!trip)return;
    const setView=view=>{trip.dataset.view=view;trip.querySelectorAll('[data-trip-view]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.tripView===view)));if(map)setTimeout(()=>map.invalidateSize(),0);};
    const select=index=>{trip.querySelectorAll('[data-stop],[data-route-stop]').forEach(el=>el.classList.toggle('wf-selected',Number(el.dataset.stop??el.dataset.routeStop)===index));if(markers[index]){map.panTo(markers[index].getLatLng());markers[index].openPopup();}};
    trip.addEventListener('click',e=>{
      const button=e.target.closest('button');if(!button)return;
      if(button.dataset.tripView)setView(button.dataset.tripView);
      if(button.dataset.showStop!==undefined){setView('map');select(Number(button.dataset.showStop));}
      if(button.dataset.routeStop!==undefined){const i=Number(button.dataset.routeStop);select(i);setView('timeline');trip.querySelector(`[data-stop="${i}"]`).focus({preventScroll:true});}
      if(button.classList.contains('wf-load-map')){
        const status=trip.querySelector('.wf-map-status');
        const valid=r=>r.place&&Number.isFinite(r.place.lat)&&Number.isFinite(r.place.lng)&&Math.abs(r.place.lat)<=90&&Math.abs(r.place.lng)<=180;
        if(!rows.some(valid)){status.textContent='No verified coordinates supplied yet. Ask your agent to map these stops.';return;}
        if(!window.L){status.textContent='Street map unavailable. Your route list is still available.';return;}
        const pane=trip.querySelector('.wf-street-map');pane.hidden=false;button.hidden=true;
        map=L.map(pane,{scrollWheelZoom:false});
        L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'}).on('tileerror',()=>{status.textContent='Some map tiles could not load. Your stops remain available below.';}).addTo(map);
        const points=[];
        rows.forEach((r,i)=>{if(!valid(r))return;const point=[r.place.lat,r.place.lng];points.push(point);const label=document.createElement('span');label.textContent=`${i+1}. ${r.place.label}`;markers[i]=L.marker(point,{icon:L.divIcon({className:'wf-map-pin',html:String(i+1),iconSize:[28,28]})}).bindPopup(label).on('click',()=>select(i)).addTo(map);});
        // Never join across an unmapped stop or two separate trips.
        rows.forEach((r,i)=>{const previous=rows[i-1];if(previous&&valid(previous)&&valid(r)&&previous.trip===r.trip)L.polyline([[previous.place.lat,previous.place.lng],[r.place.lat,r.place.lng]],{color:'#247364',dashArray:'6 8'}).addTo(map);});
        map.fitBounds(L.latLngBounds(points),{padding:[24,24],maxZoom:13});status.textContent='Dashed lines show stop order, not road or rail geometry.';
      }
    });
  }
  function renderTrip(target,rows){target.classList.add('wf-dashboard');target.innerHTML=tripHtml(rows);mountTrip(target,rows);}
  function walletCards(rows,data){return `<div class="wf-wallet-cards">${rows.map(r=>{const program=(data['wallet.programs']||[]).find(p=>p.id===r.reward_account_id);const benefits=(data['wallet.benefits']||[]).filter(b=>b.card_id&&b.card_id===r.id);const art=(data['wallet.artwork']||{})[r.name];return `<article class="wf-wallet-card">${typeof art==='string'&&/^\/(?:assets\/)?cards\/[a-zA-Z0-9._-]+$/.test(art)?`<img src="${esc(art)}" alt="" loading="lazy">`:'<span class="wf-card-symbol" aria-hidden="true">▰</span>'}<h4>${esc(r.name)}</h4><p>${program?esc(program.account_label||program.name):'Rewards account not linked'}</p>${program?`<strong>${value(program,'balance')} <small>points / miles · account balance</small></strong>`:''}<small>${benefits.length?benefits.length+' linked benefits':'No linked benefits'}</small><details><summary>Card details</summary><p>${esc(r.notes||'No notes added.')}</p><small>Reported ${esc(r.reported_on||'date unknown')}</small>${benefits.map(b=>`<p>${esc(b.name)} · ${esc(b.remaining||'Unknown remaining')} · Expires ${esc(b.expires_on||'unknown')}</p>`).join('')}</details></article>`;}).join('')}</div>`;}
  function componentHtml(block,data){
    const all=data[block.source]||[],rows=all.slice(0,100);
    if(!rows.length){const message=block.source.startsWith('wallet.')?'Set up a person’s wallet in Wallet to add cards and rewards accounts.':block.source==='spending.references'?'Add PDF, CSV or ZIP references in Spending.':block.source.startsWith('spending.')?'Ask your agent to analyze your references and publish findings here.':'Ask your agent to generate an itinerary dashboard from your destinations, dates and flexibility.';return `<p class="wf-empty">${esc(message)}</p>`;}
    let html='';
    if(block.component==='metric-cards')html=`<div class="wf-metrics">${rows.map(r=>`<article><small>${esc(r.label)}</small><strong>${esc(r.value)}</strong><p>${esc(r.detail)}</p>${sources(r,data)}</article>`).join('')}</div>`;
    if(block.component==='findings')html=rows.map(r=>`<article class="wf-finding"><strong>${esc(r.label)}</strong><p>${esc(r.detail)}</p>${sources(r,data)}</article>`).join('');
    if(block.component==='reference-list')html=rows.map(r=>`<article class="wf-reference"><span class="wf-file">${esc(r.name?.split('.').pop()?.toUpperCase()||'FILE')}</span><div><strong>${esc(r.name)}</strong><small>${r.available===false?'File missing':'Local reference'}${r.archive_name?' · '+esc(r.archive_name):''}${r.members?' · '+r.members.filter(m=>m.supported).length+' supported files':''}${Number.isFinite(r.bytes)?' · '+Math.ceil(r.bytes/1024)+' KB':''}</small></div></article>`).join('');
    if(block.component==='itinerary')html=tripHtml(rows);
    if(block.component==='wallet-cards')html=walletCards(rows,data);
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
    layout.blocks.forEach(b=>{if(b.component==='itinerary')mountTrip(target.querySelector(`[data-block="${b.id}"]`),(data[b.source]||[]).slice(0,100));});
  }
  window.WalletFreakComponents=Object.freeze({validate,render,renderTrip});
})();

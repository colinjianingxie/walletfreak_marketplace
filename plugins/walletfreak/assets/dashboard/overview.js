'use strict';
(() => {
  let catalog, saved, request=0, selectedTrip='', rendered='';
  function bind(state,references){
    const rows=[];
    for(const trip of (state.trips||[]).filter(t=>t.id===selectedTrip)){for(const item of trip.findings.itinerary||[]){const option=trip.findings.options?.find(o=>o.id===item.option_id);rows.push({...option,...item,trip:trip.findings.title,payment:option?.payment});}}
    return {'wallet.artwork':Object.fromEntries(cards.map(c=>[c.name,'/assets'+c.path])),'wallet.cards':state.wallet.cards,'wallet.programs':state.wallet.programs,'wallet.benefits':state.wallet.benefits,'spending.metrics':references.report?.metrics||[],'spending.findings':references.report?.findings||[],'spending.references':references.files,'travel.itinerary':rows,'travel.lodging_window':(state.trips||[]).find(t=>t.id===selectedTrip)?.findings.lodging_window};
  }
  window.loadOverview=async function(reset=false){
    const sequence=++request;
    try{
      const [nextCatalog,nextSaved,current,references]=await Promise.all([catalog||api('catalog'),api('layout'),api('state'),api('references')]);
      if(sequence!==request)return;
      catalog=nextCatalog;const first=!saved;saved=nextSaved;
      if(first||reset){$('#overview-template').innerHTML=catalog.templates.map(t=>`<option value="${esc(t.id)}">${esc(t.name)}</option>`).join('');$('#overview-theme').innerHTML=catalog.themes.map(t=>`<option>${esc(t)}</option>`).join('');$('#overview-density').innerHTML=catalog.densities.map(t=>`<option>${esc(t)}</option>`).join('');$('#overview-theme').value=saved.layout.theme;$('#overview-density').value=saved.layout.density;}
      const trips=current.trips||[];
      if(!trips.some(t=>t.id===selectedTrip))selectedTrip=trips[0]?.id||'';
      const selector=$('#overview-trip'), options=trips.map(t=>`<option value="${esc(t.id)}">${esc(t.findings.title)}</option>`).join('');
      if(selector.innerHTML!==options)selector.innerHTML=options;selector.value=selectedTrip;
      const hasTravel=saved.layout.blocks.some(b=>b.source==='travel.itinerary');
      $('#overview-trip-label').hidden=!hasTravel||!trips.length;$('#overview-intro').hidden=hasTravel&&trips.some(t=>t.findings.itinerary?.length||t.findings.lodging_window);
      const selected=trips.find(t=>t.id===selectedTrip),gaps=selected?.findings.gaps||[];
      const costs=selected?.totals||{cash:{},points:{},unknown:[]};
      const reported={};for(const item of selected?.findings.itinerary||[]){if(item.booking_status==='booked'&&!item.option_id){const m=/^([A-Z]{3}) ([0-9]+(?:\.[0-9]{1,2})?)$/.exec(item.price||'');if(m)reported[m[1]]=(reported[m[1]]||0)+Number(m[2]);}}
      const figures=[...Object.entries(reported).map(([currency,value])=>`<article><small>Reported bookings</small><strong>${esc(currency)} ${value.toFixed(2)}</strong></article>`),...Object.entries(costs.cash).map(([currency,value])=>`<article><small>Recorded cash</small><strong>${esc(currency)} ${esc(value)}</strong></article>`),...Object.entries(costs.points).map(([program,value])=>`<article><small>${esc(program)} points</small><strong>${Number(value).toLocaleString()}</strong></article>`)];
      $('#overview-costs').hidden=!hasTravel||!selected;$('#overview-costs').innerHTML=figures.length?figures.join('')+'<p>Selected booked or verified items only. Other potential prices appear in the timeline.</p>':'<article><small>Trip cost</small><strong>To confirm</strong></article><p>Potential prices appear on each itinerary stop.</p>';
      $('#overview-gaps').hidden=!hasTravel||!gaps.length;$('#overview-gaps').innerHTML=gaps.length?`<strong>Still to check</strong><ul>${gaps.map(g=>`<li>${esc(g)}</li>`).join('')}</ul>`:'';
      const data=bind(current,references),signature=JSON.stringify([saved.layout,data,selectedTrip]);
      if(signature!==rendered){WalletFreakComponents.render($('#overview-content'),saved.layout,catalog,data);rendered=signature;}
    }catch(e){notice(e.message,true);}
  };
  async function save(layout){WalletFreakComponents.validate(layout,catalog);await api('layout',{expected_revision:saved.revision,layout});await window.loadOverview(true);notice('Dashboard layout saved locally.');}
  $('#overview-settings').onsubmit=async e=>{e.preventDefault();try{if(!saved)throw new Error('Reload the dashboard first.');const layout=structuredClone(catalog.templates.find(t=>t.id===$('#overview-template').value).layout);layout.theme=$('#overview-theme').value;layout.density=$('#overview-density').value;await save(layout);}catch(error){notice(error.message,true);}};
  $('#overview-file').onchange=async e=>{const file=e.target.files[0];try{if(!saved)throw new Error('Reload the dashboard first.');if(!file||file.size>32000)throw new Error('Choose a layout JSON file up to 32 KB.');await save(JSON.parse(await file.text()));}catch(error){notice(error.message,true);}finally{e.target.value='';}};
  $('#overview-export').onclick=()=>{if(!saved)return;const url=URL.createObjectURL(new Blob([JSON.stringify(saved.layout,null,2)+'\n'],{type:'application/json'}));const link=document.createElement('a');link.href=url;link.download='walletfreak-layout.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
  $('#overview-trip').onchange=e=>{selectedTrip=e.target.value;window.loadOverview();};
  $('#overview-copy').onclick=async()=>{try{await navigator.clipboard.writeText($('#overview-prompt').textContent);notice('Starter prompt copied. Paste it in your agent conversation.');}catch{notice('Copy the prompt above into your agent conversation.',true);}};
  $('#overview-reload').onclick=()=>window.loadOverview(true);
  setInterval(()=>{if(currentTab==='overview')window.loadOverview();},5000);
})();

'use strict';
(() => {
  let catalog, saved, request=0;
  function bind(state,references){
    const rows=[];
    for(const trip of state.trips||[]){for(const item of trip.findings.itinerary||[]){const option=trip.findings.options?.find(o=>o.id===item.option_id);rows.push({...item,trip:trip.findings.title,payment:option?.payment});}}
    return {'wallet.cards':state.wallet.cards,'wallet.programs':state.wallet.programs,'wallet.benefits':state.wallet.benefits,'spending.metrics':references.report?.metrics||[],'spending.findings':references.report?.findings||[],'spending.references':references.files,'travel.itinerary':rows};
  }
  window.loadOverview=async function(reset=false){
    const sequence=++request;
    try{
      const [nextCatalog,nextSaved,current,references]=await Promise.all([catalog||api('catalog'),api('layout'),api('state'),api('references')]);
      if(sequence!==request)return;
      catalog=nextCatalog;const first=!saved;saved=nextSaved;
      if(first||reset){$('#overview-template').innerHTML=catalog.templates.map(t=>`<option value="${esc(t.id)}">${esc(t.name)}</option>`).join('');$('#overview-theme').innerHTML=catalog.themes.map(t=>`<option>${esc(t)}</option>`).join('');$('#overview-density').innerHTML=catalog.densities.map(t=>`<option>${esc(t)}</option>`).join('');$('#overview-theme').value=saved.layout.theme;$('#overview-density').value=saved.layout.density;}
      WalletFreakComponents.render($('#overview-content'),saved.layout,catalog,bind(current,references));
    }catch(e){notice(e.message,true);}
  };
  async function save(layout){WalletFreakComponents.validate(layout,catalog);await api('layout',{expected_revision:saved.revision,layout});await window.loadOverview(true);notice('Dashboard layout saved locally.');}
  $('#overview-settings').onsubmit=async e=>{e.preventDefault();try{if(!saved)throw new Error('Reload the dashboard first.');const layout=structuredClone(catalog.templates.find(t=>t.id===$('#overview-template').value).layout);layout.theme=$('#overview-theme').value;layout.density=$('#overview-density').value;await save(layout);}catch(error){notice(error.message,true);}};
  $('#overview-file').onchange=async e=>{const file=e.target.files[0];try{if(!saved)throw new Error('Reload the dashboard first.');if(!file||file.size>32000)throw new Error('Choose a layout JSON file up to 32 KB.');await save(JSON.parse(await file.text()));}catch(error){notice(error.message,true);}finally{e.target.value='';}};
  $('#overview-export').onclick=()=>{if(!saved)return;const url=URL.createObjectURL(new Blob([JSON.stringify(saved.layout,null,2)+'\n'],{type:'application/json'}));const link=document.createElement('a');link.href=url;link.download='walletfreak-layout.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
  $('#overview-reload').onclick=()=>window.loadOverview(true);
  setInterval(()=>{if(currentTab==='overview')window.loadOverview();},5000);
})();

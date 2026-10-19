'use strict';
(() => {
  let references, uploading=false;
  let ledger, previewInput, previewRevision, page = 0, edits = new Map(), rowsOnPage = [];
  const types=['expense','refund','payment','transfer','income','unknown'], reviews=['needs-review','approved','excluded'];
  const message = (text, error=false) => notice(text,error);
  window.loadSpending = async function(force=false) {
    await refreshReferences();
    if(edits.size && !force)return;
    try { ledger=await api('spending'); edits.clear();render(); } catch(e){message(e.message,true);}
  };

  async function refreshReferences(){
    try{references=await api('references');renderReferences();}catch(e){message(e.message,true);}
  }
  function renderReferences(){
    $('#reference-list').innerHTML=references.files.map(f=>`<article class="reference-row"><span class="file-badge">${esc(f.name.split('.').pop().toUpperCase())}</span><div><strong>${esc(f.name)}</strong><small>${Math.ceil(f.bytes/1024)} KB · ${f.available?'Ready for your agent':'File missing'}</small><code>${esc(f.path)}</code>${f.archive_name?`<small>From ${esc(f.archive_name)} / ${esc(f.member)}</small>`:''}${f.members?`<details><summary>${f.members.filter(m=>m.supported).length} supported files · ${f.extracted?'Extracted':'Ready for agent extraction'}</summary><ul>${f.members.map(m=>`<li>${esc(m.name)}${m.supported?'':' · Unsupported; skipped'}</li>`).join('')}</ul></details>`:''}</div><a href="/api/references/${f.id}" download aria-label="Download ${esc(f.name)}">Download</a><button data-remove-reference="${f.id}" aria-label="Remove ${esc(f.name)}">Remove</button></article>`).join('');
    $('#reference-copy').hidden=!references.files.length;
    const report=references.report;
    if(!report){$('#spending-report').innerHTML='<p class="muted">Your metrics and findings will appear here.</p>';return;}
    const sources=item=>item.source_ids.map(id=>{const f=references.files.find(f=>f.id===id);return f?`<a href="/api/references/${id}" download>${esc(f.name)}</a>`:'';}).join(' · ');
    $('#spending-report').innerHTML=`<div class="section-heading"><h3>${esc(report.title)}</h3><small>${esc(report.generated_at)}</small></div><div class="metric-grid">${report.metrics.map(m=>`<article class="metric"><small>${esc(m.label)}</small><strong>${esc(m.value)}</strong><p>${esc(m.detail)}</p><small>${sources(m)}</small></article>`).join('')}</div>${report.findings.map(f=>`<article class="spending-finding"><strong>${esc(f.label)}</strong><p>${esc(f.detail)}</p><small>${sources(f)}</small></article>`).join('')}`;
  }
  async function uploadReferences(files){
    if(uploading)return;uploading=true;$('#reference-choose').disabled=true;
    const failures=[];
    try{for(const file of files){
      try{
        if(!/\.(pdf|csv|zip)$/i.test(file.name)||file.size>20000000||!file.size)throw new Error('Choose a nonempty PDF, CSV or ZIP up to 20 MB.');
        $('#reference-status').textContent=`Saving ${file.name}…`;
        const content=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result.split(',')[1]);reader.onerror=()=>reject(new Error('Could not read the file.'));reader.readAsDataURL(file);});
        references=await api('references/upload',{name:file.name,content});renderReferences();
      }catch(e){failures.push(file.name+': '+e.message);}
    }
    $('#reference-status').textContent=failures.length?failures.join(' '):'Saved locally. Ask your agent to analyze these references and show the findings here.';
    }finally{uploading=false;$('#reference-choose').disabled=false;$('#reference-files').value='';}
  }
  $('#reference-choose').onclick=()=>$('#reference-files').click();
  $('#reference-files').onchange=e=>uploadReferences([...e.target.files]);
  for(const name of ['dragenter','dragover'])$('#reference-drop').addEventListener(name,e=>{e.preventDefault();$('#reference-drop').classList.add('dragging');});
  $('#reference-drop').addEventListener('dragleave',()=>$('#reference-drop').classList.remove('dragging'));
  $('#reference-drop').addEventListener('drop',e=>{e.preventDefault();$('#reference-drop').classList.remove('dragging');uploadReferences([...e.dataTransfer.files]);});
  $('#references-refresh').onclick=refreshReferences;
  $('#reference-copy').onclick=async()=>{try{await navigator.clipboard.writeText('Analyze these local WalletFreak statement references and publish the key metrics to my Spending dashboard:\n'+references.files.filter(f=>f.available).map(f=>f.path).join('\n'));message('References copied. Paste them in your agent conversation.');}catch{message('Clipboard unavailable. Copy the file paths shown above.',true);}};
  $('#reference-list').onclick=async e=>{const button=e.target.closest('[data-remove-reference]');if(!button||!confirm('Remove this local copy and findings that cite it? Your original file stays unchanged.'))return;try{references=await api('references/delete',{id:button.dataset.removeReference,expected_revision:references.revision});renderReferences();}catch(e){message(e.message,true);}};
  setInterval(()=>{if(currentTab==='spending'&&!uploading)refreshReferences();},5000);

  function select(values,current,key,id) { return `<select data-spend-field="${key}" data-id="${id}" aria-label="${key} ${id}">${values.map(v=>`<option ${v===current?'selected':''}>${v}</option>`).join('')}</select>`; }
  function plainTable(rows, columns) {return `<table><thead><tr>${columns.map(c=>`<th scope="col">${esc(c)}</th>`).join('')}</tr></thead><tbody>${rows.map(r=>`<tr>${columns.map(c=>`<td>${esc(r[c])}</td>`).join('')}</tr>`).join('')}</tbody></table>`;}
  function render() {
    if(!ledger)return;
    const query=$('#spend-search').value.toLowerCase(), filter=$('#spend-filter').value, month=$('#spend-month').value;
    const all=ledger.rows.filter(r=>(!filter||r.review===filter)&&(!month||r.date.startsWith(month))&&[r.description,r.bank,r.account,r.category].join(' ').toLowerCase().includes(query));
    WalletFreakFinance.render($('#finance-chart'),ledger.totals,category=>{tab('spending');$('#spend-advanced').open=true;$('#spend-search').value=category;page=0;render();$('#spend-table').scrollIntoView({block:'start'});});
    page=Math.min(page,Math.max(0,Math.ceil(all.length/100)-1));rowsOnPage=all.slice(page*100,(page+1)*100);
    $('#spend-count').textContent=`${all.length} matching · ${ledger.rows.length} total · page ${page+1} · ${edits.size} unsaved edits`;
    $('#spend-table').innerHTML=`<table class="transaction-sheet"><thead><tr>${['Date','Description','Amount','Currency','Account','Category','Type','Review','Source'].map(x=>`<th scope="col">${x}</th>`).join('')}</tr></thead><tbody>${rowsOnPage.map(original=>{const r={...original,...edits.get(original.id)};return `<tr><td>${esc(r.date)}</td><td>${esc(r.description)}${r.possible_duplicate?'<strong class="error"> Possible duplicate</strong>':''}</td><td class="numeric">${esc(r.amount)}</td><td>${esc(r.currency)}</td><td>${esc(r.bank)} · ${esc(r.account)}</td><td><input data-spend-field="category" data-id="${r.id}" aria-label="category ${r.id}" value="${esc(r.category)}" maxlength="100"></td><td>${select(types,r.type,'type',r.id)}</td><td>${select(reviews,r.review,'review',r.id)}</td><td>${esc(r.source)}:${r.source_row}</td></tr>`;}).join('')}</tbody></table>`;
    $('#spend-totals').innerHTML=ledger.totals.length?plainTable(ledger.totals,['month','currency','category','net_spending']):'<p>No approved spending yet. Review your transactions above.</p>';
    $('#spend-prev').disabled=page===0;$('#spend-next').disabled=(page+1)*100>=all.length;
  }
  $('#spend-table').onchange = event => {const e=event.target, key=e.dataset.spendField,id=e.dataset.id;if(!key)return;const row=ledger.rows.find(r=>r.id===id);const change=edits.get(id)||{id,category:row.category,type:row.type,review:row.review};change[key]=e.value;edits.set(id,change);$('#spend-count').textContent=`${edits.size} unsaved edits`;};
  async function save() {if(!ledger||!edits.size)return;try{ledger=await api('spending/update',{expected_revision:ledger.revision,changes:[...edits.values()]});edits.clear();render();message('Spending edits saved locally.');}catch(e){message(e.message,true);}}
  $('#spend-save').onclick=save;
  $('#spend-approve').onclick=async()=>{if(!ledger)return;for(const row of rowsOnPage){const change=edits.get(row.id)||{id:row.id,category:row.category,type:row.type,review:row.review};if(change.type==='unknown'||row.possible_duplicate||change.review==='excluded')continue;change.review='approved';edits.set(row.id,change);}await save();};
  $('#spend-reload').onclick=()=>{if(!edits.size||confirm('Discard unsaved spending edits and reload?'))window.loadSpending(true);};
  for(const id of ['spend-search','spend-filter','spend-month'])$('#'+id).addEventListener('input',()=>{page=0;render();});
  $('#spend-prev').onclick=()=>{page--;render();};$('#spend-next').onclick=()=>{page++;render();};
  function invalidate(){previewInput=null;$('#spend-confirm').hidden=true;$('#spend-preview').textContent='';$('#spend-preview-note').textContent='';}
  $('#spend-import-form').onchange=event=>{invalidate();if(event.target.id==='spend-file')$('#spend-mapping').replaceChildren();};
  $('#spend-bank').addEventListener('change',()=>{$('#spend-sign').value=$('#spend-bank').value==='Chase'?'negative':'positive';});
  $('#spend-import-form').onsubmit=async event=>{
    event.preventDefault();invalidate();event.submitter.disabled=true;
    try{
      if(!ledger)throw new Error('Reload spending before importing.');
      const file=$('#spend-file').files[0];if(!file||file.size>1200000)throw new Error('Choose a CSV file no larger than 1.2 MB.');
      const input={content:await file.text(),filename:file.name,bank:$('#spend-bank').value,account:$('#spend-account').value,currency:$('#spend-currency').value,sign:$('#spend-sign').value};
      const mapping=[...document.querySelectorAll('[data-map]')];if(mapping.length)input.mapping=Object.fromEntries(mapping.map(e=>[e.dataset.map,e.value]));
      const preview=await api('spending/preview',{import:input});
      $('#spend-mapping').innerHTML=['date','description','amount','debit','credit','category','type','currency'].map(key=>`<label>${esc(key)} column<select data-map="${key}"><option value="">Not mapped</option>${preview.headers.map(h=>`<option value="${esc(h)}" ${preview.mapping[key]===h?'selected':''}>${esc(h)}</option>`).join('')}</select></label>`).join('');
      $('#spend-preview-note').textContent=preview.already_imported?'This file and mapping were already imported.':preview.errors.length?preview.errors.join('\n'):`${preview.rows.length} transactions · ${preview.rows.filter(r=>r.possible_duplicate).length} possible duplicates · first 100 shown. Check purchase signs, refunds, dates and account. Added rows need approval before they affect totals.`;
      $('#spend-preview').innerHTML=plainTable(preview.rows.slice(0,100),['date','description','amount','currency','category','type','possible_duplicate']);
      if(!preview.errors.length&&!preview.already_imported){previewInput=input;previewRevision=ledger.revision;$('#spend-confirm').hidden=false;}
    }catch(e){message(e.message,true);}finally{event.submitter.disabled=false;}
  };
  $('#spend-confirm').onclick=async()=>{if(!previewInput)return;if(edits.size){message('Save or reload your row edits before importing.',true);return;}const b=$('#spend-confirm');b.disabled=true;try{ledger=await api('spending/import',{import:previewInput,expected_revision:previewRevision});invalidate();$('#spend-file').value='';$('#spend-mapping').replaceChildren();render();message('Imported locally. Review and approve transactions to include them in totals.');}catch(e){message(e.message,true);}finally{b.disabled=false;}};
  $('#spend-delete').onclick=async()=>{if(!ledger||!confirm('Delete the local spending ledger? Original bank downloads and exported CSV files stay on disk. Wallet and trip results stay separate.'))return;try{ledger=await api('spending/delete',{expected_revision:ledger.revision,confirm:'delete-spending'});edits.clear();invalidate();render();message('Local spending ledger deleted.');}catch(e){message(e.message,true);}};
  $('#spend-template').onclick=()=>{const url=URL.createObjectURL(new Blob(['Date,Description,Amount,Currency,Category,Type\r\n'],{type:'text/csv'}));const a=document.createElement('a');a.href=url;a.download='walletfreak-spending-template.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);message('Template uses positive purchases and negative refunds. Select the matching sign setting when importing.');};
  window.addEventListener('beforeunload',event=>{if(edits.size){event.preventDefault();event.returnValue='';}});
})();

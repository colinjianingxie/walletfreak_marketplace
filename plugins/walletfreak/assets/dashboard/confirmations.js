'use strict';
(()=>{
 let draft;
 $('#confirmation-form').onsubmit=async e=>{
  e.preventDefault();const button=e.submitter;button.disabled=true;
  try{draft=await api('confirmations/preview',{text:$('#confirmation-text').value});render();$('#confirmation-review').hidden=false;notice('Detected booking fields. Review them before saving.');}
  catch(error){notice(error.message,true);}finally{button.disabled=false;}
 };
 function render(){
  $('#confirmation-items').innerHTML=draft.items.map((item,i)=>`<article class="confirmation-item" data-index="${i}"><span class="eyebrow">BOOKING ${i+1}</span><div class="credential-grid"><label>Type<select data-field="kind"><option value="flight" ${item.kind==='flight'?'selected':''}>Flight</option><option value="hotel" ${item.kind==='hotel'?'selected':''}>Hotel</option><option value="transport" ${item.kind==='transport'?'selected':''}>Transport</option><option value="other" ${item.kind==='other'?'selected':''}>Other</option></select></label><label>Date<input data-field="day" type="date" value="${esc(item.day)}" required></label><label>Title<input data-field="title" value="${esc(item.title)}" required maxlength="200"></label><label>Time or note<input data-field="when" value="${esc(item.when)}" required maxlength="200"></label><label>Reported total<input data-field="price" value="${esc(item.price)}" placeholder="USD 240.00" pattern="[A-Z]{3} [0-9]+(\\.[0-9]{1,2})?" maxlength="40"></label><label>Status<select data-field="booking_status"><option value="proposed" ${item.booking_status==='proposed'?'selected':''}>To confirm</option><option value="booked" ${item.booking_status==='booked'?'selected':''}>Booked</option></select></label>${item.stay?`<label>Check-in<input type="date" data-stay="check_in" value="${esc(item.stay.check_in)}"></label><label>Check-out<input type="date" data-stay="check_out" value="${esc(item.stay.check_out)}"></label>`:''}</div></article>`).join('');
  const flights=draft.items.filter(item=>item.kind==='flight');
  const hasWindow=flights.length===2&&flights[0].arrival_day&&flights[0].arrival_day<flights[1].day;
  $('#confirmation-lodging-start').value=hasWindow?flights[0].arrival_day:'';
  $('#confirmation-lodging-end').value=hasWindow?flights.at(-1).day:'';
  $('#confirmation-note').textContent=draft.note;
 }
 $('#confirmation-save').onclick=async()=>{
  const inputs=[...$('#confirmation-review').querySelectorAll('input,select')];if(!inputs.every(input=>input.reportValidity()))return;
  const items=[...$('#confirmation-items').querySelectorAll('[data-index]')].map(el=>{const original=draft.items[Number(el.dataset.index)],item={};for(const key of ['kind','day','when','title','booking_status'])item[key]=el.querySelector(`[data-field="${key}"]`).value;item.price=el.querySelector('[data-field="price"]').value.trim();item.detail=original.detail;if(original.stay)item.stay={check_in:el.querySelector('[data-stay="check_in"]').value,check_out:el.querySelector('[data-stay="check_out"]').value};return item;});
  const start=$('#confirmation-lodging-start').value,end=$('#confirmation-lodging-end').value;
  if((start||end)&&(!start||!end||start>=end)){notice('Enter both hotel dates, with departure after arrival.',true);return;}
  const body={title:$('#confirmation-title').value.trim(),items};if(start)body.lodging_window={check_in:start,check_out:end};
  const button=$('#confirmation-save');button.disabled=true;try{const saved=await api('confirmations/save',body);$('#confirmation-text').value='';draft=null;$('#confirmation-review').hidden=true;$('#confirmation-import').open=false;await refresh();window.selectTravelTrip(saved.id);notice(saved.message);}catch(e){notice(e.message,true);}finally{button.disabled=false;}
 };
})();

'use strict';
(()=>{
 let snapshot;
 window.loadShopping=async()=>{try{snapshot=await api('shopping');render();}catch(e){notice(e.message,true);}};
 function render(){
  const query=$('#shopping-search').value.trim().toLowerCase();
  const deals=(snapshot?.deals||[]).filter(d=>[d.merchant,d.product,d.terms].join(' ').toLowerCase().includes(query));
  $('#shopping-count').textContent=`${deals.length} observed offers · check current terms before buying`;
  $('#shopping-deals').innerHTML=deals.length?deals.map(d=>`<article class="shop-deal"><div><span class="eyebrow">${esc(d.merchant)} · ${esc(d.status)}</span><h3>${esc(d.product)}</h3><p>${esc(d.terms)}</p><small>Observed ${esc(d.observed_at)}${d.expires_on?' · Expires '+esc(d.expires_on):''}</small></div><div class="shop-deal-value"><strong>${esc(d.currency)} ${esc(d.price)}</strong>${d.cashback?`<span>${esc(d.cashback)} cash back</span>`:''}${d.card?`<small>Suggested card: ${esc(d.card)}</small>`:''}<a href="${esc(d.source_url)}" target="_blank" rel="noopener noreferrer">See source ↗</a></div></article>`).join(''):'<div class="finance-empty"><h3>Find a better way to buy.</h3><p>Ask your agent to compare current prices, merchant offers, cash back and the cards in your wallet. Verified findings will appear here.</p></div>';
 }
 $('#shopping-search').oninput=render;
 $('#shopping-refresh').onclick=()=>window.loadShopping();
})();

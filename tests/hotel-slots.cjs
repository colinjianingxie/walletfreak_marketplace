'use strict';
const assert=require('node:assert/strict');
global.window={};
require('../plugins/walletfreak/assets/components/v1/components.js');
const {renderTrip}=window.WalletFreakComponents;
const windowDates={check_in:'2027-06-03',check_out:'2027-06-08'};
const target={classList:{add(){}},querySelector(){return null},innerHTML:''};
const show=rows=>{renderTrip(target,rows,windowDates);return target.innerHTML;};
assert.match(show([]),/2027-06-03 → 2027-06-08 · 5 nights/);
const split=show([
  {booking_status:'booked',stay:{check_in:'2027-06-04',check_out:'2027-06-06'}},
  {booking_status:'proposed',stay:{check_in:'2027-06-06',check_out:'2027-06-08'}}
]);
assert.match(split,/2027-06-03 → 2027-06-04 · 1 night/);
assert.match(split,/2027-06-06 → 2027-06-08 · 2 nights/);
assert.equal((split.match(/class="wf-needed"/g)||[]).length,2);
assert.doesNotMatch(show([
  {booking_status:'booked',stay:{check_in:'2027-06-03',check_out:'2027-06-05'}},
  {booking_status:'booked',stay:{check_in:'2027-06-05',check_out:'2027-06-08'}}
]),/class="wf-needed"/);
const flight=show([{day:'2027-06-02',when:'Departure',title:'Outbound flight',detail:'Booked flight',booking_status:'booked'}]);
assert.match(flight,/Outbound flight/);
assert.match(flight,/Hotel to book/);
console.log('hotel slots: OK');

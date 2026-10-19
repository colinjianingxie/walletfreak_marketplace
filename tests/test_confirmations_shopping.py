import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'plugins/walletfreak/scripts'))
import confirmations, local

class ConfirmationsAndShopping(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.store=local.Store(self.root)
    def test_reviewed_bookings_create_timeline_without_email_or_pnr(self):
        text='''Subject: Your trip is confirmed\nFlight: UA 123\nDeparture: February 13, 2027\nTotal: USD 420.00\nBooking confirmed\nConfirmation #: SECRET123\n---\nHotel: Example Hotel\nCheck-in: February 14, 2027\nCheck-out: February 17, 2027\nTotal: $600.00\nReservation confirmed\n'''
        preview=confirmations.parse(text);self.assertEqual(len(preview['items']),2)
        self.assertEqual(preview['items'][0]['kind'],'flight');self.assertEqual(preview['items'][1]['stay']['check_out'],'2027-02-17')
        result=self.store.user_action('import-confirmations',{'title':'February trip','items':preview['items']})
        trip=self.store.trip(result['id']);self.assertEqual(len(trip['findings']['itinerary']),2)
        self.assertEqual(trip['findings']['itinerary'][0]['booking_status'],'booked')
        self.assertEqual(local.selected_totals(trip)['cash'],{});self.assertEqual([i['price'] for i in trip['findings']['itinerary']],['USD 420.00','USD 600.00'])
        saved=(self.root/'results.json').read_text();self.assertNotIn('SECRET123',saved);self.assertNotIn('Subject:',saved)
    def test_missing_date_or_bad_stay_is_not_saved(self):
        preview=confirmations.parse('Flight: AB 123\nTotal: USD 200')
        with self.assertRaises(ValueError):self.store.user_action('import-confirmations',{'title':'Trip','items':preview['items']})
        self.assertEqual(self.store.read_results()['trips'],[])
        with self.assertRaises(ValueError):confirmations.parse('')
    def test_shopping_publish_requires_source_and_revision(self):
        current=self.store.shopping.state();deal={'id':'one','merchant':'Example Store','product':'Laptop','price':'999.00','currency':'USD','source_url':'https://example.com/item','observed_at':'2026-10-19T10:00:00Z','terms':'Shipping extra','status':'available','card':'Example card'}
        result=self.store.agent_action('shopping-publish',{'expected_revision':current['revision'],'deals':[deal]})
        self.assertEqual(self.store.shopping.state()['deals'][0]['price'],'999.00')
        with self.assertRaises(ValueError):self.store.agent_action('shopping-publish',{'expected_revision':current['revision'],'deals':[deal]})
        for url in ('http://example.com','https://user:pass@example.com','javascript:alert(1)'):
            bad={**deal,'source_url':url}
            with self.assertRaises(ValueError):self.store.agent_action('shopping-publish',{'expected_revision':result['revision'],'deals':[bad]})
        self.assertEqual(len(self.store.shopping.state()['deals']),1)

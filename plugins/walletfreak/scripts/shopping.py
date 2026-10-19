"""Private, sourced shopping findings published by the agent."""
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit
import re
import uuid

class Shopping:
    def __init__(self, root, read, write):
        self.path, self.read, self.write = root / 'shopping.json', read, write

    def state(self):
        value = self.read(self.path, {'version': 1, 'revision': 'empty', 'deals': []})
        if value.get('version') != 1:
            raise ValueError('Unsupported shopping data; preserve shopping.json.')
        return value

    def publish(self, body):
        current = self.state()
        if not isinstance(body, dict) or set(body) != {'expected_revision', 'deals'} or body['expected_revision'] != current['revision']:
            raise ValueError('Shopping findings changed. Read them before publishing.')
        deals = body['deals']
        if not isinstance(deals, list) or len(deals) > 50:
            raise ValueError('Provide at most 50 deals.')
        ids = set()
        required = {'id', 'merchant', 'product', 'price', 'currency', 'source_url', 'observed_at', 'terms', 'status'}
        for deal in deals:
            if not isinstance(deal, dict) or set(deal) - (required | {'cashback', 'card', 'expires_on'}) or required - set(deal):
                raise ValueError('Deal needs a merchant, product, price, source and observation time.')
            if not isinstance(deal['id'], str) or not re.fullmatch(r'[a-zA-Z0-9-]{1,64}', deal['id']) or deal['id'] in ids:
                raise ValueError('Deal IDs must be unique and stable.')
            ids.add(deal['id'])
            for key in ('merchant','product','terms','cashback','card'):
                if key in deal and (not isinstance(deal[key],str) or len(deal[key]) > 500 or (key in required and not deal[key].strip())):
                    raise ValueError('Invalid deal text.')
            if not isinstance(deal['price'],str) or not re.fullmatch(r'\d{1,9}(?:\.\d{1,2})?',deal['price']):
                raise ValueError('Use a nonnegative price with at most two decimals.')
            if not isinstance(deal['currency'],str) or not re.fullmatch(r'[A-Z]{3}',deal['currency']):
                raise ValueError('Use a three-letter price currency.')
            if not isinstance(deal['status'],str) or deal['status'] not in ('available','unverified','expired'):
                raise ValueError('Invalid deal status.')
            if not isinstance(deal['observed_at'],str) or not isinstance(deal['source_url'],str):
                raise ValueError('Deal source and observation time must be text.')
            try:
                observed = datetime.fromisoformat(deal['observed_at'].replace('Z','+00:00'))
            except ValueError as exc:
                raise ValueError('Invalid observation time.') from exc
            if observed.utcoffset() is None:
                raise ValueError('Deal observation needs a timezone.')
            url = urlsplit(deal['source_url'])
            if url.scheme != 'https' or not url.hostname or url.username or url.password:
                raise ValueError('Deal source must be a public HTTPS page.')
            if 'expires_on' in deal:
                from datetime import date
                if not isinstance(deal['expires_on'],str):
                    raise ValueError('Invalid expiry date.')
                try:
                    date.fromisoformat(deal['expires_on'])
                except ValueError as exc:
                    raise ValueError('Invalid expiry date.') from exc
        saved = {'version': 1, 'revision': uuid.uuid4().hex, 'deals': deals}
        self.write(self.path, saved)
        return {'revision':saved['revision'], 'message':'Shopping findings published locally.'}

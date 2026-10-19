"""Conservative preview of pasted booking confirmations; original email is never stored."""
from datetime import datetime, date
import re

DATE = r'(?:\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}|[A-Za-z]+\s+\d{1,2},?\s+\d{4})'


def normalized_date(value):
    value = value.replace(',', '').strip()
    for fmt in ('%Y-%m-%d','%m/%d/%Y','%B %d %Y','%b %d %Y'):
        try: return datetime.strptime(value,fmt).date().isoformat()
        except ValueError: pass
    return ''


def labeled(text, labels):
    match = re.search(r'(?im)^\s*(?:'+ '|'.join(labels) + r')\s*[:\-]\s*(.+?)\s*$',text)
    return match.group(1).strip() if match else ''


def parse(raw):
    if not isinstance(raw,str) or not 1 <= len(raw.strip()) <= 50000:
        raise ValueError('Paste up to 50,000 characters of confirmation text.')
    blocks=[b.strip() for b in re.split(r'(?m)^\s*-{3,}\s*$',raw) if b.strip()]
    if len(blocks)>20: raise ValueError('Paste at most 20 confirmations at once.')
    items=[]
    for block in blocks:
        kind='hotel' if re.search(r'\b(hotel|check.?in|check.?out|room|property)\b',block,re.I) else 'flight' if re.search(r'\b(flight|airline|departure|boarding)\b',block,re.I) else 'other'
        check_in=labeled(block,['check[ -]?in','arrival date'])
        check_out=labeled(block,['check[ -]?out','departure date'])
        departure=labeled(block,['departure','departing','flight date','travel date'])
        date_values=[normalized_date(m.group(0)) for m in re.finditer(DATE,block)]
        day=normalized_date(check_in if kind=='hotel' else departure) or next((d for d in date_values if d),'')
        stay=None
        if kind=='hotel' and normalized_date(check_in) and normalized_date(check_out) and normalized_date(check_out)>normalized_date(check_in):
            stay={'check_in':normalized_date(check_in),'check_out':normalized_date(check_out)}
        vendor=labeled(block,['hotel','property','airline','carrier','merchant'])
        route=labeled(block,['route','flight','from'])
        title=(vendor or route or {'hotel':'Hotel stay','flight':'Flight','other':'Travel booking'}[kind])[:180]
        total=re.search(r'(?im)^\s*(?:total(?: paid| price| cost)?|amount paid|fare)\s*[:\-]\s*(?:(USD|EUR|GBP|CAD|AUD)\s*)?(\$|€|£)?\s*([\d,]+(?:\.\d{2})?)',block)
        currency=(total.group(1) or {'$':'USD','€':'EUR','£':'GBP'}.get(total.group(2),'USD')) if total else ''
        price=(currency+' '+total.group(3).replace(',','')) if total else ''
        confirmed=bool(re.search(r'\b(booking confirmed|reservation confirmed|flight confirmed|confirmed reservation)\b',block,re.I))
        items.append({'kind':kind,'day':day,'when':day or 'Date to confirm','title':title,'detail':'Imported from pasted confirmation; verify dates, names, status and total before saving.', 'price':price,'booking_status':'booked' if confirmed else 'proposed','stay':stay})
    return {'items':items,'note':'Review every detected field. Dates, prices and booking status can be incomplete; pasted email text is not saved.'}

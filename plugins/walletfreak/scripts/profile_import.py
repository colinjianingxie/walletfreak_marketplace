"""Read the bundled legacy Markdown profile format without inventing missing facts."""
import re


def parse_profile(text):
    sections, title = {}, ''
    for line in text.splitlines():
        if line.startswith('## '):
            title = line[3:].strip(); sections[title] = []
        elif title:
            sections[title].append(line)
    def table(section, width):
        rows = []
        for line in sections.get(section, []):
            if not line.strip().startswith('|'): continue
            cells = [c.strip() for c in line.strip().strip('|').split('|')]
            if len(cells) != width or all(re.fullmatch(r'[-: ]*', c) for c in cells): continue
            rows.append(cells)
        return [r for r in rows[1:] if any(r)]
    def stamp(value):
        return value if re.fullmatch(r'\d{4}-\d{2}-\d{2}', value) else ''
    wallet = {'cards':[], 'programs':[], 'benefits':[], 'preferences':'\n'.join(sections.get('Travel preferences',[])).strip()}
    for alias, product, country, owner, shared, enrollment, reported in table('Credit cards',7):
        wallet['cards'].append({'name':product or alias, 'owner':owner, 'notes':f'Alias: {alias}\nCountry: {country}\nRelationship / allowance: {shared}\nActive / enrollment: {enrollment}', 'reported_on':stamp(reported)})
    for name, owner, amount, preference, reported in table('Points and miles',5):
        match = re.fullmatch(r'(?:About |Approximately |~)?([\d,]+)(?: pooled miles)?',amount,re.I)
        wallet['programs'].append({'name':name,'owner':owner,'balance':match[1].replace(',','') if match else '', 'approximate':bool(re.search(r'about|approximately|~',amount,re.I)), 'status':'','preserve':'preserve' in preference.lower(), 'reported_on':stamp(reported), 'notes':f'Original report: {amount}\n{preference}'})
    for name, owner, tier, expiry, reported in table('Loyalty status',5):
        row=next((p for p in wallet['programs'] if p['name']==name and p['owner']==owner),None)
        if row is None:
            row={'name':name,'owner':owner,'balance':'','approximate':False,'status':'','preserve':False,'reported_on':stamp(reported),'notes':''};wallet['programs'].append(row)
        row['status']=tier;row['notes'] += f'\nStatus valid through: {expiry}; reported {reported}'
    for name, owner, remaining, expiry, notes, reported in table('Certificates',6):
        wallet['benefits'].append({'name':name,'owner':owner,'kind':'certificate','remaining':remaining,'expires_on':stamp(expiry),'notes':f'Expiry / deadline: {expiry}\n{notes}','reported_on':stamp(reported)})
    for program, name, remaining, period, notes, reported in table('Travel credits and passes',6):
        kind='gift-card' if 'gift card' in name.lower() else 'travel-credit' if name.lower()=='travel credit' else 'credit'
        wallet['benefits'].append({'name':f'{program} · {name}','owner':'','kind':kind,'remaining':remaining,'expires_on':'','notes':f'Card / program: {program}\nPeriod / deadline: {period}\n{notes}','reported_on':stamp(reported)})
    if not any(wallet[k] for k in ('cards','programs','benefits')):
        raise ValueError('No supported profile tables found. The original file is unchanged.')
    return wallet

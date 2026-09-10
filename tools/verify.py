from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse
import json,re
O=Path(__file__).resolve().parents[1]
class Check(HTMLParser):
 def __init__(self):super().__init__();self.ids=[];self.styles=0;self.local=[];self.h1=0
 def handle_starttag(self,tag,attrs):
  d=dict(attrs);assert 'style' not in d, 'Inline style attribute';assert not any(k.startswith('on') for k in d),'Inline event handler'
  if tag=='style':self.styles+=1
  if tag=='h1':self.h1+=1
  if 'id' in d:self.ids.append(d['id'])
  for key in ['href','src']:
   u=d.get(key,'');path=urlparse(u).path
   if u and not u.startswith(('#','http:','https:','data:','mailto:','tel:')):self.local.append(path)
products=json.loads((O/'data/products.json').read_text())
for p in O.glob('*.html'):
 s=p.read_text();c=Check();c.feed(s);assert c.styles==0 and c.h1==1;assert len(c.ids)==len(set(c.ids)),p.name+' duplicate IDs';assert 'cdn.tailwindcss' not in s and '{{' not in s
 for file in c.local:assert (O/file).exists(),file
 data=json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>',s,re.S)[1]);assert data==json.loads((O/'schema'/(p.stem+'.jsonld')).read_text());nodes=data['@graph'];assert len({n['@id'] for n in nodes})==len(nodes)
 for n in nodes:
  assert n['@type'] in ['WebSite','WebPage','CheckoutPage','CollectionPage','Product','ItemList','BreadcrumbList','Organization']
  if n['@type']=='Product':assert n['name']==products[0]['name'] and n['offers']['price']==products[0]['price'] and n['offers']['priceCurrency']=='RUB';assert products[0]['name'] in s
  if n['@type']=='BreadcrumbList':assert [i['position'] for i in n['itemListElement']]==list(range(1,len(n['itemListElement'])+1))
  if n['@type']=='ItemList':assert n['numberOfItems']==len(products)
 print(p.name+': CSS external, links/IDs/headings valid; JSON-LD parsed and checked against data')
js=(O/'assets/app.js').read_text();assert '.style.' not in js and 'fetch(' not in js and 'XMLHttpRequest' not in js
assert (O/'assets/styles.css').stat().st_size>10000
print('PASS: 5 pages. Local structural checks only; not a Google Rich Results certification.')

"""Run after editing data/*.json. HTML, JS product data and JSON-LD share one source."""
from pathlib import Path
import json,re,html
from schema_builder import graph
O=Path(__file__).resolve().parents[1];site=json.loads((O/'data/site.json').read_text());products=json.loads((O/'data/products.json').read_text())
if not site['demo'] and site['baseUrl'].rstrip('/')=='https://example.com':raise ValueError('Set the actual site URL before disabling demo mode')
values={}
for p in products:
 assert isinstance(p['price'],(int,float)) and p['price']>=0
 pre='product.'+p['id']+'.'
 for k in ['name','price','image']:values[pre+k]=html.escape(str(p[k]),quote=True)
 values[pre+'priceFormatted']=f"{p['price']:,.0f}".replace(',',' ')+' ₽'
 values[pre+'sizesCsv']=','.join(map(str,p['sizes']));values[pre+'sizesText']=', '.join(map(str,p['sizes']))
 values[pre+'sizeOptions']='<option value="">Размер</option>'+''.join(f'<option value="{int(s)}">{int(s)}</option>' for s in p['sizes'])
 values[pre+'sizeButtons']=''.join(f'<button type="button" class="size-btn glass-border py-3 font-bold" data-size="{int(s)}" aria-pressed="false">{int(s)}</button>' for s in p['sizes'])
for page in ['index','catalog','product','cart','checkout']:
 data=graph(page,site,products);text=json.dumps(data,ensure_ascii=False).replace('<','\\u003c');v=dict(values,jsonld='<script type="application/ld+json">'+text+'</script>',robots='<meta name="robots" content="'+('noindex, nofollow' if site['demo'] or page in ['cart','checkout'] else 'index, follow')+'">')
 source=(O/'templates'/(page+'.html')).read_text()
 if 'rel="icon"' not in source:source=source.replace('</title>','</title><link rel="icon" href="assets/favicon.svg" type="image/svg+xml">',1)
 result=re.sub(r'\{\{([\w.-]+)\}\}',lambda m:v[m[1]],source)
 (O/(page+'.html')).write_text(result);(O/'schema'/(page+'.jsonld')).write_text(json.dumps(data,ensure_ascii=False,indent=2))
(O/'assets/products.js').write_text('window.FORMA_PRODUCTS = '+json.dumps(products,ensure_ascii=False).replace('<','\\u003c')+';\n')
print('Rendered 5 pages and 5 JSON-LD documents from data/*.json')

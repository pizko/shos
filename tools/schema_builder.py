"""CMS-independent Schema.org generator. No user/cart/contact data enters JSON-LD."""
from urllib.parse import urljoin

def graph(page,site,products):
 base=site['baseUrl'].rstrip('/')+'/'
 routes={'index':'index.html','catalog':'catalog.html','product':'product.html','cart':'cart.html','checkout':'checkout.html'}
 names={'index':site['siteName'],'catalog':'Каталог кроссовок','product':products[0]['name'],'cart':'Корзина','checkout':'Оформление заказа'}
 url=urljoin(base,routes[page]);website={'@type':'WebSite','@id':base+'#website','url':base,'name':site['siteName'],'inLanguage':'ru-RU'}
 node={'@type':{'catalog':'CollectionPage','checkout':'CheckoutPage'}.get(page,'WebPage'),'@id':url+'#webpage','url':url,'name':names[page],'inLanguage':'ru-RU','isPartOf':{'@id':base+'#website'}}
 items=[{'@type':'ListItem','position':1,'name':'Главная','item':urljoin(base,'index.html')}]
 if page!='index':
  if page=='product':items.append({'@type':'ListItem','position':2,'name':'Каталог','item':urljoin(base,'catalog.html')})
  if page=='checkout':items.append({'@type':'ListItem','position':2,'name':'Корзина','item':urljoin(base,'cart.html')})
  items.append({'@type':'ListItem','position':len(items)+1,'name':names[page],'item':url})
 nodes=[website,node]
 if page!='index':
  bread={'@type':'BreadcrumbList','@id':url+'#breadcrumbs','itemListElement':items};node['breadcrumb']={'@id':bread['@id']};nodes.append(bread)
 if page=='catalog':
  listing={'@type':'ItemList','@id':url+'#items','numberOfItems':len(products),'itemListElement':[{'@type':'ListItem','position':i+1,'item':{'@type':'Thing','name':p['name']}} for i,p in enumerate(products)]}
  node['mainEntity']={'@id':listing['@id']};nodes.append(listing)
 if page=='product':
  p=products[0];product={'@type':'Product','@id':url+'#product','name':p['name'],'image':[p['image']],'category':p['category'],'description':'Демонстрационная карточка товара. Название и цена условные.' if site['demo'] else p['description'],'offers':{'@type':'Offer','url':url,'priceCurrency':'RUB','price':p['price']}}
  # Emit only confirmed facts supplied by the CMS; never assume stock, brand, rating or policy.
  for field in ['sku','gtin13','mpn','color']:
   if p.get(field):product[field]=p[field]
  if p.get('brand'):product['brand']={'@type':'Brand','name':p['brand']}
  if p.get('availability'):product['offers']['availability']=p['availability']
  node['mainEntity']={'@id':product['@id']};nodes.append(product)
 if site.get('organization'):
  org={'@type':'Organization','@id':base+'#organization',**site['organization']};nodes.append(org);website['publisher']={'@id':org['@id']}
 return {'@context':'https://schema.org','@graph':nodes}

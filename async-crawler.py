import asyncio
from aiohttp import ClientSession, TCPConnector
from bs4 import BeautifulSoup as bs
import time
import json
import requests


start_time = time.time()

dkps = []
category_url = input('Enter category url: ')
page = requests.get(category_url)
soup = bs(page.content, 'lxml')
products = soup.findAll('div', class_='c-product-box')
for p in products:
    dkp = p.get('data-id')
    if dkp:
        dkps.append(dkp)


all_products = []

async def fetch(url, session, barcode):
    async with session.get(url) as response:
        page = await response.text()
        try:
            page_soup = bs(page, 'lxml')
            try:
                brand = page_soup.find(
                    'a', 'c-product__title-container--brand-link').text
            except:
                brand = ''

            try:
                price = page_soup.find(
                    'div', class_='c-product__seller-price-prev').text.strip()
            except:
                price = ''

            availability = page_soup.find(
                'meta', attrs={'property': 'product:availability'})['content']

            try:
                rate = page_soup.find('span', class_='js-seller-rate').text
            except:
                rate = ''

            product_specs = {'price': price, 'availability': availability,
                            'rate': rate, 'brand': brand}
            print(barcode)
            all_products.append(product_specs)
        except:
            pass

async def bound_fetch(sem, url, session, barcode):
    async with sem:
        await fetch(url, session, barcode)

delay_per_request = 0.1
async def run(_list):
    url = 'https://www.digikala.com/product/dkp-{}'
    tasks = []
    sem = asyncio.Semaphore(300)

    connector = TCPConnector(limit_per_host=50)
    async with ClientSession(connector=connector) as session:
        for dkp in _list:
            
            task = asyncio.ensure_future(bound_fetch(sem, url.format(dkp), session, dkp))
            await asyncio.sleep(delay_per_request)
            tasks.append(task)

        responses = asyncio.gather(*tasks)
        await responses


loop = asyncio.get_event_loop()

future = asyncio.ensure_future(run(dkps))
loop.run_until_complete(future)


with open('result.json', 'w') as fp:
    json.dump(all_products, fp, ensure_ascii=False)

print(len(all_products))

print("--- %s seconds ---" % (time.time() - start_time))
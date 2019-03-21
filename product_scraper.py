import requests
from lxml import html
import re
import time
from random import choice
import socket


s = requests.Session()
zip_or_branch = '673'
p_date = re.compile(r'((Jan?|Feb?|Mar?|Apr?|May|Jun?|Jul?|Aug?|Sep?|Oct?|Nov?|Dec?)\s+\d{2})')
p_time = re.compile(r'(\d{1,2}:\d{2}\s+(AM?|PM?))')
min_delay = 1
max_delay = 5


print('Saving zip or branch..')
try:
    d = {'fulfilmentType': 'Pickup', 'zipOrBranchId': zip_or_branch}
    save = s.post('https://www.grainger.com/rta/savezipOrbranch/', data=d)
    print('Success..')
except:
    print('Saving has failed..')


def post(data):
    requests.post('http://206.189.71.121:8000/api/products/', data=data)


def main(url):
    try:
        r = s.get('https://www.grainger.com/product/' + url)
        tree = html.fromstring(r.text)
        try:
            brand = tree.xpath("//a[@itemprop='Brand']/text()")[0].strip()
        except:
            brand = None
        name = tree.xpath("//h1[@itemprop='name']/text()")[0].strip()
        try:
            part_number = tree.xpath("//span[@itemprop='model']/text()")[0].strip()
        except:
            part_number = None
        '''
        try:
            main_image_url = 'https:' + tree.xpath("//img[@id='mainImageZoom']/@data-blzsrc")[0]
        except:
            main_image_url = None
        '''
        try:
            main_image_url = 'https:' + tree.xpath("//img[@id='mainImageZoom']/@src")[0].split('?')[0]
        except:
            main_image_url = None
        try:
            actual_price = tree.xpath("//span[@itemprop='price']/@content")[0].strip()
        except:
            actual_price = 0
        try:
            actual_price_desc = tree.xpath("//span[@class='gcprice-unit']/text()")[0].replace('/', '').strip()
        except:
            actual_price_desc = None
        if actual_price == 0:
            try:
                pr = s.get('https://www.grainger.com/product/info?productArray=' + url)
                actual_price = pr.json()[url]['sellPrice'].replace('$', '')
                actual_price_desc = pr.json()[url]['uomLabel']
                main_image_url = 'https:' + pr.json()[url]['pictureUrl']
            except:
                pass
        try:
            p = {"itemIDs": [url], "itemQtys": ["1"]}
            pick = s.post('https://www.grainger.com/rta/getrtamessages/', json=p)
            text = pick.json()['rtaResponseItems'][0]['rtaMessage']
        except:
            text = ''
        try:
            pickup_date = p_date.findall(text)[0][0]
        except:
            pickup_date = None
        try:
            pickup_time = p_time.findall(text)[0][0]
        except:
            pickup_time = None
        try:
            weight = tree.xpath("//li[@id='shippingWeight']/span/text()")[0]
            shipping_weight = weight.split()[0].strip()
            shipping_weight_desc = weight.split()[1].strip()
        except:
            shipping_weight = None
            shipping_weight_desc = None
        try:
            country = tree.xpath("//div[@id='countryOfOrigin']/span[@class='productInfoValue']/text()")[0].strip()
        except:
            country = None
        desc = '\n'.join(tree.xpath("//div[@id='copyTextSection']/text()")).strip()
        li = tree.xpath("//div[@class='techSpecsTable']//li")
        det = ['\n']
        for l in li:
            try:
                k = l.xpath('./span/text()')[0]
                v = l.xpath('./span/text()')[1]
                detail = '{}: {}'.format(k, v)
            except:
                detail = ''
            det.append(detail)
        details = '\n'.join(det)
        det.clear()
        full_desc = desc + details
        try:
            item_sku = tree.xpath("//span[@itemprop='productID']/text()")[0].strip()
        except:
            item_sku = None
        try:
            compilance = '\n'.join('\n'.join(tree.xpath("//ul[@class='complianceInfo']//p/text()")).split())
        except:
            compilance = ''
        out = {
            'brand_name': brand,
            'item_name': name,
            'part_number': part_number,
            'main_image_url': main_image_url,
            'actual_price': actual_price,
            'actual_price_desc': actual_price_desc,
            'pickup_date': pickup_date,
            'pickup_time': pickup_time,
            'shipping_weight': shipping_weight,
            'shipping_weight_desc': shipping_weight_desc,
            'country_of_origin': country,
            'product_description': full_desc,
            'product_compliance': compilance,
            'item_sku': item_sku,
        }
        post(out)
        print(item_sku)
        time.sleep(choice(range(min_delay, max_delay)))
    except Exception as ex:
        time.sleep(300)
        with open('/var/grainger/error.txt', 'a') as q:
            q.write('{}: {}\n'.format(url, ex))
        print(ex)


for sku in open('/var/grainger/link/{}.txt'.format(socket.gethostname())).read().split('\n'):
    main(sku)
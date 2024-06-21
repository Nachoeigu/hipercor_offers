from functions import *
from constants import CONDITIONS_JSON_JOSE, CONDITIONS_JSON_NACHO
from telegram_bot import TelegramBot
import requests
from lxml import html
import pandas as pd
import time
from datetime import datetime
import random
import jinja2

def main():
    big_df = pd.DataFrame()
    for category in ['alimentacion','desayunos-dulces-y-pan','lacteos','congelados','cuidado-personal-y-belleza','bebes','frescos','bebidas','drogueria-y-limpieza']:
        time.sleep(2)
        page = 0
        print(f"We are in category: {category}")
        category_condition = True
        while category_condition:
            time.sleep(random.choice([1,0.5,0.2,0.4,0.6]))
            page += 1
            print(f"We are in page {page}")
            headers = {
                'authority': 'www.hipercor.es',
                'accept': '*/*',
                'accept-language': 'en-US,en;q=0.8',
                'referer': 'https://www.hipercor.es/supermercado/alimentacion/',
                'sec-ch-ua': '"Brave";v="111", "Not(A:Brand";v="8", "Chromium";v="111"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'sec-gpc': '1',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
            }

            params = {
                'direction': 'next',
            }

            response = requests.get(
                f'https://www.hipercor.es/alimentacion/api/catalog/010MOH/get-page/supermercado/{category}/{page}/',
                params=params,
                headers=headers,
            )
            if len(response.content) < 50000:
                category_condition = False

            data = html.fromstring(response.content.decode('utf-8'))
            products = data.xpath(f"//div[@data-page='{page}']//div[@class='product_tile-right_container']")
            images = data.xpath(f"//div[@data-page='{page}']//div[contains(@class,'image')]//a/img//@src")
            
            titles = []
            link = []
            normal_prices = []
            offers = []
            pics = []

            for number, product in enumerate(products):
                price = ''
                for idx, character in enumerate(product.xpath(".//div[@class='prices-price _current']//span")):
                    if idx == 0:
                        price += character.text + '.'
                    else:
                        price += character.text
                    try:
                        offer = product.xpath(".//div[@class='product_tile-offers_desktop_holder']//div[@class='offer-description']")[0].text.lower()
                    except:
                        offer = 'sin oferta'
                        
                    url = 'https://www.hipercor.es' + product.xpath(".//a[contains(@href,'/supermercado/')]//@href")[0]
                    title = remove_special_characters(product.xpath(".//h3//a[@href and @data-event='product_click']//@title")[0].lower())
                    image = 'https:' + images[number]
                if price == '':
                    continue
                    
                link.append(url)
                normal_prices.append(float(price.replace('€','')))
                titles.append(title)
                offers.append(offer)
                pics.append(image)
                
            df = pd.DataFrame({
                'last_update': [datetime.now().strftime("%Y-%m-%d") for _ in range(len(titles))],
                'category':[category.replace('-',' ') for _ in range(len(titles))],
                'image': pics,
                'product': titles,
                'offer': offers,
                'price': normal_prices,
                'link': link                
            })

            big_df = pd.concat([df, big_df])

    big_df = big_df.reset_index().drop(columns = 'index')

    send_to_cloud(big_df, 'catalog')

    offers = big_df[big_df['offer'].apply(lambda offer : filtering_offers(offer))].reset_index().drop(columns = 'index')
    
    offers['price_with_discount'] = offers.apply(lambda df: calculating_price(df['price'], df['offer']), axis=1)
    
    send_to_cloud(offers, 'offers') #We send all the offers to a google spreadsheet so we can see them in details

    for user in ['jose','nacho']:
        specific_offers = pd.DataFrame()
        if user == 'jose':
            conditions = CONDITIONS_JSON_JOSE
        elif user == 'nacho':
            conditions = CONDITIONS_JSON_NACHO

        for condition in conditions:
            products_idx = finding_specific_products(condition, offers)
            df = offers[offers.index.isin(products_idx)]
            specific_offers = pd.concat([specific_offers, df])

        json_file_with_specific_offers_by_category = {}

        for category in specific_offers.category.unique():
            json_file_with_specific_offers_by_category[category] = {} 
            for type_offer in offers.offer.unique():
                json_file_with_specific_offers_by_category[category][type_offer] = []

        for row in specific_offers.values: 
            json_file_with_specific_offers_by_category[row[1]][row[4]].append((row[3], round(row[-1],2)))    
        environment = jinja2.Environment()
        telegram_bot = TelegramBot(user = user)

        for idx, category in enumerate(list(json_file_with_specific_offers_by_category.keys())):
            if idx == 0:
                template = environment.from_string("""
    ¡OFERTAS DEL DÍA PARA TUS PRODUCTOS!        
    💸 Ofertas en la categoria {{category}}:
                """)
                first_part = template.render(
                                category = f'{category}'
                )
            
            else:
                template = environment.from_string("""
    💸 Ofertas en la categoria {{category}}:
                """)
                first_part = template.render(
                                category = f'{category}'
                )
        
            first = 0
            for type_offer in list(sorted(specific_offers.offer.unique(), reverse=True)):
                if json_file_with_specific_offers_by_category[category][type_offer] == []:
                    continue
                else:
                    if first != 2:
                        first = 1
                if first == 1:
                    template = environment.from_string("""
    {{intro}}
    👉 {{offer.upper()}} 👈 
    {%- for of in products %}
    ✅ {{of[0]}} está {{of[1]}} EUR
    {%- endfor -%}

                    """)
                    first = 2
                else:
                    template = environment.from_string("""
    👉 {{offer.upper()}} 👈 
    {%- for of in products %}
    ✅ {{of[0]}} está {{of[1]}} EUR
    {%- endfor -%}
                    """)       
                    
                if json_file_with_specific_offers_by_category[category][type_offer] == []:
                    continue
                    
                second_part = template.render(
                                intro = first_part,
                                offer = f'{type_offer}',
                                products=json_file_with_specific_offers_by_category[category][type_offer])

                telegram_bot.send_message(second_part)




main()

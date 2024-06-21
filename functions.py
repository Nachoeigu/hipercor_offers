import gspread
import os
from dotenv import load_dotenv


def send_to_cloud(table, types):
    load_dotenv()
    spreadsheet_id = os.getenv('spreadsheet_id')
    # Conection with Google API
    gc = gspread.service_account(filename = 'drive_credentials.json') 
    #Before executing the Bot, we should have the Google spreadsheets where we will store the data.
    sh = gc.open_by_key(spreadsheet_id)
    if types == 'catalog':
        worksheet = sh.worksheet(f"Catalogo con todos los productos")
    elif types == 'offers':
        worksheet = sh.worksheet(f"Ofertas diarias")
    #We update the data
    worksheet.update([table.columns.values.tolist()] + table.values.tolist())


def filtering_offers(offer):
    if offer in ['2ª unidad al 50% de descuento','2ª unidad al 70% de descuento','2ª unidad al 40% de descuento']:
        return True
    else:
        return False


def remove_special_characters(text):
    return text.replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u')

def calculating_price(price, offer):
    if offer.upper() == '2ª UNIDAD AL 70% DE DESCUENTO':
        return round(price * 0.65, 2)
    elif offer.upper() == '2ª UNIDAD AL 50% DE DESCUENTO':
        return round(price * 0.75, 2)
    elif offer.upper() == '2ª UNIDAD AL 40% DE DESCUENTO':
        return round(price * 0.80, 2)


def boolean_search(text, contains_these_keywords:list, not_contains_these_keywords:list=['AAAAAAAAAAAAAAAAAAAAAJJA']):
    # Create a list to store the words in the text
    # Iterate through the list and check if the boolean value is present in the word
    result = 1
    if type(contains_these_keywords) == str:
        contains_these_keywords = [contains_these_keywords]
    if type(not_contains_these_keywords) == str:
        not_contains_these_keywords = [not_contains_these_keywords]
    
    for kw in contains_these_keywords: 
        if text.lower().find(kw.lower()) == -1:
            result = 0
    
    for kw in not_contains_these_keywords: 
        if text.lower().find(kw.lower()) != -1:
            result = 0

    if result == 0:
        return False
    else:
        return True

def finding_specific_products(conditions, offers):
    #If the product contains both words, consider it: conditions[0]
    #If the product contains one of these words, avoid it: conditions[1]
    products_idx = []
    if len(conditions) == 1:
        for idx, product in enumerate(list(offers['product'])):
            if boolean_search(product, conditions[0]):
                products_idx.append(idx)
    else:
        for idx, product in enumerate(list(offers['product'])):
            if boolean_search(product, conditions[0], conditions[1]):
                products_idx.append(idx)
    
    return products_idx

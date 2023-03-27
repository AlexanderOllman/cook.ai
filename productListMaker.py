import coles_vs_woolies.main as main
import coles_vs_woolies.search.woolies as woolies
import os
import openai
import time

session = woolies._woolies_session()

def fetch_product(product_id: str):
    url = f'https://www.woolworths.com.au/apis/ui/product/detail/{product_id}?isMobile=false'
    response = session.get(url=url)
    return response.json()

product_count = 0
for i in range(0, 999999):
    prod_no = str(i)
    while len(prod_no) < 6:
        prod_no = "0" + prod_no

    item = fetch_product(prod_no)
    if item['Product'] == None:
        print("No product under number: " + prod_no)
    else:
        print(item['Product']['DisplayName'])
        product_count = product_count + 1

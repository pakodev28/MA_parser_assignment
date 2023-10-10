import requests
from bs4 import BeautifulSoup

def get_product_info(page_url):
    response = requests.get(page_url)

    if response.status_code == 200:
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')

        product_cards = soup.find_all('div', class_='product-card__content')

        for card in product_cards:
            out_of_stock = card.find('p', {'is-out-of-stock': 'true'})
            if out_of_stock:
                continue

            product_link = card.find('a', {'data-qa': 'product-card-photo-link'})['href']
            print(f'Ссылка на товар: {product_link}')

        next_page_number = int(page_url.split('=')[-1]) + 1
        next_page_url = f'https://online.metro-cc.ru/category/molochnye-prodkuty-syry-i-yayca/morozhenoe?page={next_page_number}'

        get_product_info(next_page_url)

if __name__ == '__main__':
    start_url = 'https://online.metro-cc.ru/category/molochnye-prodkuty-syry-i-yayca/morozhenoe?page=1'
    get_product_info(start_url)

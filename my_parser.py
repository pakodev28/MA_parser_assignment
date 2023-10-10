import requests
from bs4 import BeautifulSoup

def get_product_info(page_url):
    # Отправить GET-запрос к URL страницы
    response = requests.get(page_url)

    if response.status_code == 200:
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')

        # Найдите все карточки товаров на странице
        product_cards = soup.find_all('div', class_='product-card__content')

        # Пройдитесь по каждой карточке товара и извлеките информацию
        for card in product_cards:
            out_of_stock = card.find('p', {'is-out-of-stock': 'true'})
            if out_of_stock:
                continue

            product_link = card.find('a', {'data-qa': 'product-card-photo-link'})['href']
            print(f'Ссылка на товар: {product_link}')

        # Проверьте, есть ли следующая страница (пагинация)
        next_page_number = int(page_url.split('=')[-1]) + 1
        next_page_url = f'https://online.metro-cc.ru/category/molochnye-prodkuty-syry-i-yayca/morozhenoe?page={next_page_number}'

        # Рекурсивно вызовите эту же функцию для следующей страницы
        get_product_info(next_page_url)

if __name__ == '__main__':
    start_url = 'https://online.metro-cc.ru/category/molochnye-prodkuty-syry-i-yayca/morozhenoe?page=1'
    get_product_info(start_url)

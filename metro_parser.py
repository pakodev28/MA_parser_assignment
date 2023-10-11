import asyncio
import csv
import re
from typing import Dict, List

import aiohttp
from bs4 import BeautifulSoup

BASE_URL = "https://online.metro-cc.ru"

# По умолчанию парсинг  данных для Москва, Проспект Мира, д.211, корп.1
COOKIES = {
    "pickupStore": "11",
    "metroStoreId": "11",
}


async def fetch_page(session: aiohttp.ClientSession, url: str) -> str:
    """
    Асинхронная функция для получения HTML-страницы по заданному URL,
    с использованием сеанса сессии.

    """
    async with session.get(url, cookies=COOKIES) as response:
        return await response.text()


async def get_pagination_links(
    session: aiohttp.ClientSession, page_url: str
) -> List[str]:
    """
    Асинхронная функция для извлечения ссылок на пагинацию с главной страницы.

    """
    html = await fetch_page(session, page_url)
    soup = BeautifulSoup(html, "html.parser")

    pagination = soup.find("ul", class_="catalog-paginate v-pagination")
    if pagination:
        last_li = pagination.find_all("li")[-2]
        last_page = int(last_li.text)

        page_links = [f"{page_url}?page={i}" for i in range(1, last_page + 1)]
        return page_links

    return []


async def extract_prices_and_url_from_main_page(
    session: aiohttp.ClientSession, page_url: str
) -> List[Dict[str, str]]:
    """
    Функция для извлечения цен
    и URL-адресов товаров с главной страницы.

    """
    html = await fetch_page(session, page_url)
    soup = BeautifulSoup(html, "html.parser")
    product_cards = soup.find_all("div", class_="product-card__content")
    prices = []

    for card in product_cards:
        out_of_stock = card.find("p", {"is-out-of-stock": "true"})
        if out_of_stock:
            continue

        product_link = card.find("a", {"data-qa": "product-card-photo-link"})["href"]
        product_price = card.find("span", class_="product-card-prices__actual")
        product_price_text = product_price.text if product_price else ""
        product_old_price = card.find("span", class_="product-card-prices__old")
        product_old_price_text = product_old_price.text if product_old_price else ""

        product_price_text = re.sub(r"[^\d.]", "", product_price_text)
        product_old_price_text = re.sub(r"[^\d.]", "", product_old_price_text)

        prices.append(
            {
                "url": BASE_URL + product_link,
                "price": product_price_text,
                "old_price": product_old_price_text,
            }
        )

    return prices


async def get_product_info(
    session: aiohttp.ClientSession,
    page_url: str,
    csv_writer: csv.writer,
    info: Dict[str, str],
) -> None:
    """
    Функция для получения информации о продукте и записи ее в CSV-файл.
    """
    html = await fetch_page(session, page_url)
    soup = BeautifulSoup(html, "html.parser")
    product_id = soup.find("p", {"itemprop": "productID"}).text.strip()
    product_name = soup.find(
        "h1", class_="product-page-content__product-name"
    ).text.strip()
    attributes_list = soup.find(
        "ul", class_="product-attributes__list style--product-page-full-list"
    )
    brand = attributes_list.find(
        "span", class_="product-attributes__list-item-value"
    ).text.strip()

    product_price = info["price"]
    product_old_price = info["old_price"]

    csv_writer.writerow(
        [
            product_id,
            product_name,
            brand,
            product_price,
            product_old_price,
            page_url,
        ]
    )


async def parse_products_list(
    session: aiohttp.ClientSession, page_url: str, csv_writer: csv.writer
) -> None:
    """
    Функция для обработки списка продуктов на странице.
    """
    prices_and_url = await extract_prices_and_url_from_main_page(session, page_url)
    tasks = []

    for info in prices_and_url:
        task = asyncio.create_task(
            get_product_info(session, info["url"], csv_writer, info)
        )
        tasks.append(task)

    await asyncio.gather(*tasks)


async def main() -> None:
    start_url = (
        "https://online.metro-cc.ru/category/molochnye-prodkuty-syry-i-yayca/morozhenoe"
    )

    with open("products.csv", "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "ID товара",
            "Наименование",
            "Бренд",
            "Актуальная Цена",
            "Старая цена",
            "Ссылка",
        ]
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(fieldnames)

        async with aiohttp.ClientSession() as session:
            pagination_links = await get_pagination_links(session, start_url)
            if pagination_links:
                for page_url in pagination_links:
                    await parse_products_list(session, page_url, csv_writer)
            else:
                await parse_products_list(session, start_url, csv_writer)


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import csv

from loguru import logger

from playwright.async_api import async_playwright
from selectolax.lexbor import LexborHTMLParser

logger.add("logs/mens-outdoor-hats.log", level="INFO")


def save_csv(results, filename):
    with open(filename, "w", encoding="utf-8") as f:
        keys = ["name", "vendor", "price"]
        writer = csv.DictWriter(f, keys)
        writer.writeheader()
        writer.writerows(results)


async def fetch(url: str):
    async with async_playwright() as pw:
        browser = await pw.firefox.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        )
        page = await context.new_page()
        await page.goto(url)
        # wait for content to fully load:
        await page.wait_for_selector("li.grid__item")

        # Start scrolling to find the last element
        # loop scrolling last element into view until no more new elements are created
        previous_count = 0
        same_count_rounds = 0
        # loop scrolling last element into view until no more new elements are created
        while True:
            cards = await page.locator("li.grid__item").count()
            if cards == previous_count:
                same_count_rounds += 1
            else:
                same_count_rounds = 0
            if same_count_rounds >= 3:
                break
            previous_count = cards
            await page.mouse.wheel(0, 2000)
            await asyncio.sleep(1.2)
        logger.info(f"there are {cards} cards")
        return await page.content()


def parse(html: str) -> list:
    tree = LexborHTMLParser(html)

    cards = tree.css("li.grid__item")
    results = []
    for card in cards:
        name_node = card.css_first("h3")
        name = name_node.text(strip=True)
        vendor_node = card.css_first("div.card-information div")
        vendor = vendor_node.text(strip=True)
        price_node = card.css_first("s")
        price = price_node.text(strip=True)
        result = {
            "name": name,
            "vendor": vendor,
            "price": price,
        }
        results.append(result)

    return results


async def main():
    url = "https://www.villagehatshop.com/collections/mens-outdoor-hats"
    html = await fetch(url)
    results = parse(html)
    save_csv(results, "data/mens-outdoor-hats.csv")


if __name__ == "__main__":
    asyncio.run(main())

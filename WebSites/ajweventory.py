from bs4 import BeautifulSoup
import requests


class Ajweventory:
    def __init__(self):
        self.session = requests.Session()

        self.url = "https://eventory.ajw-group.com/a/search"

        self.logged_in = True
        self.status = "OK"

    def __del__(self):
        self.session.close()

    def login_function(self, login, password):
        self.status = "OK"
        return self.status

    def search_part(self, number, search_results):
        self.status = "OK"

        page_number = 1

        exact_match = True
        while exact_match:
            try:
                page = self.session.get(self.url, params={"q": number, "page": page_number})
            except ConnectionError:
                self.status = "Connection error"
                return self.status

            bs = BeautifulSoup(page.text, "lxml")

            part_grid = bs.find("div", {"class": "grid-uniform"})
            if part_grid is None or part_grid.text == "\n":
                break

            parts = part_grid.find_all("div", {"class": "grid-item"})

            for part in parts:
                ref = part.find("a").get("href")
                part_page = self.session.get("https://eventory.ajw-group.com" + ref)
                part_bs = BeautifulSoup(part_page.text, "lxml")

                part_id = part_bs.find("h1", {"itemprop": "name"}).text
                if part_id != number:
                    exact_match = False
                    break

                price = part_bs.find("span", {"id": "displayprice"})
                qty = part_bs.find("div", {"id": "variant-inventory"})
                condition = part_bs.find(lambda tag: tag.name == "p" and "Condition" in tag.text)

                search_results.append({
                    "vendor": "ajweventory",
                    "part number": part_id,
                    "QTY": qty.text.split()[qty.text.split().index("have") + 1] if qty else '',
                    "price": price.text.strip() if price else '',
                    "condition": condition.text.split(": ")[1].lower() if condition else '',
                })

            page_number += 1

        return self.status

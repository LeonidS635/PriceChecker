from bs4 import BeautifulSoup
from requests import Session


class Aviodirect:
    def __init__(self):
        self.session = Session()

        self.url = "https://aviodirect.com/"

        self.logged_in = True
        self.status = "OK"

    def __del__(self):
        self.session.close()

    def login_function(self, login, password):
        return self.status

    def search_part(self, number, search_results):
        self.status = "OK"

        if not self.logged_in:
            self.status = "Login error"
            return self.status

        try:
            page = self.session.get(self.url, params={"post_type": "product", "product_cat": 0, "s": number}, headers={
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/102.0.0.0 Safari/537.36"
            })
        except ConnectionError:
            self.status = "Connection error"
            return self.status

        bs = BeautifulSoup(page.text, "lxml")

        part_title = bs.find("h1", {"class": "product_title entry-title"})
        if part_title is None:
            return self.status

        part_id, description = part_title.text.split(" | ") if '|' in part_title.text else part_title.text.split(" – ")
        price = bs.find("p", {"class": "price"}).text
        condition = bs.find("div", {"class": "woocommerce-product-details__short-description"}).text

        search_results.append({
            "vendor": "aviodirect",
            "part number": number,
            "description": description,
            "price": price,
            "condition": condition
        })

        return self.status

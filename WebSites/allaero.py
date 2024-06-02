from bs4 import BeautifulSoup
from requests import Session


class Allaero:
    def __init__(self):
        self.session = Session()

        self.url = "https://www.allaero.com/aircraft-parts/"

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
            page = self.session.get(self.url + number)
        except ConnectionError:
            self.status = "Connection error"
            return self.status

        if page.status_code != 200:
            return self.status

        bs = BeautifulSoup(page.text, "lxml")

        part_id = bs.find("span", {"itemprop": "identifier"}).text
        description = bs.find("span", {"itemprop": "name"}).text
        condition = bs.find("td", {"data-title": "Condition:"}).text
        availability = bs.find("td", {"data-title": "Release:"}).text
        qty = bs.find("td", {"data-title": "Stock:"}).text

        search_results.append({
            "vendor": "allaero",
            "part number": part_id,
            "description": description,
            "QTY": qty,
            "lead time": availability if availability != "Any" else "",
            "price": "",
            "condition": condition if condition != "Any" else ""
        })

        return self.status

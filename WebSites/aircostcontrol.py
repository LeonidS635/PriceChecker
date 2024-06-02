from bs4 import BeautifulSoup
from requests import Session


class Aircostcontrol:
    def __init__(self):
        self.session = Session()

        self.url = "https://ecommerce.aircostcontrol.com/search"

        self.logged_in = True
        self.status = "OK"

    def __del__(self):
        self.session.close()

    def login_function(self, login, password):
        log_in_link = "https://ecommerce.aircostcontrol.com/login"

        try:
            auth = self.session.get(log_in_link)
        except ConnectionError:
            self.status = "Connection error"
            return self.status

        login_data = {
            "back": "",
            "email": login,
            "password": password,
            "submitLogin": 1
        }

        login_page = self.session.post(log_in_link, data=login_data)
        login_bs = BeautifulSoup(login_page.text, "lxml")

        if not login_bs.find(string="Authentication failed."):
            self.logged_in = True
            self.status = "OK"
        else:
            self.status = "Login error"

        return self.status

    def search_part(self, number, search_results):
        self.status = "OK"

        if not self.logged_in:
            self.status = "Login error"
            return self.status

        params = {
            "controller": "search",
            "orderby": "position",
            "orderway": "desc",
            "submit": "",
            "search_query": number
        }

        try:
            page = self.session.get(self.url, params=params)
        except ConnectionError:
            self.status = "Connection error"
            return self.status

        if page.status_code != 200:
            return self.status

        bs = BeautifulSoup(page.text, "lxml")

        ref = bs.find("a", {"class": "btn btn-primary w-100 mb-2"})
        if ref is not None:
            ref = ref["href"]
            page = self.session.get(ref)
        else:
            return self.status

        bs = BeautifulSoup(page.text, "lxml")

        part_number = bs.find("label", string="PN:").find_next_sibling().text
        description = bs.find("label", string="Description:").next_sibling.text.strip()
        lead_time = bs.find("label", string="Lead-time:").find_next_sibling().text.strip()
        condition = bs.find("label", string="Condition:").find_next_sibling().text.strip()

        qty = bs.find("span", {"class": "hidden-in-product-pp"})
        if qty is not None:
            qty = qty.text
        else:
            qty = ""

        price = bs.find("tr", {"data-discount-type": "amount"})
        if price is not None:
            price = price.find_all("td")[1].text
        else:
            price = ""

        search_results.append({
            "vendor": "aircostcontrol",
            "part number": part_number,
            "description": description,
            "QTY": qty,
            "price": price,
            "condition": condition,
            "lead time": lead_time
        })

        return self.status

from bs4 import BeautifulSoup
from requests import Session


class Lasaero:
    def __init__(self):
        self.session = Session()

        self.url = "https://www.lasaero.com/part/"

        self.logged_in = True
        self.status = "OK"

    def __del__(self):
        self.session.close()

    def login_function(self, login, password):
        log_in_link = "https://www.lasaero.com/account/"

        try:
            auth = self.session.get(log_in_link)
        except ConnectionError:
            self.status = "Connection error"
            return self.status

        bs = BeautifulSoup(auth.text, 'lxml')
        csrf = bs.find("input", {"name": "csrfmiddlewaretoken"})["value"]

        login_data = {
            "csrfmiddlewaretoken": csrf,
            "refresh_page": "True",
            "return_path_jx": "/account/",
            "shopper_email": login,
            "shopper_pass": password
        }

        login_page = self.session.post("https://www.lasaero.com/ajax/contact/login/", data=login_data, headers={
            "Host": "www.lasaero.com",
            "Origin": "https://www.lasaero.com",
            "Refer": "https://www.lasaero.com/account/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/121.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest"})
        login_bs = BeautifulSoup(login_page.text, "lxml")

        if not login_bs.find(string="We could not log you in. Please try again, or"):
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

        try:
            page = self.session.get(self.url + number)
        except ConnectionError:
            self.status = "Connection error"
            return self.status

        if page.status_code != 200:
            return

        bs = BeautifulSoup(page.text, "lxml")

        res_table = bs.find("table", {"class": "table table-bordered table-responsive table-condensed"})

        if res_table is None:
            return self.status

        _, description, _, qty_in_stock, _, qty_on_order, _, price, _, lead_time = res_table.find_all("td")

        search_results.append({
            "vendor": "lasaero",
            "part number": number,
            "description": description.text.strip(),
            "QTY": qty_in_stock.text,
            "price": price.text[1:].replace("/ Each", "").strip(),
            "lead time": lead_time.text.strip(),
            "other information": f"qty on order: {qty_on_order.text}"
        })

        return self.status

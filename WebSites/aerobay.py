from bs4 import BeautifulSoup
from copy import deepcopy
from requests import Response, Session
from requests.exceptions import RequestException, Timeout
from typing import Callable


class Aerobay:
    def __init__(self):
        self.session = Session()

        self.delay = 20
        self.logged_in = False
        self.response = None
        self.status = "OK"

    def __del__(self):
        self.session.close()

    def request_wrapper(self, request: Callable[[], Response]) -> bool:
        try:
            self.response = request()
            self.response.raise_for_status()
        except Timeout:
            self.status = "Time error"
            return False
        except RequestException:
            self.status = "Connection error"
            return False
        else:
            self.status = "OK"
            return True

    def login_function(self, login: str, password: str) -> str:
        login_url = "https://www.aero-bay.com"
        if not self.request_wrapper(lambda: self.session.get(login_url, timeout=self.delay)):
            return self.status

        page = BeautifulSoup(self.response.text, 'lxml')
        csrf = page.find("input", {"name": "_csrf"})["value"]

        login_data = {
            "_csrf": csrf,
            "userName": login,
            "password": password
        }

        if not self.request_wrapper(
                lambda: self.session.post(login_url + "/j_spring_security_check", data=login_data, timeout=self.delay)):
            return self.status
        page = BeautifulSoup(self.response.text, "lxml")

        if not page.find(string="Email or password is incorrect"):
            self.logged_in = True
            self.status = "OK"
        else:
            self.status = "Login error"

        return self.status

    def search_part(self, number: str, search_results: list) -> str:
        if not self.logged_in:
            self.status = "Login error"
            return self.status

        product_info = {
            "vendor": "aerobay",
            "part number": "",
            "description": "",
            "QTY": "",
            "price": "",
            "condition": "",
            "lead time": "",
            "warehouse": "",
            "other information": ""
        }

        def reset_product_info():
            product_info.clear()
            product_info["vendor"] = "aerobay"

        search_url = "https://www.aero-bay.com/q"

        if not self.request_wrapper(
                lambda: self.session.get(search_url, params={"searchType": "PART_NUMBER", "item": number},
                                         timeout=self.delay)):
            return self.status
        page = BeautifulSoup(self.response.text, "lxml")

        parts_list = page.select_one("div[id='resultLists']")
        if parts_list is not None:
            for part in parts_list.select("div[class='parent_product_box_list']"):
                description, condition, qty, _, price, _, lead_time, _, _ = part.select(
                    "div[class*='product_infos_inside_product_box_list']")

                reset_product_info()
                product_info["part number"] = part.select_one("strong").text
                product_info["description"] = description.select_one("p").text.lower()
                product_info["QTY"] = qty.select_one("strong").text
                product_info["price"] = '$' + price_parts[1].text + '.' + price_parts[2].text if (
                    price_parts := price.select_one("span > span").findChildren()) else ""
                product_info["condition"] = condition.select_one("span").text
                product_info["lead time"] = lead_time.text.strip()

                search_results.append(deepcopy(product_info))

        return self.status

    def change_delay(self, new_delay):
        self.delay = new_delay

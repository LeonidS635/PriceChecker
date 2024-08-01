from bs4 import BeautifulSoup
from copy import deepcopy
from Logic.data_file import Status
from Logic.parser import ParserRequests


class Aerobay(ParserRequests):
    def __init__(self):
        super().__init__()

    def login_function(self, login: str, password: str) -> Status:
        login_url = "https://www.aero-bay.com"
        if not self.request_wrapper(self.session.get, url=login_url):
            return self.status

        page = BeautifulSoup(self.response.text, 'lxml')
        csrf = page.find("input", {"name": "_csrf"})["value"]

        login_data = {
            "_csrf": csrf,
            "userName": login,
            "password": password
        }

        if not self.request_wrapper(self.session.post, url=(login_url + "/j_spring_security_check"), data=login_data):
            return self.status

        page = BeautifulSoup(self.response.text, "lxml")
        if not page.find(string="Email or password is incorrect"):
            self.logged_in = True
            self.status = Status.OK
        else:
            self.logged_in = False
            self.status = Status.Login_error

        return self.status

    def search_part(self, number: str, search_results: list) -> Status:
        if not self.logged_in:
            self.status = Status.Login_error
            return self.status

        if not self.request_wrapper(self.session.get, url="https://www.aero-bay.com/q",
                                    params={"searchType": "PART_NUMBER", "item": number}):
            if self.response.status_code == 404:
                self.status = Status.OK
            return self.status

        page = BeautifulSoup(self.response.text, "lxml")
        parts_list = page.select_one("div[id='resultLists']")
        if parts_list is not None:
            for part in parts_list.select("div[class='parent_product_box_list']"):
                description, condition, qty, _, price, _, lead_time, _, _ = part.select(
                    "div[class*='product_infos_inside_product_box_list']")

                self.product_info["part number"] = part.select_one("strong").text
                self.product_info["description"] = description.select_one("p").text
                self.product_info["QTY"] = qty.select_one("strong").text
                self.product_info["price"] = '$' + price_parts[1].text + '.' + price_parts[2].text if (
                    price_parts := price.select_one("span > span").findChildren()) else ""
                self.product_info["condition"] = condition.select_one("span").text
                self.product_info["lead time"] = lead_time.text

                search_results.append(deepcopy(self.product_info))

        return self.status

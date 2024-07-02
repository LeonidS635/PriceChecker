from bs4 import BeautifulSoup
from copy import deepcopy
from requests import Session, Response
from requests.exceptions import Timeout, RequestException
from typing import Callable


class Scross:
    def __init__(self):
        self.session = Session()

        self.delay = 20
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

    def login_function(self, _: str, __: str) -> str:
        return self.status

    def search_part(self, number: str, search_results: list) -> str:
        product_info = {
            "vendor": "scross",
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
            product_info["vendor"] = "scross"

        search_url = f"https://www.scross.com/store/part-number?{number}"

        if not self.request_wrapper(lambda: self.session.get(search_url, timeout=self.delay)):
            return self.status

        page = BeautifulSoup(self.response.text, "lxml")
        product = page.select_one("div[class='PNindex-Items']")

        sections = product.select("div[class='SearchedPNContent'] > div")

        if sections[1].select_one("span:-soup-contains('*PN not found*')") is not None:
            return self.status

        reset_product_info()
        product_info["part number"] = sections[1].select_one("meta[itemprop='sku']").get("content")
        product_info["description"] = sections[1].select_one("meta[itemprop='description']").get("content").lower()
        product_info["condition"] = condition_el.text if (
            condition_el := sections[1].select_one("button[class='Circle OptionSelected']")) else ""
        product_info["price"] = '$' + price if (
            price := sections[2].select_one("meta[itemprop='price']").get("content")) != "0" else ""

        interchanges_list = [interchange.text.strip() for interchange in
                             product.select("h3:-soup-contains('Possible Alternate PNs') ~ span > a")]
        interchanges = " ; ".join(interchanges_list)
        product_info["other information"] = f"interchanges: {interchanges}" if interchanges else ""

        table = sections[2].select_one("table")
        cols = len(table.select("tr:nth-of-type(1) > td"))

        if warehouses_el := table.select("th:-soup-contains('Warehouse') ~ td > span[class='tooltiptext']"):
            warehouses = [warehouse.text for warehouse in warehouses_el]
        elif warehouses_el := table.select("th:-soup-contains('Warehouse') ~ td"):
            warehouses = [warehouse.text for warehouse in warehouses_el]
        else:
            warehouses = ["" for _ in range(cols)]
        availabilities = [availability.text.split(": ")[-1] for availability in availabilities_el] if (
            availabilities_el := table.select("th:-soup-contains('Availability') ~ td")) else ["" for _ in range(cols)]
        qtys = [qty.text for qty in qtys_el] if (
            qtys_el := table.select("th:-soup-contains('Qty Available') ~ td")) else ["" for _ in range(cols)]

        for col in range(cols):
            product_info["QTY"] = qtys[col]
            product_info["lead time"] = availabilities[col]
            product_info["warehouse"] = warehouses[col]

            search_results.append(deepcopy(product_info))

        return self.status

    def change_delay(self, new_delay):
        self.delay = new_delay

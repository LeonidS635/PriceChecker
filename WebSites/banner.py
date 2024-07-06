from copy import deepcopy
from requests import Session, Response
from requests.exceptions import Timeout, RequestException
from typing import Callable


class Banner:
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
            "vendor": "banner",
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
            product_info["vendor"] = "banner"

        search_url = "https://wapi-eu.erp.aero/v1/catalog/find-products"
        data = {
            "cid": "BAI",
            "pn[0]": number
        }

        if not self.request_wrapper(lambda: self.session.get(search_url, data=data, timeout=self.delay)):
            return self.status

        products_list = self.response.json()["data"]["partsList"]
        for product in products_list:
            reset_product_info()
            product_info["part number"] = product["product"]["name"]
            product_info["description"] = product["comment"].lower()
            product_info["condition"] = condition if (condition := product["condition"]) is not None else ""
            product_info["QTY"] = qty if (qty := product["quantity"]) != 0 else ""

            search_results.append(deepcopy(product_info))

        return self.status

    def change_delay(self, new_delay):
        self.delay = new_delay

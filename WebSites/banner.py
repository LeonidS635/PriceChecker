from copy import deepcopy
from Logic.data_file import Status
from Logic.parser import ParserRequests


class Banner(ParserRequests):
    def __init__(self):
        super().__init__()

    def login_function(self, login: str, password: str) -> Status:
        self.logged_in = True
        self.status = Status.OK
        return self.status

    def search_part(self, number: str, search_results: list) -> Status:
        search_url = "https://wapi-eu.erp.aero/v1/catalog/find-products"
        data = {
            "cid": "BAI",
            "pn[0]": number
        }

        if not self.request_wrapper(self.session.get, url=search_url, data=data):
            return self.status

        for product in self.response.json()["data"]["partsList"]:
            if product["product"]["name"].lower() == number.lower():
                self.product_info["part number"] = product["product"]["name"]
                self.product_info["description"] = product["comment"]
                self.product_info["condition"] = condition if (condition := product["condition"]) is not None else ""
                self.product_info["QTY"] = product["quantity"]

                search_results.append(deepcopy(self.product_info))

        return self.status

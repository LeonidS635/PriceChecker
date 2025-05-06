from bs4 import BeautifulSoup
from copy import deepcopy
from Logic.data_file import Status
from Logic.parser import ParserRequests
from PIL import Image


class Dasi(ParserRequests):
    def __init__(self):
        super().__init__()

    def login_function(self, login: str, password: str) -> Status:
        self.logged_in = True
        self.status = Status.OK

        return self.status

    def search_part(self, number: str, search_results: list) -> Status:
        if not self.logged_in:
            self.status = Status.Login_error
            return self.status

        if not self.request_wrapper(self.session.post,
                                    url="https://prod-avs-dasi.my.site.com/storeDasi/webruntime/api/apex/execute",
                                    json={
                                        "namespace": "",
                                        "classname": "@udd/01pao00000Jqxvc",
                                        "method": "searchParts",
                                        "isContinuation": False,
                                        "params": {
                                            "filters": [number],
                                            "pageSize": 500,
                                            "inventoryFilter": "all",
                                            "typeOfSearch": "simple"
                                        },
                                        "cacheable": False
                                    }):
            return self.status

        response = self.response.json()
        for item in response["returnValue"]:
            if item["productName"] == number:
                details = item["productDetails"]

                for product in details:
                    self.product_info["part number"] = item["productName"]
                    self.product_info["description"] = item["productDescription"]
                    self.product_info["QTY"] = product["quantityAv"]
                    self.product_info["price"] = f"$ {product["price"]}"
                    self.product_info["condition"] = product["conditionCodeName"]
                    self.product_info["lead time"] = str(int(product["leadTime"]))
                    self.product_info["warehouse"] = product["location"]
                    self.product_info["other information"] = f"trace: {product["traceName"]} | {product["traceTag"]}"

                    search_results.append(deepcopy(self.product_info))

                break

        return self.status

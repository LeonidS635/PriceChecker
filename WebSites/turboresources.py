from copy import deepcopy
from Logic.data_file import Status
from Logic.parser import ParserRequests


class Turboresources(ParserRequests):
    def __init__(self):
        super().__init__()

    def login_function(self, login: str, password: str) -> Status:
        self.logged_in = True
        self.status = Status.OK
        return self.status

    def search_part(self, number: str, search_results: list) -> Status:
        if not self.request_wrapper(self.session.post, url="https://turboresources.com/api/searchStock.asp",
                                    json={"searches": [{"partnumber": number}]}):
            return self.status

        page = self.response.json()
        if page["totalResults"]:
            for part in page["StockSearchResults"]:
                if part["partnumber"].lower() != number.lower():
                    break

                self.product_info["part number"] = part["partnumber"]
                self.product_info["description"] = part["description"]
                self.product_info["QTY"] = str(part["quantity"])
                self.product_info["condition"] = part["condition"]

                search_results.append(deepcopy(self.product_info))

        return self.status

from bs4 import BeautifulSoup
from copy import deepcopy
from Logic.data_file import Status
from Logic.parser import ParserRequests


class Ajweventory(ParserRequests):
    def __init__(self):
        super().__init__()

    def login_function(self, login: str, password: str) -> Status:
        self.logged_in = True
        self.status = Status.OK
        return self.status

    def search_part(self, number: str, search_results: list) -> Status:
        page_number = 1
        exact_match = True
        while exact_match:
            if not self.request_wrapper(self.session.get, url="https://eventory.ajw-group.com/a/search",
                                        params={"q": number, "page": page_number}):
                return self.status

            page = BeautifulSoup(self.response.text, "lxml")
            parts = page.select("div[class='grid-uniform'] > div")
            if len(parts) == 0:
                break

            for part in parts:
                ref = part.find("a").get("href")
                if not self.request_wrapper(self.session.get, url=("https://eventory.ajw-group.com" + ref)):
                    return self.status

                page = BeautifulSoup(self.response.text, "lxml")

                part_number = page.select_one("h1[itemprop='name']").text
                if part_number != number:
                    exact_match = False
                    break

                self.product_info["part number"] = part_number
                self.product_info["description"] = page.select_one("div[itemprop='description'] > p > strong").text
                self.product_info["price"] = price.text if (price := page.select_one("span[id='displayprice']")) else ""
                self.product_info["QTY"] = qty.text.split()[qty.text.split().index("have") + 1] if ((
                    qty := page.select_one("div[id='variant-inventory']"))) is not None else ""
                self.product_info["condition"] = condition.text.split(": ")[1] if ((
                    condition := page.find(
                        lambda tag: tag.name == "p" and "Condition" in tag.text))) is not None else ""

                search_results.append(deepcopy(self.product_info))

            page_number += 1

        return self.status

from bs4 import BeautifulSoup
from copy import deepcopy
from Logic.data_file import Status
from Logic.parser import ParserRequests


class Scross(ParserRequests):
    def __init__(self):
        super().__init__()

    def login_function(self, login: str, password: str) -> Status:
        self.logged_in = True
        self.status = Status.OK
        return self.status

    def search_part(self, number: str, search_results: list) -> Status:
        if not self.request_wrapper(self.session.get, url="https://www.scross.com/store/part-number", params=number):
            return self.status

        page = BeautifulSoup(self.response.text, "lxml")
        product = page.select_one("div[class='PNindex-Items']")
        sections = product.select("div[class='SearchedPNContent'] > div")

        if sections[1].select_one("span:-soup-contains('*PN not found*')") is not None:
            return self.status

        self.product_info["part number"] = sections[1].select_one("meta[itemprop='sku']").get("content")
        self.product_info["description"] = sections[1].select_one("meta[itemprop='description']").get("content")
        self.product_info["condition"] = condition_el.text if (
            condition_el := sections[1].select_one("button[class='Circle OptionSelected']")) else ""
        self.product_info["price"] = '$' + price if (
                                                        price := sections[2].select_one("meta[itemprop='price']").get(
                                                            "content")) != "0" else ""

        interchanges_list = [interchange.text.strip() for interchange in
                             product.select("h3:-soup-contains('Possible Alternate PNs') ~ span > a")]
        interchanges = " ; ".join(interchanges_list)
        self.product_info["other information"] = f"interchanges: {interchanges}" if interchanges else ""

        table = sections[2].select_one("table")
        cols_number = len(table.select("tr:nth-of-type(1) > td"))

        if warehouses_el := table.select("th:-soup-contains('Warehouse') ~ td > span[class='tooltiptext']"):
            warehouses = [warehouse.text for warehouse in warehouses_el]
        elif warehouses_el := table.select("th:-soup-contains('Warehouse') ~ td"):
            warehouses = [warehouse.text for warehouse in warehouses_el]
        else:
            warehouses = ["" for _ in range(cols_number)]

        availabilities = [availability.text.split(": ")[-1] for availability in availabilities_el] if (
            availabilities_el := table.select("th:-soup-contains('Availability') ~ td")) else ["" for _ in
                                                                                               range(cols_number)]
        qtys = [qty.text for qty in qtys_el] if (
            qtys_el := table.select("th:-soup-contains('Qty Available') ~ td")) else ["" for _ in range(cols_number)]

        for col in range(cols_number):
            self.product_info["QTY"] = qtys[col]
            self.product_info["lead time"] = availabilities[col]
            self.product_info["warehouse"] = warehouses[col]

            search_results.append(deepcopy(self.product_info))

        return self.status

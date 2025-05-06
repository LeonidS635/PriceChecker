from bs4 import BeautifulSoup
from copy import deepcopy
from Logic.data_file import Status
from Logic.parser import ParserRequests


class Airpowerinc(ParserRequests):
    def __init__(self):
        super().__init__()

    def login_function(self, login: str, password: str) -> Status:
        self.logged_in = True
        self.status = Status.OK
        return self.status

    def search_part(self, number: str, search_results: list) -> Status:
        if not self.request_wrapper(self.session.get, url=f"https://www.airpowerinc.com/{number}"):
            return self.status
        page = BeautifulSoup(self.response.text, "lxml")

        product_id_tag = page.select_one("div[class='sku']").select_one("span[class='value']")
        if product_id_tag is None:
            return self.status
        product_id = product_id_tag["id"].removeprefix("sku-")

        data = dict()
        data["__RequestVerificationToken"] = page.select_one("input[name='__RequestVerificationToken']")["value"]
        for attr in page.select("dd[id^='product_attribute_input']"):
            data[f"product_attribute_{attr.select_one("ul")["data-attr"]}"] = attr.select_one("ul > li")[
                "data-attr-value"]

        if not self.request_wrapper(self.session.post, params={"productId": product_id}, data=data,
                                    url="https://www.airpowerinc.com/shoppingcart/productdetails_attributechange"):
            return self.status
        json_response = self.response.json()

        if not self.request_wrapper(self.session.post, data={"id": product_id},
                                    url="https://www.airpowerinc.com/AlternateProduct/GetAlternateProducts"):
            return self.status
        alternates_json = self.response.json()

        self.product_info["part number"] = json_response["sku"]
        self.product_info["description"] = page.select_one("h1").text.split(None, 1)[1]
        self.product_info["QTY"] = availability.removesuffix("in stock") if (
                (availability := json_response["stockAvailability"]).find("in stock") != -1) else availability
        self.product_info["price"] = json_response["priceValue"]
        self.product_info["condition"] = page.select_one(
            "div[class='attributes'] dd[id^='product_attribute_input']").text
        self.product_info["lead time"] = lead_time if (lead_time := json_response["gtin"]).find('|') == -1 else ""
        self.product_info["other information"] = f"interchanges: {" ; ".join(
            [alternate["ProductSku"] for alternate in alternates_json])}" if alternates_json else ""

        search_results.append(deepcopy(self.product_info))

        return self.status

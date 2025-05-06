from bs4 import BeautifulSoup
from copy import deepcopy
from Logic.data_file import Status
from Logic.parser import ParserRequests


class Allaero(ParserRequests):
    def __init__(self):
        super().__init__()

    def login_function(self, login: str, password: str) -> Status:
        login_url = "https://www.allaero.com/SignIn"

        if not self.request_wrapper(self.session.get, url=login_url):
            return self.status

        page = BeautifulSoup(self.response.text, "lxml")
        token = page.select_one("input[name='__RequestVerificationToken']")["value"]

        if not self.request_wrapper(self.session.post,
                                    url=login_url,
                                    params={"handler": "json-signin"},
                                    data={
                                        "SignInAttempt.EmailAddress": login,
                                        "SignInAttempt.Password": password,
                                        "__RequestVerificationToken": token,
                                    }):
            return self.status

        if self.response.url.startswith(login_url):
            self.logged_in = False
            self.status = Status.Login_error
            return self.status

        self.logged_in = True
        self.status = Status.OK
        return self.status

    def search_part(self, number: str, search_results: list) -> Status:
        if not self.request_wrapper(self.session.get, url=("https://www.allaero.com/aircraft-parts/" + number)):
            if self.response.status_code == 404:
                self.status = Status.OK
            return self.status

        page = BeautifulSoup(self.response.text, "lxml")

        self.product_info["part number"] = page.select_one("span[itemprop='identifier']").text
        self.product_info["description"] = page.select_one("span[itemprop='name']").text
        self.product_info["condition"] = condition.text if (condition := page.select_one(
            "td[data-title='Condition / Certification']")) is not None and condition.text != "Any" else ""
        self.product_info["lead time"] = availability.text if (availability := page.select_one(
            "td[data-title='Release:']")) is not None and availability.text != "Any" else ""
        self.product_info["QTY"] = qty.text.split(maxsplit=1)[0] if (qty := page.select_one(
            "td[data-title='Stock:']")) is not None else ""
        self.product_info["price"] = price.text if (price := page.select_one(
            "td[data-title='Price'] > div[id='CoreValue_0'] > span[class='value']")) is not None else ""

        alternatives = [part.select("a")[1].select_one("span").text.strip() for part in
                        page.select("div[class$='alternate-part']")]
        self.product_info["other information"] = f"interchanges: {" ; ".join(alternatives)}" if alternatives else ""

        search_results.append(deepcopy(self.product_info))

        return self.status

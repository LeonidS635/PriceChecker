from bs4 import BeautifulSoup
from copy import deepcopy
from Logic.data_file import Status
from Logic.parser import ParserRequests
from re import compile


class Boeingshop(ParserRequests):
    def __init__(self):
        super().__init__()

        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/121.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest"
        })

    def login_function(self, login: str, password: str) -> Status:
        self.session.cookies.clear()
        link = "https://shop.boeing.com/aviation-supply/"
        if not self.request_wrapper(self.session.get, url=(link + "login")):
            return self.status

        page = BeautifulSoup(self.response.text, 'lxml')
        csrf = page.select_one("input[name='CSRFToken']")["value"]
        login_data = {
            "isepubs": "false",
            "j_username": login,
            "j_password": password,
            "CSRFToken": csrf
        }

        if not self.request_wrapper(self.session.post, url=(link + "j_spring_security_check"), data=login_data):
            return self.status

        page = BeautifulSoup(self.response.text, "lxml")
        if page.find(string="Your email or password did not match our records. Please correct and try again.") or (
                page.find(string=" Please enter valid Username and Password.")):
            self.logged_in = False
            self.status = Status.Login_error
        else:
            self.logged_in = True
            self.status = Status.OK

        return self.status

    def search_part(self, number: str, search_results: list) -> Status:
        if not self.logged_in:
            self.status = Status.Login_error
            return self.status

        if not self.request_wrapper(self.session.get, url="https://shop.boeing.com/aviation-supply/search",
                                    params={"text": number}):
            return self.status

        page = BeautifulSoup(self.response.text, "lxml")
        for ref in page.select("a[class='productMainLink baselink level3 basefont blue hoverBrightBlue']"):
            part_number = ref.text.strip()
            if part_number != number:
                break

            if not self.request_wrapper(self.session.get, url=("https://shop.boeing.com" + ref["href"])):
                return self.status

            page = BeautifulSoup(self.response.text, "lxml")

            self.product_info["part number"] = part_number
            self.product_info["description"] = page.select_one("h1[class='breakWord']").text
            self.product_info["QTY"] = qty.text if ((
                qty := page.select_one("div[class='basefont level2']"))) is not None else ""
            self.product_info["price"] = price.text if ((
                price := page.select_one("span[id='prodNetPrice']"))) is not None else ""
            self.product_info["QTY"] = condition.text if ((
                condition := page.find("div", string=compile("Condition")).find_next_sibling(
                    "div"))) is not None else ""
            self.product_info["lead time"] = lead_time.text if ((
                lead_time := page.select_one("h1[class='basefont level5 mr-15']"))) is not None else ""
            self.product_info["warehouse"] = page.select_one("a[class='basefont level5 light notranslate']").text
            self.product_info["other information"] = f"available on {availability.text.strip()}" if ((
                availability := page.select_one(
                    "div[class='basefont light level5 floatleft']"))) is not None and availability.text.strip() else ""

            search_results.append(deepcopy(self.product_info))

        return self.status

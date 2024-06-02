from bs4 import BeautifulSoup
from re import compile
from requests import Session


class Boeingshop:
    def __init__(self):
        self.session = Session()

        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/121.0.0.0 Safari/537.36",
                "X-Requested-With": "XMLHttpRequest"
            })

        self.url = "https://shop.boeing.com/aviation-supply/search"

        self.logged_in = False
        self.status = "OK"

    def __del__(self):
        self.session.close()

    def login_function(self, login, password):
        log_in_link = "https://shop.boeing.com/aviation-supply/login"

        try:
            auth = self.session.get(log_in_link)
        except ConnectionError:
            self.status = "Connection error"
            return self.status

        bs = BeautifulSoup(auth.text, 'lxml')
        csrf = bs.find("input", {"name": "CSRFToken"})["value"]

        login_data = {
            "isepubs": "false",
            "j_username": login,
            "j_password": password,
            "CSRFToken": csrf
        }

        login_page = self.session.post("https://shop.boeing.com/aviation-supply/j_spring_security_check",
                                       data=login_data)
        login_bs = BeautifulSoup(login_page.text, "lxml")

        if login_bs.find(string="Your email or password did not match our records. Please correct and try again.") or (
                login_bs.find(string=" Please enter valid Username and Password.")):
            self.status = "Login error"
        else:
            self.logged_in = True
            self.status = "OK"

        return self.status

    def search_part(self, number, search_results):
        self.status = "OK"

        if not self.logged_in:
            self.status = "Login error"
            return self.status

        try:
            page = self.session.get(self.url, params={"text": number})
        except ConnectionError:
            self.status = "Connection error"
            return self.status

        bs = BeautifulSoup(page.text, "lxml")

        parts_refs = bs.find_all("a", {"class": "productMainLink baselink level3 basefont blue hoverBrightBlue"})

        if parts_refs:
            for ref in parts_refs:
                part_id = ref.text.strip()
                if part_id != number:
                    break

                part_page = self.session.get("https://shop.boeing.com" + ref["href"])
                part_bs = BeautifulSoup(part_page.text, "lxml")

                description = part_bs.find("h1", {"class": "breakWord"}).text.strip().lower()

                warehouse = part_bs.find("a", {"class": "basefont level5 light notranslate"}).text.strip()

                lead_time = part_bs.find("h1", {"class": "basefont level5 mr-15"})
                if lead_time is not None:
                    lead_time = lead_time.text.strip()
                else:
                    lead_time = ""

                availability = part_bs.find("div", {"class": "basefont light level5 floatleft"})
                if availability is not None:
                    availability = availability.text.strip()
                else:
                    availability = ""

                price = part_bs.find("span", {"id": "prodNetPrice"})
                if price is not None:
                    price = price.text.strip()
                else:
                    price = ""

                qty = part_bs.find("div", {"class": "basefont level2"})
                if qty is not None:
                    qty = qty.text.strip()
                else:
                    qty = ""

                condition = part_bs.find("div", string=compile("Condition")).find_next_sibling("div")
                if condition is not None:
                    condition = condition.text.strip()
                else:
                    condition = ""

                search_results.append({
                    "vendor": "boeingshop",
                    "part number": number,
                    "description": description,
                    "QTY": qty,
                    "price": price,
                    "condition": condition,
                    "lead time": lead_time,
                    "warehouse": warehouse,
                    "other information": f"available on{availability}" if availability else ""
                })

        return self.status

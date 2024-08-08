from bs4 import BeautifulSoup
from copy import deepcopy
from Logic.data_file import Status
from Logic.parser import ParserRequests
import re


class Aerospareparts(ParserRequests):
    def __init__(self):
        super().__init__()

    def login_function(self, login: str, password: str) -> Status:
        login_url = "https://aerospareparts.com/Utilisateur/Login"
        if not self.request_wrapper(self.session.get, url=login_url):
            return self.status

        page = BeautifulSoup(self.response.text, "lxml")
        token = page.select_one("input[name='__RequestVerificationToken']")["value"]

        login_data = {
            "__RequestVerificationToken": token,
            "UserName": login,
            "Password": password,
        }

        if not self.request_wrapper(self.session.post, url=login_url, data=login_data):
            return self.status

        page = BeautifulSoup(self.response.text, "lxml")
        error_notification = page.select_one("div[class='validation-summary-errors text-danger']")

        if error_notification is not None:
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

        self.status = Status.OK
        self.reset_product_info()

        if not self.request_wrapper(self.session.get, url=("https://aerospareparts.com/PartNumber/" + number)):
            return self.status

        page = BeautifulSoup(self.response.text, "lxml")
        if page.select_one("div[class='alert alert-warning fade in']") is not None:
            self.logged_in = False
            self.status = Status.Login_error
            return self.status

        if page.find(string="has not been found.") is not None:
            self.status = Status.OK
            return self.status

        self.product_info["part number"] = page.find("span", string="Part Number :").next_sibling.text
        self.product_info["description"] = page.find("span", string="Description :").next_sibling.text
        self.product_info["QTY"] = qty.next_sibling.text.split()[0] if ((
            qty := page.find("span", string="Stock available :"))) is not None else ""

        titles = [title.next_sibling.text.strip().replace(" :", "") for title in
                  page.select("h4[class='Mine'] > label")]
        tables = page.select("table[class='Grid']")
        quote_request_refs: list[(str, dict[str, str])] = []
        refs_set = set()
        for i in range(len(tables)):
            title = titles[i]
            refs = [elem.get("href") for elem in tables[i].select("a[class='AutoquoteActionLink']")]
            if len(refs) == 0:
                if title == "on request":
                    table_headers = [table_header.text.strip() for table_header in tables[i].select("th")]
                    for row in tables[i].select("tbody > tr"):
                        cols = row.select("td")
                        self.product_info["vendor"] = self.vendor + f" ({title})"
                        self.product_info["condition"] = cols[table_headers.index("CD")].text
                        self.product_info["warehouse"] = cols[table_headers.index("Incoterms")].text
                        self.product_info["lead time"] = cols[table_headers.index("Std Leadtime")].text
                        try:
                            self.product_info["QTY"] = cols[table_headers.index("Stk qty")].text.split('*')[0]
                        except ValueError:
                            pass

                        search_results.append(deepcopy(self.product_info))
            else:
                for ref in refs:
                    a = ref.find("StockLocation")
                    b = ref.find('&', a)
                    copy_ref = ref.replace(ref[a:b+1], "")
                    if copy_ref not in refs_set:
                        refs_set.add(copy_ref)
                        if not self.request_wrapper(self.session.get, url=("https://aerospareparts.com/" + ref)):
                            return self.status

                        page = BeautifulSoup(self.response.text, "lxml")
                        payload = {
                            "PN": page.select_one("input[name='PN']")["value"],
                            "Description": page.select_one("input[name='Description']")["value"],
                            "UOM": page.select_one("input[name='UOM']")["value"],
                            "COND": page.select_one("input[name='COND']")["value"],
                            "Country": page.select_one("input[name='Country']")["value"],
                            "StockAvailable": page.select_one("input[name='StockAvailable']")["value"],
                            "StockAvailableToDisplay": page.select_one("input[name='StockAvailableToDisplay']")[
                                "value"],
                            "LT": page.select_one("input[name='LT']")["value"],
                            "RequestedQuantity": "1",
                            "submit": "Quote now",
                        }
                        quote_request_refs.append((title, payload))

        for title, payload in quote_request_refs:
            if not self.request_wrapper(self.session.post, url="https://aerospareparts.com/PN/InstantQuote",
                                        data=payload):
                return self.status

            page = BeautifulSoup(self.response.text, "lxml")
            table = page.select_one("table[class='Grid']")
            if table is not None:
                table_headers = [table_header.text.strip() for table_header in table.select("th")]
                for row in table.select("tbody > tr"):
                    cols = row.select("td")
                    self.product_info["vendor"] = self.vendor + f" ({title})"
                    self.product_info["condition"] = page.find(
                        "label", string=re.compile("Condition")).find_next_sibling("span").text
                    self.product_info["QTY"] = qty.find_next_sibling("span").text if ((
                        qty := page.find("label", string=re.compile("Stock available")))) is not None else re.sub(
                        "[^0-9]", "", cols[table_headers.index("QTY")].text.split()[0])
                    self.product_info["price"] = cols[table_headers.index("Unit price")].text
                    self.product_info["lead time"] = cols[table_headers.index("LT")].text.replace('*', "")
                    self.product_info["warehouse"] = cols[table_headers.index("Incoterms")].text

                    search_results.append(deepcopy(self.product_info))

        return self.status

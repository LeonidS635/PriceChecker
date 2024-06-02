from bs4 import BeautifulSoup
import requests


class Aerobay:
    def __init__(self):
        self.session = requests.Session()

        self.url = "https://www.aero-bay.com/q"

        self.logged_in = False
        self.status = "OK"

    def __del__(self):
        self.session.close()

    def login_function(self, login, password):
        log_in_link = "https://www.aero-bay.com"

        try:
            auth = self.session.get(log_in_link)
        except ConnectionError:
            self.status = "Connection error"
            return self.status

        bs = BeautifulSoup(auth.text, 'lxml')
        csrf = bs.find("input", {"name": "_csrf"})["value"]

        login_data = {
            "_csrf": csrf,
            "userName": login,
            "password": password
        }

        login_page = self.session.post(log_in_link + "/j_spring_security_check", data=login_data)
        login_bs = BeautifulSoup(login_page.text, "lxml")

        if not login_bs.find(string="Email or password is incorrect"):
            self.logged_in = True
            self.status = "OK"
        else:
            self.status = "Login error"

        return self.status

    def search_part(self, number, search_results):
        if not self.logged_in:
            self.status = "Login error"
            return self.status

        self.status = "OK"

        page_number = 1

        exact_match = True
        while exact_match:
            try:
                page = self.session.get(self.url,
                                        params={"searchType": "PART_NUMBER", "item": number, "page": page_number})
            except ConnectionError:
                self.status = "Connection error"
                return self.status

            bs = BeautifulSoup(page.text, "lxml")

            part = bs.find("div", {"class": "item"})

            if not part:
                break

            while part:
                part_id = part.find("strong").text
                if part_id != number:
                    exact_match = False
                    break

                price_span = part.find("span", {"class": "small-text bold"}).find("span")

                if price_span["class"][0] == "blue-text":
                    spans = price_span.contents
                    price = spans[1].text + spans[3].text + '.' + spans[5].text
                else:
                    price = ''

                description = part.find("p", {"class": "lit-bold black-text"}).text.lower()

                table = part.find("table")
                cc, qty, _, _, lead_time, _, _ = table.find_all("tr")[1].find_all("td")

                search_results.append({
                    "vendor": "aerobay",
                    "part number": number,
                    "description": description,
                    "QTY": qty.contents[0].text,
                    "price": price,
                    "condition": cc.find("span").text,
                    "lead time": lead_time.text.strip()
                })

                part = part.find_next("div", {"class": "item"})

            page_number += 1

        return self.status

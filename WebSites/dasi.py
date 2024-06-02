from bs4 import BeautifulSoup
from PIL import Image
from requests import Session


class Dasi:
    def __init__(self):
        self.session = Session()

        self.url = "https://store.dasi.com/search.aspx"

        self.logged_in = False
        self.status = "OK"

    def __del__(self):
        self.session.close()

    def download_captcha(self):
        captcha_url = "https://store.dasi.com/captchaimage.aspx"

        try:
            img_bytes = self.session.get(captcha_url).content
        except ConnectionError:
            self.status = "Connection error"
            return self.status

        file = "../captcha.png"
        with open(file, "wb") as f:
            f.write(img_bytes)

        img = Image.open(file)

        return img

    def login_function(self, login, password, captcha_code):
        log_in_link = "https://store.dasi.com/login.aspx"

        login_data = {
            "__EVENTTARGET": '',
            "__EVENTARGUMENT": '',
            "__VIEWSTATE": "/wEPDwUJNTIyOTQwNjUwDxYCHhNWYWxpZGF0ZVJlcXVlc3RNb2RlAgEWAmYPZBYCZg9kFgQCAQ9kFgQCAQ8WAh4HY29"
                           "udGVudAVJYWlyY3JhZnQgcGFydHMgc2hvcCwgYWlyY3JhZnQgcGFydHMsIGFpcmNyYWZ0IHBhcnRzIHN0b3JlLGFpcm"
                           "NyYWZ0IHNwYXJlc2QCAg8WAh8BBUlhaXJjcmFmdCBwYXJ0cyBzaG9wLCBhaXJjcmFmdCBwYXJ0cywgYWlyY3JhZnQgc"
                           "GFydHMgc3RvcmUsYWlyY3JhZnQgc3BhcmVzZAIDD2QWBgIDD2QWBgIBDw8WAh4EVGV4dGVkZAIED2QWAgIBDw8WBB8C"
                           "BUZZb3VyIFJGUSBMaXN0ICA8c3BhbiBjbGFzcz0ibnVtYmVyLW9mLWl0ZW1zIGF2YW50Z2FyZGUiPjAgaXRlbXM8L3N"
                           "wYW4+HgdWaXNpYmxlZ2RkAgUPZBYCZg8PFgQfAgVEWW91ciBCYXNrZXQgIDxzcGFuIGNsYXNzPSJudW1iZXItb2YtaX"
                           "RlbXMgYXZhbnRnYXJkZSI+MCBpdGVtczwvc3Bhbj4fA2dkZAIHD2QWAgIBD2QWAgIBD2QWBmYPDxYEHghDc3NDbGFzc"
                           "wUbbG9naW4tYmxvY2sgY2FwdGNoYS1lbmFibGVkHgRfIVNCAgJkFgICAQ9kFgJmD2QWBgIBDw8WAh8CBQ5FLU1haWwg"
                           "QWRkcmVzc2RkAgUPDxYEHgxFcnJvck1lc3NhZ2UFEkUtTWFpbCBpcyByZXF1aXJlZB4HVG9vbFRpcAUSRS1NYWlsIGl"
                           "zIHJlcXVpcmVkZGQCEw8QDxYCHgdDaGVja2VkZ2RkZGQCAQ8WAh4FY2xhc3MFDnJlZ2lzdGVyLWJsb2NrZAICDw8WAh"
                           "8DaGRkAgkPDxYCHwNoZGQYAQUeX19Db250cm9sc1JlcXVpcmVQb3N0QmFja0tleV9fFgEFPGN0bDAwJGN0bDAwJGNwa"
                           "DEkY3BoMSRjdHJsQ3VzdG9tZXJMb2dpbiRMb2dpbkZvcm0kUmVtZW1iZXJNZTjF+9m2oAG/L3N1s8h7bEk1zUPqHsgv"
                           "0+IpXKxOh7ZD",
            "__VIEWSTATEGENERATOR": "C2EE9ABB",
            "__EVENTVALIDATION": "/wEdAAr3bUa7Wg4d/ZBb1nLyJe9KB1UBbML48F9m+hWYCnqUDTUmcUgfosjnvZMp2kV7czLNgF8KE98jjndmd"
                                 "Hmxe+sJMd+x9CnyE6uy9EdExtQCi7k1aWiQn7HuxXZiIiXKqSQGTifwAIfWsMP5RrgbOsx2yZsu2o3OMkbLMd"
                                 "ZLie/WDTnaq4fovkG52O4F9W/i5U2Rs0ZWZysMhcm+7TN2GSNmOUVZgVa+L9MzoM9FruZIBM++DIGc22vJsaV"
                                 "8Ck6KUPU=",
            "ctl00$ctl00$cph1$cph1$ctrlCustomerLogin$LoginForm$UserName": login,
            "ctl00$ctl00$cph1$cph1$ctrlCustomerLogin$LoginForm$Password": password,
            "ctl00$ctl00$cph1$cph1$ctrlCustomerLogin$LoginForm$CaptchaCtrl$txtCode": captcha_code,
            "ctl00$ctl00$cph1$cph1$ctrlCustomerLogin$LoginForm$LoginButton": "Log in"
        }

        try:
            login_page = self.session.post(log_in_link, data=login_data)
        except ConnectionError:
            self.status = "Connection error"
            return self.status

        login_bs = BeautifulSoup(login_page.text, "lxml")

        if not login_bs.find(string="Incorrect, try again."):
            self.logged_in = True
            self.status = "OK"
        else:
            self.status = "Login error"

        return self.status

    def search_part(self, number, search_results):
        self.status = "OK"

        if not self.logged_in:
            self.status = "Login error"
            return self.status

        try:
            page = self.session.get(self.url, params={"searchterms": number})
        except ConnectionError:
            self.status = "Connection error"
            return self.status

        bs = BeautifulSoup(page.text, "lxml")

        parts_table = bs.find("table", {"id": "ctl00_ctl00_cph1_cph1_ctrlSearch_ctrlProductsInGrid_gvProducts"})

        if parts_table:
            exact_match = False
            for part in parts_table.select("tr"):
                if exact_match:
                    break

                if not part.find("table"):
                    continue

                part_id = part.find("div", {"class": "product_list_title"}).text.strip().split()[0]
                if part_id != number:
                    continue

                exact_match = True

                table = part.select("table", {"class": "prodlist"})[0]
                for tr in table.select("tr"):
                    td = tr.select("td")
                    if not td:
                        continue

                    condition, stock_descr, warehouse, lead_time, trace_to_org, _, _, avail, price, _, _, _, _, _ = td

                    trace_to_org_text = trace_to_org.text
                    if trace_to_org_text:
                        trace_to_org_text = " ".join([word.strip() for word in trace_to_org_text.split()])

                    search_results.append({
                        "vendor": "dasi",
                        "part number": number,
                        "description": stock_descr.text.lower(),
                        "QTY": avail.find("span").text,
                        "price": price.find("span").text,
                        "condition": condition.text,
                        "lead time": lead_time.text.strip(),
                        "warehouse": warehouse.find("span").text,
                        "other information": f"trace to org: {trace_to_org_text}"
                    })

        return self.status

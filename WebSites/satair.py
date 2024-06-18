from copy import deepcopy
from requests import Session, Response
from requests.exceptions import Timeout, RequestException
from typing import Callable


class Satair:
    def __init__(self):
        self.session = Session()

        self.auth_info = {}
        self.logged_in = False
        self.status = "OK"

        self.response = None

        self.delay = 20

    def __del__(self):
        self.session.close()

    def request_wrapper(self, request: Callable[[], Response]) -> bool:
        try:
            self.response = request()
            self.response.raise_for_status()
        except Timeout:
            self.status = "Time error"
            return False
        except RequestException:
            self.status = "Connection error"
            return False
        else:
            return True

    def login_function(self, login: str, password: str) -> str:
        login_url = "https://www.satair.com/api/login"
        payload = {
            "userId": login,
            "password": password,
            "rememberMe": False
        }

        if not self.request_wrapper(lambda: self.session.post(login_url, json=payload, timeout=self.delay)):
            return self.status

        data = self.response.json()

        if "Notification" in data.keys():
            self.status = "Login error"
            self.logged_in = False
        else:
            self.auth_info = {
                "accessToken": data["Authentication"]["AccessToken"],
                "refreshToken": data["Authentication"]["RefreshToken"],
                "globalId": data["Authentication"]["GlobalId"]
            }

            self.status = "OK"
            self.logged_in = True

        return self.status

    def search_part(self, number: str, search_results: list) -> str:
        if not self.logged_in:
            self.status = "Login error"
            return self.status

        product_info = {
            "vendor": "satair",
            "part number": "",
            "description": "",
            "QTY": "",
            "price": "",
            "condition": "",
            "lead time": "",
            "warehouse": "",
            "other information": ""
        }

        add_info_url = "https://www.satair.com/api/product/additionalinfo/"
        interchanges_url = "https://www.satair.com/api/product/interchangeable"
        plants_url = "https://www.satair.com/api/product/plants/"
        offer_search_url = f"https://www.satair.com/api/offersearch?urlParams=q%3D{number}"

        if not self.request_wrapper(lambda: self.session.get(offer_search_url, timeout=self.delay)):
            return self.status

        products = self.response.json()["Data"]["Products"]
        info_params = {"productPriceRequests": []}
        for product in products:
            if product["ManufacturerAid"] != number:
                break

            info_params["productPriceRequests"].append({
                "OfferId": product["Code"],
                "Quantity": 1
            })

        if not info_params["productPriceRequests"]:
            return self.status

        if not self.request_wrapper(
                lambda: self.session.post(add_info_url, json=info_params, cookies=self.auth_info, timeout=self.delay)):
            return self.status

        add_info_products = self.response.json()
        if not add_info_products:
            return self.status

        for i, product in enumerate(products):
            product_info["part number"] = product["Sku"]
            product_info["description"] = product["Name"].lower()
            product_info["condition"] = product["State"]
            product_info["QTY"] = str(add_info_products["Data"][i]["RemainingOfferQuantity"]) \
                if add_info_products["Data"][i]["RemainingOfferQuantity"] else ""
            product_info["price"] = add_info_products["Data"][i]["Price"]["Value"] \
                if ("Value" in add_info_products["Data"][i]["Price"].keys() and
                    add_info_products["Data"][i]["Price"]["Value"] != "0") else ""
            product_info["lead time"] = add_info_products["Data"][i]["StockIndication"] \
                if add_info_products["Data"][i]["StockIndication"] != "N/A" else ""
            product_info["warehouse"] = add_info_products["Data"][i]["Warehouse"]["Name"] \
                if "Warehouse" in add_info_products["Data"][i].keys() else ""

            if not self.request_wrapper(
                    lambda: self.session.get(interchanges_url, data={"sku": product_info["part number"]},
                                             cookies=self.auth_info)):
                return self.status

            interchanges_data = self.response.json()
            interchanges_list = []
            if interchanges_data:
                for interchangeable in interchanges_data["Data"]:
                    interchanges_list.append(interchangeable["Sku"])
            interchanges = " ; ".join(interchanges_list) if interchanges_list else ""
            product_info["other information"] = f"interchanges: {interchanges}" if interchanges else ""

            if not self.request_wrapper(
                    lambda: self.session.get(plants_url + product["Code"], cookies=self.auth_info, timeout=self.delay)):
                return self.status

            plants_data = self.response.json()
            if plants_data and plants_data["Data"]["HasPlants"]:
                for plant in plants_data["Data"]["Plants"]:
                    if plant["InStock"]:
                        product_info["lead time"] = "In stock"
                    product_info["QTY"] = str(plant["Quantity"])
                    product_info["warehouse"] = plant["Warehouse"]

                    search_results.append(deepcopy(product_info))
            else:
                search_results.append(deepcopy(product_info))

        return self.status

    def change_delay(self, new_delay):
        self.delay = new_delay

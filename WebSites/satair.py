from copy import deepcopy
from Logic.data_file import Status
from Logic.parser import ParserRequests


class Satair(ParserRequests):
    def __init__(self):
        super().__init__()

        self.auth_info = {}

    def login_function(self, login: str, password: str) -> Status:
        login_url = "https://www.satair.com/api/login"
        payload = {
            "userId": login,
            "password": password,
            "rememberMe": False
        }

        if not self.request_wrapper(self.session.post, url=login_url, json=payload):
            return self.status

        data = self.response.json()

        if "Notification" in data.keys():
            self.status = Status.Login_error
            self.logged_in = False
        else:
            self.auth_info = {
                "accessToken": data["Authentication"]["AccessToken"],
                "refreshToken": data["Authentication"]["RefreshToken"],
                "globalId": data["Authentication"]["GlobalId"]
            }

            self.status = Status.OK
            self.logged_in = True

        return self.status

    def search_part(self, number: str, search_results: list) -> Status:
        if not self.logged_in:
            self.status = Status.Login_error
            return self.status

        add_info_url = "https://www.satair.com/api/product/additionalinfo/"
        interchanges_url = "https://www.satair.com/api/product/interchangeable"
        plants_url = "https://www.satair.com/api/product/plants/"
        offer_search_url = f"https://www.satair.com/api/offersearch?urlParams=q%3D{number}"

        if not self.request_wrapper(self.session.get, url=offer_search_url):
            return self.status

        products = self.response.json()["Data"]["Products"]
        products_number = len(products)
        batch_size = 5

        for batch_index in range((products_number + batch_size - 1) // batch_size):
            info_params = {"productPriceRequests": []}
            for i in range(batch_index * batch_size, min(products_number, (batch_index + 1) * batch_size)):
                if products[i]["ManufacturerAid"].upper() != number.upper():
                    break

                info_params["productPriceRequests"].append({
                    "OfferId": products[i]["Code"],
                    "Quantity": 1
                })

            if not info_params["productPriceRequests"]:
                return self.status

            if not self.request_wrapper(self.session.post, url=add_info_url, json=info_params, cookies=self.auth_info):
                return self.status

            add_info_products = self.response.json()
            if not add_info_products:
                return self.status

            for i in range(batch_index * batch_size, min(products_number, (batch_index + 1) * batch_size)):
                if products[i]["ManufacturerAid"].upper() != number.upper():
                    break

                batch_int_index = i - batch_index * batch_size

                self.reset_product_info()
                self.product_info["part number"] = products[i]["Sku"]
                self.product_info["description"] = products[i]["Name"]
                self.product_info["condition"] = products[i]["State"]
                self.product_info["QTY"] = str(qty) if (
                    qty := add_info_products["Data"][batch_int_index]["RemainingOfferQuantity"]) else ""
                self.product_info["price"] = '$' + price if (
                        (price := add_info_products["Data"][batch_int_index]["Price"].get("Value")) is not None and
                        price != "0") else ""
                self.product_info["lead time"] = lead_time if (
                        (lead_time := add_info_products["Data"][batch_int_index]["StockIndication"]) != "N/A") else ""
                self.product_info["warehouse"] = warehouse_dict["Name"] if (
                        (warehouse_dict := add_info_products["Data"][batch_int_index].get(
                            "Warehouse")) is not None) else ""

                interchanges_list = []
                for interchangeable in products[i].get("SatairInterchangeables", []):
                    interchanges_list.append(f"{interchangeable["PartNumber"]}:{interchangeable['CageCode']}")
                interchanges = " ; ".join(interchanges_list) if interchanges_list else ""
                self.product_info["other information"] = f"interchanges: {interchanges}" if interchanges else ""

                if not self.request_wrapper(self.session.get, url=plants_url + products[i]["Code"],
                                            cookies=self.auth_info):
                    return self.status

                plants_data = self.response.json()
                if plants_data and plants_data["Data"]["HasPlants"]:
                    for plant in plants_data["Data"]["Plants"]:
                        if plant["InStock"]:
                            self.product_info["lead time"] = "In stock"
                        self.product_info["QTY"] = str(plant["Quantity"])
                        self.product_info["warehouse"] = plant["Warehouse"]

                        search_results.append(deepcopy(self.product_info))
                else:
                    search_results.append(deepcopy(self.product_info))

        return self.status

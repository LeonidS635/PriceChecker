from importlib import import_module
from enum import Enum
from os import listdir


class Status(Enum):
    OK = 1
    Login_error = 2
    Connection_error = 3
    Time_error = 4
    Other = 5


class DataClass:
    def __init__(self):
        self.parsers = []
        self.websites_names = []
        self.websites_names_with_captcha_for_login = ["Dasi"]

        for file_name in listdir("PriceChecker-master/WebSites"):
            if file_name[-3:] == ".py":
                module_name = file_name.split('.')[0]
                class_name = module_name.capitalize()

                module = import_module(f"WebSites.{module_name}")
                cls = getattr(module, class_name)

                self.parsers.append(cls)
                self.websites_names.append(class_name)

        self.conditions_checkers = [
            ("New surplus", lambda condition: condition.lower() == "new surplus" or condition.lower() == "ns"),
            ("New", lambda condition: condition.lower().find("new") != -1 or condition.lower() == "ne"),
            ("Overhaul", lambda condition: condition.lower() == "overhaul" or condition.lower() == "oh"),
            ("As removed", lambda condition: condition.lower() == "as removed" or condition.lower() == "ar"),
        ]
        self.conditions_checkers.append(
            ("Serviceable", lambda condition: all(not condition_checker(condition) for name, condition_checker in
                                                  self.conditions_checkers if name != "Serviceable"))
        )

        self.websites_to_search = {website_name: True for website_name in self.websites_names}
        self.conditions_to_search = [True for _ in range(len(self.conditions_checkers))]
        self.logged_in_websites = {website_name: False for website_name in self.websites_names}

        self.all_search_results: list[tuple[str, list]] = []
        self.headers = ["vendor", "part number", "description", "QTY", "price", "condition", "lead time",
                        "warehouse", "other information"]

        self.passwords_file = "passwords.json"

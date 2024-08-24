from enum import Enum
from importlib import import_module
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
        self.parsers_classes = []
        self.loaded_excel_files_data: dict[str, list[dict[str, str]]] = {}
        self.websites_names: list[str] = []
        self.websites_names_with_captcha_for_login: list[str] = ["Dasi"]
        self.conditions: list[str] = ["New surplus", "New", "Overhaul", "As removed", "Serviceable"]

        for file_name in listdir("PriceChecker-master/WebSites"):
            if file_name[-3:] == ".py":
                module_name = file_name.split('.')[0]
                class_name = module_name.capitalize()

                module = import_module(f"WebSites.{module_name}")
                cls = getattr(module, class_name)

                self.parsers_classes.append(cls)
                self.websites_names.append(class_name)

        self.websites_to_search = {website_name: True for website_name in self.websites_names}
        self.conditions_to_search = {condition: True for condition in self.conditions}
        self.logged_in_websites = {website_name: False for website_name in self.websites_names}

        self.all_search_results: list[tuple[str, list[dict[str, str]]]] = []
        self.headers = ["vendor", "part number", "description", "QTY", "price", "condition", "lead time",
                        "warehouse", "other information"]

        self.passwords_file = "passwords.json"

    @staticmethod
    def get_condition(condition: str) -> str:
        if condition.lower() == "new surplus" or condition.lower() == "ns":
            return "New surplus"
        if condition.lower().find("new") != -1 or condition.lower() == "ne":
            return "New"
        if condition.lower() == "overhaul" or condition.lower() == "oh":
            return "Overhaul"
        if condition.lower() == "as removed" or condition.lower() == "ar":
            return "As removed"
        return "Serviceable"

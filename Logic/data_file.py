from importlib import import_module
from os import listdir


class DataClass:
    def __init__(self, master):
        self.master = master

        self.parsers = []
        self.websites_names = []

        for file_name in listdir("PriceChecker-master/WebSites"):
            if file_name[-3:] == ".py":
                module_name = file_name.split('.')[0]
                class_name = module_name.capitalize()

                module = import_module(f"WebSites.{module_name}")
                cls = getattr(module, class_name)

                self.parsers.append(cls)
                self.websites_names.append(class_name)

        self.conditions_checker = {
            "New surplus": lambda condition: condition.lower() == "new surplus" or condition.lower() == "ns",
            "New": lambda condition: condition.lower().find("new") != -1 or condition.lower() == "ne",
            "Overhaul": lambda condition: condition.lower() == "overhaul" or condition.lower() == "oh",
            "As removed": lambda condition: condition.lower() == "as removed" or condition.lower() == "ar",
            "Serviceable": lambda condition: not self.conditions_checker["New surplus"](condition) and (
                    not self.conditions_checker["New"](condition) and not self.conditions_checker["Overhaul"](condition)
                    and not self.conditions_checker["As removed"](condition)
            )
        }

        self.websites_to_search = [True for _ in range(len(self.websites_names))]
        self.conditions_to_search = [True for _ in range(len(self.conditions_checker))]
        self.logged_in_websites = [False for _ in range(len(self.websites_names))]

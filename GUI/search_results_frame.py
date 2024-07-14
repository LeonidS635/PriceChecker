from CTkXYFrame import CTkXYFrame
from csv import DictWriter
from Logic.data_file import DataClass
from pyperclip import copy
from textwrap import wrap
from tkinter import ttk, CENTER
from time import localtime, strftime


class SearchResultsFrame(CTkXYFrame):
    def __init__(self, data: DataClass, **kwargs):
        super().__init__(master=data.master, **kwargs)

        self.data = data
        self.all_search_results = {}

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.results_tables = []
        self.table_headers = ["vendor", "part number", "description", "QTY", "price", "condition", "lead time",
                              "warehouse", "other information"]

        self.style = ttk.Style()
        self.style.theme_use("default")

        self.style.configure("Treeview",
                             background="#2a2d2e",
                             foreground="white",
                             fieldbackground="#343638",
                             bordercolor="#343638",
                             borderwidth=0)
        self.style.map('Treeview', background=[('selected', '#22559b')])

        self.style.configure("Treeview.Heading",
                             background="#32a8a4",
                             foreground="black",
                             relief="flat")

        self.style.map("Treeview.Heading",
                       background=[('active', '#3484F0')])

    def print_search_results(self, part_number: int, search_results: list):
        table = ttk.Treeview(self, columns=self.table_headers, show="headings", style="Treeview")

        for i, header in enumerate(self.table_headers):
            table.heading(i, text=header)
            if header in ["QTY", "price", "condition"]:
                table.column(i, anchor=CENTER, width=100)
            elif header in ["lead time", "vendor", "part number"]:
                table.column(i, anchor=CENTER, width=200)
            elif header == "other information":
                table.column(i, anchor=CENTER, width=600)
            else:
                table.column(i, anchor=CENTER, width=300)

        rows_num = 0
        if len(search_results) == 0:
            table.insert('', "end", values=[f"{part_number}" if key == "part number" else
                                            ("No such part" if key == "description" else "") for key in
                                            self.table_headers], tags=("odd",))
            rows_num = 1
        else:
            self.prepare_search_results(search_results)

            for index, dictionary in enumerate(sorted(search_results, key=lambda d: d["vendor"])):
                for i in range(len(self.data.websites_to_search)):
                    if self.data.websites_names[i].lower() in dictionary["vendor"] and (
                            not self.data.websites_to_search[i]):
                        break
                else:
                    for i, (_, checker) in enumerate(self.data.conditions_checker.items()):
                        if self.data.conditions_to_search[i] and checker(dictionary["condition"]):
                            rows_num += 1
                            table.insert('', "end", tags=("odd" if rows_num % 2 == 1 else "even",),
                                         values=[self.wrap(dictionary[key], table.column(i, "width")) for key in
                                                 self.table_headers])
                            break

        if rows_num != 0:
            table.configure(height=rows_num)

            table.tag_configure("odd", foreground="black", background="lightgrey")
            table.tag_configure("even", foreground="black", background="white")

            table.bind("<Control-Key-c>", lambda event: self.copy_from_treeview(table))

            table.grid()

            self.results_tables.append(table)

    def update_search_results(self, _=None):
        for table in self.results_tables:
            table.destroy()
        self.results_tables.clear()

        for part_number, search_results in self.all_search_results.items():
            self.print_search_results(part_number, search_results)

    def create_csv(self):
        moment = strftime("%Y-%b-%d__%H_%M_%S", localtime())
        with open(f"out_{moment}.csv", "w") as out:
            writer = DictWriter(out, fieldnames=self.table_headers)
            writer.writeheader()

            for part_number, search_results in self.all_search_results.items():
                self.prepare_search_results(search_results)

                for dictionary in sorted(search_results, key=lambda d: d["vendor"]):
                    for i in range(len(self.data.websites_to_search)):
                        if self.data.websites_names[i].lower() in dictionary["vendor"] and (
                                not self.data.websites_to_search[i]):
                            break
                    else:
                        for i, (_, checker) in enumerate(self.data.conditions_checker.items()):
                            if self.data.conditions_to_search[i] and checker(dictionary["condition"]):
                                writer.writerow(dictionary)
                                break

    def prepare_search_results(self, search_results):
        all_keys = set(self.table_headers)

        for dictionary in search_results:
            missing_keys = all_keys - dictionary.keys()
            for key in missing_keys:
                dictionary[key] = ""

        for dictionary in search_results:
            for key in dictionary.keys():
                if dictionary[key] == "":
                    dictionary[key] = " "

    @staticmethod
    def copy_from_treeview(table):
        copied_string = ""
        for row in table.selection():
            values = table.item(row, "values")
            copied_string += ','.join(values)
            copied_string += '\n'

        copy(copied_string)

    @staticmethod
    def wrap(string, length):
        return '\n'.join(wrap(string, int(length)))

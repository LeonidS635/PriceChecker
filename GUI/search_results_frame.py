from CTkXYFrame import CTkXYFrame
from Logic.data_file import DataClass
from pyperclip import copy
from textwrap import wrap
from tkinter import ttk, CENTER


class SearchResultsFrame(CTkXYFrame):
    def __init__(self, master, data: DataClass, **kwargs):
        super().__init__(master=master, **kwargs)

        self.data = data
        self.search_results_idx = 0
        self.results_tables = []

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

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

    def clear(self):
        for table in self.results_tables:
            table.destroy()
        self.results_tables.clear()
        self.search_results_idx = 0

    def beautify_search_results(self):
        for _, product_info_list in self.data.all_search_results:
            for product_info in product_info_list:
                for key in product_info.keys():
                    product_info[key] = product_info[key].strip()

    def prepare_search_results(self, search_results):
        all_keys = set(self.data.headers)

        for dictionary in search_results:
            missing_keys = all_keys - dictionary.keys()
            for key in missing_keys:
                dictionary[key] = ""

        for dictionary in search_results:
            for key in dictionary.keys():
                if dictionary[key] == "":
                    dictionary[key] = " "

    def print_search_results(self):
        part_number, search_results = self.data.all_search_results[self.search_results_idx]
        self.search_results_idx += 1

        table = ttk.Treeview(self, columns=self.data.headers, show="headings", style="Treeview")

        for i, header in enumerate(self.data.headers):
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
                                            self.data.headers], tags=("odd",))
            rows_num = 1
        else:
            self.beautify_search_results()
            self.prepare_search_results(search_results)

            for index, dictionary in enumerate(sorted(search_results, key=lambda d: d["vendor"])):
                for website_name in self.data.websites_names:
                    if website_name.lower() in dictionary["vendor"] and not self.data.websites_to_search[website_name]:
                        break
                else:
                    for i in range(len(self.data.conditions_to_search)):
                        if self.data.conditions_to_search[i] and self.data.conditions_checkers[i][1](
                                dictionary["condition"]):
                            rows_num += 1
                            table.insert('', "end", tags=("odd" if rows_num % 2 == 1 else "even",),
                                         values=[self.wrap(dictionary[key], table.column(i, "width")) for key in
                                                 self.data.headers])
                            break

        if rows_num != 0:
            table.configure(height=rows_num)

            table.tag_configure("odd", foreground="black", background="lightgrey")
            table.tag_configure("even", foreground="black", background="white")

            table.bind("<Control-Key-c>", lambda event: self.copy_from_treeview(table))

            table.grid()

            self.results_tables.append(table)

    def update_search_results(self, _=None):
        self.clear()
        for _ in range(len(self.data.all_search_results)):
            self.print_search_results()

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

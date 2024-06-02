import tkinter

import customtkinter
from threading import Thread
from concurrent.futures import ThreadPoolExecutor, wait
from CTkXYFrame import CTkXYFrame
import ctypes
from csv import DictWriter
from pyperclip import copy
import textwrap

from tkinter import ttk
import time


class SearchResultsFrame(CTkXYFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

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

    def print_search_results(self, search_results_dict, websites_list_frame):
        for part_number, search_results in search_results_dict.items():
            # if len(search_results) == 0:
            #     table = CTkTable(self, values=[self.table_headers], header_color="#32a8a4", corner_radius=0, width=200)
            #     table.add_row(values=[f"{part_number}" if key == "part number" else
            #                           ("No such part" if key == "description" else "") for key in self.table_headers])
            #     table.edit_column(len(self.table_headers) - 1, width=1000)
            # else:
            # table = CTkTable(self, column=len(self.table_headers), values=[self.table_headers],
            #                  header_color="#32a8a4", corner_radius=0, width=1000, wraplength=200,
            #                  command=lambda cell: copy(" ".join(table.get_row(cell["row"]))))
            #
            # for i, header in enumerate(self.table_headers):
            #     if header in ["QTY", "price", "condition", "lead time"]:
            #         table.edit_column(i, width=100)
            #     elif header == "other information":
            #         table.edit_column(i, width=500)
            #     else:
            #         table.edit_column(i, width=200)
            #
            # self.prepare_search_results(search_results)
            #
            # for index, dictionary in enumerate(sorted(search_results, key=lambda d: d["vendor"])):
            #     for i in range(len(websites_list_frame.websites_to_search)):
            #         if websites_list_frame.websites_names[i].lower() in dictionary["vendor"] and (
            #                 not websites_list_frame.websites_to_search[i]):
            #             break
            #     else:
            #         for i, (_, checker) in enumerate(websites_list_frame.conditions_checker.items()):
            #             if websites_list_frame.conditions_to_search[i] and checker(dictionary["condition"]):
            #                 table.add_row(values=[dictionary[key] for key in self.table_headers])
            #                 break

            table = ttk.Treeview(self, columns=self.table_headers, show="headings", style="Treeview")

            for i, header in enumerate(self.table_headers):
                table.heading(i, text=header)
                if header in ["QTY", "price", "condition"]:
                    table.column(i, anchor=tkinter.CENTER, width=100)
                elif header in ["lead time", "vendor", "part number"]:
                    table.column(i, anchor=tkinter.CENTER, width=200)
                elif header == "other information":
                    table.column(i, anchor=tkinter.CENTER, width=600)
                else:
                    table.column(i, anchor=tkinter.CENTER, width=300)

            rows_num = 0
            if len(search_results) == 0:
                table.insert('', "end", values=[f"{part_number}" if key == "part number" else
                                                ("No such part" if key == "description" else "") for key in
                                                self.table_headers], tags=("odd",))
                rows_num = 1
            else:
                self.prepare_search_results(search_results)

                for index, dictionary in enumerate(sorted(search_results, key=lambda d: d["vendor"])):
                    for i in range(len(websites_list_frame.websites_to_search)):
                        if websites_list_frame.websites_names[i].lower() in dictionary["vendor"] and (
                                not websites_list_frame.websites_to_search[i]):
                            break
                    else:
                        for i, (_, checker) in enumerate(websites_list_frame.conditions_checker.items()):
                            if websites_list_frame.conditions_to_search[i] and checker(dictionary["condition"]):
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

    def create_csv(self, search_results_dict, websites_list_frame):
        moment = time.strftime("%Y-%b-%d__%H_%M_%S", time.localtime())
        with open(f"out_{moment}.csv", "w") as out:
            writer = DictWriter(out, fieldnames=self.table_headers)
            writer.writeheader()

            for part_number, search_results in search_results_dict.items():
                self.prepare_search_results(search_results)

                for dictionary in sorted(search_results, key=lambda d: d["vendor"]):
                    for i in range(len(websites_list_frame.websites_to_search)):
                        if websites_list_frame.websites_names[i].lower() in dictionary["vendor"] and (
                                not websites_list_frame.websites_to_search[i]):
                            break
                    else:
                        for i, (_, checker) in enumerate(websites_list_frame.conditions_checker.items()):
                            if websites_list_frame.conditions_to_search[i] and checker(dictionary["condition"]):
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
        return '\n'.join(textwrap.wrap(string, int(length)))


class SearchFrame(customtkinter.CTkFrame):
    def __init__(self, master, websites_list_frame, **kwargs):
        super().__init__(master, **kwargs)

        self.master = master
        self.websites_list_frame = websites_list_frame

        self.search_results = {}
        self.search_results_dict = {}

        self.master.bind("<<PrintResults>>", self.print_results)

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure((0, 1, 2), weight=1)

        self.part_number_label = customtkinter.CTkLabel(self, text="Enter part number:")
        self.part_number_label.grid(row=0, column=0, padx=(5, 5), pady=(5, 5))

        self.part_number_input = customtkinter.CTkEntry(self, state="disabled")
        self.part_number_input.grid(row=0, column=1, sticky="we")
        self.part_number_input.bind("<Return>", self.search)
        self.part_number_input.bind("<Control-KeyPress>", self.keypress)

        self.search_button = customtkinter.CTkButton(self, text="Search", command=self.search, state="disabled")
        self.search_button.grid(row=0, column=2, padx=(5, 5), pady=(5, 5))

        self.search_frame = SearchResultsFrame(self, corner_radius=0)
        self.search_frame.grid(row=1, column=0, columnspan=3, sticky="nswe")

    @staticmethod
    def keypress(event):
        def is_ru_lang():
            user = ctypes.windll.LoadLibrary("user32.dll")
            return hex(getattr(user, "GetKeyboardLayout")(0)) == "0x4190419"

        if is_ru_lang():
            if event.keycode == 86:
                event.widget.event_generate("<<Paste>>")
            if event.keycode == 67:
                event.widget.event_generate("<<Copy>>")
            if event.keycode == 88:
                event.widget.event_generate("<<Cut>>")

    def search(self, _=None):
        for table in self.search_frame.results_tables:
            table.destroy()

        self.search_results_dict.clear()
        self.master.event_generate("<<DisableSearchButton>>")

        part_numbers = [pn.strip() for pn in self.part_number_input.get().split(',')]

        thread = Thread(target=self.search_part, args=(part_numbers,), daemon=True)
        thread.start()

    def search_part(self, part_numbers):
        with ThreadPoolExecutor() as executor:
            for part_number in part_numbers:
                if len(part_number) > 2:
                    self.search_results = {part_number: list()}

                    futures = []
                    for i, website in enumerate(self.websites_list_frame.websites):
                        if self.websites_list_frame.websites_to_search[i]:
                            self.master.event_generate(f"<<StartProgressBar-{i}>>")

                            future = executor.submit(website.search_part, number=part_number,
                                                     search_results=self.search_results[part_number])
                            future.add_done_callback(lambda f, number=i: self.callback(f, number))

                            futures.append(future)

                    wait(futures)

                    self.master.event_generate("<<PrintResults>>")

        self.master.event_generate("<<EnableSearchButton>>")

    def callback(self, future, number):
        self.master.event_generate(f"<<StopProgressBar-{number}>>")

        status = future.result()
        if status == "Time error":
            self.master.event_generate(f"<<ReportErrorTime-{self.websites_list_frame.websites_names[number]}>>")
        elif status == "Login error":
            self.master.event_generate(f"<<ReportErrorLogin-{self.websites_list_frame.websites_names[number]}>>")
        elif status == "Connection error":
            self.master.event_generate(f"<<ReportErrorConnection-{self.websites_list_frame.websites_names[number]}>>")

    def print_results(self, event=None):
        if event is None:
            for table in self.search_frame.results_tables:
                table.destroy()

            for part_number in list(self.search_results_dict.keys()):
                if len(self.search_results_dict[part_number]) == 0:
                    del self.search_results_dict[part_number]

            self.search_frame.print_search_results(self.search_results_dict, self.websites_list_frame)
        else:
            self.search_results_dict.update(self.search_results)
            self.search_frame.print_search_results(self.search_results, self.websites_list_frame)

    def create_csv(self):
        self.search_frame.create_csv(self.search_results_dict, self.websites_list_frame)

import customtkinter
from GUI import (connection_frame, delay_frame, filters_frame, search_frame, search_results_frame,
                 excel_files_frame, websites_list_frame)
from Logic.controller import Controller
from Logic.data_file import DataClass


class MainFrame(customtkinter.CTkFrame):
    def __init__(self, master: customtkinter.CTk, data: DataClass, controller: Controller, **kwargs):
        super().__init__(master=master, **kwargs)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.label = customtkinter.CTkLabel(self, text="Price\nChecker", font=("Arial", 25), justify=customtkinter.LEFT)
        self.label.grid(row=0, column=0, sticky="nw", padx=5, pady=(5, 5))

        self.search_frame = search_frame.SearchFrame(master=self, controller=controller, corner_radius=0)
        self.search_frame.grid(row=0, column=1, sticky="nsew")

        self.filters_frame = filters_frame.FiltersFrame(master=self, data=data, corner_radius=0)
        self.filters_frame.grid(row=0, column=2, sticky="nsew")

        self.excel_files_frame = excel_files_frame.ExcelFilesFrame(master=self, data=data, corner_radius=0)
        self.excel_files_frame.grid(row=1, column=0, sticky="nsew")

        self.search_results_frame = search_results_frame.SearchResultsFrame(master=self, data=data, corner_radius=0)
        self.search_results_frame.grid(row=1, column=1, sticky="nsew", rowspan=5, columnspan=2)

        self.websites_list_frame = websites_list_frame.WebsitesListFrame(master=self, data=data, corner_radius=0,
                                                                         height=600)
        self.websites_list_frame.grid(row=3, column=0, sticky="nsew")

        self.connection_frame = connection_frame.ConnectionFrame(master=self, data=data, controller=controller,
                                                                 corner_radius=0)
        self.connection_frame.grid(row=4, column=0, sticky="nsew")

        self.delay_frame = delay_frame.DelayFrame(master=self, data=data, corner_radius=0)
        self.delay_frame.grid(row=5, column=0, sticky="nsew")

        self.frames_with_interactive_elements = [
            self.connection_frame,
            self.delay_frame,
            self.filters_frame,
            self.search_frame,
            self.excel_files_frame
        ]

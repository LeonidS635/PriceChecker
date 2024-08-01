import customtkinter
from GUI.frame import Frame
from GUI.filters_window import FiltersWindow
from Logic.data_file import DataClass


class FiltersFrame(Frame):
    def __init__(self, master, data: DataClass, **kwargs):
        super().__init__(master, **kwargs)

        self.master = master
        self.data = data

        self.rowconfigure((0, 1), weight=1)

        self.filters_button = customtkinter.CTkButton(self, text="Filters", command=self.create_filters_frame)
        self.filters_button.grid(row=0, column=0, padx=(5, 5), pady=(5, 5), sticky="sew")
        self.interactive_elements.append(self.filters_button)

        self.update_search_results_button = customtkinter.CTkButton(
            self, text="Update search results", command=lambda: master.event_generate("<<UpdateSearchResults>>"),
            state="disabled")
        self.update_search_results_button.grid(row=1, column=0, padx=(5, 5), pady=(5, 5), sticky="new")
        self.interactive_elements.append(self.update_search_results_button)

    def create_filters_frame(self):
        FiltersWindow(master=self.master, data=self.data).grab_set()

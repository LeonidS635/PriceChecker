import customtkinter
from GUI.frame import Frame
from GUI.filters_window import FiltersWindow
from Logic.data_file import DataClass


class FiltersFrame(Frame):
    def __init__(self, master, data: DataClass, **kwargs):
        super().__init__(master, **kwargs)

        self.master = master
        self.data = data

        self.rowconfigure(0, weight=1)

        self.filters_button = customtkinter.CTkButton(self, text="Filters", command=self.create_filters_frame)
        self.filters_button.grid(row=0, column=0, padx=(5, 5), pady=(5, 5), sticky="sew")
        self.interactive_elements.append(self.filters_button)

    def create_filters_frame(self):
        FiltersWindow(master=self.master, data=self.data).grab_set()

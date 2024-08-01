import ctypes
import customtkinter
from GUI.frame import Frame
from Logic.controller import Controller


class SearchFrame(Frame):
    def __init__(self, master, controller: Controller, **kwargs):
        super().__init__(master, **kwargs)

        self.controller = controller

        self.grid_columnconfigure(1, weight=1)

        self.part_number_label = customtkinter.CTkLabel(self, text="Enter part number:")
        self.part_number_label.grid(row=0, column=0, padx=(5, 5), pady=(5, 5), sticky="we")

        self.part_number_input = customtkinter.CTkEntry(self, state="disabled")
        self.part_number_input.grid(row=0, column=1, sticky="we")
        self.part_number_input.bind("<Return>", self.search)
        self.part_number_input.bind("<Control-KeyPress>", self.keypress)
        self.interactive_elements.append(self.part_number_input)

        self.search_button = customtkinter.CTkButton(self, text="Search", command=self.search, state="disabled")
        self.search_button.grid(row=0, column=2, padx=(5, 5), pady=(5, 5), sticky="we")

    def search(self, _=None):
        if self.search_button not in self.interactive_elements:
            self.interactive_elements.append(self.search_button)
        part_numbers_str = self.part_number_input.get()
        self.controller.search(part_numbers_str)

    def disable_all_interactive_elements(self):
        super().disable_all_interactive_elements()
        if self.search_button in self.interactive_elements:
            self.search_button.configure(text="Stop search", command=self.controller.stop_search, state="normal")

    def enable_all_interactive_elements(self):
        super().enable_all_interactive_elements()
        self.search_button.configure(text="Search", command=self.search, state="normal")

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

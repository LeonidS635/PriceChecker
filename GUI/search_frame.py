import ctypes
import customtkinter


class SearchFrame(customtkinter.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure((0, 1, 2), weight=1)

        self.part_number_label = customtkinter.CTkLabel(self, text="Enter part number:")
        self.part_number_label.grid(row=0, column=0, padx=(5, 5), pady=(5, 5))

        self.part_number_input = customtkinter.CTkEntry(self, state="disabled")
        self.part_number_input.grid(row=0, column=1, sticky="we")
        self.part_number_input.bind("<Return>", master.search)
        self.part_number_input.bind("<Control-KeyPress>", self.keypress)

        self.search_button = customtkinter.CTkButton(self, text="Search", command=master.search, state="disabled")
        self.search_button.grid(row=0, column=2, padx=(5, 5), pady=(5, 5))

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

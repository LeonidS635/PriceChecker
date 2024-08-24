import customtkinter
from GUI.frame import Frame
from Logic.controller import Controller


class SearchFrame(Frame):
    def __init__(self, master, controller: Controller, **kwargs):
        super().__init__(master, **kwargs)

        self.master = master
        self.controller = controller

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.part_number_label = customtkinter.CTkLabel(self, text="Enter part number:")
        self.part_number_label.grid(row=0, column=0, padx=(5, 5), pady=(5, 5), sticky="swe")

        self.part_number_input = customtkinter.CTkEntry(self, state="disabled")
        self.part_number_input.grid(row=0, column=1, padx=(5, 5), pady=(5, 5), sticky="swe")
        self.part_number_input.bind("<Return>", self.search)
        self.part_number_input.bind("<Control-KeyPress>", self.keypress)
        self.interactive_elements.append(self.part_number_input)

        self.search_button = customtkinter.CTkButton(self, text="Search", command=self.search, state="disabled")
        self.search_button.grid(row=0, column=2, padx=(5, 5), pady=(5, 5), sticky="swe")

    def search(self, _=None):
        if self.search_button not in self.interactive_elements:
            self.interactive_elements.append(self.search_button)
        part_numbers_str = self.part_number_input.get()
        self.after(100, self.controller.search, part_numbers_str)

    def disable_all_interactive_elements(self):
        super().disable_all_interactive_elements()
        if self.search_button in self.interactive_elements:
            self.search_button.configure(text="Stop search", command=self.controller.stop_search, state="normal")

    def enable_all_interactive_elements(self):
        super().enable_all_interactive_elements()
        self.search_button.configure(text="Search", command=self.search, state="normal")

    @staticmethod
    def keypress(event):
        if event.keycode == 88 and event.keysym.lower() != "x":
            event.widget.event_generate("<<Cut>>")
        elif event.keycode == 86 and event.keysym.lower() != "v":
            event.widget.event_generate("<<Paste>>")
        elif event.keycode == 67 and event.keysym.lower() != "c":
            event.widget.event_generate("<<Copy>>")

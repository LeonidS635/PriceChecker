import customtkinter


class Frame(customtkinter.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.interactive_elements = []

    def disable_all_interactive_elements(self):
        for element in self.interactive_elements:
            element.configure(state="disabled")

    def enable_all_interactive_elements(self):
        for element in self.interactive_elements:
            element.configure(state="normal")

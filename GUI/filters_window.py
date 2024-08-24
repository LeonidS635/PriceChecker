import customtkinter
from Logic.data_file import DataClass


class FiltersWindow(customtkinter.CTkToplevel):
    def __init__(self, master, data: DataClass, **kwargs):
        super().__init__(master=master, **kwargs)

        self.master = master
        self.data = data

        self.title("Search filters")
        self.geometry("400x440")
        self.resizable(False, False)
        self.attributes("-topmost", True)

        self.columnconfigure((0, 1), weight=1)

        self.label = customtkinter.CTkLabel(self, text="Select websites and part conditions to search:")
        self.label.grid(column=0, columnspan=2, padx=(10, 10), pady=(10, 5))

        self.select_all_websites_button = customtkinter.CTkButton(
            self, text="Deselect all", command=self.deselect_all_websites) if any(
            self.data.websites_to_search.values()) else customtkinter.CTkButton(
            self, text="Select all", command=self.select_all_websites)
        self.select_all_websites_button.grid(row=1, column=0, padx=(10, 5), pady=(5, 5))

        self.select_all_conditions_button = customtkinter.CTkButton(
            self, text="Deselect all", command=self.deselect_all_conditions) if any(
            self.data.conditions_to_search.values()) else customtkinter.CTkButton(
            self, text="Select all", command=self.select_all_conditions)
        self.select_all_conditions_button.grid(row=1, column=1, padx=(5, 10), pady=(5, 5))

        self.websites_frame = customtkinter.CTkScrollableFrame(master=self, corner_radius=0, height=300, width=150)
        self.websites_frame.grid(row=2, column=0, sticky="nsew", pady=(5, 5))
        self.conditions_frame = customtkinter.CTkFrame(master=self, corner_radius=0, height=300, width=250)
        self.conditions_frame.grid(row=2, column=1, sticky="nsew", pady=(5, 5))

        self.checkboxes_websites = []
        self.checkboxes_conditions = []
        for i, website_name in enumerate(self.data.websites_names):
            self.checkboxes_websites.append(
                customtkinter.CTkCheckBox(master=self.websites_frame, text=website_name, corner_radius=12))
            self.checkboxes_websites[i].grid(row=i, column=0, padx=(10, 10), pady=(5, 5), sticky="w")

            if self.data.websites_to_search[website_name]:
                self.checkboxes_websites[i].select()

        for i, condition in enumerate(self.data.conditions):
            self.checkboxes_conditions.append(
                customtkinter.CTkCheckBox(self.conditions_frame, text=condition, corner_radius=12))
            self.checkboxes_conditions[i].grid(row=i, column=1, padx=(10, 10), pady=(5, 5), sticky="w")

            if self.data.conditions_to_search[condition]:
                self.checkboxes_conditions[i].select()

        self.confirm_button = customtkinter.CTkButton(self, text="Confirm", command=self.confirm)
        self.confirm_button.grid(row=3, column=0, columnspan=2, padx=(10, 10), pady=(5, 10), sticky="nsew")

    def select_all_websites(self):
        for checkbox in self.checkboxes_websites:
            checkbox.select()

        self.select_all_websites_button.configure(text="Deselect all")
        self.select_all_websites_button.configure(command=self.deselect_all_websites)

    def deselect_all_websites(self):
        for checkbox in self.checkboxes_websites:
            checkbox.deselect()

        self.select_all_websites_button.configure(text="Select all")
        self.select_all_websites_button.configure(command=self.select_all_websites)

    def select_all_conditions(self):
        for checkbox in self.checkboxes_conditions:
            checkbox.select()

        self.select_all_conditions_button.configure(text="Deselect all")
        self.select_all_conditions_button.configure(command=self.deselect_all_conditions)

    def deselect_all_conditions(self):
        for checkbox in self.checkboxes_conditions:
            checkbox.deselect()

        self.select_all_conditions_button.configure(text="Select all")
        self.select_all_conditions_button.configure(command=self.select_all_conditions)

    def confirm(self):
        for i, website_name in enumerate(self.data.websites_names):
            self.data.websites_to_search[website_name] = self.checkboxes_websites[i].get()
        for i, condition in enumerate(self.data.conditions):
            self.data.conditions_to_search[condition] = self.checkboxes_conditions[i].get()

        self.master.event_generate("<<UpdateSearchResults>>")
        self.destroy()

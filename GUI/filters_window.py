import customtkinter
from Logic.data_file import DataClass


class FiltersWindow(customtkinter.CTkToplevel):
    def __init__(self, master, data: DataClass, **kwargs):
        super().__init__(master=master, **kwargs)

        self.master = master
        self.data = data

        self.title("Search filters")
        self.resizable(False, False)

        self.attributes("-topmost", "true")

        self.grid_columnconfigure((0, 1), weight=1)

        self.label = customtkinter.CTkLabel(self, text="Select websites and part conditions to search:",
                                            justify=customtkinter.CENTER)
        self.label.grid(column=0, columnspan=2, padx=(10, 10), pady=(10, 5))

        self.checkboxes_websites = []
        self.checkboxes_conditions = []
        for i, website_name in enumerate(self.data.websites_names):
            self.checkboxes_websites.append(
                customtkinter.CTkCheckBox(self, text=website_name, corner_radius=10, checkbox_height=20,
                                          checkbox_width=20))
            self.checkboxes_websites[i].grid(row=i + 1, column=0, padx=(10, 10), pady=(5, 5), sticky="sw")

            if self.data.websites_to_search[website_name]:
                self.checkboxes_websites[i].select()

        for i in range(len(self.data.conditions_to_search)):
            self.checkboxes_conditions.append(
                customtkinter.CTkCheckBox(self, text=self.data.conditions_checkers[i][0],
                                          corner_radius=10, checkbox_height=20, checkbox_width=20))
            self.checkboxes_conditions[i].grid(row=i + 1, column=1, padx=(10, 10), pady=(5, 5), sticky="sw")

            if self.data.conditions_to_search[i]:
                self.checkboxes_conditions[i].select()

        self.select_all_websites_button = customtkinter.CTkButton(
            self, text="Deselect all", command=self.deselect_all_websites) if any(
            self.data.websites_to_search.values()) else customtkinter.CTkButton(
            self,  text="Select all", command=self.select_all_websites)
        self.select_all_websites_button.grid(column=0, padx=(10, 5), pady=(5, 5))

        self.select_all_conditions_button = customtkinter.CTkButton(
            self, text="Deselect all", command=self.deselect_all_conditions) if any(
            self.data.conditions_to_search) else customtkinter.CTkButton(
            self, text="Select all", command=self.select_all_conditions)
        self.select_all_conditions_button.grid(row=self.select_all_websites_button.grid_info()["row"], column=1,
                                               padx=(5, 10), pady=(5, 5))

        self.confirm_button = customtkinter.CTkButton(self, text="Confirm", command=self.confirm)
        self.confirm_button.grid(column=0, columnspan=2, padx=(5, 5), pady=(5, 10))

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
            if self.checkboxes_websites[i].get():
                self.data.websites_to_search[website_name] = True
            else:
                self.data.websites_to_search[website_name] = False

        for i in range(len(self.checkboxes_conditions)):
            if self.checkboxes_conditions[i].get():
                self.data.conditions_to_search[i] = True
            else:
                self.data.conditions_to_search[i] = False

        self.master.event_generate("<<UpdateSearchResults>>")
        self.destroy()

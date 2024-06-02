import customtkinter


class FiltersFrame(customtkinter.CTkToplevel):
    def __init__(self, master, websites_frame, **kwargs):
        super().__init__(master, **kwargs)

        self.websites_frame = websites_frame

        self.title("Search filters")
        self.geometry("380x540")
        self.resizable(False, False)

        self.attributes("-topmost", "true")

        self.grid_columnconfigure((0, 1), weight=1)

        self.label = customtkinter.CTkLabel(self, text="Select websites and part conditions to search:",
                                            justify=customtkinter.CENTER)
        self.label.grid(column=0, columnspan=2)

        self.checkboxes_websites = []
        self.checkboxes_conditions = []
        for i in range(len(self.websites_frame.websites_names)):
            self.checkboxes_websites.append(
                customtkinter.CTkCheckBox(self, text=self.websites_frame.websites_names[i], corner_radius=10,
                                          checkbox_height=20, checkbox_width=20))
            self.checkboxes_websites[i].grid(row=i + 1, column=0, padx=(5, 5), pady=(0, 5), sticky="sw")

            if self.websites_frame.websites_to_search[i]:
                self.checkboxes_websites[i].select()

        for i in range(len(self.websites_frame.conditions_to_search)):
            self.checkboxes_conditions.append(
                customtkinter.CTkCheckBox(self, text=list(self.websites_frame.conditions_checker.keys())[i],
                                          corner_radius=10, checkbox_height=20, checkbox_width=20))
            self.checkboxes_conditions[i].grid(row=i + 1, column=1, padx=(5, 5), pady=(0, 5), sticky="sw")

            if self.websites_frame.conditions_to_search[i]:
                self.checkboxes_conditions[i].select()

        self.select_all_websites_button = customtkinter.CTkButton(self, text="Deselect all",
                                                                  command=self.deselect_all_websites)
        self.select_all_websites_button.grid(column=0, padx=(5, 5), pady=(5, 5))

        self.select_all_conditions_button = customtkinter.CTkButton(self, text="Deselect all",
                                                                    command=self.deselect_all_conditions)
        self.select_all_conditions_button.grid(row=self.select_all_websites_button.grid_info()["row"], column=1,
                                               padx=(5, 5), pady=(5, 5))

        self.confirm_button = customtkinter.CTkButton(self, text="Confirm", command=self.confirm)
        self.confirm_button.grid(column=0, columnspan=2, padx=(5, 5), pady=(5, 5))

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
        for i in range(len(self.checkboxes_websites)):
            if self.checkboxes_websites[i].get():
                self.websites_frame.websites_to_search[i] = True
            else:
                self.websites_frame.websites_to_search[i] = False

        for i in range(len(self.checkboxes_conditions)):
            if self.checkboxes_conditions[i].get():
                self.websites_frame.conditions_to_search[i] = True
            else:
                self.websites_frame.conditions_to_search[i] = False

        self.destroy()

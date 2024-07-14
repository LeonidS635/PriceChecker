import customtkinter
from Logic.data_file import DataClass


class WebsitesListFrame(customtkinter.CTkFrame):
    def __init__(self, data: DataClass, **kwargs):
        super().__init__(data.master, **kwargs)

        self.data = data

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.checkboxes = []
        self.progressbars = []

        for i in range(len(self.data.websites_names)):
            self.checkboxes.append(
                customtkinter.CTkCheckBox(self, text=self.data.websites_names[i], state="DISABLED", fg_color="green"))
            self.checkboxes[i].grid(row=i, column=0, padx=(5, 0), pady=(0, 5), sticky="sw")

            self.progressbars.append(customtkinter.CTkProgressBar(self, mode="indeterminate"))
            self.progressbars[i].grid(row=i, column=1, columnspan=2, padx=(5, 5), pady=(0, 5), sticky="we")

        self.delay_label = customtkinter.CTkLabel(self, text="Waiting time (seconds):", justify=customtkinter.LEFT)
        self.delay_label.grid(row=len(self.data.websites_names) + 1, column=0, sticky="nw", padx=5, pady=(5, 5))

        self.delay_input = customtkinter.CTkEntry(self, textvariable=customtkinter.StringVar(self, value="20"))
        self.delay_input.grid(row=len(self.data.websites_names) + 1, column=1, sticky="we")
        self.delay_input.bind("<Return>", self.change_delay)

        self.change_delay_button = customtkinter.CTkButton(self, text="Change delay", command=self.change_delay,
                                                           state="disabled")
        self.change_delay_button.grid(row=len(self.data.websites_names) + 1, column=2, padx=(5, 5), pady=(5, 5))

    def change_delay(self, _=None):
        new_delay = self.delay_input.get()
        if len(new_delay) == 0 or not new_delay.isnumeric():
            new_delay = 0
        else:
            new_delay = int(new_delay)

        new_delay = max(0, new_delay)

        for website in self.data.parsers:
            if website.__class__.__name__ not in ["Aerobay", "Dasi", "AJWeventory"]:
                website.change_delay(new_delay)

        self.delay_input.configure(textvariable=customtkinter.StringVar(self, value=str(new_delay)))

    def deselect_checkboxes(self):
        for checkbox in self.checkboxes:
            checkbox.deselect()

    def start_progressbars(self):
        for progressbar in self.progressbars:
            progressbar.start()

    def stop_progressbars(self):
        for progressbar in self.progressbars:
            progressbar.stop()

    def start_progressbar(self, number):
        self.progressbars[number].start()

    def stop_progressbar(self, number):
        self.progressbars[number].stop()

    def select_checkbox(self, number):
        self.checkboxes[number].select()

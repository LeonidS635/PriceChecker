import customtkinter
from Logic.data_file import DataClass


class DelayFrame(customtkinter.CTkFrame):
    def __init__(self, data: DataClass, **kwargs):
        super().__init__(data.master, **kwargs)

        self.data = data

        self.grid_columnconfigure(1, weight=1)

        self.delay_label = customtkinter.CTkLabel(self, text="Waiting time (seconds):", justify=customtkinter.LEFT)
        self.delay_label.grid(row=0, column=0, sticky="nw", padx=5, pady=(5, 5))

        self.delay_input = customtkinter.CTkEntry(self, textvariable=customtkinter.StringVar(self, value="20"))
        self.delay_input.grid(row=0, column=1, sticky="we")
        self.delay_input.bind("<Return>", self.change_delay)

        self.change_delay_button = customtkinter.CTkButton(self, text="Change delay", command=self.change_delay)
        self.change_delay_button.grid(row=0, column=2, padx=(5, 5), pady=(5, 5))

    def change_delay(self, _=None):
        new_delay = self.delay_input.get()
        if len(new_delay) == 0 or not new_delay.isnumeric():
            new_delay = 0
        else:
            new_delay = int(new_delay)

        new_delay = max(0, new_delay)

        for website in self.data.parsers:
            website.delay = new_delay

        self.delay_input.configure(textvariable=customtkinter.StringVar(self, value=str(new_delay)))

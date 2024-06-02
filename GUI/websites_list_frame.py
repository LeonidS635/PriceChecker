import customtkinter
from WebSites import aerobay, aerospareparts, aircostcontrol, allaero, ajweventory, aviodirect, boeingshop, dasi, \
    globalaviation, lasaero, primaaviation, proponent, satair, turboresources, wencor


class WebsitesListFrame(customtkinter.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.conditions_checker = {
            "New surplus": lambda condition: condition.lower() == "new surplus" or condition.lower() == "ns",
            "New": lambda condition: condition.lower().find("new") != -1 or condition.lower() == "ne",
            "Overhaul": lambda condition: condition.lower() == "overhaul" or condition.lower() == "oh",
            "As removed": lambda condition: condition.lower() == "as removed" or condition.lower() == "ar",
            "Serviceable": lambda condition: not self.conditions_checker["New surplus"](condition) and (
                    not self.conditions_checker["New"](condition) and not self.conditions_checker["Overhaul"](condition)
                    and not self.conditions_checker["As removed"](condition)
            )
        }

        self.websites = []
        self.websites_names = [
            "Aerobay",
            "Aerospareparts",
            "Aircostcontrol",
            "Allaero",
            "AJWeventory",
            "Aviodirect",
            "Boeingshop",
            "Dasi",
            "Globalaviation",
            "Lasaero",
            "Primaaviation",
            "Proponent",
            "Satair",
            "Turboresources",
            "Wencor"
        ]
        self.websites_to_search = [True for _ in range(len(self.websites_names))]
        self.conditions_to_search = [True for _ in range(len(self.conditions_checker))]
        self.logged_in_websites = [False for _ in range(len(self.websites_names))]

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.checkboxes = []
        self.progressbars = []

        for i in range(len(self.websites_names)):
            self.checkboxes.append(
                customtkinter.CTkCheckBox(self, text=self.websites_names[i], state="DISABLED", fg_color="green"))
            self.checkboxes[i].grid(row=i, column=0, padx=(5, 0), pady=(0, 5), sticky="sw")

            self.progressbars.append(customtkinter.CTkProgressBar(self, mode="indeterminate"))
            self.progressbars[i].grid(row=i, column=1, columnspan=2, padx=(5, 5), pady=(0, 5), sticky="we")

        self.delay_label = customtkinter.CTkLabel(self, text="Waiting time (seconds):", justify=customtkinter.LEFT)
        self.delay_label.grid(row=len(self.websites_names) + 1, column=0, sticky="nw", padx=5, pady=(5, 5))

        self.delay_input = customtkinter.CTkEntry(self, textvariable=customtkinter.StringVar(self, value="20"))
        self.delay_input.grid(row=len(self.websites_names) + 1, column=1, sticky="we")
        self.delay_input.bind("<Return>", self.change_delay)

        self.change_delay_button = customtkinter.CTkButton(self, text="Change delay", command=self.change_delay,
                                                           state="disabled")
        self.change_delay_button.grid(row=len(self.websites_names) + 1, column=2, padx=(5, 5), pady=(5, 5))

        self.init_classes()

    def init_classes(self):
        self.websites.append(aerobay.Aerobay())
        self.websites.append(aerospareparts.Aerospareparts())
        self.websites.append(aircostcontrol.Aircostcontrol())
        self.websites.append(allaero.Allaero())
        self.websites.append(ajweventory.AJWeventory())
        self.websites.append(aviodirect.Aviodirect())
        self.websites.append(boeingshop.Boeingshop())
        self.websites.append(dasi.Dasi())
        self.websites.append(globalaviation.Globalaviation())
        self.websites.append(lasaero.Lasaero())
        self.websites.append(primaaviation.Primaaviation())
        self.websites.append(proponent.Proponent())
        self.websites.append(satair.Satair())
        self.websites.append(turboresources.Turboresources())
        self.websites.append(wencor.Wencor())

    def change_delay(self, _=None):
        new_delay = self.delay_input.get()
        if len(new_delay) == 0 or not new_delay.isnumeric():
            new_delay = 0
        else:
            new_delay = int(new_delay)

        new_delay = max(0, new_delay)

        for website in self.websites:
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

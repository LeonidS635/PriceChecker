import customtkinter
from Logic.data_file import DataClass
from GUI.frame import Frame


class WebsitesListFrame(Frame):
    def __init__(self, master, data: DataClass, **kwargs):
        super().__init__(master=master, **kwargs)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.checkboxes = []
        self.progressbars = []

        for i in range(len(data.websites_names)):
            self.checkboxes.append(
                customtkinter.CTkCheckBox(self, text=data.websites_names[i], state="DISABLED", fg_color="green"))
            self.checkboxes[i].grid(row=i, column=0, padx=(5, 0), pady=(0, 5), sticky="sw")

            self.progressbars.append(customtkinter.CTkProgressBar(self, mode="indeterminate"))
            self.progressbars[i].grid(row=i, column=1, padx=(5, 5), pady=(0, 5), sticky="we")

    def start_progressbar(self, number):
        self.progressbars[number].start()

    def stop_progressbar(self, number):
        self.progressbars[number].stop()

    def select_checkbox(self, number):
        self.checkboxes[number].select()

    def deselect_checkbox(self, number):
        self.checkboxes[number].deselect()

    def deselect_checkboxes(self):
        for checkbox in self.checkboxes:
            checkbox.deselect()

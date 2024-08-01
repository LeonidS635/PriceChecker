import customtkinter
from GUI.frame import Frame
from GUI.passwords_window import PasswordsWindow
from Logic.controller import Controller
from Logic.data_file import DataClass


class ConnectionFrame(Frame):
    def __init__(self, master, data: DataClass, controller: Controller,  **kwargs):
        super().__init__(master, **kwargs)

        self.master = master
        self.data = data

        self.reconnect_button = customtkinter.CTkButton(self, text="Reconnect", command=controller.reconnect)
        self.reconnect_button.grid(row=0, column=0, padx=(5, 5), pady=(5, 5))
        self.interactive_elements.append(self.reconnect_button)

        self.connect_button = customtkinter.CTkButton(self, text="Connect", command=controller.connect)
        self.connect_button.grid(row=0, column=1, padx=(5, 5), pady=(5, 5))
        self.interactive_elements.append(self.connect_button)

        self.passwords_button = customtkinter.CTkButton(self, text="Passwords", command=self.change_passwords)
        self.passwords_button.grid(row=0, column=2, padx=(5, 5), pady=(5, 5))
        self.interactive_elements.append(self.passwords_button)

    def change_passwords(self):
        PasswordsWindow(master=self.master, data=self.data).grab_set()

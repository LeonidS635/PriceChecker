import customtkinter


class ConnectionFrame(customtkinter.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.reconnect_button = customtkinter.CTkButton(self, text="Reconnect", command=master.reconnect)
        self.reconnect_button.grid(row=0, column=0, padx=(5, 5), pady=(5, 5))

        self.connect_button = customtkinter.CTkButton(self, text="Connect", command=master.connect)
        self.connect_button.grid(row=0, column=1, padx=(5, 5), pady=(5, 5))

        self.passwords_button = customtkinter.CTkButton(self, text="Passwords", command=master.change_passwords)
        self.passwords_button.grid(row=0, column=2, padx=(5, 5), pady=(5, 5))

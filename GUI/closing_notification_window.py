import customtkinter


class AppClosingNotification(customtkinter.CTkToplevel):
    def __init__(self, master, master_width: int, master_height: int, master_x: int, master_y: int):
        super().__init__(master=master)

        width = 300
        height = 150

        self.title("")
        self.geometry(f"{width}x{height}+{master_x + (master_width - width) // 2}+"
                      f"{master_y + (master_height - height) // 2}")
        self.resizable(width=False, height=False)
        self.attributes("-topmost", True)
        self.overrideredirect(True)

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.frame = customtkinter.CTkFrame(master=self, corner_radius=0, border_width=1, border_color='black')
        self.frame.grid(sticky="nsew")

        self.frame.rowconfigure(0, weight=1)
        self.frame.columnconfigure(0, weight=1)

        self.label = customtkinter.CTkLabel(master=self.frame, text="Program is closing...")
        self.label.grid()

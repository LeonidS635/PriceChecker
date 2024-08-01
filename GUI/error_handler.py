from CTkMessagebox import CTkMessagebox


class ErrorHandler(CTkMessagebox):
    def __init__(self, master, title: str, message: str):
        super().__init__(master=master, title=title, message=message, icon="warning")


class FatalErrorHandler(CTkMessagebox):
    def __init__(self, master, title: str, message: str):
        super().__init__(master=master, title=title, icon="cancel", width=500, height=200, wraplength=500,
                         button_height=30, justify="center", option_focus=1,
                         message=f"The program will be closed due to the error:\n{message}")

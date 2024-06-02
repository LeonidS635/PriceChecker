from CTkMessagebox import CTkMessagebox


class ErrorHandler:
    def __init__(self, master, website, error):
        message_box = CTkMessagebox(master=master, title=website, message=error, icon="warning")
        message_box.grab_set()


class FatalErrorHandler:
    def __init__(self, master, error, exit_function):
        self.exit_function = exit_function
        self.message_box = CTkMessagebox(master=master, title="Fatal error",
                                         message=f"The program will be closed due to the error:\n{error}",
                                         icon="cancel", width=700, button_height=30, justify="center",
                                         cancel_button="None", option_focus=1)

        self.message_box.grab_set()
        self.destroy_and_exit()

    def destroy_and_exit(self):
        if self.message_box.get():
            self.message_box.destroy()
            self.exit_function()

import customtkinter
from CTkMessagebox import CTkMessagebox
from GUI.closing_notification_window import AppClosingNotification
from GUI.main_frame import MainFrame
from Logic.controller import Controller
from Logic.data_file import DataClass
from queue import SimpleQueue
import traceback


class Root(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.data = DataClass()
        self.controller = Controller(master=self, data=self.data)

        self.geometry("1200x800")
        self.title("Price checker")

        self.protocol("WM_DELETE_WINDOW", self.stop_working_and_destroy_parsers)
        self.report_callback_exception = self.report_tkinter_error
        self.error_messages: SimpleQueue[tuple[str, str]] = SimpleQueue()
        self.fatal_error_messages: SimpleQueue[tuple[str, str]] = SimpleQueue()
        self.fatal_error_window: CTkMessagebox | None = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.main_frame = MainFrame(master=self, data=self.data, controller=self.controller)
        self.main_frame.grid(column=0, row=0, sticky="nsew")

        self.bind_events()
        self.controller.init_parsers()

    def enable_interactive_elements(self):
        for frame in self.main_frame.frames_with_interactive_elements:
            frame.enable_all_interactive_elements()

    def disable_interactive_elements(self):
        for frame in self.main_frame.frames_with_interactive_elements:
            frame.disable_all_interactive_elements()

    def bind_events(self):
        for website_name in self.data.websites_names_with_captcha_for_login:
            self.bind(f"<<CreateCaptchaForm-{website_name}>>",
                      lambda event, website=website_name: self.controller.connector.create_captcha_form(website))

        self.bind("<<CreatePasswordsForm>>", lambda event: self.main_frame.connection_frame.change_passwords())

        self.bind("<<EnableElems>>", lambda event: self.enable_interactive_elements())
        self.bind("<<DisableElems>>", lambda event: self.disable_interactive_elements())

        for i, website_name in enumerate(self.data.websites_names):
            self.bind(f"<<StartProgressBar-{website_name}>>",
                      lambda event, number=i: self.main_frame.websites_list_frame.start_progressbar(number))
            self.bind(f"<<StopProgressBar-{website_name}>>",
                      lambda event, number=i: self.main_frame.websites_list_frame.stop_progressbar(number))
            self.bind(f"<<SelectCheckbox-{website_name}>>",
                      lambda event, number=i: self.main_frame.websites_list_frame.select_checkbox(number))
            self.bind(f"<<DeselectCheckbox-{website_name}>>",
                      lambda event, number=i: self.main_frame.websites_list_frame.deselect_checkbox(number))
        self.bind("<<DeselectAllCheckboxes>>",
                  lambda event, number=i: self.main_frame.websites_list_frame.deselect_checkboxes())

        self.bind("<<ClearSearchResults>>", lambda event: self.main_frame.search_results_frame.clear())
        self.bind("<<PrintSearchResults>>", lambda event: self.main_frame.search_results_frame.print_search_results())
        self.bind("<<UpdateSearchResults>>", lambda event: self.main_frame.search_results_frame.update_search_results())

        self.bind("<<ReportError>>", lambda event: self.report_error())
        self.bind("<<ReportFatalError>>", lambda event: self.report_fatal_error())

    def report_error(self):
        title, message = self.error_messages.get()
        CTkMessagebox(master=self, title=title, message=message, icon="warning", width=500, height=200,
                      button_height=30, justify="center")

    def report_fatal_error(self):
        title, message = self.fatal_error_messages.get()
        if self.fatal_error_window is None:
            self.fatal_error_window = CTkMessagebox(master=self, title=title, icon="cancel", width=500, height=200,
                                                    button_height=30, justify="center",
                                                    message=f"The program will be closed due to the error:\n{message}")
            self.fatal_error_window.grab_set()
            self.stop_working_and_destroy_parsers()
        elif self.fatal_error_window.winfo_exists():
            self.fatal_error_window.focus()

    def report_tkinter_error(self, *_):
        self.fatal_error_messages.put(("GUI Error", traceback.format_exc(limit=0)))
        self.report_fatal_error()

    def stop_working_and_destroy_parsers(self):
        if self.fatal_error_window is not None and self.fatal_error_window.winfo_exists():
            self.fatal_error_window.wait_window()

        AppClosingNotification(master=self, master_width=self.winfo_width(), master_height=self.winfo_height(),
                               master_x=self.winfo_x(), master_y=self.winfo_y())
        self.controller.stop_parsers()
        self.after(100, self.controller.del_parsers)

    def exit(self):
        self.destroy()

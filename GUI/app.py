import customtkinter
from GUI.error_handler import ErrorHandler, FatalErrorHandler
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

        self.protocol("WM_DELETE_WINDOW", self.exit)
        self.report_callback_exception = self.report_tkinter_error
        self.need_to_destroy = False
        self.error_messages = SimpleQueue()
        self.fatal_error_messages = SimpleQueue()

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

        self.bind("<<CheckNeedToDestroy>>", lambda event: self.check_need_to_destroy())

    def report_error(self):
        title, message = self.error_messages.get()
        ErrorHandler(master=self, title=title, message=message)

    def report_fatal_error(self):
        self.need_to_destroy = True
        title, message = self.fatal_error_messages.get()
        FatalErrorHandler(master=self, title=title, message=message)

    def report_tkinter_error(self, *_):
        FatalErrorHandler(master=self, title="GUI Error", message=traceback.format_exc(limit=0))
        self.after(1000, self.exit)

    def check_need_to_destroy(self):
        if self.need_to_destroy:
            self.exit()

    def exit(self):
        self.controller.del_parsers()
        self.quit()

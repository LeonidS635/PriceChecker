import customtkinter
from GUI import filters_window, passwords_window, error_handler, frames
from Logic import controller, data_file
import traceback


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.data = data_file.DataClass(master=self)
        self.frames = frames.Frames(data=self.data)
        self.controller = controller.Controller(data=self.data, frames=self.frames)

        self.geometry("1000x800")
        self.title("Price checker")

        self.protocol("WM_DELETE_WINDOW", self.exit)
        self.report_callback_exception = self.report_callback_exception

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.label = customtkinter.CTkLabel(self, text="Price\nChecker", font=("Arial", 25), justify=customtkinter.LEFT)
        self.label.grid(row=0, column=0, sticky="nw", padx=5, pady=(5, 5))

        self.frames.connection_frame.grid(row=6, column=0, sticky="nsew")
        self.frames.connection_frame.grid(row=5, column=0, sticky="nsew")
        self.frames.search_frame.grid(row=0, column=1, sticky="nsew")
        self.frames.search_results_frame.grid(row=1, column=1, sticky="nsew", rowspan=6)
        self.frames.websites_list_frame.grid(row=4, column=0, sticky="nsew")

        self.create_csv_button = customtkinter.CTkButton(self, text="Create csv",
                                                         command=self.frames.search_results_frame.create_csv)
        self.create_csv_button.grid(row=1, column=0, padx=(5, 5), pady=(5, 5))

        self.filters_button = customtkinter.CTkButton(self, text="Filters", command=self.create_filters_frame)
        self.filters_button.grid(row=2, column=0, padx=(5, 5), pady=(5, 5))

        self.update_search_results_button = customtkinter.CTkButton(
            self, text="Update search results", command=self.frames.search_results_frame.update_search_results)
        self.update_search_results_button.grid(row=3, column=0, padx=(5, 5), pady=(5, 5))

        self.interactive_elements = [
            self.filters_button,
            self.update_search_results_button,
            self.create_csv_button,
            self.frames.connection_frame.connect_button,
            self.frames.connection_frame.reconnect_button,
            self.frames.connection_frame.passwords_button,
            self.frames.search_frame.part_number_input,
            self.frames.search_frame.search_button,
            self.frames.websites_list_frame.delay_input,
            self.frames.websites_list_frame.change_delay_button
        ]

        self.bind_events()
        self.controller.init_parsers()

    def create_filters_frame(self):
        filters_window.FiltersFrame(self.data).grab_set()

    def bind_events(self):
        self.bind("<<LoginDasi>>", lambda event: self.controller.connector.login_with_captcha("Dasi"))

        for website in self.data.websites_names:
            self.bind(f"<<ReportErrorTime-{website}>>", lambda event, site=website: self.report_error_time(site))
        for website in self.data.websites_names:
            self.bind(f"<<ReportErrorLogin-{website}>>",
                      lambda event, site=website: self.report_error_login(site))
        for website in self.data.websites_names:
            self.bind(f"<<ReportErrorConnection-{website}>>",
                      lambda event, site=website: self.report_error_connection(site))

    def connect(self):
        self.controller.connect()

    def reconnect(self):
        self.controller.reconnect()

    def search(self, _=None):
        self.controller.search()

    def change_passwords(self):
        passwords_window.PasswordsWindow(self.data, self.controller.connector.passwords_file).grab_set()

    def enable_interactive_elements(self):
        for elem in self.interactive_elements:
            elem.configure(state="normal")

    def disable_interactive_elements(self):
        for elem in self.interactive_elements:
            elem.configure(state="disabled")

    def report_error_time(self, website):
        error_handler.ErrorHandler(self, website, "Loading took too much time!")

    def report_error_login(self, website):
        error_handler.ErrorHandler(self, website, "Login failed!")

    def report_error_connection(self, website):
        error_handler.ErrorHandler(self, website, f"Unable to connect {website}!")

    def report_callback_exception(self, *_):
        traceback.print_exc()
        error_handler.FatalErrorHandler(self, traceback.format_exc(limit=0), self.exit)

    def exit(self):
        self.controller.del_parsers()
        self.destroy()

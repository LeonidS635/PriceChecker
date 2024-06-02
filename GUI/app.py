import customtkinter
import traceback
from GUI import connection_frame, search_frame, websites_list_frame, filters_frame, error_handler


class ButtonsFrame(customtkinter.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.reconnect_button = customtkinter.CTkButton(self, text="Reconnect", command=master.reconnect,
                                                        state="disabled")
        self.reconnect_button.grid(row=0, column=0, padx=(5, 5), pady=(5, 5))

        self.connect_button = customtkinter.CTkButton(self, text="Connect", command=master.connect)
        self.connect_button.grid(row=0, column=1, padx=(5, 5), pady=(5, 5))

        self.exit_button = customtkinter.CTkButton(self, text="Exit", command=master.exit)
        self.exit_button.grid(row=0, column=2, padx=(5, 5), pady=(5, 5))


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.geometry("1000x800")
        self.title("Price checker")

        self.protocol("WM_DELETE_WINDOW", self.exit)
        self.report_callback_exception = self.report_callback_exception

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.label = customtkinter.CTkLabel(self, text="Price\nChecker", font=("Arial", 25), justify=customtkinter.LEFT)
        self.label.grid(row=0, column=0, sticky="nw", padx=5, pady=(5, 5))

        self.filters_frame = None

        self.filters_button = customtkinter.CTkButton(self, text="Filters", command=self.create_filters_frame)
        self.filters_button.grid(row=2, column=0, padx=(5, 5), pady=(5, 5))

        self.websites_list_frame = websites_list_frame.WebsitesListFrame(self, corner_radius=0)
        self.websites_list_frame.grid(row=4, column=0, sticky="nswe")

        self.connection_frame = connection_frame.ConnectionFrame(self, self.websites_list_frame)

        self.buttons_frame = ButtonsFrame(self, corner_radius=0)
        self.buttons_frame.grid(row=5, column=0, sticky="nswe")

        self.search_frame = search_frame.SearchFrame(self, self.websites_list_frame, corner_radius=0)
        self.search_frame.grid(row=0, column=1, sticky="nswe", rowspan=6)

        self.update_search_results_button = customtkinter.CTkButton(self, text="Update search results",
                                                                    command=self.search_frame.print_results,
                                                                    state="disabled")
        self.update_search_results_button.grid(row=3, column=0, padx=(5, 5), pady=(5, 5))

        self.create_csv_button = customtkinter.CTkButton(self, text="Create csv", command=self.search_frame.create_csv,
                                                         state="disabled")
        self.create_csv_button.grid(row=1, column=0, padx=(5, 5), pady=(5, 5))

        self.bind_events()

    def create_filters_frame(self):
        self.filters_frame = filters_frame.FiltersFrame(self, self.websites_list_frame)
        self.filters_frame.grab_set()

    def bind_events(self):
        for i in range(len(self.websites_list_frame.websites)):
            self.bind(f"<<StartProgressBar-{i}>>",
                      lambda event, number=i: self.websites_list_frame.start_progressbar(number))
        for i in range(len(self.websites_list_frame.websites)):
            self.bind(f"<<StopProgressBar-{i}>>",
                      lambda event, number=i: self.websites_list_frame.stop_progressbar(number))
        for i in range(len(self.websites_list_frame.websites)):
            self.bind(f"<<SelectCheckBox-{i}>>",
                      lambda event, number=i: self.websites_list_frame.select_checkbox(number))

        self.bind("<<StartProgressBars>>", self.websites_list_frame.start_progressbars)
        self.bind("<<StopProgressBars>>", self.websites_list_frame.stop_progressbars)

        self.bind("<<EnableConnectionButton>>", self.enable_buttons_connection)
        self.bind("<<EnableSearchButton>>", self.enable_buttons_search)
        self.bind("<<DisableSearchButton>>", self.disable_buttons_search)

        self.bind("<<LoginDasi>>",
                  lambda event: self.connection_frame.login(
                      self.websites_list_frame.websites[self.websites_list_frame.websites_names.index("Dasi")],
                      self.websites_list_frame.login_data["Dasi"]["login"],
                      self.websites_list_frame.login_data["Dasi"]["password"]))

        for website in self.websites_list_frame.websites_names:
            self.bind(f"<<ReportErrorTime-{website}>>", lambda event, site=website: self.report_error_time(site))
        for website in self.websites_list_frame.websites_names:
            self.bind(f"<<ReportErrorLogin-{website}>>",
                      lambda event, site=website: self.report_error_login(site))
        for website in self.websites_list_frame.websites_names:
            self.bind(f"<<ReportErrorConnection-{website}>>",
                      lambda event, site=website: self.report_error_connection(site))

    def connect(self):
        self.search_frame.part_number_input.configure(state="disabled")
        self.search_frame.search_button.configure(state="disabled")
        self.create_csv_button.configure(state="disabled")
        self.websites_list_frame.delay_input.configure(state="disabled")
        self.websites_list_frame.change_delay_button.configure(state="disabled")
        self.buttons_frame.reconnect_button.configure(state="disabled")
        self.buttons_frame.connect_button.configure(state="disabled")
        self.buttons_frame.exit_button.configure(state="disabled")

        self.connection_frame.connect()

    def reconnect(self):
        self.websites_list_frame.deselect_checkboxes()
        self.websites_list_frame.logged_in_websites = [False for _ in
                                                       range(len(self.websites_list_frame.websites_names))]
        self.connect()

    def enable_buttons_connection(self, _):
        for i, is_connected in enumerate(self.websites_list_frame.logged_in_websites):
            if is_connected:
                self.buttons_frame.connect_button.configure(state="disabled")
                break
        else:
            self.buttons_frame.connect_button.configure(state="normal")

        self.websites_list_frame.delay_input.configure(state="normal")
        self.websites_list_frame.change_delay_button.configure(state="normal")
        self.search_frame.part_number_input.configure(state="normal")
        self.search_frame.search_button.configure(state="normal")
        self.buttons_frame.reconnect_button.configure(state="normal")
        self.buttons_frame.exit_button.configure(state="normal")

    def enable_buttons_search(self, _):
        self.filters_button.configure(state="normal")
        self.websites_list_frame.delay_input.configure(state="normal")
        self.websites_list_frame.change_delay_button.configure(state="normal")
        self.update_search_results_button.configure(state="normal")
        self.search_frame.part_number_input.configure(state="normal")
        self.search_frame.search_button.configure(state="normal")
        self.create_csv_button.configure(state="normal")
        self.buttons_frame.reconnect_button.configure(state="normal")

    def disable_buttons_search(self, _):
        self.filters_button.configure(state="disabled")
        self.websites_list_frame.delay_input.configure(state="disabled")
        self.websites_list_frame.change_delay_button.configure(state="disabled")
        self.update_search_results_button.configure(state="disabled")
        self.search_frame.part_number_input.configure(state="disabled")
        self.search_frame.search_button.configure(state="disabled")
        self.create_csv_button.configure(state="disabled")
        self.buttons_frame.reconnect_button.configure(state="disabled")

    def report_error_time(self, website):
        error_handler.ErrorHandler(self, website, "Loading took too much time!")

    def report_error_login(self, website):
        error_handler.ErrorHandler(self, website, "Login failed!")

    def report_error_connection(self, website):
        error_handler.FatalErrorHandler(self, f"Unable to connect {website}!", self.exit)

    def report_callback_exception(self, *_):
        traceback.print_exc()
        error_handler.FatalErrorHandler(self, traceback.format_exc(limit=0), self.exit)

    def exit(self):
        for website in self.websites_list_frame.websites:
            website.__del__()

        self.destroy()

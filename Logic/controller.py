from threading import Thread
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from GUI.frames import Frames
from Logic.connector import Connector
from Logic.data_file import DataClass
from Logic.searcher import Searcher


class Controller:
    def __init__(self, data: DataClass, frames: Frames):
        self.data = data
        self.frames = frames

        self.connector = Connector(data=self.data, frames=self.frames,
                                   callback=lambda future, number: self.callback(future, number,
                                                                                 is_connection_phase=True))
        self.searcher = Searcher(data=self.data, frames=self.frames,
                                 callback=lambda future, number: self.callback(future, number,
                                                                               is_connection_phase=False))

    def init_parsers(self):
        with ThreadPoolExecutor() as executor:
            futures = []
            for parser in self.data.parsers:
                futures.append(executor.submit(parser))

            for i, future in enumerate(as_completed(futures)):
                self.data.parsers[i] = future.result()

        self.data.parsers.sort(key=lambda obj: obj.__class__.__name__)

    def del_parsers(self):
        with ThreadPoolExecutor() as executor:
            futures = []
            for parser in self.data.parsers:
                futures.append(executor.submit(parser.__del__))

    def connect(self):
        thread = Thread(target=lambda: (
            self.data.master.disable_interactive_elements(),
            self.connector.connect(),
            self.data.master.enable_interactive_elements()
        ), daemon=True)
        thread.start()

    def reconnect(self):
        thread = Thread(target=lambda: (
            self.data.master.disable_interactive_elements(),
            self.connector.reconnect(),
            self.data.master.enable_interactive_elements()
        ), daemon=True)
        thread.start()

    def search(self):
        thread = Thread(target=lambda: (
            self.data.master.disable_interactive_elements(),
            # self.frames.search_frame.search_button.configure(text="Stop search", command=self.stop_search,
            #                                                  state="normal"),
            self.searcher.search(),
            # self.frames.search_frame.search_button.configure(text="Search", command=self.search),
            self.data.master.enable_interactive_elements()
        ), daemon=True)
        thread.start()

    def stop_search(self):
        self.searcher.stop_search_flag = True

    def callback(self, future: Future, number: int, is_connection_phase: bool):
        self.frames.websites_list_frame.stop_progressbar(number)

        status = future.result()
        if status == "Time error":
            self.data.master.event_generate(f"<<ReportErrorTime-{self.data.websites_names[number]}>>")
        elif status == "Login error":
            self.data.master.event_generate(f"<<ReportErrorLogin-{self.data.websites_names[number]}>>")
        elif status == "Connection error":
            self.data.master.event_generate(f"<<ReportErrorConnection-{self.data.websites_names[number]}>>")
        elif is_connection_phase:
            self.data.logged_in_websites[number] = True
            self.frames.websites_list_frame.select_checkbox(number)

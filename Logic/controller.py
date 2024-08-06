from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from Logic.connector import Connector
from Logic.data_file import DataClass, Status
from Logic.searcher import Searcher
from threading import Thread
from typing import Callable


class Controller:
    def __init__(self, master, data: DataClass):
        self.data = data
        self.master = master

        self.connector = Connector(master=self.master, data=self.data,
                                   callback=lambda future, number: self.callback(future, number,
                                                                                 is_connection_phase=True))
        self.searcher = Searcher(master=self.master, data=self.data,
                                 callback=lambda future, number: self.callback(future, number,
                                                                               is_connection_phase=False))

    def wrapper(self, func: Callable, *args):
        thread = Thread(target=lambda: (
            self.master.event_generate("<<DisableElems>>"),
            func(*args),
            self.master.event_generate("<<EnableElems>>"),
            self.master.event_generate("<<CheckNeedToDestroy>>", when="tail"),
        ), daemon=True)
        thread.start()

    def init_parsers(self):
        with ThreadPoolExecutor() as executor:
            futures = []
            for parser in self.data.parsers:
                futures.append(executor.submit(parser))

            for i, future in enumerate(as_completed(futures)):
                self.data.parsers[i] = future.result()

    def del_parsers(self):
        with ThreadPoolExecutor() as executor:
            futures = []
            for parser in self.data.parsers:
                futures.append(executor.submit(parser.__del__))

    def connect(self):
        self.wrapper(self.connector.connect)

    def reconnect(self):
        self.wrapper(self.connector.reconnect)

    def search(self, part_numbers_str: str):
        self.wrapper(self.searcher.search, part_numbers_str)

    def stop_search(self):
        self.searcher.stop_search_flag = True

    def callback(self, future: Future, website: str, is_connection_phase: bool):
        self.master.event_generate(f"<<StopProgressBar-{website}>>")

        try:
            status = future.result()
        except Exception as e:
            self.master.error_messages.put((website, repr(e)))
            self.master.event_generate("<<ReportError>>")
        else:
            if status != Status.OK:
                if status == Status.Time_error:
                    exception_message = "Loading took too much time!"
                elif status == Status.Login_error:
                    if self.data.logged_in_websites[website]:
                        self.data.logged_in_websites[website] = False
                        self.master.event_generate(f"<<DeselectCheckbox-{website}>>")

                    exception_message = f"Login to {website} failed!"
                elif status == Status.Connection_error:
                    exception_message = f"Unable to connect {website}!"
                else:
                    exception_message = "Something went wrong :("

                self.master.error_messages.put((website, exception_message))
                self.master.event_generate(f"<<ReportError>>")
            elif is_connection_phase:
                self.data.logged_in_websites[website] = True
                self.master.event_generate(f"<<SelectCheckbox-{website}>>")

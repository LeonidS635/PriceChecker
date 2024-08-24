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
        self.thread = Thread()

        self.connector = Connector(master=self.master, data=self.data,
                                   callback=lambda future, number: self.callback(future, number,
                                                                                 is_connection_phase=True))
        self.searcher = Searcher(master=self.master, data=self.data,
                                 callback=lambda future, number: self.callback(future, number,
                                                                               is_connection_phase=False))

    def wrapper(self, func: Callable, *args):
        self.thread = Thread(target=lambda: (
            self.master.event_generate("<<DisableElems>>"),
            func(*args),
            self.master.event_generate("<<EnableElems>>"),
        ), daemon=True)
        self.thread.start()

    def init_parsers(self):
        with ThreadPoolExecutor() as executor:
            futures = []
            for parser_class in self.data.parsers_classes:
                futures.append(executor.submit(parser_class))

            for i, future in enumerate(as_completed(futures)):
                try:
                    self.data.parsers.append(future.result())
                except Exception as e:
                    self.master.fatal_error_messages.put(("Initialization error", repr(e)))
                    self.master.event_generate("<<ReportFatalError>>")

    def stop_parsers(self):
        for parser in self.data.parsers:
            parser.stop_event.set()

    def del_parsers(self):
        if self.thread.is_alive():
            self.master.after(100, self.del_parsers)
        else:
            with ThreadPoolExecutor() as executor:
                futures = []
                for parser in self.data.parsers:
                    futures.append(executor.submit(parser.__del__))

            self.master.exit()

    def connect(self):
        self.wrapper(self.connector.connect)

    def reconnect(self):
        self.wrapper(self.connector.reconnect)

    def search(self, part_numbers_str: str):
        self.wrapper(self.searcher.search, part_numbers_str)

    def stop_search(self):
        self.searcher.stop_search_flag.set()

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

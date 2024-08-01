from Logic.data_file import DataClass
from concurrent.futures import Future, ThreadPoolExecutor
from copy import deepcopy
from typing import Callable


class Searcher:
    def __init__(self, master, data: DataClass, callback: Callable[[Future, int], None]):
        self.callback = callback
        self.data = data
        self.master = master

        self.stop_search_flag = False

    def search(self, part_numbers_str: str):
        self.master.event_generate(f"<<ClearSearchResults>>")
        self.data.all_search_results.clear()

        part_numbers = [pn.strip() for pn in part_numbers_str.split(',')]
        for part_number in part_numbers:
            if self.stop_search_flag:
                self.stop_search_flag = False
                break

            if len(part_number) > 2:
                search_results = []
                with ThreadPoolExecutor() as executor:
                    futures = []
                    for parser in self.data.parsers:
                        website_name = parser.__class__.__name__
                        if self.data.websites_to_search[website_name]:
                            self.master.event_generate(f"<<StartProgressBar-{website_name}>>")

                            future = executor.submit(parser.search_part, number=part_number,
                                                     search_results=search_results)
                            future.add_done_callback(lambda f, website=website_name: self.callback(f, website))
                            futures.append(future)

                self.data.all_search_results.append((part_number, deepcopy(search_results)))
                self.master.event_generate(f"<<PrintSearchResults>>")

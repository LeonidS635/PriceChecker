from Logic.data_file import DataClass
from GUI.frames import Frames
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Callable


class Searcher:
    def __init__(self, data: DataClass, frames: Frames, callback: Callable[[Future, int], None]):
        self.callback = callback
        self.data = data
        self.frames = frames

        self.stop_search_flag = False

    def search(self):
        for table in self.frames.search_results_frame.results_tables:
            table.destroy()
        self.frames.search_results_frame.results_tables.clear()

        part_numbers = [pn.strip() for pn in self.frames.search_frame.part_number_input.get().split(',')]
        for part_number in part_numbers:
            if self.stop_search_flag:
                self.stop_search_flag = False
                break

            if len(part_number) > 2:
                self.frames.search_results_frame.all_search_results[part_number] = []
                with ThreadPoolExecutor() as executor:
                    futures = []
                    for i, parser in enumerate(self.data.parsers):
                        if self.data.websites_to_search[i]:
                            self.data.master.event_generate(f"<<StartProgressBar-{i}>>")

                            future = executor.submit(parser.search_part, number=part_number,
                                                     search_results=self.frames.search_results_frame.all_search_results[
                                                         part_number])
                            future.add_done_callback(lambda f, number=i: self.callback(f, number))
                            futures.append(future)

                self.frames.search_results_frame.print_search_results(
                    part_number, self.frames.search_results_frame.all_search_results[part_number])

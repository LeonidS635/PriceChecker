from concurrent.futures import Future, ThreadPoolExecutor
from copy import deepcopy
from Logic.data_file import DataClass, Status
import openpyxl
from threading import Event
from typing import Callable


class Searcher:
    def __init__(self, master, data: DataClass, callback: Callable[[Future, int], None]):
        self.callback = callback
        self.data = data
        self.master = master

        self.stop_search_flag = Event()

    def search(self, part_numbers_str: str):
        self.master.event_generate(f"<<ClearSearchResults>>")
        self.data.all_search_results.clear()

        part_numbers = [pn.strip() for pn in part_numbers_str.split(',')]
        for part_number in part_numbers:
            if self.stop_search_flag.is_set():
                self.stop_search_flag.clear()
                break

            if len(part_number) > 2:
                search_results: list[dict[str, str]] = []
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

                    for file_name, file_path in self.data.loaded_excel_files.items():
                        future = executor.submit(self.search_part_in_excel_data, file_name=file_name,
                                                 file_path=file_path, part_number=part_number,
                                                 search_results=search_results)
                        future.add_done_callback(lambda f, website=file_name: self.callback(f, website))
                        futures.append(future)

                self.data.all_search_results.append((part_number, deepcopy(search_results)))
                self.master.event_generate(f"<<PrintSearchResults>>")

    @staticmethod
    def search_part_in_excel_data(file_name: str, file_path: str, part_number: str,
                                  search_results: list[dict[str, str]]) -> Status:
        try:
            workbook = openpyxl.load_workbook(filename=file_path, read_only=True)
        except FileNotFoundError:
            raise FileNotFoundError(f"No excel file \"{file_path}\" found")

        sheet = workbook.active
        if sheet is None:
            workbook.close()
            raise FileNotFoundError(f"Empty excel file \"{file_path}\"!")

        products: list[dict[str, str]] = []
        table_headers = [cell.value for cell in sheet[1]]
        for row in sheet.iter_rows(min_row=2, values_only=True):
            products.append({})
            for i, (header, cell) in enumerate(zip(table_headers, row)):
                products[-1][header] = str(cell) if cell is not None else ""
            products[-1]["vendor"] = file_name

        for product in products:
            if product["part number"] == part_number and product["description"] != "No such part":
                search_results.append(deepcopy(product))

        workbook.close()
        return Status.OK

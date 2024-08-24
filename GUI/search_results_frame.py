from GUI.frame import Frame
from Logic.data_file import DataClass
from tksheet import Sheet


class SearchResultsFrame(Frame):
    def __init__(self, master, data: DataClass, **kwargs):
        super().__init__(master=master, **kwargs)

        self.data = data
        self.search_results_idx = 0
        self.sheet = Sheet(parent=self, headers=self.data.headers, align="center", show_row_index=False,
                           show_top_left=False, header_bg="#2db1e0",
                           horizontal_grid_to_end_of_window=True, total_columns=len(self.data.headers))
        self.sheet.enable_bindings("single_select", "drag_select", "column_select", "row_select", "column_width_resize",
                                   "row_width_resize", "column_height_resize", "row_height_resize", "arrowkeys",
                                   "right_click_popup_menu", "rc_select", "copy")

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

    def clear(self):
        self.sheet.grid_forget()
        self.sheet.delete_rows(rows=iter(range(self.sheet.get_total_rows())))
        self.search_results_idx = 0

    def beautify_search_results(self):
        for _, product_info_list in self.data.all_search_results:
            for product_info in product_info_list:
                for header in self.data.headers:
                    product_info[header] = product_info.setdefault(header, "").strip()

    def print_search_results(self):
        self.beautify_search_results()

        part_number, search_results = self.data.all_search_results[self.search_results_idx]
        self.search_results_idx += 1

        data = []
        for search_result in sorted(search_results, key=lambda d: d["vendor"]):
            if (self.data.websites_to_search[search_result["vendor"].split()[0].capitalize()] and
                    self.data.conditions_to_search[self.data.get_condition(search_result["condition"])]):
                data.append([search_result[header] for header in self.data.headers])

        if len(data) == 0:
            data.append([
                str(part_number) if header == "part number" else ("No such part" if header == "description" else "")
                for header in self.data.headers
            ])

        self.sheet.insert_rows(create_selections=False, rows=data)
        self.sheet.set_all_cell_sizes_to_text()

        self.sheet.grid(row=0, column=0, sticky="nsew")

    def update_search_results(self, _=None):
        self.clear()
        for _ in range(len(self.data.all_search_results)):
            self.print_search_results()

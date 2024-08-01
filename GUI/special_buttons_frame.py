from csv import DictWriter
import customtkinter
from GUI.frame import Frame
from Logic.data_file import DataClass
from time import localtime, strftime


class SpecialButtonsFrame(Frame):
    def __init__(self, master, data: DataClass, **kwargs):
        super().__init__(master, **kwargs)

        self.columnconfigure(0, weight=1)

        self.data = data

        self.create_csv_button = customtkinter.CTkButton(self, text="Create csv", command=self.create_csv,
                                                         state="disabled")
        self.create_csv_button.grid(padx=(5, 5), pady=(5, 5))
        self.interactive_elements.append(self.create_csv_button)

    def create_csv(self):
        moment = strftime("%Y-%b-%d__%H_%M_%S", localtime())
        with (open(f"out_{moment}.csv", "w") as out):
            writer = DictWriter(out, fieldnames=self.data.headers)
            writer.writeheader()

            for part_number, search_results in self.data.all_search_results:
                for dictionary in sorted(search_results, key=lambda d: d["vendor"]):
                    for website_name in self.data.websites_names:
                        if website_name.lower() in dictionary["vendor"] and (
                                not self.data.websites_to_search[website_name]):
                            break
                    else:
                        for i in range(len(self.data.conditions_to_search)):
                            if self.data.conditions_to_search[i] and self.data.conditions_checkers[i][1](
                                    dictionary["condition"]):
                                writer.writerow(dictionary)
                                break

import customtkinter
from CTkMessagebox import CTkMessagebox
from Logic.data_file import DataClass
import openpyxl
import re


class ExcelFilesWindow(customtkinter.CTkToplevel):
    def __init__(self, master, data: DataClass):
        super().__init__(master=master)

        self.master = master
        self.data = data
        self.checkboxes = []
        self.labels = []

        self.title("Excel Files")
        self.geometry("360x200")
        self.resizable(width=False, height=True)
        self.minsize(width=360, height=200)
        self.transient(self.master)

        self.rowconfigure(0, weight=1)
        self.columnconfigure((0, 1), weight=1)

        self.files_frame = customtkinter.CTkScrollableFrame(master=self, corner_radius=0)
        self.files_frame.columnconfigure((0, 1), weight=1)
        self.no_files_label = customtkinter.CTkLabel(master=self, text="No excel files loaded")

        if not self.data.loaded_excel_files:
            self.no_files_label.grid(row=0, column=0, columnspan=2, sticky="ew")
        else:
            self.files_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")
            for i, file_name in enumerate(self.data.loaded_excel_files.keys()):
                checkbox = customtkinter.CTkCheckBox(self.files_frame, corner_radius=12, width=24, text="")
                label = customtkinter.CTkLabel(master=self.files_frame, text=file_name)
                checkbox.grid(row=i + 1, column=0, padx=(10, 0), pady=(5, 0), sticky="e")
                checkbox.grid_remove()
                label.grid(row=i + 1, column=1, padx=(0, 10), pady=(5, 0), sticky="w")
                self.checkboxes.append(checkbox)
                self.labels.append(label)

        self.load_button = customtkinter.CTkButton(master=self, text="Load", command=self.load_excel_file)
        self.load_button.grid(column=0, padx=(10, 10), pady=(10, 10))
        self.delete_button = customtkinter.CTkButton(master=self, text="Delete", command=self.switch_in_deletion_mode)
        self.delete_button.grid(row=self.load_button.grid_info()["row"], column=1, padx=(10, 10), pady=(10, 10))
        self.cancel_button = customtkinter.CTkButton(master=self, text="Cancel", command=self.switch_in_normal_mode)

    def load_excel_file(self):
        file_path = customtkinter.filedialog.askopenfilename(title="Select an excel file",
                                                             filetypes=[("Excel", "*.xlsx")])
        file_name = re.split(r"[/\\]", file_path)[-1]

        if file_path:
            if file_name in self.data.loaded_excel_files.keys():
                CTkMessagebox(master=self, title="Warning",
                              message=f"The excel file \"{file_name}\" is already loaded!",
                              icon="warning", width=500, height=300, button_height=30, justify="center")
                return

            workbook = openpyxl.load_workbook(filename=file_path, read_only=True)
            sheet = workbook.active

            table_headers = [cell.value for cell in sheet[1]]
            for table_header in table_headers:
                for header in self.data.headers:
                    if table_header.lower() == header.lower():
                        break
                else:
                    CTkMessagebox(master=self, title="Warning",
                                  message=f"The excel file format is incorrect!\n(header \"{table_header}\" "
                                          "is not valid)",
                                  icon="warning", width=500, height=300, button_height=30, justify="center")
                    return

            workbook.close()

            self.data.websites_to_search[file_name] = True
            self.data.loaded_excel_files[file_name] = file_path

            if not self.files_frame.grid_info():
                self.no_files_label.grid_forget()
                self.files_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")

            checkbox = customtkinter.CTkCheckBox(self.files_frame, corner_radius=12, width=24, text="")
            label = customtkinter.CTkLabel(master=self.files_frame, text=file_name)
            checkbox.grid(column=0, padx=(10, 0), pady=(5, 0), sticky="e")
            label.grid(row=checkbox.grid_info()["row"], column=1, padx=(0, 10), pady=(5, 0), sticky="w")
            checkbox.grid_remove()
            self.checkboxes.append(checkbox)
            self.labels.append(label)

    def delete_excel_files(self):
        for i, checkbox in enumerate(self.checkboxes):
            if checkbox.get():
                checkbox.deselect()
                checkbox.grid_forget()
                self.labels[i].grid_forget()
                del self.data.loaded_excel_files[self.labels[i].cget("text")]
                del self.data.websites_to_search[self.labels[i].cget("text")]

        if not self.data.loaded_excel_files:
            self.files_frame.grid_forget()
            self.no_files_label.grid(row=0, column=0, columnspan=2, sticky="ew")
            self.switch_in_normal_mode()

    def switch_in_deletion_mode(self):
        if self.data.loaded_excel_files:
            for i, checkbox in enumerate(self.checkboxes):
                if self.labels[i].grid_info():
                    checkbox.grid()
            self.delete_button.configure(command=self.delete_excel_files)

            row = self.delete_button.grid_info()["row"]
            self.load_button.grid_forget()
            self.delete_button.grid_forget()
            self.delete_button.grid(row=row, column=0, padx=(10, 10), pady=(10, 10))
            self.cancel_button.grid(row=row, column=1, padx=(10, 10), pady=(10, 10))

    def switch_in_normal_mode(self):
        for checkbox in self.checkboxes:
            checkbox.deselect()
            checkbox.grid_remove()
        self.delete_button.configure(command=self.switch_in_deletion_mode)

        row = self.delete_button.grid_info()["row"]
        self.delete_button.grid_forget()
        self.cancel_button.grid_forget()
        self.load_button.grid(row=row, column=0, padx=(10, 10), pady=(10, 10))
        self.delete_button.grid(row=row, column=1, padx=(10, 10), pady=(10, 10))

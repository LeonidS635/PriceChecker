import customtkinter
from Logic.data_file import DataClass
from GUI.frames import Frames


class CaptchaWindow(customtkinter.CTkToplevel):
    def __init__(self, data: DataClass, frames: Frames, website_index: int, login: str, password: str):
        super().__init__()

        self.data = data
        self.frames = frames
        self.login = login
        self.password = password
        self.website_index = website_index

        self.title(self.data.websites_names[self.website_index])
        self.geometry("320x150")
        self.resizable(False, False)

        self.attributes("-topmost", "true")
        self.protocol("WM_DELETE_WINDOW", self.login_with_captcha)

        captcha = self.data.parsers[website_index].download_captcha()
        self.captcha = customtkinter.CTkImage(light_image=captcha, size=captcha.size)

        self.captcha_label_text = customtkinter.CTkLabel(self, text="Enter captcha code:")
        self.captcha_label_text.grid(row=2, column=0, padx=(20, 0), pady=(5, 10), sticky="w")

        self.captcha_input = customtkinter.CTkEntry(self)
        self.captcha_input.grid(row=2, column=1, padx=(20, 20), pady=(5, 10), sticky="nswe")
        self.captcha_input.bind("<Return>", self.login_with_captcha)

        self.captcha_label_img = customtkinter.CTkLabel(self, image=self.captcha, text="")
        self.captcha_label_img.grid(row=3, column=0, padx=(20, 0), pady=(5, 5), columnspan=2)

        self.login_button = customtkinter.CTkButton(self, text="Log in", command=self.login_with_captcha)
        self.login_button.grid(column=0, padx=(20, 20), pady=(5, 10), columnspan=2)

    def login_with_captcha(self, _=None):
        captcha_code = self.captcha_input.get()
        status = self.data.parsers[self.website_index].login_function(self.login, self.password, captcha_code)

        self.frames.websites_list_frame.stop_progressbar(self.website_index)

        if status == "OK":
            self.data.logged_in_websites[self.website_index] = True
            self.frames.websites_list_frame.select_checkbox(self.website_index)
            self.destroy()
        else:
            self.destroy()

            if status == "Time error":
                self.master.event_generate(f"<<ReportErrorTime-{self.data.websites_names[self.website_index]}>>")
            elif status == "Login error":
                self.master.event_generate(f"<<ReportErrorLogin-{self.data.websites_names[self.website_index]}>>")
            elif status == "Connection error":
                self.master.event_generate(f"<<ReportErrorConnection-{self.data.websites_names[self.website_index]}>>")

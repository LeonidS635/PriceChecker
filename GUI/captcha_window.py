import customtkinter
from Logic.data_file import DataClass
from threading import Thread


class CaptchaWindow(customtkinter.CTkToplevel):
    def __init__(self, master, master_x: int, master_y: int, data: DataClass, website_name: str,
                 captcha_code: customtkinter.StringVar, **kwargs):
        super().__init__(master=master, **kwargs)

        self.captcha = None
        self.captcha_code = captcha_code
        for parser in data.parsers:
            if parser.__class__.__name__ == website_name:
                self.parser = parser

        self.title(website_name)
        self.geometry(f"+{master_x + 70}+{master_y + 50}")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self.get_captcha_code)

        self.captcha_label_text = customtkinter.CTkLabel(self, text="Enter captcha code:")
        self.captcha_label_text.grid(row=2, column=0, padx=(20, 0), pady=(5, 10), sticky="w")

        self.captcha_input = customtkinter.CTkEntry(self)
        self.captcha_input.grid(row=2, column=1, padx=(20, 20), pady=(5, 10), sticky="nsew")
        self.captcha_input.bind("<Return>", self.get_captcha_code)

        self.captcha_label_img = customtkinter.CTkLabel(self, text="Loading captcha...")
        self.captcha_label_img.grid(row=3, column=0, padx=(20, 0), pady=(5, 5), columnspan=2)

        self.login_button = customtkinter.CTkButton(self, text="Log in", command=self.get_captcha_code)
        self.login_button.grid(column=0, padx=(20, 20), pady=(5, 10), columnspan=2)

        self.bind("<<DownloadingFailed>>",
                  lambda event: self.captcha_label_img.configure(text="Failed to download captcha"))
        self.bind("<<DownloadingSucceed>>",
                  lambda event: self.captcha_label_img.configure(image=customtkinter.CTkImage(light_image=self.captcha,
                                                                                              size=self.captcha.size),
                                                                 text=""))

        Thread(target=self.download_captcha, daemon=True).start()
        self.after(60000, self.get_captcha_code)

    def download_captcha(self):
        self.captcha = self.parser.download_captcha()
        if self.captcha_label_img.winfo_exists():
            if self.captcha is None:
                self.event_generate("<<DownloadingFailed>>")
            else:
                self.event_generate("<<DownloadingSucceed>>")

    def get_captcha_code(self, _=None):
        self.captcha_code.set(self.captcha_input.get())
        self.destroy()

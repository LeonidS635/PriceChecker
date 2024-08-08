import customtkinter
from Logic.data_file import DataClass
from threading import Thread


class CaptchaWindow(customtkinter.CTkToplevel):
    def __init__(self, master, data: DataClass, website_name: str, captcha_code: customtkinter.StringVar, **kwargs):
        super().__init__(master=master, **kwargs)

        self.master = master
        self.data = data
        self.captcha_code = captcha_code
        self.website_name = website_name
        for parser in self.data.parsers:
            if parser.__class__.__name__ == self.website_name:
                self.parser = parser

        self.title(self.website_name)
        self.resizable(False, False)

        self.attributes("-topmost", "true")
        self.protocol("WM_DELETE_WINDOW", self.login_with_captcha)

        self.captcha_label_text = customtkinter.CTkLabel(self, text="Enter captcha code:")
        self.captcha_label_text.grid(row=2, column=0, padx=(20, 0), pady=(5, 10), sticky="w")

        self.captcha_input = customtkinter.CTkEntry(self)
        self.captcha_input.grid(row=2, column=1, padx=(20, 20), pady=(5, 10), sticky="nswe")
        self.captcha_input.bind("<Return>", self.login_with_captcha)

        self.captcha_label_img = customtkinter.CTkLabel(self, text="Loading captcha...")
        self.captcha_label_img.grid(row=3, column=0, padx=(20, 0), pady=(5, 5), columnspan=2)

        self.login_button = customtkinter.CTkButton(self, text="Log in", command=self.login_with_captcha)
        self.login_button.grid(column=0, padx=(20, 20), pady=(5, 10), columnspan=2)

        Thread(target=self.download_captcha, daemon=True).start()

    def download_captcha(self):
        captcha = self.parser.download_captcha()
        if self.captcha_label_img.winfo_exists():
            if captcha is None:
                self.captcha_label_img.configure(text="Failed to download captcha")
            else:
                self.captcha_label_img.configure(image=customtkinter.CTkImage(light_image=captcha, size=captcha.size),
                                                 text="")

    def login_with_captcha(self, _=None):
        self.captcha_code.set(self.captcha_input.get())
        self.destroy()

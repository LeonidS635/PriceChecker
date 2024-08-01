from abc import abstractmethod
from Logic.data_file import Status
from requests import Response, Session
from requests.exceptions import ConnectionError, HTTPError, RequestException, Timeout
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
import time
from typing import Callable


class Parser:
    def __init__(self):
        self.delay: int = 20
        self.logged_in: bool = False
        self.vendor: str = self.__class__.__name__.lower()
        self.status: Status = Status.OK

        self.product_info: dict[str, str] = {
            "vendor": self.vendor,
            "part number": "",
            "description": "",
            "QTY": "",
            "price": "",
            "condition": "",
            "lead time": "",
            "warehouse": "",
            "other information": ""
        }

    def reset_product_info(self):
        self.product_info.clear()
        self.product_info["vendor"] = self.vendor

    @abstractmethod
    def request_wrapper(self, _) -> bool:
        pass

    @abstractmethod
    def login_function(self, login: str, password: str) -> str:
        pass

    @abstractmethod
    def search_part(self, part_number: str, search_results: list) -> str:
        pass


class ParserRequests(Parser):
    def __init__(self):
        super().__init__()

        self.session = Session()
        self.response = Response()

    def __del__(self):
        self.session.close()

    def request_wrapper(self, request: Callable[..., Response], **kwargs) -> bool:
        try:
            self.response = request(timeout=self.delay, **kwargs)
            self.response.raise_for_status()
        except Timeout:
            self.status = self.status.Time_error
        except ConnectionError:
            self.status = self.status.Connection_error
        except HTTPError:
            if self.response.status_code == 429:
                time.sleep(int(self.response.headers['Retry-After']))
                return self.request_wrapper(request, **kwargs)
            else:
                self.status = self.status.Connection_error
        except RequestException:
            self.status = self.status.Other
        else:
            self.status = self.status.OK
            return True
        return False

    @abstractmethod
    def login_function(self, login: str, password: str) -> Status:
        pass

    @abstractmethod
    def search_part(self, part_number: str, search_results: list) -> Status:
        pass


class ParserSelenium(Parser):
    def __init__(self, **kwargs):
        super().__init__()

        self.driver = webdriver.Chrome(**kwargs)
        self.driver.set_page_load_timeout(self.delay)
        self.is_destroyed = False

    def __del__(self):
        if not self.is_destroyed:
            self.driver.quit()
            self.is_destroyed = True

    def request_wrapper(self, url: str) -> bool:
        try:
            self.driver.get(url)
        except TimeoutException:
            self.status = self.status.Time_error
        except WebDriverException:
            self.status = self.status.Connection_error
        else:
            self.status = self.status.OK
            return True
        return False

    @abstractmethod
    def login_function(self, login: str, password: str) -> Status:
        pass

    @abstractmethod
    def search_part(self, part_number: str, search_results: list) -> Status:
        pass

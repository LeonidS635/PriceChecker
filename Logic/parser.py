from abc import abstractmethod
from Logic.data_file import Status
from requests import Response, Session
from requests.exceptions import ConnectionError, HTTPError, RequestException, Timeout
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from threading import Event
from time import sleep
from typing import Any, Callable, Type


class Parser:
    def __init__(self):
        self.delay = 20
        self.logged_in = False
        self.is_destroyed = False
        self.status = Status.OK
        self.stop_event = Event()
        self.vendor = self.__class__.__name__.lower()

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
    def __del__(self):
        pass

    @abstractmethod
    def request_wrapper(self, *_: Any, **__: Any) -> Any:
        pass

    @abstractmethod
    def login_function(self, login: str, password: str) -> str:
        pass

    @abstractmethod
    def search_part(self, number: str, search_results: list) -> str:
        pass


class ParserRequests(Parser):
    def __init__(self):
        super().__init__()

        self.session = Session()
        self.response = Response()

    def __del__(self):
        if not self.is_destroyed and hasattr(self, "session"):
            self.session.close()
            self.is_destroyed = True

    def request_wrapper(self, request: Callable[..., Response], **kwargs) -> bool:
        if self.stop_event.is_set():
            return False

        try:
            self.response = request(timeout=self.delay, **kwargs)
            self.response.raise_for_status()
        except Timeout:
            self.status = self.status.Time_error
        except ConnectionError:
            self.status = self.status.Connection_error
        except HTTPError:
            if self.response.status_code == 429:
                sleep(int(self.response.headers['Retry-After']))
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
    def search_part(self, number: str, search_results: list) -> Status:
        pass


class ParserSelenium(Parser):
    def __init__(self, **kwargs):
        super().__init__()

        self.driver = webdriver.Chrome(**kwargs)
        self.driver.set_page_load_timeout(self.delay)

    def __del__(self):
        if not self.is_destroyed and hasattr(self, "driver"):
            self.driver.quit()
            self.is_destroyed = True

    def request_wrapper(self, request: Callable[..., Any], *args, exceptions_to_ignore: tuple[Type[Exception]] = (),
                        **kwargs) -> Any:
        if self.stop_event.is_set():
            raise Exception("Process needs to be stopped")

        try:
            self.status = Status.OK
            return request(*args, **kwargs)
        except exceptions_to_ignore:
            return None
        except TimeoutException:
            self.status = Status.Time_error
            raise
        except WebDriverException:
            self.status = Status.Connection_error
            raise
        except Exception:
            self.status = Status.Other
            raise

    @abstractmethod
    def login_function(self, login: str, password: str) -> Status:
        pass

    @abstractmethod
    def search_part(self, number: str, search_results: list) -> Status:
        pass

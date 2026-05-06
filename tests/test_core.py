import builtins

import pytest

import nfcl.core as core
from nfcl.core import ComciganAPI


def test_split_subject_teacher_empty():
    assert ComciganAPI._split_subject_teacher("") == ("-", "")


def test_split_subject_teacher_subject_only():
    assert ComciganAPI._split_subject_teacher("수학") == ("수학", "")


def test_split_subject_teacher_subject_and_teacher():
    assert ComciganAPI._split_subject_teacher("영어 홍길동") == ("영어", "홍길동")


def test_split_subject_teacher_multiline():
    assert ComciganAPI._split_subject_teacher("물리\n이순신") == ("물리", "이순신")


def test_missing_selenium_error_mentions_only_selenium(monkeypatch):
    real_import = builtins.__import__

    def blocked_import(name, *args, **kwargs):
        if name == "selenium" or name.startswith("selenium."):
            raise ImportError("blocked selenium import")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked_import)

    with pytest.raises(RuntimeError) as exc_info:
        core._load_selenium()

    message = str(exc_info.value)
    assert "selenium" in message
    assert "webdriver-manager" not in message


def test_driver_creation_uses_selenium_manager_not_webdriver_manager(monkeypatch):
    calls = {}

    class FakeOptions:
        def __init__(self):
            self.arguments = []
            self.experimental_options = {}
            self.page_load_strategy = None

        def add_experimental_option(self, key, value):
            self.experimental_options[key] = value

        def add_argument(self, argument):
            self.arguments.append(argument)

    class FakeWebDriver:
        def ChromeOptions(self):
            return FakeOptions()

        def Chrome(self, **kwargs):
            calls["chrome_kwargs"] = kwargs
            return object()

    class FakeWait:
        def __init__(self, driver, timeout):
            self.driver = driver
            self.timeout = timeout

    class FakeBy:
        ID = "id"
        TAG_NAME = "tag name"
        CLASS_NAME = "class name"
        CSS_SELECTOR = "css selector"

    class FakeEC:
        pass

    class FakeSelect:
        pass

    monkeypatch.setattr(
        core,
        "_load_selenium",
        lambda: (FakeWebDriver(), LookupError, TimeoutError, FakeBy, FakeEC, FakeSelect, FakeWait),
    )

    api = ComciganAPI()

    assert api.driver is not None
    assert "options" in calls["chrome_kwargs"]
    assert "service" not in calls["chrome_kwargs"]

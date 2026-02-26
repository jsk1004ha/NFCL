from nfcl.core import ComciganAPI


def test_split_subject_teacher_empty():
    assert ComciganAPI._split_subject_teacher("") == ("-", "")


def test_split_subject_teacher_subject_only():
    assert ComciganAPI._split_subject_teacher("수학") == ("수학", "")


def test_split_subject_teacher_subject_and_teacher():
    assert ComciganAPI._split_subject_teacher("영어 홍길동") == ("영어", "홍길동")


def test_split_subject_teacher_multiline():
    assert ComciganAPI._split_subject_teacher("물리\n이순신") == ("물리", "이순신")


def test_get_cached_chromedriver_path_reuses_cached_value(monkeypatch):
    calls = {"count": 0}

    class FakeManager:
        def install(self):
            calls["count"] += 1
            return "/tmp/fake/chromedriver"

    monkeypatch.setattr("nfcl.core.ChromeDriverManager", FakeManager)
    ComciganAPI._CHROMEDRIVER_PATH = None

    first = ComciganAPI._get_cached_chromedriver_path()
    second = ComciganAPI._get_cached_chromedriver_path()

    assert first == "/tmp/fake/chromedriver"
    assert second == "/tmp/fake/chromedriver"
    assert calls["count"] == 1

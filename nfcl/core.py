from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

try:
    from selenium import webdriver
    from selenium.common.exceptions import NoSuchElementException, TimeoutException
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import Select, WebDriverWait
    from webdriver_manager.chrome import ChromeDriverManager
    _SELENIUM_IMPORT_ERROR: Optional[Exception] = None
except Exception as import_error:  # pragma: no cover
    webdriver = None
    NoSuchElementException = Exception
    TimeoutException = Exception
    Service = None
    By = None
    EC = None
    Select = None
    WebDriverWait = None
    ChromeDriverManager = None
    _SELENIUM_IMPORT_ERROR = import_error


@dataclass(frozen=True)
class ComciganConfig:
    headless: bool = True
    timeout_seconds: int = 12
    base_url: str = "http://www.xn--s39aj90b0nb2xw6xh.kr/"


class ComciganAPI:
    """컴시간 알리미 시간표를 수집하는 API 클라이언트."""

    WEEK_DAYS = ("월", "화", "수", "목", "금")

    def __init__(self, headless: bool = True, timeout_seconds: int = 12):
        if _SELENIUM_IMPORT_ERROR is not None:
            raise RuntimeError(
                "selenium 및 webdriver-manager 의존성이 필요합니다. "
                "`pip install selenium webdriver-manager` 후 다시 시도해주세요."
            ) from _SELENIUM_IMPORT_ERROR

        self.config = ComciganConfig(headless=headless, timeout_seconds=timeout_seconds)
        self.driver = self._create_driver()
        self.wait = WebDriverWait(self.driver, self.config.timeout_seconds)

    def _create_driver(self):
        options = webdriver.ChromeOptions()
        options.page_load_strategy = "eager"
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1200,900")
        options.add_argument("--blink-settings=imagesEnabled=false")
        if self.config.headless:
            options.add_argument("--headless=new")

        return webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options,
        )

    def close(self) -> None:
        if self.driver:
            self.driver.quit()
            self.driver = None

    def __enter__(self) -> "ComciganAPI":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _switch_to_search_context(self) -> bool:
        driver = self.driver

        def _has_search_box() -> bool:
            try:
                driver.find_element(By.ID, "sc")
                return True
            except NoSuchElementException:
                return False

        driver.switch_to.default_content()
        if _has_search_box():
            return True

        for selector in ("frame", "iframe"):
            frames = driver.find_elements(By.TAG_NAME, selector)
            for frame in frames:
                driver.switch_to.default_content()
                driver.switch_to.frame(frame)
                if _has_search_box():
                    return True

        driver.switch_to.default_content()
        return False

    @staticmethod
    def _split_subject_teacher(raw_text: str) -> Tuple[str, str]:
        text = raw_text.replace("\n", " ").strip()
        if not text:
            return "-", ""

        parts = text.split()
        if len(parts) == 1:
            return parts[0], ""

        return parts[0], " ".join(parts[1:])

    def _extract_timetable(self) -> Dict[str, List[Dict[str, str]]]:
        schedule = {day: [] for day in self.WEEK_DAYS}
        rows = self.driver.find_elements(By.TAG_NAME, "tr")
        header_count = 0

        for row in rows:
            periods = row.find_elements(By.CLASS_NAME, "교시")
            if not periods:
                continue

            period_text = periods[0].text.strip()
            if period_text == "교시":
                header_count += 1
                if header_count > 1:
                    break
                continue

            simple_period = period_text.split("(")[0].strip()
            cells = row.find_elements(By.CSS_SELECTOR, "td.내용, td.변경")
            if len(cells) != 5:
                continue

            for day_idx, cell in enumerate(cells):
                subject, teacher = self._split_subject_teacher(cell.text)
                class_attr = cell.get_attribute("class") or ""

                schedule[self.WEEK_DAYS[day_idx]].append(
                    {
                        "period": simple_period,
                        "subject": subject,
                        "teacher": teacher,
                        "changed": "변경" in class_attr,
                    }
                )

        return schedule

    def get_timetable(self, school_name: str, grade: int, class_num: int):
        if not self.driver:
            return {"error": "브라우저 세션이 종료되었습니다. 새 ComciganAPI 인스턴스를 생성해주세요."}

        try:
            self.driver.get(self.config.base_url)

            if not self._switch_to_search_context():
                return {"error": "프레임 탐색 실패"}

            search_box = self.wait.until(EC.element_to_be_clickable((By.ID, "sc")))
            search_box.clear()
            search_box.send_keys(school_name)
            self.driver.find_element(By.CSS_SELECTOR, 'input[value="검색"]').click()

            self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "tr.검색")))
            rows = self.driver.find_elements(By.CSS_SELECTOR, "tr.검색")

            found_school_name = ""
            clicked = False
            for row in rows:
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) < 2:
                    continue

                try:
                    link = cols[1].find_element(By.TAG_NAME, "a")
                except NoSuchElementException:
                    continue

                if school_name in link.text:
                    found_school_name = link.text
                    link.click()
                    clicked = True
                    break

            if not clicked:
                return {"error": f"'{school_name}' 학교를 찾을 수 없습니다."}

            select_el = self.wait.until(EC.presence_of_element_located((By.ID, "ba")))
            selector = Select(select_el)
            try:
                selector.select_by_value(f"{grade}-{class_num}")
            except NoSuchElementException:
                return {"error": "해당 반 정보가 없습니다."}

            self.wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "td.내용, td.변경"))
            )
            final_schedule = self._extract_timetable()

            return {
                "school": found_school_name,
                "class": f"{grade}-{class_num}",
                "timetable": final_schedule,
            }

        except TimeoutException:
            return {"error": "요청 제한 시간 초과. 학교명/반 정보를 확인하거나 잠시 후 다시 시도해주세요."}
        except Exception as exc:
            return {"error": str(exc)}

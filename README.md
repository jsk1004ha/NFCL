# NFCL (New Fantastic Comsigan Loader)

[![PyPI version](https://badge.fury.io/py/NFCL.svg)](https://badge.fury.io/py/NFCL)

본 프로그램은 컴시간 알리미에서 학교 시간표 데이터를 가져오는 Python 라이브러리입니다. 학교 이름, 학년, 반 정보를 입력하여 주간 시간표를 JSON 형식으로 받아올 수 있습니다.

## 주요 기능

- **시간표 추출**: 월요일부터 금요일까지의 교시별 과목 및 담당 교사 정보를 추출합니다.
- **성능 최적화 옵션 기본 적용**: 불필요한 이미지 로딩을 막고, `eager` 페이지 로드 전략으로 응답 속도를 개선했습니다.
- **세션 재사용 가능**: `ComciganAPI` 인스턴스를 여러 번 호출할 때 브라우저를 재활용할 수 있습니다.

## 설치 방법

```bash
pip install NFCL
```

*참고: Chrome 브라우저가 설치되어 있어야 합니다.*

## 사용 방법

### 1. 간단한 함수 호출 방식
```python
import nfcl

# 학교명, 학년, 반 입력
result = nfcl.get_timetable("인천과학고등학교", 1, 1)
print(result)
```

### 2. 클래스 인스턴스 사용 방식 (권장: 반복 조회 시)
```python
from nfcl import ComciganAPI

# API 객체 생성 (headless=False로 설정하면 브라우저 창이 보입니다)
with ComciganAPI(headless=True, timeout_seconds=12) as api:
    # 첫 조회
    result1 = api.get_timetable("인천과학고등학교", 1, 1)

    # 같은 브라우저 세션으로 추가 조회
    result2 = api.get_timetable("인천과학고등학교", 1, 2)

    print(result1)
    print(result2)
```

### 결과 데이터 구조

```json
{
    "school": "학교명",
    "class": "1-1",
    "timetable": {
        "월": [
            {
                "period": "1",
                "subject": "수학",
                "teacher": "홍길동",
                "changed": false
            }
        ],
        "화": [],
        "수": [],
        "목": [],
        "금": []
    }
}
```

- `period`: 교시
- `subject`: 과목명
- `teacher`: 담당 교사
- `changed`: 시간표 변경 여부 (`true`면 변경됨, `false`면 일반)

## 의존성

- [selenium](https://pypi.org/project/selenium/)
- [webdriver-manager](https://pypi.org/project/webdriver-manager/)

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 문제 해결 (Troubleshooting)

### `RuntimeError: selenium 및 webdriver-manager 의존성이 필요합니다`
이 오류는 `selenium` 또는 `webdriver-manager` 패키지가 올바르게 설치되지 않았을 때 발생합니다.
아래 명령어로 직접 의존성을 설치해보세요:

```bash
pip install selenium webdriver-manager
```

### 브라우저 닫힘 현상
`ComciganAPI`를 `with` 구문 없이 사용할 경우, Python 스크립트가 종료될 때 브라우저도 함께 닫힐 수 있습니다. 프로세스가 종료되지 않게 하려면 `time.sleep()` 등을 사용하여 대기하거나, `headless=True` (기본값) 모드를 사용하세요.


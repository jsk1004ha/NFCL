from .core import ComciganAPI


def get_timetable(school_name, grade, class_num):
    """학교 이름, 학년, 반을 입력하면 시간표 데이터를 반환합니다."""
    with ComciganAPI(headless=True) as api:
        return api.get_timetable(school_name, grade, class_num)

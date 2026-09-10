from datetime import date, datetime
from zoneinfo import ZoneInfo


def today_bangkok() -> date:
    return datetime.now(ZoneInfo("Asia/Bangkok")).date()

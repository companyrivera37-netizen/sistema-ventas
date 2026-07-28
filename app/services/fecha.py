from datetime import datetime
from zoneinfo import ZoneInfo

ZONA_PERU = ZoneInfo("America/Lima")


def hoy_peru():
    return datetime.now(ZONA_PERU).date()

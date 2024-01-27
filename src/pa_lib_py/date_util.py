from datetime import datetime, timedelta

def dateFromMidnight(since: datetime):
    return since.replace(hour=0, minute=0, second=1, microsecond=0)

def dateToMidnight(until: datetime):
    return until.replace(hour=23, minute=59, second=59, microsecond=0)



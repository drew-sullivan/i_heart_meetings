import datetime
from datetime import timedelta

WORK_HOURS_PER_YEAR = 2000
WORK_HOURS_PER_DAY = 8
WORK_DAYS_PER_WEEK = 5
WORK_HOURS_PER_WEEK = WORK_HOURS_PER_DAY * WORK_DAYS_PER_WEEK
WORK_SECONDS_PER_WEEK = WORK_HOURS_PER_WEEK * 3600
WORK_WEEKS_PER_YEAR = WORK_HOURS_PER_YEAR / (WORK_HOURS_PER_DAY * WORK_DAYS_PER_WEEK)
WORK_DAYS_PER_YEAR = WORK_WEEKS_PER_YEAR * WORK_DAYS_PER_WEEK
WORK_SECONDS_PER_YEAR = WORK_HOURS_PER_YEAR * 3600

FORMAT_DATETIME_OBJ_TO_STR = '%Y-%m-%d %H:%M:%S'
FORMAT_STR_TO_DATETIME_OBJ = '%A, %b %d, %Y - %I:%M'

def translate_seconds(total_seconds):
    # divmod returns quotient and remainder
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    work_days, hours = divmod(hours, WORK_HOURS_PER_DAY)
    return (int(work_days), int(hours), int(minutes), int(seconds))


def make_pretty_for_printing(work_days, hours, minutes, seconds):
    seconds = "{} second{}".format(int(seconds), "" if seconds == 1 else "s")
    minutes = "{} minute{}".format(int(minutes), "" if minutes == 1 else "s")
    hours = "{} hour{}".format(int(hours), "" if hours == 1 else "s")
    work_days = "{} work-day{}".format(int(work_days), "" if work_days == 1 else "s")
    return (work_days, hours, minutes, seconds)

def make_dt_or_time_str_pretty_for_printing(dt_obj_or_str):
    if isinstance(dt_obj_or_str, str):
        if dt_obj_or_str[-6] == '-':
            dt_obj_or_str = dt_obj_or_str[:19]
        dt_obj_or_str = datetime.datetime.strptime(dt_obj_or_str, FORMAT_DATETIME_OBJ_TO_STR)
    pretty_printed_str = datetime.datetime.strftime(dt_obj_or_str, FORMAT_STR_TO_DATETIME_OBJ)
    return pretty_printed_str

def convert_duration_to_work_seconds(duration):
    seconds = duration.total_seconds()
    hours = float(seconds) / 3600
    if hours > WORK_HOURS_PER_DAY and hours < 24:
        hours = WORK_HOURS_PER_DAY
    if hours >= 24:
        days, hours = divmod(hours, 24)
        if hours <= WORK_HOURS_PER_DAY:
            hours += days * WORK_HOURS_PER_DAY
    seconds = hours * 3600
    return seconds

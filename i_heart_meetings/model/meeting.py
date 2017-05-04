#!/usr/bin/python

import datetime
import dateutil

from datetime import time
from datetime import timedelta
from dateutil.parser import parse
from money import Money # Currently only supporting USD, but others coming soon!


class Meeting:
    """A meeting extracted from the Google Calendar API

    Attributes:
        num: int - 1, 2, 3...
        summary: str - description of meeting
        start: str - human readable start time of meeting
        end: str - human readable end time of meeting
        duration: str - duration of event
        num_attendees: int - number of attendees

    Can return:
        cost_in_dollars: Money object of cost in dollars
        financial_cost_for_printing: str version of above
        cost_in_seconds: int
        time_cost_for_printing: str - formatted work_days, hrs, mins, secs
        percent_time: float - percent of team's time spent in the meeting
    """

    WORK_HOURS_PER_YEAR = 2000
    WORK_HOURS_PER_DAY = 8
    WORK_SECONDS_PER_YEAR = WORK_HOURS_PER_YEAR * 3600
    YEARLY_SALARY_USD = 75000
    COST_PER_SECOND = float(YEARLY_SALARY_USD) / WORK_SECONDS_PER_YEAR

    ROUND_TO_THIS_MANY_PLACES = 2
    CURRENCY = 'USD'
    CURRENCY_FORMAT = 'en_US'
    FORMAT_DATETIME_OBJ_TO_STR = '%Y-%m-%d %H:%M:%S'
    FORMAT_STR_TO_DATETIME_OBJ = '%A, %b %d, %Y - %I:%M'

    def __init__(self, meeting_num, summary, start, end, duration,
                 num_attendees):
        self.num = meeting_num
        self.summary = summary
        self.start = start
        self.end = end
        self.duration = duration
        self.num_attendees = num_attendees


    def percent_time(self):
        work_seconds = self._get_seconds_from_duration()
        work_hours = work_seconds / 3600
        percent_time = (float(work_hours) / self.WORK_HOURS_PER_DAY) * 100
        percent_time = round(percent_time, self.ROUND_TO_THIS_MANY_PLACES)
        return percent_time


    def cost_in_seconds(self):
        work_seconds = self._get_seconds_from_duration()
        cost_in_seconds = self.num_attendees * work_seconds
        return cost_in_seconds


    def time_cost_for_printing(self):
        seconds = self.cost_in_seconds()
        work_days, hours, minutes, seconds = self._translate_seconds(seconds)
        work_days, hours, minutes, seconds = self._make_pretty_for_printing(work_days, hours, minutes, seconds)
        time_cost = '{}, {}, {}, {}'.format(work_days, hours, minutes, seconds)
        return time_cost


    def cost_in_dollars(self):
        work_seconds = self._get_seconds_from_duration()
        cost_in_dollars = work_seconds * self.COST_PER_SECOND * self.num_attendees
        cost_in_dollars = Money(cost_in_dollars, self.CURRENCY)
        return cost_in_dollars


    def cost_in_dollars_pretty_print(self):
        work_seconds = self._get_seconds_from_duration()
        cost_in_dollars = work_seconds * self.COST_PER_SECOND * self.num_attendees
        cost_in_dollars = Money(cost_in_dollars, self.CURRENCY).format(self.CURRENCY_FORMAT)
        return cost_in_dollars


    def _make_pretty_for_printing(self, days, hours, minutes, seconds):
        seconds = "{} second{}".format(int(seconds), "" if seconds == 1 else "s")
        minutes = "{} minute{}".format(int(minutes), "" if minutes == 1 else "s")
        hours = "{} hour{}".format(int(hours), "" if hours == 1 else "s")
        work_days = "{} work-day{}".format(int(days), "" if days == 1 else "s")
        return work_days, hours, minutes, seconds


    def _translate_seconds(self, seconds):
        # divmod returns quotient and remainder
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        work_days, hours = divmod(hours, self.WORK_HOURS_PER_DAY)
        return (int(work_days), int(hours), int(minutes), int(seconds))


    def _get_seconds_from_duration(self):
        seconds = self.duration.total_seconds()
        seconds = self.__convert_seconds_to_work_seconds(seconds)
        return seconds


    def __convert_seconds_to_work_seconds(self, seconds):
        hours = float(seconds) / 3600
        if hours > self.WORK_HOURS_PER_DAY and hours < 24:
            hours = self.WORK_HOURS_PER_DAY
        if hours >= 24:
            days, hours = divmod(hours, 24)
            if hours <= self.WORK_HOURS_PER_DAY:
                hours += days * self.WORK_HOURS_PER_DAY
        seconds = hours * 3600
        return seconds


    def print_meeting_info(self):
        print("""
        Meeting {0}: {1}
        **************************************************
        Start: {2}
        End: {3}
        Duration: {4}
        Number of Attendees: {5}
        Cost: {6}
        Cost in Time: {7}
        Percentage of time spent in meeting: {8}% """.format(
            self.num, 
            self.summary,
            self._make_dt_or_time_str_pretty_for_printing(self.start),
            self._make_dt_or_time_str_pretty_for_printing(self.end),
            self.duration, self.num_attendees,
            self.cost_in_dollars(),
            self.time_cost_for_printing(),
            self.percent_time()
            )
        )


    def _make_dt_or_time_str_pretty_for_printing(self, dt_obj_or_str):
        if isinstance(dt_obj_or_str, str):
            if dt_obj_or_str[-6] == '-':
                dt_obj_or_str = dt_obj_or_str[:19]
            dt_obj_or_str = datetime.datetime.strptime(dt_obj_or_str, self.FORMAT_DATETIME_OBJ_TO_STR)
        pretty_printed_str = datetime.datetime.strftime(dt_obj_or_str, self.FORMAT_STR_TO_DATETIME_OBJ)
        return pretty_printed_str

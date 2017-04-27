#!/usr/bin/python

import dateutil

from model.meeting import Meeting 
from dateutil.parser import parse # used to get meeting_duration by subtracting datetime objects

class Week_Of_Meetings:
    """Calculates the costs of a meetings pull when passed a list of meetings
    objects

    Attributes:
        google_meetings_blob: blob - meeting info obtained from Google
        time_cost_weekly_in_seconds:
        financial_cost_weekly:
        percent_time_spent:
        numbers: list - meeting nums
        durations: list - durations of meetings
        summaries: list - summaries of meetings
        num_meetings: int - number of meetings in pull
        avg_meeting_duration: int - total seconds from all meetings in pull
        meeting_frequency = dict - k: meeting start, v: num_attendees
    """

    WORK_HOURS_PER_YEAR = 2000
    WORK_HOURS_PER_DAY = 8
    WORK_DAYS_PER_WEEK = 5
    WORK_HOURS_PER_WEEK = WORK_HOURS_PER_DAY * WORK_DAYS_PER_WEEK
    WORK_SECONDS_PER_WEEK = WORK_HOURS_PER_WEEK * 3600
    WORK_WEEKS_PER_YEAR = WORK_HOURS_PER_YEAR / (WORK_HOURS_PER_DAY * WORK_DAYS_PER_WEEK)
    WORK_DAYS_PER_YEAR = WORK_WEEKS_PER_YEAR * WORK_DAYS_PER_WEEK
    WORK_SECONDS_PER_YEAR = WORK_HOURS_PER_YEAR * 3600

    IDEAL_PERCENT_TIME_IN_MEETINGS = 5

    YEARLY_SALARY_USD = 75000
    COST_PER_SECOND = float(YEARLY_SALARY_USD) / WORK_SECONDS_PER_YEAR
    CURRENCY = 'USD'
    CURRENCY_FORMAT = 'en_US'

    TEAM_SIZE = 10

    PERSON_SECONDS_PER_WEEK = TEAM_SIZE * WORK_SECONDS_PER_WEEK
    PERSON_SECONDS_PER_YEAR = TEAM_SIZE * WORK_SECONDS_PER_YEAR

    ROUND_TO_THIS_MANY_PLACES = 2
    FORMAT_DATETIME_OBJ_TO_STR = '%Y-%m-%d %H:%M:%S'
    FORMAT_STR_TO_DATETIME_OBJ = '%A, %b %d, %Y - %I:%M'

    NUM_TOP_MEETING_TIMES = 3


    def __init__(self, google_meetings_blob):
        self.google_meetings_blob = google_meetings_blob


    def main(self, google_meetings_blob):
        meetings_list = self.get_meetings_list(google_meetings_blob)


    def cost_in_seconds(self, meetings):
        cost_in_seconds = 0
        for meeting in meetings:
            cost_in_seconds += meeting.cost_in_seconds()
        return cost_in_seconds


    def time_cost_for_printing(self):
        seconds = self.cost_in_seconds()
        work_days, hours, minutes, seconds = self._translate_seconds(seconds)
        work_days, hours, minutes, seconds = self._make_pretty_for_printing(work_days, hours, minutes, seconds)
        time_cost = '{}, {}, {}, {}'.format(work_days, hours, minutes, seconds)
        return time_cost


    def cost_in_dollars(self, meetings):
        cost_in_dollars = 0
        for meeting in meetings:
            cost_in_dollars += meeting.cost_in_dollars()
        return cost_in_dollars


    def percent_time_spent(self, meetings):
        percent_time_spent = 0
        for meeting in meetings:
            percent_time_spent += float(self.cost_in_seconds) / PERSON_SECONDS_PER_WEEK
        percent_time_spent = round(percent_time_spent * 100, ROUND_TO_THIS_MANY_PLACES)
        return percent_time_spent


    def ideal_time_cost(self, meetings):
        ideal_time_cost = IDEAL_PERCENT_TIME_IN_MEETINGS
        ideal_time_cost /= 100
        ideal_time_cost *= PERSON_SECONDS_PER_WEEK
        days, hours, minutes, seconds = _translate_seconds(ideal_time_cost)
        days, hours, minutes, seconds = _make_pretty_for_printing(days, hours, minutes, seconds)
        ideal_time_cost = ('{0}, {1}, {2}, {3}').format(days, hours, minutes, seconds)
        return ideal_time_cost


    def ideal_financial_cost(self, meetings):
        ideal_financial_cost = float(IDEAL_PERCENT_TIME_IN_MEETINGS)
        ideal_financial_cost /= 100
        ideal_financial_cost *= COST_PER_SECOND
        ideal_financial_cost *= PERSON_SECONDS_PER_WEEK
        ideal_financial_cost = Money(ideal_financial_cost, CURRENCY).format(CURRENCY_FORMAT)
        return ideal_financial_cost


    def num_meetings(self, meetings):
        num_meetings = 0
        for meeting in meetings:
            num_meetings += 1
        return num_meetings


    def avg_cost_in_seconds(self, cost_in_seconds, num_meetings):
        avg_cost_in_seconds = float(self.cost_in_seconds) / self.num_meetings
        days, hours, minutes, seconds = _translate_seconds(avg_cost_in_seconds)
        days, hours, minutes, seconds = _make_pretty_for_printing(days, hours, minutes, seconds)
        avg_cost_in_seconds = ('{0}, {1}, {2}, {3}').format(days, hours, minutes, seconds)
        return avg_cost_in_seconds


    def avg_cost_in_dollars(self, cost_in_dollars, num_meetings):
        avg_meeting_cost = float(self.cost_in_dollars) / self.num_meetings
        avg_meeting_cost = Money(avg_meeting_cost, CURRENCY).format(CURRENCY_FORMAT)
        return avg_meeting_cost


    def _get_avg_meeting_duration(self, meetings):
        total_seconds = 0
        num_meetings = 0
        for meeting in meetings:
            total_seconds += meeting._get_seconds()
            num_meetings += 1
        avg_meeting_duration = total_seconds / num_meetings
        days, hours, minutes, seconds = _translate_seconds(avg_meeting_duration)
        days, hours, minutes, seconds = _make_pretty_for_printing(days, hours, minutes, seconds)
        avg_meeting_duration = ('{0}, {1}, {2}, {3}').format(days, hours, minutes, seconds)
        return avg_meeting_duration


    def time_recovered(self, percent_time_in_meetings):
        time_recovered_weekly = float(self.percent_time_in_meetings - self.IDEAL_PERCENT_TIME_IN_MEETINGS)
        time_recovered_weekly /= 100
        time_recovered_weekly *= PERSON_SECONDS_PER_WEEK
        days, hours, minutes, seconds = _translate_seconds(time_recovered_weekly)
        days, hours, minutes, seconds = _make_pretty_for_printing(days, hours, minutes, seconds)
        time_recovered_weekly = ('{0}, {1}, {2}, {3}').format(days, hours, minutes, seconds)
        return time_recovered


    def money_recovered(percent_time_in_meetings):
        money_recovered = float(percent_time_in_meetings - IDEAL_PERCENT_TIME_IN_MEETINGS)
        money_recovered /= 100
        money_recovered *= COST_PER_SECOND
        money_recovered *= PERSON_SECONDS_PER_WEEK
        money_recovered = Money(money_recovered, CURRENCY).format(CURRENCY_FORMAT)
        return money_recovered


    def get_meetings_list(self, google_meetings_blob):
        meetings_list = []
        for meeting_id, meeting in enumerate(self.google_meetings_blob, 1):
            meeting_id = meeting_id
            summary = self._get_summary(meeting)
            start = parse(meeting['start'].get('dateTime', meeting['start'].get('date')))
            end = parse(meeting['end'].get('dateTime', meeting['end'].get('date')))
            duration = end - start
            num_attendees = self._get_num_attendees(meeting.get('attendees'))

            m = Meeting(meeting_id, summary, start, end, duration, num_attendees)
            meetings_list.append(m)
        return meetings_list


    def _get_summary(self, meeting):
        summary = meeting.get('summary', 'No summary given')
        return summary


    def _get_num_attendees(self, num_attendees):
        if num_attendees == None:
            num_attendees = 1
        # if sharing multiple calendars, uncomment below
        #num_attendees = 1
        else:
            num_attendees = len(num_attendees)
        return num_attendees

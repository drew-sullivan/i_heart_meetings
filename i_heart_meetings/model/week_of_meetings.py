#!/usr/bin/python

import dateutil

from dateutil.parser import parse # used to get meeting_duration by subtracting datetime objects
from model.meeting import Meeting 
from money import Money # Currently only supporting USD, but others coming soon!

class Week_Of_Meetings:
    """Calculates the costs of a meetings pull when passed a list of meetings
    objects

    Attributes:
        google_meetings_blob: blob - meeting info obtained from Google
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
        self.percent_time_spent = 0

    def main(self, google_meetings_blob):
        meetings_list = self.get_meetings_list(google_meetings_blob)


    def time_cost(self, meetings):
        time_cost_in_seconds = 0
        for meeting in meetings:
            time_cost_in_seconds += meeting.cost_in_seconds()
        return time_cost_in_seconds


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
        cost_in_seconds = self.cost_in_seconds
        for meeting in meetings:
            percent_time_spent += (float(cost_in_seconds) / self.PERSON_SECONDS_PER_WEEK)
        percent_time_spent_2 = round(percent_time_spent * 100, self.ROUND_TO_THIS_MANY_PLACES)
        return percent_time_spent


    def ideal_time_cost(self, meetings):
        ideal_time_cost = self.IDEAL_PERCENT_TIME_IN_MEETINGS
        ideal_time_cost /= 100
        ideal_time_cost *= self.PERSON_SECONDS_PER_WEEK
        work_days, hours, minutes, seconds = self._translate_seconds(ideal_time_cost)
        work_days, hours, minutes, seconds = self._make_pretty_for_printing(work_days, hours, minutes, seconds)
        ideal_time_cost = ('{0}, {1}, {2}, {3}').format(work_days, hours, minutes, seconds)
        return ideal_time_cost


    def ideal_financial_cost(self, meetings):
        ideal_financial_cost = float(self.IDEAL_PERCENT_TIME_IN_MEETINGS)
        ideal_financial_cost /= 100
        ideal_financial_cost *= self.COST_PER_SECOND
        ideal_financial_cost *= self.PERSON_SECONDS_PER_WEEK
        ideal_financial_cost = Money(ideal_financial_cost, self.CURRENCY).format(self.CURRENCY_FORMAT)
        return ideal_financial_cost

    def num_meetings(self, meetings):
        num_meetings = 0
        for meeting in meetings:
            num_meetings += 1
        return num_meetings


    def avg_cost_in_seconds(self, time_cost, num_meetings):
        time_cost = self.time_cost
        num_meetings = self.num_meetings
        avg_cost_in_seconds = float(time_cost) / num_meetings
        work_days, hours, minutes, seconds = self._translate_seconds(avg_cost_in_seconds)
        work_days, hours, minutes, seconds = self._make_pretty_for_printing(work_days, hours, minutes, seconds)
        avg_cost_in_seconds = ('{0}, {1}, {2}, {3}').format(work_days, hours, minutes, seconds)
        return avg_cost_in_seconds


    def avg_cost_in_dollars(self, cost_in_dollars, num_meetings):
        avg_meeting_cost = float(self.cost_in_dollars) / self.num_meetings
        avg_meeting_cost = Money(avg_meeting_cost, CURRENCY).format(CURRENCY_FORMAT)
        return avg_meeting_cost


    def avg_duration(self, meetings):
        total_seconds = 0
        num_meetings = 0
        for meeting in meetings:
            total_seconds += meeting._get_seconds()
            num_meetings += 1
        avg_meeting_duration = total_seconds / num_meetings
        work_days, hours, minutes, seconds = self._translate_seconds(avg_meeting_duration)
        work_days, hours, minutes, seconds = self._make_pretty_for_printing(work_days, hours, minutes, seconds)
        avg_meeting_duration = ('{0}, {1}, {2}, {3}').format(work_days, hours, minutes, seconds)
        return avg_meeting_duration


    def time_recovered(self, percent_time_in_meetings):
        time_recovered_weekly = float(self.percent_time_in_meetings - self.IDEAL_PERCENT_TIME_IN_MEETINGS)
        time_recovered_weekly /= 100
        time_recovered_weekly *= PERSON_SECONDS_PER_WEEK
        work_days, hours, minutes, seconds = _translate_seconds(time_recovered_weekly)
        work_days, hours, minutes, seconds = _make_pretty_for_printing(work_days, hours, minutes, seconds)
        time_recovered_weekly = ('{0}, {1}, {2}, {3}').format(work_days, hours, minutes, seconds)
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


    def _translate_seconds(self, total_seconds):
        # divmod returns quotient and remainder
        minutes, seconds = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        work_days, hours = divmod(hours, self.WORK_HOURS_PER_DAY)
        return (int(work_days), int(hours), int(minutes), int(seconds))


    def _make_pretty_for_printing(self, work_days, hours, minutes, seconds):
        seconds = "{} second{}".format(int(seconds), "" if seconds == 1 else "s")
        minutes = "{} minute{}".format(int(minutes), "" if minutes == 1 else "s")
        hours = "{} hour{}".format(int(hours), "" if hours == 1 else "s")
        work_days = "{} work-day{}".format(int(work_days), "" if work_days == 1 else "s")
        return (work_days, hours, minutes, seconds)

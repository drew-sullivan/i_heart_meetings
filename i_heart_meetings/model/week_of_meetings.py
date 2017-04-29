#!/usr/bin/python

import datetime
import dateutil

from datetime import timedelta
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
        self.meetings_list = []
        self.weekly_cost_in_seconds = 0
        self.weekly_cost_in_dollars = Money(0, self.CURRENCY)
        self.num_meetings = 0
        self.percent_time_spent = 0
        self.frequency = {}
        self.top_meeting_times = []


    def process_google_blob(self):
        self.meetings_list = self.get_meetings_list(self.google_meetings_blob)
        for meeting in self.meetings_list:
            self.weekly_cost_in_seconds += meeting.cost_in_seconds()
            self.weekly_cost_in_dollars += meeting.cost_in_dollars()
            self.num_meetings += 1

            start = meeting.start
            end = meeting.end
            while start < end:
                start_str = str(start)
                if start_str in self.frequency:
                    self.frequency[start_str] += 1
                else:
                    self.frequency[start_str] = 1
                start += datetime.timedelta(minutes=30)


    def weekly_cost_in_seconds(self):
        return self.weekly_cost_in_seconds


    def weekly_cost_in_seconds_pretty_print(self):
        seconds = self.weekly_cost_in_seconds
        work_days, hours, minutes, seconds = _translate_seconds(seconds)
        work_days, hours, minutes, seconds = _make_pretty_for_printing(work_days, hours, minutes, seconds)
        weekly_cost_in_seconds_pretty_print = ('{0}, {1}, {2}, {3}').format(work_days, hours, minutes, seconds)
        return weekly_cost_in_seconds_pretty_print


    def weekly_cost_in_dollars(self):
        return self.weekly_cost_in_dollars


    def weekly_cost_in_dollars_pretty_print(self):
        return self.weekly_cost_in_dollars.format(self.CURRENCY_FORMAT)


    def num_meetings(self):
        return self.num_meetings


    def percent_time_spent(self):
        percent_time_spent += (float(self.weekly_cost_in_seconds) / self.PERSON_SECONDS_PER_WEEK)
        percent_time_spent = round(percent_time_spent * 100, self.ROUND_TO_THIS_MANY_PLACES)
        return percent_time_spent


    def avg_cost_in_seconds(self):
        avg_cost_in_seconds = float(self.weekly_cost_in_seconds) / self.num_meetings
        work_days, hours, minutes, seconds = self._translate_seconds(avg_cost_in_seconds)
        work_days, hours, minutes, seconds = self._make_pretty_for_printing(work_days, hours, minutes, seconds)
        avg_cost_in_seconds = ('{0}, {1}, {2}, {3}').format(work_days, hours, minutes, seconds)
        return avg_cost_in_seconds


    def avg_cost_in_dollars(self):
        avg_meeting_cost = float(self.weekly_cost_in_dollars) / self.num_meetings
        avg_meeting_cost = Money(avg_meeting_cost, CURRENCY).format(CURRENCY_FORMAT)
        return avg_meeting_cost


    def avg_duration(self):
        avg_duration = self.weekly_cost_in_seconds / self.num_meetings
        work_days, hours, minutes, seconds = self._translate_seconds(avg_duration)
        work_days, hours, minutes, seconds = self._make_pretty_for_printing(work_days, hours, minutes, seconds)
        avg_duration = ('{0}, {1}, {2}, {3}').format(work_days, hours, minutes, seconds)
        return avg_duration


    def weekly_potential_time_recovered(self):
        weekly_potential_time_recovered = float(self.percent_time_spent - self.IDEAL_PERCENT_TIME_IN_MEETINGS)
        weekly_potential_time_recovered /= 100
        weekly_potential_time_recovered *= self.PERSON_SECONDS_PER_WEEK
        work_days, hours, minutes, seconds = self._translate_seconds(weekly_potential_time_recovered)
        work_days, hours, minutes, seconds = self._make_pretty_for_printing(work_days, hours, minutes, seconds)
        weekly_potential_time_recovered = ('{0}, {1}, {2}, {3}').format(work_days, hours, minutes, seconds)
        return weekly_potential_time_recovered


    def weekly_potential_money_recovered(self):
        weekly_potential_money_recovered = float(self.percent_time_spent - self.IDEAL_PERCENT_TIME_IN_MEETINGS)
        weekly_potential_money_recovered /= 100
        weekly_potential_money_recovered *= self.COST_PER_SECOND
        weekly_potential_money_recovered *= self.PERSON_SECONDS_PER_WEEK
        weekly_potential_money_recovered = Money(weekly_potential_money_recovered, self.CURRENCY).format(self.CURRENCY_FORMAT)
        return weekly_potential_money_recovered


    def yearly_cost_in_seconds(self):
        yearly_cost_in_seconds = self.weekly_cost_in_seconds * self.WORK_WEEKS_PER_YEAR
        return yearly_cost_in_seconds


    def yearly_cost_in_dollars(self):
        yearly_cost_in_dollars = self.weekly_cost_in_dollars * self.WORK_WEEKS_PER_YEAR
        return yearly_cost_in_dollars


    def yearly_time_recovered(self):
        time_recovered_yearly = float(self.percent_time_in_meetings - self.IDEAL_PERCENT_TIME_IN_MEETINGS)
        time_recovered_yearly /= 100
        time_recovered_yearly *= self.PERSON_SECONDS_PER_YEAR
        days, hours, minutes, seconds = self._translate_seconds(time_recovered_yearly)
        days, hours, minutes, seconds = self._make_pretty_for_printing(days, hours, minutes, seconds)
        time_recovered_yearly = ('{0}, {1}, {2}, {3}').format(days, hours, minutes, seconds)
        return time_recovered_yearly


    def yearly_money_recovered(self):
        money_recovered_yearly = float(self.percent_time_in_meetings - self.IDEAL_PERCENT_TIME_IN_MEETINGS)
        money_recovered_yearly /= 100
        money_recovered_yearly *= self.COST_PER_SECOND
        money_recovered_yearly *= self.PERSON_SECONDS_PER_YEAR
        money_recovered_yearly = Money(money_recovered_yearly, self.CURRENCY).format(self.CURRENCY_FORMAT)
        return money_recovered_yearly



    def yearly_ideal_time_cost(self):
        yearly_ideal_time_cost = self.IDEAL_PERCENT_TIME_IN_MEETINGS
        yearly_ideal_time_cost /= 100
        yearly_ideal_time_cost *= self.PERSON_SECONDS_PER_WEEK
        work_days, hours, minutes, seconds = self._translate_seconds(yearly_ideal_time_cost)
        work_days, hours, minutes, seconds = self._make_pretty_for_printing(work_days, hours, minutes, seconds)
        yearly_ideal_time_cost = ('{0}, {1}, {2}, {3}').format(work_days, hours, minutes, seconds)
        return yearly_ideal_time_cost


    def yearly_ideal_financial_cost(self):
        yearly_ideal_financial_cost = float(self.IDEAL_PERCENT_TIME_IN_MEETINGS)
        yearly_ideal_financial_cost /= 100
        yearly_ideal_financial_cost *= self.COST_PER_SECOND
        yearly_ideal_financial_cost *= self.PERSON_SECONDS_PER_WEEK
        yearly_ideal_financial_cost = Money(yearly_ideal_financial_cost, self.CURRENCY).format(self.CURRENCY_FORMAT)
        return yearly_ideal_financial_cost


    def _get_top_meeting_times(self):
        num_meeting_times = len(self.frequency.values())
        if num_meeting_times < self.NUM_TOP_MEETING_TIMES:
            unpretty_meeting_times = sorted(self.frequency, key=self.frequency.get, reverse=True)[:num_meeting_times]
        else:
            unpretty_meeting_times = sorted(self.frequency, key=self.frequency.get, reverse=True)[:NUM_TOP_MEETING_TIMES]
        for meeting_time in unpretty_meeting_times:
            meeting_time = self._make_dt_or_time_str_pretty_for_printing(meeting_time)
            self.top_meeting_times.append(meeting_time)
        return top_meeting_times


    def _get_top_three_meeting_times(top_meeting_times):
        top_meeting_times_length = len(top_meeting_times)
        if not top_meeting_times:
            return "Calendar empty","Calendar empty","Calendar empty"
        elif top_meeting_times_length == 1:
            top_meeting_time_1 = top_meeting_times[0]
            top_meeting_time_2 = "Calendar empty"
            top_meeting_time_3 = "Calendar empty"
        elif top_meeting_times_length == 2:
            top_meeting_time_1 = top_meeting_times[0]
            top_meeting_time_2 = top_meeting_times[1]
            top_meeting_time_3 = "Calendar empty"
        else:
            top_meeting_time_1 = top_meeting_times[0]
            top_meeting_time_2 = top_meeting_times[1]
            top_meeting_time_3 = top_meeting_times[2]
        return top_meeting_time_1, top_meeting_time_2, top_meeting_time_3



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

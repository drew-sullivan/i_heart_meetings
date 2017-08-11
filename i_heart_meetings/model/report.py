#!/isr/bin/env python

import collections
import datetime
import dateutil
import heapq
import ihm_time
import smtplib
import textwrap
import urllib2
import webbrowser

from collections import namedtuple
from datetime import timedelta
from dateutil.parser import parse # used to get meeting_duration by subtracting datetime objects
from email.mime.text import MIMEText
from model.meeting import Meeting
from money import Money # Currently only supporting USD, but others coming soon!

class Report:

    help = textwrap.dedent("""
        -Takes the Google blob, and turns it into a list of Meeting objects
        -Performs calculations on those objects
        -Sets the results of those calculations to attributes

        Attributes:
            raw_calendar_data: list - received from google after query
            meetings_list: list - list of meeting objects
            weekly_cost_in_seconds: int - cost of each meeting in a week added together
            weekly_cost_in_seconds_readable: str - DD, HH, MM, SS version of above
            weekly_cost_in_dollars: Money - cost of each meeting in a week added together
            weekly_cost_in_dollars_readable: str - added a dollar sign of above
            weekly_duration: int - total number of seconds in meetings in a week
            yearly_cost_in_seconds_readable: str - DD, HH, MM, SS version of above
            yearly_cost_in_dollars: Money - added dollar sign and * 50 to weekly_cost_in_dollars
            weekly_time_recovered_readable: str - DD, HH, MM, SS version of above
            weekly_money_recovered_readable: str - added dollar sign to above
            yearly_money_recovered_readable: str - added dollar sign to above
            yearly_time_recovered_readable: str - DD, HH, MM, SS version of above
            avg_cost_in_seconds_readable: str - DD, HH, MM, SS of above
            avg_cost_in_dollars_readable: str - added dollar sign to above
            avg_duration_in_seconds_readable: str - DD, HH, MM, SS
            yearly_ideal_time_cost_readable: str - DD, HH, MM, SS version of ideal
            yearly_ideal_financial_cost_readable: str - format $100.00
            frequency: dict - k: meeting time, v: num people in meetings
            printable_data = tuple - all the calculations. Can be passed between classes
        """)

    WORK_HOURS_PER_YEAR = 2000
    WORK_HOURS_PER_DAY = 8
    WORK_DAYS_PER_WEEK = 5
    WORK_HOURS_PER_WEEK = WORK_HOURS_PER_DAY * WORK_DAYS_PER_WEEK
    WORK_SECONDS_PER_WEEK = WORK_HOURS_PER_WEEK * 3600
    WORK_WEEKS_PER_YEAR = WORK_HOURS_PER_YEAR / (WORK_HOURS_PER_DAY * WORK_DAYS_PER_WEEK)
    WORK_DAYS_PER_YEAR = WORK_WEEKS_PER_YEAR * WORK_DAYS_PER_WEEK
    WORK_SECONDS_PER_YEAR = WORK_HOURS_PER_YEAR * 3600

    IDEAL_PERCENT_TIME_IN_MEETINGS = 7.5

    YEARLY_SALARY_USD = 75000
    COST_PER_SECOND = float(YEARLY_SALARY_USD) / 7200000
    CURRENCY = 'USD'
    CURRENCY_FORMAT = 'en_US'

    TEAM_SIZE = 6

    PERSON_SECONDS_PER_WEEK = TEAM_SIZE * WORK_SECONDS_PER_WEEK
    PERSON_SECONDS_PER_YEAR = TEAM_SIZE * WORK_SECONDS_PER_YEAR

    WEEKLY_IDEAL_COST_IN_SECONDS = (float(IDEAL_PERCENT_TIME_IN_MEETINGS) / 100) * PERSON_SECONDS_PER_WEEK
    WEEKLY_IDEAL_COST_IN_DOLLARS = Money((float(IDEAL_PERCENT_TIME_IN_MEETINGS) / 100) * COST_PER_SECOND * PERSON_SECONDS_PER_WEEK, CURRENCY)

    YEARLY_IDEAL_COST_IN_SECONDS = (float(IDEAL_PERCENT_TIME_IN_MEETINGS) / 100) * PERSON_SECONDS_PER_YEAR
    YEARLY_IDEAL_COST_IN_DOLLARS = Money((float(IDEAL_PERCENT_TIME_IN_MEETINGS) / 100) * COST_PER_SECOND * PERSON_SECONDS_PER_YEAR, CURRENCY)

    ROUND_TO_THIS_MANY_PLACES = 2

    NUM_TOP_MEETING_TIMES = 3

    def __init__(self, raw_calendar_data):
        self.raw_calendar_data = raw_calendar_data
        self.printable_data = None
        self.meetings_list = self.get_meetings_list(self.raw_calendar_data)
        self.set_printable_data()


    def get_weekly_cost_in_seconds(self):
        weekly_cost_in_seconds = 0
        for meeting in self.meetings_list:
            weekly_cost_in_seconds += meeting.cost_in_seconds()
        return weekly_cost_in_seconds


    def get_weekly_cost_in_dollars(self):
        weekly_cost_in_dollars = Money(0, self.CURRENCY)
        for meeting in self.meetings_list:
            weekly_cost_in_dollars += meeting.cost_in_dollars()
        return weekly_cost_in_dollars


    def get_num_meetings(self):
        num_meetings = 0
        for meeting in self.meetings_list:
            num_meetings += 1
        return num_meetings


    def get_weekly_duration(self):
        weekly_duration = 0
        for meeting in self.meetings_list:
            weekly_duration += ihm_time.convert_duration_to_work_seconds(meeting.duration)
        return weekly_duration


    def get_num_start_times(self):
        num_start_times = {}
        for meeting in self.meetings_list:
            start = meeting.start
            end = meeting.end
            summary = meeting.summary
            duration = meeting.duration

            start_time = str(start)
            time_summary_duration = str(start) + ' ' + summary + ' ' + str(duration)
            if time_summary_duration not in num_start_times:
                num_start_times[time_summary_duration] = 1
        return len(num_start_times)


    def get_meeting_frequency(self):
        frequency = {}
        for meeting in self.meetings_list:
            start_str = str(meeting.start)
            while meeting.start < meeting.end:
                if start_str in frequency:
                    frequency[start_str] += 1
                else:
                    frequency[start_str] = 1
                meeting.start += datetime.timedelta(minutes=15)
        return frequency


    def get_most_frequent_meeting_times(self):
        frequency = self.get_meeting_frequency()
        most_frequent_meeting_times = heapq.nlargest(n=3, iterable=frequency, key=frequency.get)
        return most_frequent_meeting_times


    def set_printable_data(self):
        self.printable_data = (
            self.weekly_cost_in_seconds_readable(), #0
            self.weekly_cost_in_dollars_readable(), #1
            self.yearly_cost_in_seconds_readable(), #2
            self.yearly_cost_in_dollars(), #3
            self.avg_cost_in_seconds_readable(), #4
            self.avg_cost_in_dollars_readable(), #5
            self.avg_duration_in_seconds_readable(), #6
            self.get_most_frequent_meeting_times(), #7
            self.get_most_frequent_meeting_times(), #8
            self.get_most_frequent_meeting_times(), #9
            "{0}%".format(self.get_percent_time_spent()), #10
            self.yearly_ideal_time_cost_readable(), #11
            self.yearly_ideal_financial_cost_readable(), #12
            self.weekly_money_recovered_readable(), #13
            self.weekly_time_recovered_readable(), #14
            self.yearly_money_recovered_readable(), #15
            self.yearly_time_recovered_readable(), #16
            self.frequency_keys_readable(), #17
            self.get_meeting_frequency(), #18
            self.get_percent_time_spent(), #19
            self.IDEAL_PERCENT_TIME_IN_MEETINGS, #20
            self.get_num_meetings(), #21
            self.get_num_start_times(), #22
            self.weekly_ideal_time_cost_readable(), #23
            self.weekly_ideal_financial_cost_readable() #24
        )


    def write_report_html(self, *printable_data):
        f = open('templates/report.html','w')

        message = """
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" type="text/css" href="../static/style.css">
</head>
<body>
    <img src="http://i.imgur.com/zBxQt6J.png" />
    <div class='report'>
        <table id="ihmReport">
            <caption>Meetings Report</caption>
            <tr>
                <th>Description</td>
                <th>Value</td>
            </tr>
            <tr>
                <td>Number of Meetings</td>
                <td>{17}</td>
            </tr>
            <tr>
                <td>Weekly Cost: Financial</td>
                <td>{0}</td>
            </tr>
            <tr>
                <td>Weekly Cost: Time</td>
                <td>{1}</td>
            </tr>
            <tr>
                <td>Average Finanical Cost Per Meeting</td>
                <td>{2}</td>
            </tr>
            <tr>
                <td>Average Time Cost Per Meeting</td>
                <td>{3}</td>
            </tr>
            <tr>
                <td>Average Duration Per Meeting</td>
                <td>{4}</td>
            </tr>
            <tr>
                <td>Projected Yearly Cost: Financial</td>
                <td>{5}</td>
            </tr>
            <tr>
                <td>Projected Yearly Cost: Time</td>
                <td>{6}</td>
            </tr>
            <tr>
                <td>Top Meeting Time No. 1</td>
                <td>{7}</td>
            </tr>
            <tr>
                <td>Top Meeting Time No. 2</td>
                <td>{8}</td>
            </tr>
            <tr>
                <td>Top Meeting Time No. 3</td>
                <td>{9}</td>
            </tr>
            <tr>
                <td>Percent Time Spent in Meetings</td>
                <td>{10}</td>
            </tr>
            <tr>
                <td>Ideal Weekly Costs: Financial</td>
                <td>{19}</td>
            </tr>
            <tr>
                <td>Ideal Weekly Costs: Time</td>
                <td>{18}</td>
            </tr>
            <tr>
                <td>Ideal Yearly Costs: Financial</td>
                <td>{11}</td>
            </tr>
            <tr>
                <td>Ideal Yearly Costs: Time</td>
                <td>{12}</td>
            </tr>
            <tr>
                <td>Weekly Potential Savings: Financial</td>
                <td>{13}</td>
            </tr>
            <tr>
                <td>Weekly Potential Savings: Time</td>
                <td>{14}</td>
            </tr>
            <tr>
                <td>Yearly Potential Savings: Financial</td>
                <td>{15}</td>
            </tr>
            <tr>
                <td>Yearly Potential Savings: Time</td>
                <td>{16}</td>
            </tr>
            <tr>
                <th></td>
                <th></td>
            </tr>
        </table>
    </div>
</body>
</html>""".format(self.printable_data[1],self.printable_data[0],
                  self.printable_data[5],
                  self.printable_data[4],self.printable_data[6],
                  self.printable_data[3],self.printable_data[2],
                  self.printable_data[7],
                  self.printable_data[8],self.printable_data[9],
                  self.printable_data[10],self.printable_data[12],
                  self.printable_data[11],
                  self.printable_data[13],self.printable_data[14],
                  self.printable_data[15],self.printable_data[16],
                  self.printable_data[22], self.printable_data[23],
                  self.printable_data[24])
        f.write(message)
        f.close()


    def weekly_cost_in_seconds_readable(self):
        seconds = self.get_weekly_cost_in_seconds()
        work_days, hours, minutes, seconds = ihm_time.translate_seconds(seconds)
        work_days, hours, minutes, seconds = ihm_time.make_pretty_for_printing(work_days, hours, minutes, seconds)
        weekly_cost_in_seconds_pretty_print = ('{0}, {1}, {2}, {3}').format(work_days, hours, minutes, seconds)
        return weekly_cost_in_seconds_pretty_print


    def weekly_cost_in_dollars_readable(self):
        return str(self.get_weekly_cost_in_dollars().format('en_US'))


    def get_percent_time_spent(self):
        percent_time_spent = (float(self.get_weekly_cost_in_seconds()) / self.PERSON_SECONDS_PER_WEEK)
        percent_time_spent = round(percent_time_spent * 100, self.ROUND_TO_THIS_MANY_PLACES)
        return percent_time_spent


    def avg_cost_in_seconds_readable(self):
        avg_cost_in_seconds = float(self.get_weekly_cost_in_seconds()) / self.get_num_start_times()
        work_days, hours, minutes, seconds = ihm_time.translate_seconds(avg_cost_in_seconds)
        work_days, hours, minutes, seconds = ihm_time.make_pretty_for_printing(work_days, hours, minutes, seconds)
        return ('{0}, {1}, {2}, {3}').format(work_days, hours, minutes, seconds)


    def avg_cost_in_dollars(self):
        avg_meeting_cost_in_dollars = float(self.get_weekly_cost_in_dollars()) / self.get_num_start_times()
        avg_meeting_cost_in_dollars = Money(avg_meeting_cost_in_dollars, self.CURRENCY).format(self.CURRENCY_FORMAT)
        return avg_meeting_cost_in_dollars


    def avg_cost_in_dollars_readable(self):
        return self.avg_cost_in_dollars().format(self.CURRENCY_FORMAT)


    def avg_duration_in_seconds(self):
        avg_duration_in_seconds = self.get_weekly_duration() / self.get_num_meetings()
        return avg_duration_in_seconds


    def avg_duration_in_seconds_readable(self):
        avg_duration_in_seconds_readable = self.avg_duration_in_seconds()
        work_days, hours, minutes, seconds = ihm_time.translate_seconds(avg_duration_in_seconds_readable)
        work_days, hours, minutes, seconds = ihm_time.make_pretty_for_printing(work_days, hours, minutes, seconds)
        return ('{0}, {1}, {2}, {3}').format(work_days, hours, minutes, seconds)


    def weekly_time_recovered_in_seconds(self):
        weekly_time_recovered_in_seconds = float(self.get_percent_time_spent() - self.IDEAL_PERCENT_TIME_IN_MEETINGS)
        weekly_time_recovered_in_seconds /= 100
        weekly_time_recovered_in_seconds *= self.PERSON_SECONDS_PER_WEEK
        return weekly_time_recovered_in_seconds


    def weekly_time_recovered_readable(self):
        weekly_time_recovered_in_seconds = self.weekly_time_recovered_in_seconds()
        work_days, hours, minutes, seconds = ihm_time.translate_seconds(weekly_time_recovered_in_seconds)
        work_days, hours, minutes, seconds = ihm_time.make_pretty_for_printing(work_days, hours, minutes, seconds)
        weekly_time_recovered_in_seconds = ('{0}, {1}, {2}, {3}').format(work_days, hours, minutes, seconds)
        return weekly_time_recovered_in_seconds


    def weekly_money_recovered_in_dollars(self):
        weekly_money_recovered_in_dollars = float(self.get_percent_time_spent() - self.IDEAL_PERCENT_TIME_IN_MEETINGS)
        weekly_money_recovered_in_dollars /= 100
        weekly_money_recovered_in_dollars *= self.COST_PER_SECOND
        weekly_money_recovered_in_dollars *= self.PERSON_SECONDS_PER_WEEK
        return Money(weekly_money_recovered_in_dollars, self.CURRENCY)


    def weekly_money_recovered_readable(self):
        self.weekly_money_recovered_readable = self.weekly_money_recovered_in_dollars().format(self.CURRENCY_FORMAT)


    def yearly_money_recovered_in_dollars(self):
        return self.weekly_money_recovered_in_dollars() * self.WORK_WEEKS_PER_YEAR


    def yearly_money_recovered_readable(self):
        self.yearly_money_recovered_readable = self.yearly_money_recovered_in_dollars().format(self.CURRENCY_FORMAT)


    def yearly_cost_in_seconds(self):
        yearly_cost_in_seconds = self.get_weekly_cost_in_seconds() * self.WORK_WEEKS_PER_YEAR
        return yearly_cost_in_seconds


    def yearly_cost_in_seconds_readable(self):
        seconds = self.yearly_cost_in_seconds()
        work_days, hours, minutes, seconds = ihm_time.translate_seconds(seconds)
        work_days, hours, minutes, seconds = ihm_time.make_pretty_for_printing(work_days, hours, minutes, seconds)
        yearly_cost_in_seconds_readable = ('{0}, {1}, {2}, {3}').format(work_days, hours, minutes, seconds)
        return yearly_cost_in_seconds_readable


    def yearly_cost_in_dollars(self):
        yearly_cost_in_dollars = self.get_weekly_cost_in_dollars() * self.WORK_WEEKS_PER_YEAR
        yearly_cost_in_dollars = yearly_cost_in_dollars.format(self.CURRENCY_FORMAT)
        return yearly_cost_in_dollars


    def yearly_time_recovered_in_seconds(self):
        time_recovered_yearly = float(self.get_percent_time_spent() - self.IDEAL_PERCENT_TIME_IN_MEETINGS)
        time_recovered_yearly /= 100
        time_recovered_yearly *= self.PERSON_SECONDS_PER_YEAR
        return time_recovered_yearly


    def yearly_time_recovered_readable(self):
        time_recovered_yearly = self.yearly_time_recovered_in_seconds()
        days, hours, minutes, seconds = ihm_time.translate_seconds(time_recovered_yearly)
        days, hours, minutes, seconds = ihm_time.make_pretty_for_printing(days, hours, minutes, seconds)
        time_recovered_yearly = ('{0}, {1}, {2}, {3}').format(days, hours, minutes, seconds)
        return time_recovered_yearly


    def weekly_ideal_time_cost_readable(self):
        weekly_ideal_time_cost = self.WEEKLY_IDEAL_COST_IN_SECONDS
        work_days, hours, minutes, seconds = ihm_time.translate_seconds(weekly_ideal_time_cost)
        work_days, hours, minutes, seconds = ihm_time.make_pretty_for_printing(work_days, hours, minutes, seconds)
        weekly_ideal_time_cost = ('{0}, {1}, {2}, {3}').format(work_days, hours, minutes, seconds)
        return weekly_ideal_time_cost


    def weekly_ideal_financial_cost_readable(self):
        weekly_ideal_financial_cost = self.WEEKLY_IDEAL_COST_IN_DOLLARS.format(self.CURRENCY_FORMAT)
        return weekly_ideal_financial_cost


    def yearly_ideal_time_cost_readable(self):
        yearly_ideal_time_cost = self.YEARLY_IDEAL_COST_IN_SECONDS
        work_days, hours, minutes, seconds = ihm_time.translate_seconds(yearly_ideal_time_cost)
        work_days, hours, minutes, seconds = ihm_time.make_pretty_for_printing(work_days, hours, minutes, seconds)
        yearly_ideal_time_cost = ('{0}, {1}, {2}, {3}').format(work_days, hours, minutes, seconds)
        return yearly_ideal_time_cost


    def yearly_ideal_financial_cost_readable(self):
        yearly_ideal_financial_cost = self.YEARLY_IDEAL_COST_IN_DOLLARS.format(self.CURRENCY_FORMAT)
        return yearly_ideal_financial_cost


    def frequency_keys_readable(self):
        frequency_keys_readable = []
        dates = list(self.get_meeting_frequency().keys())
        for date in dates:
            date = ihm_time.make_dt_or_time_str_pretty_for_printing(date)
            frequency_keys_readable.append(date)
        return frequency_keys_readable


    def get_meetings_list(self, raw_calendar_data):
        meetings_list = []
        for num, meeting in enumerate(self.raw_calendar_data, 1):
            num = num
            summary = self._get_summary(meeting)
            start = parse(meeting['start'].get('dateTime', meeting['start'].get('date')))
            end = parse(meeting['end'].get('dateTime', meeting['end'].get('date')))
            duration = end - start
            num_attendees = self._get_num_attendees(meeting.get('attendees'))

            m = Meeting(num, summary, start, end, duration, num_attendees)
            meetings_list.append(m)
        return meetings_list


    def _get_summary(self, meeting):
        summary = meeting.get('summary', 'No summary given')
        return summary


    def _get_num_attendees(self, num_attendees):
        if num_attendees == None:
            num_attendees = 1
        # if sharing multiple calendars, uncomment below
        num_attendees = 1
        #else:
        #    num_attendees = len(num_attendees)
        return num_attendees

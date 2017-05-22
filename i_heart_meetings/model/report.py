#!/isr/bin/env python

import collections
import csv
import datetime
import dateutil
import json
import smtplib
import sqlite3
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
            google_meetings_blob: list - received from google after query
            meetings_list: list - list of meeting objects
            weekly_cost_in_seconds: int - cost of each meeting in a week added together
            weekly_cost_in_seconds_readable: str - DD, HH, MM, SS version of above
            weekly_cost_in_dollars: Money - cost of each meeting in a week added together
            weekly_cost_in_dollars_readable: str - added a dollar sign of above
            weekly_duration: int - total number of seconds in meetings in a week
            yearly_cost_in_seconds: int - weekly_cost_in_seconds * 50
            yearly_cost_in_seconds_readable: str - DD, HH, MM, SS version of above
            yearly_cost_in_dollars: Money - added dollar sign and * 50 to weekly_cost_in_dollars
            num_meetings: int - number of meetings in a week
            weekly_time_recovered_in_seconds: int - difference between ideal and actual
            weekly_time_recovered_readable: str - DD, HH, MM, SS version of above
            weekly_money_recovered_in_dollars: int - difference between ideal and actual
            weekly_money_recovered_readable: str - added dollar sign to above
            yearly_money_recovered_in_dollars: int - weekly * 50
            yearly_money_recovered_readable: str - added dollar sign to above
            yearly_time_recovered_in_seconds: int - difference between ideal and actual
            yearly_time_recovered_readable: str - DD, HH, MM, SS version of above
            avg_cost_in_seconds: int - average cost of a meeting in seconds
            avg_cost_in_seconds_readable: str - DD, HH, MM, SS of above
            avg_cost_in_dollars: Money - average cost in dollars
            avg_cost_in_dollars_readable: str - added dollar sign to above
            avg_duration_in_seconds_readable: str - DD, HH, MM, SS 
            percent_time_spent: int - percent time spent in meetings
            percent_time_spent_readable: str - adds % to above
            yearly_ideal_time_cost_readable: str - DD, HH, MM, SS version of ideal
            yearly_ideal_financial_cost_readable: str - format $100.00
            frequency: dict - k: meeting time, v: num people in meetings
            top_meeting_times: list - top 3 meeting times
            top_meeting_time_1: str - top meeting time in Tuesday, Apr 25, 2017 - 09:30
            top_meeting_time_2: str - #2
            top_meeting_time_3: str - #3
            frequency_keys_readable: list - all meeting times as Tuesday, Apr 25, 2017 - 09:30
            summary_printout: str - formatted printout of data for printing
            printable_data = tuple - all the calculations. Can be passed between classes
            print_template: str - template for printing info in the same format
            num_start_times: int - number of meeting starting times
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

    YEARLY_SALARY_USD = 74926
    COST_PER_SECOND = float(YEARLY_SALARY_USD) / WORK_SECONDS_PER_YEAR
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
    FORMAT_DATETIME_OBJ_TO_STR = '%Y-%m-%d %H:%M:%S'
    FORMAT_STR_TO_DATETIME_OBJ = '%A, %b %d, %Y - %I:%M'

    NUM_TOP_MEETING_TIMES = 3

    DB_IHM_SQLITE = '/Users/drew-sullivan/codingStuff/i_heart_meetings/i_heart_meetings/db_ihm.sqlite'
    CSV_FILE = 'meetings_ihm.csv'
    JSON_FIELDS = ('id', 'num', 'summary', 'start', 'end', 'duration',
                   'num_attendees')
    JSON_FILE = 'meetings_ihm.json'

    QUESTIONNAIRE_LINK = 'https://docs.google.com/a/decisiondesk.com/forms/d/e/1FAIpQLSfnDgSB9UoAMUtrLlNoBjuo1e8qe25deJD53LjJEWw5vyd-hQ/viewform?usp=sf_link'
    SLACK_HOOK = 'https://hooks.slack.com/services/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'

    def __init__(self, google_meetings_blob):
        self.google_meetings_blob = google_meetings_blob
        self.meetings_list = []
        self.weekly_cost_in_seconds = 0
        self.weekly_cost_in_seconds_readable = ''
        self.weekly_cost_in_dollars = Money(0, self.CURRENCY)
        self.weekly_cost_in_dollars_readable = ''
        self.weekly_duration = 0
        self.yearly_cost_in_seconds = 0
        self.yearly_cost_in_seconds_readable = ''
        self.yearly_cost_in_dollars = None
        self.num_meetings = 0
        self.weekly_time_recovered_in_seconds = 0
        self.weekly_time_recovered_readable = ''
        self.weekly_money_recovered_in_dollars = 0
        self.weekly_money_recovered_readable = ''
        self.yearly_money_recovered_in_dollars = 0
        self.yearly_money_recovered_readable = ''
        self.yearly_time_recovered_in_seconds = 0
        self.yearly_time_recovered_readable = ''
        self.avg_cost_in_seconds = 0
        self.avg_cost_in_seconds_readable = ''
        self.avg_cost_in_dollars = Money(0, self.CURRENCY)
        self.avg_cost_in_dollars_readable = ''
        self.avg_duration_in_seconds_readable = ''
        self.percent_time_spent = 0
        self.percent_time_spent_readable = 0
        self.weekly_ideal_time_cost_readable = ''
        self.weekly_ideal_financial_cost_readable = ''
        self.yearly_ideal_time_cost_readable = ''
        self.yearly_ideal_financial_cost_readable = ''
        self.frequency = {}
        self.top_meeting_times = []
        self.top_meeting_time_1 = ''
        self.top_meeting_time_2 = ''
        self.top_meeting_time_3 = ''
        self.frequency_keys_readable = []
        self.summary_printout = ''
        self.printable_data = None
        self.print_template = ''
        self.num_start_times = {}
        self.meetings_list = self.get_meetings_list(self.google_meetings_blob)

        for meeting in self.meetings_list:
            #self._add_row_to_db(meeting)
            self.weekly_cost_in_seconds += meeting.cost_in_seconds()
            self.weekly_cost_in_dollars += meeting.cost_in_dollars()
            self.num_meetings += 1
            self.weekly_duration += self._convert_duration_to_work_seconds(meeting.duration)

            start = meeting.start
            end = meeting.end
            summary = meeting.summary
            duration = meeting.duration

            start_time = str(start)
            time_summary_duration = str(start) + ' ' + summary + ' ' + str(duration)
            if time_summary_duration not in self.num_start_times:
                self.num_start_times[time_summary_duration] = 1

            while start < end:
                start_str = str(start)
                if start_str in self.frequency:
                    self.frequency[start_str] += 1
                else:
                    self.frequency[start_str] = 1
                start += datetime.timedelta(minutes=15)

        self.frequency = collections.OrderedDict(sorted(self.frequency.items()))
        self.num_start_times = len(self.num_start_times)
        self.yearly_cost_in_seconds = self.weekly_cost_in_seconds * self.WORK_WEEKS_PER_YEAR
        self.yearly_cost_in_dollars = self.weekly_cost_in_dollars * self.WORK_WEEKS_PER_YEAR
        self.set_weekly_cost_in_seconds_readable()
        self.set_weekly_cost_in_dollars_readable()
        self.set_avg_cost_in_seconds_readable()
        self.set_avg_cost_in_dollars()
        self.set_avg_cost_in_dollars_readable()
        self.set_avg_duration_in_seconds()
        self.set_avg_duration_in_seconds_readable()
        self.set_yearly_cost_in_seconds_readable()
        self.set_percent_time_spent()
        self.set_percent_time_readable()
        self.set_yearly_cost_in_dollars()
        self.set_yearly_time_recovered_in_seconds()
        self.set_yearly_time_recovered_readable()
        self.set_weekly_time_recovered_in_seconds()
        self.set_weekly_time_recovered_readable()
        self.set_weekly_money_recovered_in_dollars()
        self.set_weekly_money_recovered_readable()
        self.set_yearly_money_recovered_in_dollars()
        self.set_yearly_money_recovered_readable()
        self.set_weekly_ideal_time_cost_readable()
        self.set_weekly_ideal_financial_cost_readable()
        self.set_yearly_ideal_time_cost_readable()
        self.set_yearly_ideal_financial_cost_readable()
        self.set_top_meeting_times()
        self.set_top_three_meeting_times()
        self.set_frequency_keys_readable()

        self.set_printable_data()
        self.set_print_template()
        self.set_summary()
        #self.write_db_to_csv()
        #self.write_csv_to_json()


    def write_csv_to_json(self):
        csv_file = open(self.CSV_FILE, 'r')
        json_file = open(self.JSON_FILE, 'w')

        field_names = self.JSON_FIELDS
        reader = csv.DictReader(csv_file, field_names)
        for row in reader:
            json.dump(row, json_file, sort_keys=True, indent=4, separators=(',', ': '))
            json_file.write('\n')

    def write_db_to_csv(self):
        with sqlite3.connect(self.DB_IHM_SQLITE) as conn:
            csvWriter = csv.writer(open(self.CSV_FILE, 'w'))
            c = conn.cursor()
            c.execute('SELECT * from meetings')

            rows = c.fetchall()
            csvWriter.writerows(rows)

    def _add_row_to_db(self, meeting):
        id = str(datetime.datetime.now())
        start = str(meeting.start)
        end = str(meeting.end)
        duration = str(meeting.duration)
        conn = sqlite3.connect(self.DB_IHM_SQLITE)
        c = conn.cursor()
        c.execute('INSERT INTO meetings VALUES(?,?,?,?,?,?,?)',
                  (id, meeting.num, meeting.summary,
                   start, end, duration,
                   meeting.num_attendees))
        conn.commit()
        conn.close()

    def set_printable_data(self):
        self.printable_data = (
            self.weekly_cost_in_seconds_readable, #0
            self.weekly_cost_in_dollars_readable, #1
            self.yearly_cost_in_seconds_readable, #2
            self.yearly_cost_in_dollars, #3
            self.avg_cost_in_seconds_readable, #4
            self.avg_cost_in_dollars_readable, #5
            self.avg_duration_in_seconds_readable, #6
            self.top_meeting_time_1, #7
            self.top_meeting_time_2, #8
            self.top_meeting_time_3, #9
            self.percent_time_spent_readable, #10
            self.yearly_ideal_time_cost_readable, #11
            self.yearly_ideal_financial_cost_readable, #12
            self.weekly_money_recovered_readable, #13
            self.weekly_time_recovered_readable, #14
            self.yearly_money_recovered_readable, #15
            self.yearly_time_recovered_readable, #16
            self.frequency_keys_readable, #17
            self.frequency, #18
            self.percent_time_spent, #19
            self.IDEAL_PERCENT_TIME_IN_MEETINGS, #20
            self.num_meetings, #21
            self.num_start_times, #22
            self.weekly_ideal_time_cost_readable, #23
            self.weekly_ideal_financial_cost_readable #24
        )


    def post_report_to_slack(self):
        data = str(
            {'text': self.summary_printout,
                'attachments': [
                    {
                        "fallback": "Was this a good use of time and money?",
                        "title": "Was this a good use of time and money?",
                        "callback_id": "meetings_survey",
                        "color": "#800080",
                        "attachment_type": "default",
                        "actions": [
                            {
                                "name": "yes",
                                "text": "Yes",
                                "type": "button",
                                "value": "yes"
                            },
                            {
                                "name": "no",
                                "text": "No",
                                "type": "button",
                                "value": "no"
                            },
                            {
                                "name": "maybe",
                                "text": "I'm Not Sure",
                                "type": "button",
                                "value": "maybe"
                            }
                        ]
                    }
                ]
            }
        )
        url = self.SLACK_HOOK
        req = urllib2.Request(url, data, {'Content-Type': 'application/json'})
        f = urllib2.urlopen(req)
        f.close()


    def set_summary(self):
        self.summary_printout = self.print_template.format(*self.printable_data)


    def write_report_html(self, *printable_data):
        f = open('templates/report.html','w')

        message = """
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" type="text/css" href="../static/style.css">
</head>
<body>
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


    def set_print_template(self):
        self.print_template = """
*Summary*

*Number of Meetings*
{22}

*Weekly Costs*
{0}
{1}

*Average Per Meeting*

Time Cost: {4}
Financial Cost: {5}
Duration: {6}

*Projected Yearly Costs*
{2}
{3}

*Top 3 Meeting Times*
{7},
{8},
{9}

*{10}* of Your Time is Spent in Meetings

*Ideal Weekly Costs*
{24} and {23}

*Ideal Yearly Costs*
{11} and {12}

*Potential Savings*
{13} and {14} per week
{15} and {16} per year
        """


    def set_weekly_cost_in_seconds_readable(self):
        seconds = self.weekly_cost_in_seconds
        work_days, hours, minutes, seconds = self._translate_seconds(seconds)
        work_days, hours, minutes, seconds = self._make_pretty_for_printing(work_days, hours, minutes, seconds)
        weekly_cost_in_seconds_pretty_print = ('{0}, {1}, {2}, {3}').format(work_days, hours, minutes, seconds)
        self.weekly_cost_in_seconds_readable = weekly_cost_in_seconds_pretty_print


    def set_weekly_cost_in_dollars_readable(self):
        self.weekly_cost_in_dollars_readable = str(self.weekly_cost_in_dollars.format('en_US'))


    def set_percent_time_spent(self):
        self.percent_time_spent += (float(self.weekly_cost_in_seconds) / self.PERSON_SECONDS_PER_WEEK)
        self.percent_time_spent = round(self.percent_time_spent * 100, self.ROUND_TO_THIS_MANY_PLACES)


    def set_percent_time_readable(self):
        self.percent_time_spent_readable += (float(self.weekly_cost_in_seconds) / self.PERSON_SECONDS_PER_WEEK)
        self.percent_time_spent_readable = round(self.percent_time_spent_readable * 100, self.ROUND_TO_THIS_MANY_PLACES)
        self.percent_time_spent_readable = str("{}%".format(self.percent_time_spent_readable))


    def set_avg_cost_in_seconds_readable(self):
        avg_cost_in_seconds = float(self.weekly_cost_in_seconds) / self.num_start_times
        work_days, hours, minutes, seconds = self._translate_seconds(avg_cost_in_seconds)
        work_days, hours, minutes, seconds = self._make_pretty_for_printing(work_days, hours, minutes, seconds)
        self.avg_cost_in_seconds_readable = ('{0}, {1}, {2}, {3}').format(work_days, hours, minutes, seconds)


    def set_avg_cost_in_dollars(self):
        avg_meeting_cost_in_dollars = float(self.weekly_cost_in_dollars) / self.num_start_times
        avg_meeting_cost_in_dollars = Money(avg_meeting_cost_in_dollars, self.CURRENCY).format(self.CURRENCY_FORMAT)
        self.avg_cost_in_dollars = avg_meeting_cost_in_dollars


    def set_avg_cost_in_dollars_readable(self):
        self.avg_cost_in_dollars_readable = self.avg_cost_in_dollars.format(self.CURRENCY_FORMAT)


    def set_avg_duration_in_seconds(self):
        avg_duration_in_seconds = self.weekly_duration / self.num_meetings
        self.avg_duration_in_seconds = avg_duration_in_seconds


    def set_avg_duration_in_seconds_readable(self):
        avg_duration_in_seconds_readable = self.avg_duration_in_seconds
        work_days, hours, minutes, seconds = self._translate_seconds(avg_duration_in_seconds_readable)
        work_days, hours, minutes, seconds = self._make_pretty_for_printing(work_days, hours, minutes, seconds)
        self.avg_duration_in_seconds_readable = ('{0}, {1}, {2}, {3}').format(work_days, hours, minutes, seconds)


    def set_weekly_time_recovered_in_seconds(self):
        weekly_time_recovered_in_seconds = float(self.percent_time_spent - self.IDEAL_PERCENT_TIME_IN_MEETINGS)
        weekly_time_recovered_in_seconds /= 100
        weekly_time_recovered_in_seconds *= self.PERSON_SECONDS_PER_WEEK
        self.weekly_time_recovered_in_seconds = weekly_time_recovered_in_seconds


    def set_weekly_time_recovered_readable(self):
        weekly_time_recovered_in_seconds = self.weekly_time_recovered_in_seconds
        work_days, hours, minutes, seconds = self._translate_seconds(weekly_time_recovered_in_seconds)
        work_days, hours, minutes, seconds = self._make_pretty_for_printing(work_days, hours, minutes, seconds)
        weekly_time_recovered_in_seconds = ('{0}, {1}, {2}, {3}').format(work_days, hours, minutes, seconds)
        self.weekly_time_recovered_readable = weekly_time_recovered_in_seconds


    def set_weekly_money_recovered_in_dollars(self):
        weekly_money_recovered_in_dollars = float(self.percent_time_spent - self.IDEAL_PERCENT_TIME_IN_MEETINGS)
        weekly_money_recovered_in_dollars /= 100
        weekly_money_recovered_in_dollars *= self.COST_PER_SECOND
        weekly_money_recovered_in_dollars *= self.PERSON_SECONDS_PER_WEEK
        self.weekly_money_recovered_in_dollars = Money(weekly_money_recovered_in_dollars, self.CURRENCY)


    def set_weekly_money_recovered_readable(self):
        self.weekly_money_recovered_readable = self.weekly_money_recovered_in_dollars.format(self.CURRENCY_FORMAT)


    def set_yearly_money_recovered_in_dollars(self):
        self.yearly_money_recovered_in_dollars = self.weekly_money_recovered_in_dollars * self.WORK_WEEKS_PER_YEAR


    def set_yearly_money_recovered_readable(self):
        self.yearly_money_recovered_readable = self.yearly_money_recovered_in_dollars.format(self.CURRENCY_FORMAT)


    def set_yearly_cost_in_seconds(self):
        yearly_cost_in_seconds = self.weekly_cost_in_seconds * self.WORK_WEEKS_PER_YEAR
        self.yearly_cost_in_seconds = yearly_cost_in_seconds


    def set_yearly_cost_in_seconds_readable(self):
        seconds = self.yearly_cost_in_seconds
        work_days, hours, minutes, seconds = self._translate_seconds(seconds)
        work_days, hours, minutes, seconds = self._make_pretty_for_printing(work_days, hours, minutes, seconds)
        yearly_cost_in_seconds_readable = ('{0}, {1}, {2}, {3}').format(work_days, hours, minutes, seconds)
        self.yearly_cost_in_seconds_readable = yearly_cost_in_seconds_readable


    def set_yearly_cost_in_dollars(self):
        yearly_cost_in_dollars = self.weekly_cost_in_dollars * self.WORK_WEEKS_PER_YEAR
        yearly_cost_in_dollars = yearly_cost_in_dollars.format(self.CURRENCY_FORMAT)
        self.yearly_cost_in_dollars = yearly_cost_in_dollars


    def set_yearly_time_recovered_in_seconds(self):
        time_recovered_yearly = float(self.percent_time_spent - self.IDEAL_PERCENT_TIME_IN_MEETINGS)
        time_recovered_yearly /= 100
        time_recovered_yearly *= self.PERSON_SECONDS_PER_YEAR
        self.yearly_time_recovered_in_seconds =  time_recovered_yearly


    def set_yearly_time_recovered_readable(self):
        time_recovered_yearly = self.yearly_time_recovered_in_seconds
        days, hours, minutes, seconds = self._translate_seconds(time_recovered_yearly)
        days, hours, minutes, seconds = self._make_pretty_for_printing(days, hours, minutes, seconds)
        time_recovered_yearly = ('{0}, {1}, {2}, {3}').format(days, hours, minutes, seconds)
        self.yearly_time_recovered_readable =  time_recovered_yearly


    def set_weekly_ideal_time_cost_readable(self):
        weekly_ideal_time_cost = self.WEEKLY_IDEAL_COST_IN_SECONDS
        work_days, hours, minutes, seconds = self._translate_seconds(weekly_ideal_time_cost)
        work_days, hours, minutes, seconds = self._make_pretty_for_printing(work_days, hours, minutes, seconds)
        weekly_ideal_time_cost = ('{0}, {1}, {2}, {3}').format(work_days, hours, minutes, seconds)
        self.weekly_ideal_time_cost_readable = weekly_ideal_time_cost


    def set_weekly_ideal_financial_cost_readable(self):
        weekly_ideal_financial_cost = self.WEEKLY_IDEAL_COST_IN_DOLLARS.format(self.CURRENCY_FORMAT)
        self.weekly_ideal_financial_cost_readable =  weekly_ideal_financial_cost


    def set_yearly_ideal_time_cost_readable(self):
        yearly_ideal_time_cost = self.YEARLY_IDEAL_COST_IN_SECONDS
        work_days, hours, minutes, seconds = self._translate_seconds(yearly_ideal_time_cost)
        work_days, hours, minutes, seconds = self._make_pretty_for_printing(work_days, hours, minutes, seconds)
        yearly_ideal_time_cost = ('{0}, {1}, {2}, {3}').format(work_days, hours, minutes, seconds)
        self.yearly_ideal_time_cost_readable = yearly_ideal_time_cost


    def set_yearly_ideal_financial_cost_readable(self):
        yearly_ideal_financial_cost = self.YEARLY_IDEAL_COST_IN_DOLLARS.format(self.CURRENCY_FORMAT)
        self.yearly_ideal_financial_cost_readable =  yearly_ideal_financial_cost


    def set_frequency_keys_readable(self):
        dates = list(self.frequency.keys())
        for date in dates:
            date = self._make_dt_or_time_str_pretty_for_printing(date)
            self.frequency_keys_readable.append(date)


    def set_top_meeting_times(self):
        num_meeting_times = len(self.frequency.values())
        if num_meeting_times < self.NUM_TOP_MEETING_TIMES:
            unpretty_meeting_times = sorted(self.frequency, key=self.frequency.get, reverse=True)[:num_meeting_times]
        else:
            unpretty_meeting_times = sorted(self.frequency, key=self.frequency.get, reverse=True)[:self.NUM_TOP_MEETING_TIMES]
        for meeting_time in unpretty_meeting_times:
            meeting_time = self._make_dt_or_time_str_pretty_for_printing(meeting_time)
            self.top_meeting_times.append(meeting_time)


    def set_top_three_meeting_times(self):
        top_meeting_times_length = len(self.top_meeting_times)
        if not self.top_meeting_times:
            return "Calendar empty","Calendar empty","Calendar empty"
        elif top_meeting_times_length == 1:
            self.top_meeting_time_1 = self.top_meeting_times[0]
            self.top_meeting_time_2 = "Calendar empty"
            self.top_meeting_time_3 = "Calendar empty"
        elif top_meeting_times_length == 2:
            self.top_meeting_time_1 = self.top_meeting_times[0]
            self.top_meeting_time_2 = self.top_meeting_times[1]
            self.top_meeting_time_3 = "Calendar empty"
        else:
            self.top_meeting_time_1 = self.top_meeting_times[0]
            self.top_meeting_time_2 = self.top_meeting_times[1]
            self.top_meeting_time_3 = self.top_meeting_times[2]


    def get_meetings_list(self, google_meetings_blob):
        meetings_list = []
        for num, meeting in enumerate(self.google_meetings_blob, 1):
            num = num
            summary = self._get_summary(meeting)
            start = parse(meeting['start'].get('dateTime', meeting['start'].get('date')))
            end = parse(meeting['end'].get('dateTime', meeting['end'].get('date')))
            duration = end - start
            num_attendees = self._get_num_attendees(meeting.get('attendees'))

            m = Meeting(num, summary, start, end, duration, num_attendees)
            meetings_list.append(m)
        return meetings_list

    def _add_row_to_db(self, meeting):
        id = str(datetime.datetime.now())
        start = str(meeting.start)
        end = str(meeting.end)
        duration = str(meeting.duration)
        conn = sqlite3.connect(self.DB_IHM_SQLITE)
        c = conn.cursor()
        c.execute('INSERT INTO meetings VALUES(?,?,?,?,?,?,?)',
                  (id, meeting.num, meeting.summary,
                   start, end, duration,
                   meeting.num_attendees))
        conn.commit()
        conn.close()

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


    def _make_dt_or_time_str_pretty_for_printing(self, dt_obj_or_str):
        if isinstance(dt_obj_or_str, str):
            if dt_obj_or_str[-6] == '-':
                dt_obj_or_str = dt_obj_or_str[:19]
            dt_obj_or_str = datetime.datetime.strptime(dt_obj_or_str, self.FORMAT_DATETIME_OBJ_TO_STR)
        pretty_printed_str = datetime.datetime.strftime(dt_obj_or_str, self.FORMAT_STR_TO_DATETIME_OBJ)
        return pretty_printed_str


    def _convert_duration_to_work_seconds(self, duration):
        seconds = duration.total_seconds()
        hours = float(seconds) / 3600
        if hours > self.WORK_HOURS_PER_DAY and hours < 24:
            hours = self.WORK_HOURS_PER_DAY
        if hours >= 24:
            days, hours = divmod(hours, 24)
            if hours <= self.WORK_HOURS_PER_DAY:
                hours += days * self.WORK_HOURS_PER_DAY
        seconds = hours * 3600
        return seconds

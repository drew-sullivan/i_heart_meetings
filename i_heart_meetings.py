#!/isr/bin/env python

import csv
import datetime
import dateutil # used to get meeting_duration by subtracting datetime objects
import httplib2 # used to perform the get request to the Google API
import json
import os
import requests
import sqlite3
import textwrap
import time
import urllib2

from apiclient import discovery
from datetime import time
from datetime import timedelta
from dateutil.parser import parse # used to get meeting_duration by subtracting datetime objects
from flask import Flask
from flask import render_template
from money import Money # Currently only supporting USD, but others coming soon!
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

help = textwrap.dedent("""
    -Gathers all events in the given time frame from Google Calendar.
    -Parses event duration, meeting_number, summary, start, end, meeting_duration, num_attendees, financial_cost_single_meeting, time_cost_single_meeting.
    -Adds a row to SQLite database for each event. Each of the above are columns in the table.
    -Reads from db and prints to csv
    -Reads from csv and pretty prints to json
    -Calculates time and financial costs of individual events, the past week's events, and estimates the costs of meetings given the current pattern
    -Posts the results to Slack
    """ )

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/calendar-python-quickstart.json

SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Calendar API Python Quickstart'

WORK_HOURS_PER_YEAR = 2000
WORK_HOURS_PER_DAY = 8
WORK_DAYS_PER_WEEK = 5
WORK_HOURS_PER_WEEK = WORK_HOURS_PER_DAY * WORK_DAYS_PER_WEEK
WORK_SECONDS_PER_WEEK = WORK_HOURS_PER_WEEK * 3600
WORK_WEEKS_PER_YEAR = WORK_HOURS_PER_YEAR / (WORK_HOURS_PER_DAY * WORK_DAYS_PER_WEEK)
WORK_DAYS_PER_YEAR = WORK_WEEKS_PER_YEAR * WORK_DAYS_PER_WEEK
WORK_SECONDS_PER_YEAR = WORK_HOURS_PER_YEAR * 3600

IDEAL_PERCENT_TIME_IN_MEETINGS = 5
IDEAL_PERCENT_TIME_IN_MEETINGS_DECIMAL = float(IDEAL_PERCENT_TIME_IN_MEETINGS / 100)

YEARLY_SALARY_USD = 75000
COST_PER_SECOND = float(YEARLY_SALARY_USD) / WORK_SECONDS_PER_YEAR
CURRENCY = 'USD'
CURRENCY_FORMAT = 'en_US'

TEAM_SIZE = 10

PERSON_SECONDS_PER_WEEK = TEAM_SIZE * WORK_SECONDS_PER_WEEK
PERSON_SECONDS_PER_YEAR = TEAM_SIZE * WORK_SECONDS_PER_YEAR

ARBITRARY_DATE = '2017-01-17T09:00:00Z' # for formatting
TIMEFRAME_END = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
TIMEFRAME_START = str(datetime.datetime.now() - datetime.timedelta(days=7)).replace(' ', 'T') + 'Z' # currently 7 days
MAX_NUM_RESULTS = 100
ORDER_BY_JSON_KEY = 'startTime'
CALENDAR_ID = 'primary'

QUESTIONNAIRE_LINK = 'https://docs.google.com/a/decisiondesk.com/forms/d/e/1FAIpQLSfnDgSB9UoAMUtrLlNoBjuo1e8qe25deJD53LjJEWw5vyd-hQ/viewform?usp=sf_link'
SLACK_HOOK = 'https://hooks.slack.com/services/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'

DB_IHM_SQLITE = '/Users/drew-sullivan/codingStuff/i_heart_meetings/db_ihm.sqlite'

JSON_FIELDS = ('meeting_id', 'meeting_number', 'summary', 'start', 'end',
'meeting_duration', 'num_attendees', 'financial_cost_single_meeting',
'time_cost_single_meeting_days', 'time_cost_single_meeting_hours',
'time_cost_single_meeting_minutes', 'time_cost_single_meeting_seconds')
CSV_FILE = 'meetings_ihm.csv'
JSON_FILE = 'meetings_ihm.json'

ROUND_TO_THIS_MANY_PLACES = 2

app = Flask(__name__)


def perform_i_heart_meetings_calculations ():
    credentials = _get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

    print('\nGetting past week\'s meetings\n')

    google_calendar_data = service.events().list(
        calendarId='primary', timeMin=TIMEFRAME_START, timeMax=TIMEFRAME_END, maxResults=MAX_NUM_RESULTS, singleEvents=True,
        orderBy=ORDER_BY_JSON_KEY).execute()

    meetings = google_calendar_data.get('items', [])

    # _print_entire_google_calendar_results_as_json(meetings)

    time_cost_weekly_in_seconds, financial_cost_total, percent_time_weekly, list_of_meeting_numbers, list_of_meeting_durations, list_of_meeting_summaries, num_meetings, avg_meeting_duration = _calculate_cost_totals(meetings)

    time_cost_weekly = _get_time_cost_weekly(time_cost_weekly_in_seconds)
    time_cost_yearly = _get_time_cost_yearly(time_cost_weekly_in_seconds)
    financial_cost_weekly = _get_financial_cost_weekly(financial_cost_total)
    financial_cost_yearly = _get_financial_cost_yearly(financial_cost_total)
    percent_time_in_meetings = _calculate_percent_time_in_meetings(percent_time_weekly)
    avg_meeting_cost_time = _get_avg_meeting_time_cost(num_meetings, time_cost_weekly_in_seconds)
    avg_meeting_cost_money = _get_avg_meeting_financial_cost(num_meetings, financial_cost_total)
    avg_meeting_duration = _get_avg_meeting_duration(num_meetings, avg_meeting_duration)
    time_recovered_weekly = _calculate_time_recovered_weekly(percent_time_in_meetings)
    time_recovered_yearly = _calculate_time_recovered_yearly(percent_time_in_meetings)
    money_recovered_weekly = _calculate_money_recovered_weekly(percent_time_in_meetings)
    money_recovered_yearly = _calculate_money_recovered_yearly(percent_time_in_meetings)
    ideal_time_yearly = _calculate_ideal_time_yearly()
    ideal_financial_cost_yearly = _calculate_ideal_financial_cost_yearly()

    _print_summary(time_cost_weekly, financial_cost_weekly, time_cost_yearly,
            financial_cost_yearly, avg_meeting_cost_time,
            avg_meeting_cost_money, avg_meeting_duration,
            percent_time_in_meetings, time_recovered_weekly,
            money_recovered_weekly, time_recovered_yearly,
            money_recovered_yearly, ideal_time_yearly,
            ideal_financial_cost_yearly)
#    _write_db_to_csv()
#    _write_csv_to_json()
#    _post_to_slack(time_cost_weekly, financial_cost_weekly, time_cost_yearly,
#            financial_cost_yearly, avg_meeting_cost_time, avg_meeting_cost_money,
#            avg_meeting_duration, percent_time_in_meetings,
#            time_recovered_weekly, money_recovered_weekly,
#            time_recovered_yearly, money_recovered_yearly, ideal_time_yearly,
#            ideal_financial_cost_yearly)
    _generate_charts(time_cost_weekly, financial_cost_weekly, time_cost_yearly,
            financial_cost_yearly, avg_meeting_cost_time,
            avg_meeting_cost_money, avg_meeting_duration,
            percent_time_in_meetings, time_recovered_weekly,
            money_recovered_weekly, time_recovered_yearly,
            money_recovered_yearly, ideal_time_yearly,
            ideal_financial_cost_yearly)


def _calculate_cost_totals(meetings):
    time_cost_weekly_in_seconds = 0
    financial_cost_total = 0
    percent_time_weekly = 0
    list_of_meeting_numbers = []
    list_of_meeting_durations = []
    list_of_meeting_summaries = []
    num_meetings = 0
    avg_meeting_duration = 0
    if not meetings:
        print('No meetings found.')
    for meeting_number, meeting in enumerate(meetings, 1):

        # For printing meeting info and adding info to database

        meeting_number = meeting_number
        summary = str(meeting['summary'])
        start = parse(meeting['start'].get('dateTime', meeting['start'].get('date')))
        end = parse(meeting['end'].get('dateTime', meeting['end'].get('date')))
        meeting_duration = end - start
        num_attendees = _get_num_attendees(meeting.get('attendees'))

        # For returning

        seconds_in_meeting, hours_in_meeting = _convert_time_obj_to_seconds_and_hours(meeting_duration)
        financial_cost_single_meeting = _get_financial_cost_single_meeting(seconds_in_meeting, num_attendees)
        time_cost_single_meeting = _get_time_cost_single_meeting(seconds_in_meeting, num_attendees)
        days, hours, minutes, seconds = _translate_seconds(time_cost_single_meeting)
        percent_time_meeting_single = _calculate_percentage_time_in_meeting_single(seconds_in_meeting)

        percent_time_weekly += float(time_cost_single_meeting) / PERSON_SECONDS_PER_WEEK
        time_cost_weekly_in_seconds += time_cost_single_meeting
        financial_cost_total += (seconds_in_meeting * COST_PER_SECOND * num_attendees)
        list_of_meeting_numbers.append(meeting_number)
        list_of_meeting_durations.append(hours_in_meeting)
        list_of_meeting_summaries.append(summary)
        num_meetings = meeting_number
        avg_meeting_duration += seconds_in_meeting

        meeting_duration = str(meeting_duration)

        #_add_row_to_db(meeting_number, summary, start, end, meeting_duration,
        #        num_attendees, financial_cost_single_meeting, days, hours,
        #        minutes, seconds)

        days, hours, minutes, seconds = _make_pretty_for_printing(days, hours, minutes, seconds)

        _print_meeting_info(meeting_number, summary, start, end,
                meeting_duration, num_attendees, financial_cost_single_meeting,
                days, hours, minutes, seconds, percent_time_meeting_single)

    return(time_cost_weekly_in_seconds, financial_cost_total, percent_time_weekly,
        list_of_meeting_numbers, list_of_meeting_durations,
        list_of_meeting_summaries, num_meetings, avg_meeting_duration)


def _calculate_ideal_time_yearly():
    ideal_time_yearly = float(IDEAL_PERCENT_TIME_IN_MEETINGS)
    ideal_time_yearly /= 100
    ideal_time_yearly *= PERSON_SECONDS_PER_WEEK
    days, hours, minutes, seconds = _translate_seconds(ideal_time_yearly)
    days, hours, minutes, seconds = _make_pretty_for_printing(days, hours, minutes, seconds)
    ideal_time_yearly = ('{0}, {1}, {2}, {3}').format(days, hours, minutes, seconds)
    return ideal_time_yearly


def _calculate_ideal_financial_cost_yearly():
    ideal_financial_cost_yearly = float(IDEAL_PERCENT_TIME_IN_MEETINGS)
    ideal_financial_cost_yearly /= 100
    ideal_financial_cost_yearly *= COST_PER_SECOND
    ideal_financial_cost_yearly *= PERSON_SECONDS_PER_YEAR
    ideal_financial_cost_yearly = Money(ideal_financial_cost_yearly, CURRENCY).format(CURRENCY_FORMAT)
    return ideal_financial_cost_yearly


def _calculate_time_recovered_weekly(percent_time_in_meetings):
    time_recovered_weekly = float(percent_time_in_meetings - IDEAL_PERCENT_TIME_IN_MEETINGS)
    time_recovered_weekly /= 100
    time_recovered_weekly *= PERSON_SECONDS_PER_WEEK
    days, hours, minutes, seconds = _translate_seconds(time_recovered_weekly)
    days, hours, minutes, seconds = _make_pretty_for_printing(days, hours, minutes, seconds)
    time_recovered_weekly = ('{0}, {1}, {2}, {3}').format(days, hours, minutes, seconds)
    return time_recovered_weekly


def _calculate_time_recovered_yearly(percent_time_in_meetings):
    time_recovered_yearly = float(percent_time_in_meetings - IDEAL_PERCENT_TIME_IN_MEETINGS)
    time_recovered_yearly /= 100
    time_recovered_yearly *= PERSON_SECONDS_PER_YEAR
    days, hours, minutes, seconds = _translate_seconds(time_recovered_yearly)
    days, hours, minutes, seconds = _make_pretty_for_printing(days, hours, minutes, seconds)
    time_recovered_yearly = ('{0}, {1}, {2}, {3}').format(days, hours, minutes, seconds)
    return time_recovered_yearly


def _calculate_money_recovered_weekly(percent_time_in_meetings):
    money_recovered_weekly = float(percent_time_in_meetings - IDEAL_PERCENT_TIME_IN_MEETINGS)
    money_recovered_weekly /= 100
    money_recovered_weekly *= COST_PER_SECOND
    money_recovered_weekly *= PERSON_SECONDS_PER_WEEK
    money_recovered_weekly = Money(money_recovered_weekly, CURRENCY).format(CURRENCY_FORMAT)
    return money_recovered_weekly


def _calculate_money_recovered_yearly(percent_time_in_meetings):
    money_recovered_yearly = float(percent_time_in_meetings - IDEAL_PERCENT_TIME_IN_MEETINGS)
    money_recovered_yearly /= 100
    money_recovered_yearly *= COST_PER_SECOND
    money_recovered_yearly *= PERSON_SECONDS_PER_YEAR
    money_recovered_yearly = Money(money_recovered_yearly, CURRENCY).format(CURRENCY_FORMAT)
    return money_recovered_yearly


def _get_avg_meeting_duration(num_meetings, seconds_in_meeting):
    avg_meeting_duration = seconds_in_meeting / num_meetings
    days, hours, minutes, seconds = _translate_seconds(avg_meeting_duration)
    days, hours, minutes, seconds = _make_pretty_for_printing(days, hours, minutes, seconds)
    avg_meeting_duration = ('{0}, {1}, {2}, {3}').format(days, hours, minutes, seconds)
    return avg_meeting_duration


def _get_avg_meeting_time_cost(num_meetings, time_cost_weekly_in_seconds):
    avg_meeting_length = float(time_cost_weekly_in_seconds) / num_meetings
    days, hours, minutes, seconds = _translate_seconds(avg_meeting_length)
    days, hours, minutes, seconds = _make_pretty_for_printing(days, hours, minutes, seconds)
    avg_meeting_length = ('{0}, {1}, {2}, {3}').format(days, hours, minutes, seconds)
    return avg_meeting_length


def _get_avg_meeting_financial_cost(num_meetings, financial_cost_total):
    avg_meeting_cost = float(financial_cost_total) / num_meetings
    avg_meeting_cost = Money(avg_meeting_cost, CURRENCY).format(CURRENCY_FORMAT)
    return avg_meeting_cost


def _get_list_of_meeting_numbers(list_of_meeting_numbers):
    return list_of_meeting_numbers


def _get_list_of_meeting_durations(list_of_meeting_durations):
    return list_of_meeting_durations


def _get_time_cost_single_meeting(seconds_in_meeting, num_attendees):
    time_cost_single_meeting = num_attendees * seconds_in_meeting
    return time_cost_single_meeting


def _get_financial_cost_single_meeting(seconds_in_meeting, num_attendees):
    financial_cost_single_meeting = seconds_in_meeting * COST_PER_SECOND * num_attendees
    financial_cost_single_meeting = Money(financial_cost_single_meeting,
            CURRENCY).format(CURRENCY_FORMAT)
    financial_cost_single_meeting = str(financial_cost_single_meeting)
    return financial_cost_single_meeting


def _get_num_attendees(num_attendees):
    if num_attendees == None:
        num_attendees = 1
    # if sharing multiple calendars, uncomment below
    #num_attendees = 1
    else:
        num_attendees = len(num_attendees)
    return num_attendees


def _convert_time_obj_to_seconds_and_hours(duration):
    seconds = duration.total_seconds()
    hours = float(seconds) / 3600
    return seconds, hours


def _calculate_percentage_time_in_meeting_single(seconds_in_meeting):
    hours_in_meeting = seconds_in_meeting / 3600
    percent_time_in_meeting = (float(hours_in_meeting) / WORK_HOURS_PER_DAY) * 100
    return percent_time_in_meeting


def _calculate_percent_time_in_meetings(percent_time_weekly):
    percent_time_in_meetings = round(percent_time_weekly * 100, ROUND_TO_THIS_MANY_PLACES)
    return percent_time_in_meetings


def _write_csv_to_json():
    csv_file = open(CSV_FILE, 'r')
    json_file = open(JSON_FILE, 'w')

    field_names = JSON_FIELDS
    reader = csv.DictReader(csv_file, field_names)
    for row in reader:
        json.dump(row, json_file, sort_keys=True, indent=4, separators=(',', ': '))
        json_file.write('\n')


def _write_db_to_csv():
    with sqlite3.connect(DB_IHM_SQLITE) as conn:
        csvWriter = csv.writer(open(CSV_FILE, 'w'))
        c = conn.cursor()
        c.execute('SELECT * from meetings')

        rows = c.fetchall()
        csvWriter.writerows(rows)


def _add_row_to_db(meeting_number, summary, start, end, meeting_duration,
        num_attendees, financial_cost_single_meeting,
        time_cost_single_meeting_days, time_cost_single_meeting_hours,
        time_cost_single_meeting_minutes, time_cost_single_meeting_seconds):
    meeting_id = "{0}-{1}".format(start, meeting_number)
    conn = sqlite3.connect(DB_IHM_SQLITE)
    c = conn.cursor()
    c.execute('INSERT INTO meetings VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(
                meeting_id, meeting_number,
                summary, start, end, meeting_duration, num_attendees,
                financial_cost_single_meeting, time_cost_single_meeting_days,
                time_cost_single_meeting_hours,
                time_cost_single_meeting_minutes,
                time_cost_single_meeting_seconds))
    conn.commit()
    conn.close()


def _get_financial_cost_weekly(financial_cost_total):
    financial_cost_weekly = Money(financial_cost_total, CURRENCY).format(CURRENCY_FORMAT)
    return financial_cost_weekly


def _get_financial_cost_yearly(financial_cost_total):
    financial_cost_yearly = Money(financial_cost_total * WORK_WEEKS_PER_YEAR, CURRENCY).format(CURRENCY_FORMAT)
    return financial_cost_yearly


def _get_time_cost_weekly(total_seconds):
    time_cost_weekly = round(float(total_seconds), ROUND_TO_THIS_MANY_PLACES)
    days, hours, minutes, seconds = _translate_seconds(time_cost_weekly)
    days, hours, minutes, seconds = _make_pretty_for_printing(days, hours, minutes, seconds)
    time_cost_weekly = ('{0}, {1}, {2}, {3}').format(days, hours, minutes, seconds)
    return time_cost_weekly


def _get_time_cost_yearly(total_seconds):
    time_cost_yearly= round(float(total_seconds * WORK_WEEKS_PER_YEAR), ROUND_TO_THIS_MANY_PLACES)
    days, hours, minutes, seconds = _translate_seconds(time_cost_yearly)
    days, hours, minutes, seconds = _make_pretty_for_printing(days, hours, minutes, seconds)
    time_cost_yearly = ('{0}, {1}, {2}, {3}').format(days, hours, minutes, seconds)
    return time_cost_yearly


def _translate_seconds(total_seconds):
    # divmod returns quotient and remainder
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    work_days, hours = divmod(hours, WORK_HOURS_PER_DAY)
    return (int(work_days), int(hours), int(minutes), int(seconds))


def _make_pretty_for_printing(days, hours, minutes, seconds):
    seconds = "{} second{}".format(int(seconds), "" if seconds == 1 else "s")
    minutes = "{} minute{}".format(int(minutes), "" if minutes == 1 else "s")
    hours = "{} hour{}".format(int(hours), "" if hours == 1 else "s")
    work_days = "{} work-day{}".format(int(days), "" if days == 1 else "s")
    return (work_days, hours, minutes, seconds)


def _post_to_slack(time_cost_weekly, financial_cost_weekly, time_cost_yearly,
        financial_cost_yearly, avg_meeting_cost_time, avg_meeting_cost_money,
        avg_meeting_duration, percent_time_in_meetings, time_recovered_weekly,
        money_recovered_weekly, time_recovered_yearly, money_recovered_yearly,
        ideal_time_yearly, ideal_financial_cost_yearly):
    data = str(
        {'text':'Weekly Costs:\n{0}, {1}\n\nProjected Yearly Costs:\n{2}, {3}\n\nAverage Time Cost: {4}\nAverage Financial Cost: {5}\nAverage Duration: {6}\n\n{7}% of Your Time is Spent in Meetings\n\nYour Ideal Yearly Costs:\n{13} and {12}\n\nUsing I Heart Meetings Could Save You:\n{9} and {8} per week\n{11} and {10} per year'.format(
                time_cost_weekly, financial_cost_weekly, time_cost_yearly,
                financial_cost_yearly, avg_meeting_cost_time,
                avg_meeting_cost_money, avg_meeting_duration,
                percent_time_in_meetings, time_recovered_weekly,
                money_recovered_weekly, time_recovered_yearly,
                money_recovered_yearly, ideal_time_yearly,
                ideal_financial_cost_yearly),
            'attachments': [
                {
                    'title': 'Please click here to take a 3-question poll about this meetings report',
                    'title_link': QUESTIONNAIRE_LINK
                }
            ]
        }
    )
    url = SLACK_HOOK
    req = urllib2.Request(url, data, {'Content-Type': 'application/json'})
    f = urllib2.urlopen(req)
    f.close()


def _print_entire_google_calendar_results_as_json(meetings):
    print(json.dumps(meetings, indent=4, sort_keys=True))


def _print_meeting_info(meeting_number, summary, start, end, meeting_duration,
        num_attendees, financial_cost_single_meeting, days, hours, minutes,
        seconds, percent_time_meeting_single):
    print("""
    Meeting {0}: {1}
    ======================================================================
    Start: {2}
    End: {3}
    Duration: {4}
    Number of Attendees: {5}
    Cost: {6}
    Cost in Time: {7}, {8}, {9}, {10}
    Percentage of time spent in meeting: {11}%
    """.format(meeting_number, summary, start, end, meeting_duration,
        num_attendees, financial_cost_single_meeting, days, hours, minutes,
        seconds, percent_time_meeting_single))


def _print_summary(time_cost_weekly, financial_cost_weekly, time_cost_yearly,
        financial_cost_yearly, avg_meeting_cost_time,
        avg_meeting_cost_money, avg_meeting_duration,
        percent_time_in_meetings, time_recovered_weekly, money_recovered_weekly,
        time_recovered_yearly, money_recovered_yearly, ideal_time_yearly,
        ideal_financial_cost_yearly):
    print("""
    +++++++++++
    + SUMMARY +
    +++++++++++

    Weekly cost in time: {0}
    Weekly cost in money: {1}

    At this time next year:
    Yearly cost in time: {2}
    Yearly cost in money: {3}

    Average time cost: {4}
    Average financial cost: {5}
    Average duration: {6}

    {7}% of Your Time is Spent in Meetings

    Your ideal yearly costs:
    {13} and {12}

    Using I Heart Meetings could save you:
    {9} and {8} per week
    {11} and {10} per year
    """.format(time_cost_weekly, financial_cost_weekly, time_cost_yearly,
        financial_cost_yearly, avg_meeting_cost_time,
        avg_meeting_cost_money, avg_meeting_duration,
        percent_time_in_meetings, time_recovered_weekly, money_recovered_weekly,
        time_recovered_yearly, money_recovered_yearly, ideal_time_yearly,
        ideal_financial_cost_yearly))


def _get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """

    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'calendar-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def _generate_charts(time_cost_weekly, financial_cost_weekly, time_cost_yearly,
    financial_cost_yearly, avg_meeting_cost_time, avg_meeting_cost_money,
    avg_meeting_duration, percent_time_in_meetings, time_recovered_weekly,
    money_recovered_weekly, time_recovered_yearly, money_recovered_yearly,
    ideal_time_yearly, ideal_financial_cost_yearly):

    @app.route("/line_chart")
    def chart():
        legend = list_of_meeting_numbers
        # X axis - list
        labels = list_of_meeting_numbers
        # Y axis - list
        values = list_of_meeting_durations
        return render_template('line.html', values=values, labels=labels, legend=legend)

    @app.route("/line_chart_2")
    def chart_2():
        legend = 'Meeting Durations'
        # X axis - list
        labels = list_of_meeting_summaries
        # Y axis - list
        values = list_of_meeting_durations
        return render_template('line_2.html', values=values, labels=labels, legend=legend)

    @app.route("/bar_chart")
    def bar_chart():
        legend = 'Meeting Durations'
        #labels = list_of_meeting_numbers
        labels = list_of_meeting_summaries
        values = list_of_meeting_durations
        return render_template('bar.html', values=values, labels=labels, legend=legend)

    @app.route('/radar_chart')
    def radar_chart():
        legend = 'Meeting Durations'
        #labels = list_of_meeting_numbers
        labels = list_of_meeting_summaries
        values = list_of_meeting_durations
        return render_template('radar.html', values=values, labels=labels, legend=legend)

    @app.route('/polar_chart')
    def polar_chart():
        legend = 'Meeting Durations'
        labels = list_of_meeting_numbers
        values = list_of_meeting_durations
        return render_template('polar.html', values=values, labels=labels, legend=legend)

    @app.route('/pie_chart')
    def pie_chart():
        legend = 'Meeting Durations'
        labels = list_of_meeting_numbers
        values = list_of_meeting_durations
        return render_template('pie.html', values=values, labels=labels, legend=legend)

    @app.route('/percent_pie')
    def percent_pie():
        current_costs = 'Current Costs: {0} and {1} yearly'.format(
            financial_cost_yearly, time_cost_yearly
        )
        ideal_meeting_investment = 'Ideal Meeting Investment: {0} and {1}'.format(
            ideal_financial_cost_yearly, ideal_time_yearly
        )
        potential_savings = 'Potential Savings: {0} and {1}'.format(
            money_recovered_yearly, time_recovered_yearly
        )
        remainder = 100 - percent_time_in_meetings
        recovered_percent = percent_time_in_meetings - IDEAL_PERCENT_TIME_IN_MEETINGS
        legend = 'Percentage of Time Spent in Meetings'
        labels = [
            current_costs,
            'Non-Meetings',
            ideal_meeting_investment,
            potential_savings
        ]
        values = [
            percent_time_in_meetings,
            remainder,
            IDEAL_PERCENT_TIME_IN_MEETINGS,
            recovered_percent
        ]
        return render_template('pie.html', values=values, labels=labels, legend=legend)

    @app.route('/doughnut_chart')
    def doughnut_chart():
        legend = 'Meeting Durations'
        labels = list_of_meeting_numbers
        values = list_of_meeting_durations
        return render_template('doughnut.html', values=values, labels=labels, legend=legend)

    @app.route('/timer')
    def meeting_timer():
        return render_template('meeting_timer.html')



if __name__ == '__main__':
    perform_i_heart_meetings_calculations()
    app.run(debug=False)

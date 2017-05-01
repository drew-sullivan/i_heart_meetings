#!/isr/bin/env python

import csv
import collections
import datetime
import dateutil # used to get meeting_duration by subtracting datetime objects
import httplib2 # used to perform the get request to the Google API
import json
import os
import pdb
import requests
import sqlite3
import textwrap
import time
import webbrowser

from apiclient import discovery
from collections import namedtuple
from datetime import time
from datetime import timedelta
from dateutil.parser import parse # used to get meeting_duration by subtracting datetime objects
from model.meeting import Meeting
from model.data_cruncher import Data_Cruncher
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

DB_IHM_SQLITE = '/Users/drew-sullivan/codingStuff/i_heart_meetings/i_heart_meetings/db_ihm.sqlite'

JSON_FIELDS = ('meeting_id', 'meeting_number', 'summary', 'start', 'end',
'meeting_duration', 'num_attendees', 'financial_cost_single_meeting',
'time_cost_single_meeting_days', 'time_cost_single_meeting_hours',
'time_cost_single_meeting_minutes', 'time_cost_single_meeting_seconds')
CSV_FILE = 'meetings_ihm.csv'
JSON_FILE = 'meetings_ihm.json'

ROUND_TO_THIS_MANY_PLACES = 2
FORMAT_DATETIME_OBJ_TO_STR = '%Y-%m-%d %H:%M:%S'
FORMAT_STR_TO_DATETIME_OBJ = '%A, %b %d, %Y - %I:%M'

NUM_TOP_MEETING_TIMES = 3

# for Flask - MAKE SURE TO TURN ON THE LAST LINE, TOO!

from flask import Flask
from flask import render_template
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

#    _print_entire_google_calendar_results_as_json(meetings)

    dc = Data_Cruncher(meetings)
    dc.process_google_blob()
#    _write_db_to_csv()
#    _write_csv_to_json()
    printable_data = dc.printable_data
    _generate_charts(printable_data)
    _open_charts_in_browser()

        #_add_row_to_db(meeting_id, summary, start, end, meeting_duration,
        #        num_attendees, financial_cost_single_meeting, days, hours,
        #        minutes, seconds)

def _open_charts_in_browser():
    webbrowser.open('http://localhost:5000/percent_time_in_meetings')
    webbrowser.open('http://localhost:5000/when_you_meet_most')


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


def _add_row_to_db(meeting_id, summary, start, end, meeting_duration,
        num_attendees, financial_cost_single_meeting,
        time_cost_single_meeting_days, time_cost_single_meeting_hours,
        time_cost_single_meeting_minutes, time_cost_single_meeting_seconds):
    meeting_id = "{0}-{1}".format(start, meeting_id)
    conn = sqlite3.connect(DB_IHM_SQLITE)
    c = conn.cursor()
    c.execute('INSERT INTO meetings VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(
                meeting_id, meeting_id,
                summary, start, end, meeting_duration, num_attendees,
                financial_cost_single_meeting, time_cost_single_meeting_days,
                time_cost_single_meeting_hours,
                time_cost_single_meeting_minutes,
                time_cost_single_meeting_seconds))
    conn.commit()
    conn.close()


def _print_entire_google_calendar_results_as_json(meetings):
    print(json.dumps(meetings, indent=4, sort_keys=True))


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
    credential_path = os.path.join(
        credential_dir,'calendar-python-quickstart.json'
    )
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


def _generate_charts(printable_data):

    @app.route("/when_you_meet_most")
    def chart():
        legend = 'test'
        # X axis - list
        labels = printable_data[17]
        # Y axis - list
        values = list(printable_data[18].values())
        return render_template('when_you_meet_most_line.html', values=values, labels=labels, legend=legend)

    @app.route("/line_chart_2")
    def chart_2():
        legend = 'Meeting Durations'
        # X axis - list
        labels = list_of_meeting_summaries
        # Y axis - list
        values = list_of_meeting_durations
        return render_template('line.html', values=values, labels=labels, legend=legend)

    @app.route("/bar_chart")
    def bar_chart():
        legend = 'Meeting Durations'
        #labels = list_of_meeting_ids
        labels = list_of_meeting_summaries
        values = list_of_meeting_durations
        return render_template('bar.html', values=values, labels=labels, legend=legend)

    @app.route('/radar_chart')
    def radar_chart():
        legend = 'Meeting Durations'
        #labels = list_of_meeting_ids
        labels = list_of_meeting_summaries
        values = list_of_meeting_durations
        return render_template('radar.html', values=values, labels=labels, legend=legend)

    @app.route('/polar_chart')
    def polar_chart():
        legend = 'Meeting Durations'
        labels = list_of_meeting_ids
        values = list_of_meeting_durations
        return render_template('polar.html', values=values, labels=labels, legend=legend)

    @app.route('/pie_chart')
    def pie_chart():
        legend = 'Meeting Durations'
        labels = list_of_meeting_ids
        values = list_of_meeting_durations
        return render_template('pie.html', values=values, labels=labels, legend=legend)

    @app.route('/percent_time_in_meetings')
    def percent_pie():
        current_costs = 'Current Costs: {0} and {1} yearly'.format(
            dc.yearly_cost_in_dollars, dc.yearly_cost_in_seconds_readable
            #dc.yearly_cost_in_dollars, dc.yearly_cost_in_seconds_readable
            #[3], [2]
        )
        ideal_meeting_investment = 'Ideal Meeting Investment: {0} and {1}'.format(
            dc.yearly_ideal_financial_cost_readable, dc.yearly_ideal_time_cost_readable
            #[12], [11]
        )
        potential_savings = 'Potential Savings: {0} and {1}'.format(
            dc.yearly_money_recovered_readable, dc.yearly_time_recovered_readable
            [15], [14]
        )
        remainder = 100 - dc.percent_time_spent()
        recovered_percent = dc.percent_time_spent() - dc.IDEAL_PERCENT_TIME_IN_MEETINGS
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
        return render_template('percent_time_in_meetings_pie.html', values=values, labels=labels, legend=legend)


    @app.route('/doughnut_chart')
    def doughnut_chart():
        legend = 'Meeting Durations'
        labels = list_of_meeting_ids
        values = list_of_meeting_durations
        return render_template('doughnut.html', values=values, labels=labels, legend=legend)

    @app.route('/timer')
    def meeting_timer():
        return render_template('meeting_timer.html')



if __name__ == '__main__':
    perform_i_heart_meetings_calculations()
    app.run(debug=False)

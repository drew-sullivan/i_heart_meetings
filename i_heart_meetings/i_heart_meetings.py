#!/isr/bin/env python

import datetime
import httplib2 # used to perform the get request to the Google API
import os
import pdb
import textwrap
import time
import webbrowser

from apiclient import discovery
from datetime import time
from datetime import timedelta
from model.meeting import Meeting
from model.report import Report
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

ARBITRARY_DATE = '2017-01-17T09:00:00Z' # for formatting
TIMEFRAME_END = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
TIMEFRAME_START = str(datetime.datetime.now() - datetime.timedelta(days=7)).replace(' ', 'T') + 'Z' # currently 7 days
MAX_NUM_RESULTS = 500
ORDER_BY_JSON_KEY = 'startTime'
CALENDAR_ID = 'primary'

# for Flask - MAKE SURE TO TURN ON THE LAST LINE, TOO!

from flask import Flask
from flask import render_template
app = Flask(__name__)


def perform_i_heart_meetings_calculations ():
    credentials = _get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)


    google_calendar_data = service.events().list(
        calendarId='primary', timeMin=TIMEFRAME_START, timeMax=TIMEFRAME_END, maxResults=MAX_NUM_RESULTS, singleEvents=True,
        orderBy=ORDER_BY_JSON_KEY).execute()

    meetings = google_calendar_data.get('items', [])

#    _print_entire_google_calendar_results_as_json(meetings)

    dc = Report(meetings)
    dc.process_google_blob()

    data = dc.printable_data

# WIP


    _generate_charts(data)
    _open_charts_in_browser()
#    _create_slack_html(data)


def _open_charts_in_browser():
    webbrowser.open('http://localhost:5000/percent_time_in_meetings')
    webbrowser.open('http://localhost:5000/when_you_meet_most')
    webbrowser.open('file:///Users/drew-sullivan/codingStuff/i_heart_meetings/i_heart_meetings/templates/report.html')


def _create_slack_html(data):
    f = open('helloworld.html','w')

    message = """
    <!DOCTYPE html>
    <html>
    <head></head>
    <body>
        <h1>Summary</h1>
            <h2>Weekly Costs</h2>
            <p>{0}</p>
            <p>{1}</p>
            <h2>Averages</h2>
            <h3>Costs Per Meeting</h3>
            <p>{2}</p>
            <p>{3}</p>
            <h3>Meeting Duration</h3>
            <p>{4}</p>
            <h2>Projected Yearly Costs</h2>
            <p>{5}</p>
            <p>{6}</p>
            <h2>Top Meeting Times</h2>
            <p>{7}</p>
            <p>{8}</p>
            <p>{9}</p>
            <h2>{10} of Your Time is Spent in Meetings</h2>
            <h2>Ideal Yearly Costs</h2>
            <p>{11}</p>
            <p>{12}</p>
            <h2>Potential Savings</h2>
            <h3>Weekly</h3>
            <p>{13}</p>
            <p>{14}</p>
            <h3>Yearly</h3>
            <p>{15}</p>
            <p>{16}</p>
    </body>
    </html>""".format(data[1],data[0],data[5],data[4],data[6],
                      data[3],data[2],data[7],data[8],data[9],
                      data[10],data[12],data[11],data[13],data[14],
                      data[15],data[16])

    f.write(message)
    f.close()


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


def _generate_charts(data):

    @app.route("/when_you_meet_most")
    def chart():
        legend = 'test'
        # X axis - list
        labels = data[17]
        # Y axis - list
        values = list(data[18].values())
        return render_template('when_you_meet_most_line.html', values=values, labels=labels, legend=legend)

    @app.route('/percent_time_in_meetings')
    def percent_pie():
        current_costs = 'Current Costs: {0} and {1} yearly'.format(
            data[3], data[2])
        ideal_costs = 'Ideal Meeting Investment: {0} and {1}'.format(
            data[12], data[11])
        savings = 'Potential Savings: {0} and {1}'.format(data[15],
            data[16])
        remainder = 100 - data[19]
        recovered_costs = data[19] - data[20]
        legend = 'Percentage of Time Spent in Meetings'
        labels = [current_costs, 'Non-Meetings', ideal_costs, savings]
        values = [data[19], remainder, data[20], recovered_costs]
        return render_template('percent_time_in_meetings_pie.html', values=values, labels=labels, legend=legend)

    @app.route('/slack_printout_test')
    def slack_printout_test():
        weekly_cost_in_seconds_readable = data[0]
        return render_template('slack_printout_test.html', weekly_cost_in_seconds=weekly_cost_in_seconds)

    @app.route('/summary')
    def summary():
        weekly_costs = [data[1], data[0]]
        return render_template('summary.html', weekly_costs=weekly_costs)

    #Plug-and-play templates

    #@app.route("/line_chart_2")
    #def chart_2():
    #    legend = 'Meeting Durations'
    #    # X axis - list
    #    labels = list_of_meeting_summaries
    #    # Y axis - list
    #    values = list_of_meeting_durations
    #    return render_template('line.html', values=values, labels=labels, legend=legend)

    #@app.route("/bar_chart")
    #def bar_chart():
    #    legend = 'Meeting Durations'
    #    #labels = list_of_meeting_ids
    #    labels = list_of_meeting_summaries
    #    values = list_of_meeting_durations
    #    return render_template('bar.html', values=values, labels=labels, legend=legend)

    #@app.route('/radar_chart')
    #def radar_chart():
    #    legend = 'Meeting Durations'
    #    #labels = list_of_meeting_ids
    #    labels = list_of_meeting_summaries
    #    values = list_of_meeting_durations
    #    return render_template('radar.html', values=values, labels=labels, legend=legend)

    #@app.route('/polar_chart')
    #def polar_chart():
    #    legend = 'Meeting Durations'
    #    labels = list_of_meeting_ids
    #    values = list_of_meeting_durations
    #    return render_template('polar.html', values=values, labels=labels, legend=legend)

    #@app.route('/pie_chart')
    #def pie_chart():
    #    current_costs = 'Current Costs: {0} and {1} yearly'.format(
    #        data[3], data[2])
    #    ideal_costs = 'Ideal Meeting Investment: {0} and {1}'.format(
    #        data[12], data[11])
    #    savings = 'Potential Savings: {0} and {1}'.format(data[15],
    #        data[16])
    #    legend = 'Meeting Durations'
    #    labels = [current_costs, 'Non-Meetings', ideal_costs, savings]
    #    values = [data[19],9,8,15]
    #    return render_template('pie.html', values=values, labels=labels, legend=legend)

    #@app.route('/doughnut_chart')
    #def doughnut_chart():
    #    legend = 'Meeting Durations'
    #    labels = list_of_meeting_ids
    #    values = list_of_meeting_durations
    #    return render_template('doughnut.html', values=values, labels=labels, legend=legend)


if __name__ == '__main__':
    perform_i_heart_meetings_calculations()
    app.run(debug=False)

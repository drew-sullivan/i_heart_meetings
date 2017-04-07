#!/usr/bin/env python

import datetime
import dateutil
import httplib2
import json
import logging
import os
import requests
import time
import urllib2

from apiclient import discovery
from datetime import timedelta
from dateutil.parser import parse
from money import Money
from oauth2client import client, tools
from oauth2client.file import Storage

log = logging.getLogger(__name__)

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
YEARLY_SALARY_USD = 100000
WORK_HOURS_PER_YEAR = 2000
WEEKS_PER_YEAR = 52
WORK_SECONDS_PER_YEAR = WORK_HOURS_PER_YEAR * 3600
COST_PER_SECOND = float(YEARLY_SALARY_USD) / WORK_SECONDS_PER_YEAR
ARBITRARY_DATE = '2017-01-17T09:00:00Z' # for formatting
TIMEFRAME_END = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
TIMEFRAME_START = str(datetime.datetime.now() - datetime.timedelta(days=7)).replace(' ', 'T') + 'Z' # currently 7 days
MAX_NUM_RESULTS = 100
ORDER_BY_JSON_KEY = 'startTime'
CALENDAR_ID = 'primary'
QUESTIONNAIRE_LINK = 'https://docs.google.com/a/decisiondesk.com/forms/d/e/1FAIpQLSfnDgSB9UoAMUtrLlNoBjuo1e8qe25deJD53LjJEWw5vyd-hQ/viewform?usp=sf_link'
SLACK_HOOK = 'https://hooks.slack.com/services/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'


def main():
    """Get all requested meetings, do calculations, print results
    """

    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

    print('\nGetting past week\'s meetings\n')

    google_calendar_data = service.events().list(
        calendarId='primary', timeMin=TIMEFRAME_START, timeMax=TIMEFRAME_END, maxResults=MAX_NUM_RESULTS, singleEvents=True,
        orderBy=ORDER_BY_JSON_KEY).execute()

    meetings = google_calendar_data.get('items', [])

    # print_as_json(meetings)
    time_cost_total, financial_cost_total = _calculate_cost_totals(meetings)

    time_cost_weekly = _get_time_cost_weekly(time_cost_total)
    time_cost_yearly = _get_time_cost_yearly(time_cost_total * WEEKS_PER_YEAR)
    financial_cost_weekly = _get_financial_cost_weekly(financial_cost_total)
    financial_cost_yearly = _get_financial_cost_yearly(financial_cost_total * WEEKS_PER_YEAR)

    print_summary(time_cost_weekly, financial_cost_weekly, time_cost_yearly, financial_cost_yearly)
    _post_to_slack(time_cost_weekly, financial_cost_weekly, time_cost_yearly, financial_cost_yearly)

def _calculate_cost_totals(meetings):
    time_cost_total = 0
    financial_cost_total = 0
    if not meetings:
        print('No meetings found.')
    for meeting_number, meeting in enumerate(meetings, 1):
        start = parse(meeting['start'].get('dateTime', meeting['start'].get('date')))
        end = parse(meeting['end'].get('dateTime', meeting['end'].get('date')))
        summary = meeting['summary']
        meeting_duration = end - start
        if meeting.get('attendees') == None:
            num_attendees = 1
        else:
            num_attendees = len(meeting.get('attendees'))
        seconds_in_meeting = meeting_duration.total_seconds()
        financial_cost_single_meeting = Money(seconds_in_meeting * COST_PER_SECOND * num_attendees, 'USD').format('en_US')
        time_cost_single_meeting = round(float(num_attendees) * seconds_in_meeting, 2)

        time_cost_total += time_cost_single_meeting
        financial_cost_total += (seconds_in_meeting * COST_PER_SECOND * num_attendees)
        time_cost_single_meeting = ('{0}, {1}, {2}, {3}').format(*_translate_seconds(time_cost_single_meeting))
        print_meeting_info(meeting_number, summary, start, end, meeting_duration, num_attendees, financial_cost_single_meeting, time_cost_single_meeting)
    return time_cost_total, financial_cost_total

def _get_financial_cost_weekly(integer):
    financial_cost_weekly = Money(integer, 'USD').format('en_US')
    return financial_cost_weekly

def _get_financial_cost_yearly(integer):
    financial_cost_yearly = Money(integer, 'USD').format('en_US')
    return financial_cost_yearly

def _get_time_cost_weekly(seconds):
    time_cost_weekly = round(float(seconds), 2)
    time_cost_weekly = ('{0}, {1}, {2}, {3}').format(*_translate_seconds(time_cost_weekly))
    return time_cost_weekly

def _get_time_cost_yearly(seconds):
    time_cost_yearly = ('{0}, {1}, {2}, {3}').format(*_translate_seconds(seconds))
    return time_cost_yearly

def _translate_seconds(total_seconds):
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)

    seconds = "{} second{}".format(int(seconds), "" if seconds == 1 else "s")
    minutes = "{} minute{}".format(int(minutes), "" if minutes == 1 else "s")
    hours = "{} hour{}".format(int(hours), "" if hours == 1 else "s")
    days = "{} day{}".format(int(days), "" if days == 1 else "s")
    return (days, hours, minutes, seconds)

def _post_to_slack(time_cost_weekly, financial_cost_weekly, time_cost_yearly, financial_cost_yearly):
    data = str(
        {'text': 'Weekly Meetings Costs\nTime: {0}\nMoney: {1}\n\nYearly Meetings Costs\nTime: {2}\nMoney: {3}'.format(time_cost_weekly, financial_cost_weekly, time_cost_yearly, financial_cost_yearly),
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

def print_as_json(meetings):
    print json.dumps(meetings, indent=4, sort_keys=True)

def print_meeting_info(meeting_number, summary, start, end, meeting_duration, num_attendees, financial_cost_single_meeting, time_cost_single_meeting):
        print("""
        Meeting {0}: {1}
        ======================================================================
        Start: {2}
        End: {3}
        Duration: {4}
        Number of Attendees: {5}
        Cost: {6}
        Cost in Time: {7}
        """.format(meeting_number, summary, start, end, meeting_duration, num_attendees, financial_cost_single_meeting, time_cost_single_meeting))
def print_summary(time_cost_weekly, financial_cost_weekly, time_cost_yearly, financial_cost_yearly):
    print("""
    Weekly cost in time: {0}
    Weekly cost in money: {1}

    At this time next year:
    Yearly cost in time: {2}
    Yearly cost in money: {3}
    """.format(time_cost_weekly, financial_cost_weekly, time_cost_yearly, financial_cost_yearly))

def get_credentials():
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

if __name__ == '__main__':
    main()


from datetime import datetime
from dateutil.parser import parse
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from money import Money

import httplib2
import os
import dateutil
import datetime
import logging
import json

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

def main():
    """Shows basic usage of the Google Calendar API.

    Creates a Google Calendar API service object and outputs a list of the next
    50 events on the user's calendar.
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    start_date = '2017-01-17T09:00:00Z'
    print('Getting the upcoming 50 events')
    eventsResult = service.events().list(
        calendarId='primary', timeMin=start_date, timeMax=now, maxResults=500, singleEvents=True,
        orderBy='startTime').execute()
    events = eventsResult.get('items', [])
    total_meeting_cost = 0
    yearly_salary = 100000
    work_seconds_per_year = 2000 * 3600
    cost_per_second = float(yearly_salary) / work_seconds_per_year 

    #print json.dumps(events, indent=4, sort_keys=True)
    total_financial_cost = 0
    total_time_cost = 0
    if not events:
        print('No upcoming events found.')
    for event_number, event in enumerate(events, 1):
        start_raw = event['start'].get('dateTime', event['start'].get('date'))
        end_raw = event['end'].get('dateTime', event['end'].get('date'))
        summary = event['summary'] 
        start = parse(start_raw)
        end = parse(end_raw)
        meeting_duration = end - start
        if event.get('attendees') == None:
            num_attendees = 1
        else:
            num_attendees = len(event.get('attendees'))
        seconds_in_meeting = meeting_duration.total_seconds()
        meeting_cost = Money(seconds_in_meeting * cost_per_second * num_attendees, 'USD').format('en_US')
        meeting_cost_in_time = float(num_attendees * (seconds_in_meeting / 60))
        print("""
        Event {0}: {1}
        Meeting Start: {2}
        Meeting End: {3}
        Meeting Duration: {4}
        Meeting Cost: {5}
        Number of Attendees: {6}
        Meeting Cost in Time: {7} minutes
        """.format(event_number, summary, start, end, meeting_duration, meeting_cost, num_attendees, meeting_cost_in_time)),

        total_time_cost += meeting_cost_in_time
        total_financial_cost += (seconds_in_meeting * cost_per_second) 

    total_time_cost = round(float(total_time_cost / 60),2)
    total_financial_cost = Money(total_financial_cost, 'USD').format('en_US')
    print("""
    Total cost in time: {0} hours 
    Total cost in money: {1}
    """.format(total_time_cost, total_financial_cost)) 

# TODO: 
#-Create 'total meetings cost that prints at the end of everything'
#-Estimate their salaries
if __name__ == '__main__':
    main()

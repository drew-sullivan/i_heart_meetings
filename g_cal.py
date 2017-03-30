#!/usr/bin/env python

from datetime import datetime, timedelta
from dateutil.parser import parse
from apiclient import discovery
from oauth2client import client, tools
from oauth2client.file import Storage
from money import Money

import urllib2
import requests
import httplib2
import os
import dateutil
import datetime
import logging
import json
import time 

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
    """Insert description here
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    start_date = '2017-01-17T09:00:00Z'
    past_week = str(datetime.datetime.now() - datetime.timedelta(days=7))
    past_week = past_week.replace(' ', 'T')
    past_week = past_week + 'Z'
    print('\nGetting past week\'s events\n')

    eventsResult = service.events().list(
        calendarId='primary', timeMin=past_week, timeMax=now, maxResults=100, singleEvents=True,
        orderBy='startTime').execute()
    events = eventsResult.get('items', [])
    total_meeting_cost = 0
    yearly_salary = 100000
    work_hours_per_year= 2000
    work_seconds_per_year = work_hours_per_year  * 3600
    cost_per_second = float(yearly_salary) / work_seconds_per_year 
    

    total_financial_cost = 0
    total_time_cost = 0

    ###
    # json for all requested events
    ###

    # print json.dumps(events, indent=4, sort_keys=True)

 
    if not events:
        print('No upcoming events found.')
    for event_number, event in enumerate(events, 1):
        start = parse(event['start'].get('dateTime', event['start'].get('date')))
        end = parse(event['end'].get('dateTime', event['end'].get('date')))
        summary = event['summary'] 
        meeting_duration = end - start
        if event.get('attendees') == None:
            num_attendees = 1
        else:
            num_attendees = len(event.get('attendees'))
        seconds_in_meeting = meeting_duration.total_seconds()
        meeting_cost = Money(seconds_in_meeting * cost_per_second * num_attendees, 'USD').format('en_US')
        meeting_cost_in_time = round(float(num_attendees) * seconds_in_meeting, 2)

        total_time_cost += meeting_cost_in_time
        total_financial_cost += (seconds_in_meeting * cost_per_second * num_attendees) 
        
        meeting_cost_in_time = time.strftime("%H:%M:%S", time.gmtime(meeting_cost_in_time)) 

        print("""
        Event {0}: {1}
        ======================================================================
        Start: {2}
        End: {3}
        Duration: {4}
        Number of Attendees: {6}
        Cost: {5}
        Cost in Time: {7} 
        """.format(event_number, summary, start, end, meeting_duration, meeting_cost, num_attendees, meeting_cost_in_time)),
    
    total_time_cost = round(float(total_time_cost), 2)
    total_time_cost = time.strftime("%H:%M:%S", time.gmtime(total_time_cost))
    total_financial_cost = Money(total_financial_cost, 'USD').format('en_US')

    print("""
    Total cost in time: {0}
    Total cost in money: {1}
    """.format(total_time_cost, total_financial_cost)) 

    ###
    # Posting to Slack
    ###

    data = str({'text': 'In the past week, meetings cost you {0} minutes and {1}'.format(total_time_cost, total_financial_cost)}) 
    url = 'https://hooks.slack.com/services/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'
    req = urllib2.Request(url, data, {'Content-Type': 'application/json'})
    f = urllib2.urlopen(req)
    f.close()

# TODO: 
#-Estimate salaries
#-Estimate percentage of salary budget spent on meetings
if __name__ == '__main__':
    main()

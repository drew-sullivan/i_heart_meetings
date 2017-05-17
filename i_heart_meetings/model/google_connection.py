
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



try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

class Google_Connection:

    # If modifying these scopes, delete your previously saved credentials
    # at ~/.credentials/calendar-python-quickstart.json

    SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
    CLIENT_SECRET_FILE = 'client_secret.json'
    APPLICATION_NAME = 'I Heart Meetings'

    ARBITRARY_DATE = '2017-01-17T09:00:00Z' # for formatting
    TIMEFRAME_END = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    TIMEFRAME_START = str(datetime.datetime.now() - datetime.timedelta(days=7)).replace(' ', 'T') + 'Z' # currently 7 days
    MAX_NUM_RESULTS = 500
    ORDER_BY_JSON_KEY = 'startTime'
    CALENDAR_ID = 'primary'

    def __init__(self):
        self.credentials = self._get_credentials()
        self.http = self.credentials.authorize(httplib2.Http())
        self.service = discovery.build('calendar', 'v3', http=self.http)
        self.google_calendar_data = self.service.events().list(
            calendarId='primary', timeMin=self.TIMEFRAME_START, timeMax=self.TIMEFRAME_END, maxResults=self.MAX_NUM_RESULTS, singleEvents=True,
            orderBy=self.ORDER_BY_JSON_KEY).execute()
        self.meetings = self.google_calendar_data.get('items', [])



    def _get_credentials(self):
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
            credential_dir,'google_credentials.json'
        )
        store = Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(self.CLIENT_SECRET_FILE, self.SCOPES)
            flow.user_agent = self.APPLICATION_NAME
            if flags:
                credentials = tools.run_flow(flow, store, flags)
            else: # Needed only for compatibility with Python 2.6
                credentials = tools.run(flow, store)
            print('Storing credentials to ' + credential_path)
        return credentials

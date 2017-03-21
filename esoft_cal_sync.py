#! python3.6

from __future__ import print_function
from bs4 import BeautifulSoup
import requests
import configparser
from datetime import datetime, date, time

# required modules for Google Cal API
import httplib2
import os
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/calendar-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/calendar'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'esoft-cal-sync'

month = 0  # value is month to begin sync: 0 = current, 1 = next month, 2 = 2 months forward, etc

def get_credentials():
    """
        Gets valid user credentials from storage.

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


def login():
    """
        Pulls credentials from local config file
    """

    config = configparser.ConfigParser()
    config.read("c:/code/config.ini")
    client_key = config.get("esoft", "client_key")
    access = config.get("esoft", "access")
    username = config.get("esoft", "username")
    password = config.get("esoft", "password")
    loginurl = 'https://www.esoftplanner.com/v3/employee/login.php?access=' + access
    loginCreds = {'action': 'login', 'client_key': client_key, 'access': access, 'login': username, 'password': password}

    # create the eSoft session by posting creds to login page
    global session
    session = requests.session()
    login = session.post(loginurl, data=loginCreds)
    if login.status_code == 200:
        print('Logged in to eSoft Successfully...')

    # pull the Google creds from Google supplied get_credentials() function and create session
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    global service
    service = discovery.build('calendar', 'v3', http=http)


def resetCal(outlook):
    """
        Locates lessons previously scheduled in Google Calendar and deletes them
        to prevent duplicate events
    """
    lessons = []
    first = datetime.today().replace(day=1, hour=0).isoformat() + 'Z'
    current_month = int(datetime.now().strftime("%m"))
    end_month = int(datetime.now().strftime("%m")) + outlook + 1
    end_year = int(datetime.now().strftime("%Y"))
    if current_month <= 12 and end_month > 12:
        end_month -= 12
        end_month = '%02d' % end_month
        end_year += 1

    last = datetime.today().replace(year=end_year, month=int(end_month), day=1).isoformat() + 'Z'
    short_last = str(date.today().replace(year=end_year, month=int(end_month), day=1))
    print('Searching for events through ' + short_last)
    eventsResult = service.events().list(
        calendarId='primary', timeMin=first, timeMax=last, maxResults=300, singleEvents=True,
        orderBy='startTime').execute()
    scheduled = eventsResult.get('items', [])

    if not scheduled:
        print('No upcoming events found.')

    for item in scheduled:
        if 'Lesson:' in item['summary']:
            print('Deleting: ' + item['summary'])
            lessons.append(item['summary'])
            service.events().delete(calendarId='primary', eventId=item['id']).execute()
    if len(lessons) == 0:
        print('No scheduled lessons found in Google calendar')


def pullSched(cal_mon):
    """
    Takes one parameter to determine # of months ahead to check schedule.
    Scrapes the eSoft schedule for lessons
    Calls the formatEvents() function with events found as parameter
    """

    # constructs URL based on month of interest
    url = 'https://www.esoftplanner.com/v3/employee/myaccount.php?ddate=&wdate=&mdate=%s&fdate=0&adate=&adddate=' %(str(cal_mon))

    cal = session.get(url)
    soup = BeautifulSoup(cal.text, "html.parser")

    # searches page for tables with following attributes
    tables = soup.find_all('table', attrs={'border': '1', 'cellpadding': '4', 'cellspacing': '0', 'class': 'form', 'style': 'margin-top: 5px;', 'width': '99%'})

    sub_tbl = 0
    events = []
    weekdays = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat']

    # iterates through tables matching specs to locate the table of interest
    for subtable in tables:
        sub_tbl += 1

        # splits data of table and converts to list
        if sub_tbl == 3:
            data = subtable.get_text(',', strip=True)
            items = data.split(',')

            for item in items:
                # identifies 'date' field and creates new event
                if len(item) <= 2:

                    # checks to see if event has been constructed with corresponding details
                    if len(events) > 1:

                        # formats event details for google cal event. createGevent() is called within formatEvents()
                        formatEvents(events, cal_mon)

                    day_num = item
                    events = []
                    events.append(day_num)

                # adds corresponding details to event
                elif len(item) >= 2 and item not in weekdays:
                    events.append(item)


def formatEvents(events, cal_mon):
    """
    Takes the events found in pullSched() function
    Formats the events to meet Google Event structure
    Calls createGevent() function with formatted event
    """
    # parses one event from list at a time
    while len(events) >= 3:
        event = events[0:3]
        event_day = int(event[0])
        current_month = int(datetime.now().strftime("%m"))
        event_month = int(datetime.now().strftime("%m")) + cal_mon
        event_year = int(datetime.now().strftime("%Y"))

        if current_month <= 12 and event_month > 12:
            event_month -= 12
            event_month = '%02d' % event_month
            event_year += 1

        event_date = date(event_year, int(event_month), event_day)
        event[0] = str(event_date)

        createGevent(event)

        # deletes event from daily list after it has been processed
        del events[1:3]


def createGevent(event):
    """
    Applies event data to Google Event format
    Creates the event
    """
    tmp_time = event[1].split(' - ')
    start_time = tmp_time[0]
    end_time = tmp_time[1]
    tmp_start = event[0] + ' ' + start_time
    tmp_end = event[0] + ' ' + end_time

    start = datetime.strptime(tmp_start, '%Y-%m-%d %I:%M%p').isoformat('T')
    end = datetime.strptime(tmp_end, '%Y-%m-%d %I:%M%p').isoformat('T')
    summary = 'Lesson: ' + event[2]
    location = 'Performance Sport Systems, 16778 Oakmont Ave, Gaithersburg, MD 20877'

    new_event = {
        'summary': summary,
        'description': 'https://www.esoftplanner.com/v3/employee/login.php?access=0dG81LSVxNmo65bEyHqDuJ2Jpw==',
        'location': location,
        'start': {
            'dateTime': start,
            'timeZone': 'America/New_York',
        },
        'end': {
            'dateTime': end,
            'timeZone': 'America/New_York',
        },
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 10 * 60}, # hours * minutes
                {'method': 'popup', 'minutes': 60},
            ],
        },
        'colorId': '11'
    }

    new_event = service.events().insert(calendarId='primary', body=new_event).execute()
    print('Creating: %s\n%s\n' % (new_event['summary'], new_event.get('htmlLink')))


if __name__ == '__main__':
    login()
    resetCal(11) # value is how many months ahead to refresh calendar
    while month <= 11: # value is how many months ahead to sync
        print("Checking " + str(month) + " month(s) ahead...")
        pullSched(month)
        month += 1
    else:
        print('\nSync complete.')

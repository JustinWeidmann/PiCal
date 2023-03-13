from __future__ import print_function

import datetime
import os.path
from types import new_class
import requests, time, json
from collections import defaultdict

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']
calenderID = 'GoogleCalGroup' # PiCal Group


def main():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)   # Default: port 0
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('calendar', 'v3', credentials=creds)

        lastWeek = datetime.date.today() + datetime.timedelta(days=-7)
        nowDatetime = datetime.datetime.utcnow().isoformat() + 'Z'
        lastWeekTime = str(lastWeek) + nowDatetime[10 : : ]

        rawLastWeekCal = service.events().list(
            calendarId=calenderID,
            timeMin=lastWeekTime,
            timeMax=nowDatetime,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        lastWeekCal = rawLastWeekCal['items']
        # print(json.dumps(rawLastWeekCal, indent=2))

        checkCalUpdate(lastWeekCal, service)


    except HttpError as error:
        print('An error occurred: %s' % error)

def callToggleEntrys(timesCalled):
    getToggleEntrys = 'https://api.track.toggl.com/api/v8/time_entries'
    toggleAPIKey = 'Shhhhhhhhhhhhh'
    rawToggleData = requests.get(getToggleEntrys, auth=(toggleAPIKey, 'api_token'))
    print("Calling Toggle...")

    if(rawToggleData.status_code == 200): return rawToggleData.json()
    else: 
        print('err: ', rawToggleData.status_code)
        if(timesCalled < 4):
            print("Taking 10...")
            time.sleep(10)
            callToggleEntrys(timesCalled + 1)
        else: 
            print("Lost the will to call, QUITTING...")
            exit()


def callToggleProjects(timesCalled, pid):
    getProjectData = f'https://api.track.toggl.com/api/v8/projects/{pid}'
    toggleAPIKey = 'Shhhhhhhhhhhhh'
    rawProjectData = requests.get(getProjectData, auth=(toggleAPIKey, 'api_token'))
    print("Calling Toggle Proj...")

    if(rawProjectData.status_code == 200):
        projectData = rawProjectData.json()
        return projectData['data']['name']
    else: 
        print('err: ', rawProjectData.status_code)
        if(timesCalled < 4):
            print("Taking 10...")
            time.sleep(10)
            callToggleEntrys(timesCalled + 1)
        else: 
            print("Lost the will to call, QUITTING...")
            exit()


def checkCalUpdate(lastWeekCal, service):
    toggleData = callToggleEntrys(0)
    toggIndexOffset = 1 # Find index of newest toggle entry

    # Find completed timer index
    while not('stop' in toggleData[len(toggleData)-toggIndexOffset]):
        toggIndexOffset = toggIndexOffset + 1

    newestCalTime = lastWeekCal[len(lastWeekCal)-1]['start']['dateTime'][:-1]
    if (toggIndexOffset == 2): toggleData.pop()    # Remove entry if currently running
   
    i = 1
    while True:
        indexedToggleTime = toggleData[len(toggleData)-i]['start'][:-6]
        # print(f"{indexedToggleTime} vs {newestCalTime} with i={i}")

        if (indexedToggleTime == newestCalTime and i==1):
            print("No new data, exiting...")
            quit()   # No new data -> Stop script
        elif (indexedToggleTime == newestCalTime and i!=1):
            print(f"Updating data from index = {i}")
            writeNewtoCal(toggleData, service, i)
            break   # Update from data from index i
        elif (i == len(toggleData)):
            print("No shared data, must write everything...")
            writeAlltoCal(toggleData, service)
            break   # No shared data, must write everything
        i = i+1


def writeNewtoCal(toggleData, service, i):
    print("Updating new...")
    for k in range(i-1):
        # print(f"k={k+1} and i={i}")
        toggleEntry = toggleData[len(toggleData)-(k+1)]

        f = open('pids.json')
        pidsData = json.load(f)
        pidsData = pidsData['pids']
        for j, l in enumerate(pidsData):
            if (int(pidsData[j]['pid']) == toggleEntry['pid']):
                print(pidsData[j]['name'])
                projectName = pidsData[j]['name']
                break
            elif (j == range(j)): 
                projectName = callToggleProjects(0, toggleEntry['pid'])
                break
        f.close()

        timeEntryEvent = {
            'summary': projectName,
            'description': toggleEntry.get('description', ''),  # .get() sets default if empty
            'start': {
                'dateTime': toggleEntry['start'],
                'timeZone': 'Europe/London',
            },
            'end': {
                'dateTime': toggleEntry['stop'],
                'timeZone': 'Europe/London',
            },
        }
        print(timeEntryEvent)

        service.events().insert(calendarId=calenderID, body=timeEntryEvent).execute()


def writeAlltoCal(toggleData, service):
    print("Updating all...")
    for toggleEntry in toggleData:
        f = open('pids.json')
        pidsData = json.load(f)
        pidsData = pidsData['pids']
        for i, k in enumerate(pidsData):
            if (int(pidsData[i]['pid']) == toggleEntry['pid']):
                print(pidsData[i]['name'])
                projectName = pidsData[i]['name']
                break
            elif (i == range(pidsData)): 
                projectName = callToggleProjects(0, toggleEntry['pid'])
                break
        f.close()

        timeEntryEvent = {
            'summary': projectName,
            'description': toggleEntry.get('description', ''),  # .get() sets default if empty
            'start': {
                'dateTime': toggleEntry['start'],
                'timeZone': 'Europe/London',
            },
            'end': {
                'dateTime': toggleEntry['stop'],
                'timeZone': 'Europe/London',
            },
        }
        print(timeEntryEvent)

        service.events().insert(calendarId=calenderID, body=timeEntryEvent).execute()




if __name__ == '__main__':
    main()

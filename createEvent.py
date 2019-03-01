from __future__ import print_function
import datetime
import sys
import requests
import re
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools

# If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/calendar'

def main():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('calendar', 'v3', http=creds.authorize(Http()))

    # Call the Calendar API
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    #print(sys.argv[1])
    events_result = service.events().list(calendarId='primary', timeMin=now,
                                        maxResults=10, singleEvents=True,
                                        orderBy='startTime').execute()
    event = {
        'summary': sys.argv[1],
        'location': sys.argv[2],
        'description': sys.argv[2],
        'start': {
            'dateTime': sys.argv[3],
            'timeZone': sys.argv[5],
        },
        'end': {
            'dateTime': sys.argv[4],
            'timeZone': sys.argv[5],
        },
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'popup', 'minutes': 10},
            ],
        },
    }
    try:
        event = service.events().insert(calendarId='primary', body=event).execute()
    except:
        #Send Error alert to Slack
        e = sys.exc_info()[1]
        headers = {
            'Content-type': 'application/json',
        }
        group=sys.argv[1]
        input=" - <!channel> EVENT ERROR: "
        error=str(e)
        error=re.sub("<|>", "", error)
        error= error.split("returned",1)[1]
        error= error.split("\"")[1]
        output=group+input+error
        data = '{"text":"%s"}' % (output)
        response = requests.post('https://hooks.slack.com/services/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', headers=headers, data=data)
        #print( response )
        #print( "Caught HTTP Error", e )
        sys.exit()

    #print( 'Event created: %s' % (event.get('htmlLink'))) #Debugging

    #Verbose notifications of creation of each event
    #headers = {
    #    'Content-type': 'application/json',
    #}
    #group=sys.argv[1]
    #input=" - Event Created: "
    #output=group+input+link
    #data = '{"text":"%s"}' % (output)
    #response = requests.post('https://hooks.slack.com/services/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', headers=headers, data=data)
    #print( response ) #Debugging

if __name__ == '__main__':
    main()

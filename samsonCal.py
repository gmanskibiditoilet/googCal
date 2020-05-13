#!/usr/bin/env python3

import os, re, requests, sys, subprocess
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools

debugging = False

os.chdir('/etc/googleCalendar/')

headers = {
    'Content-type': 'application/json',
}
f=open("/etc/googleCalendar/slack.txt", "r")
if f.mode == 'r':
    slackapikey=f.read().strip()
    f.close()
    if debugging:
        print("Slack API Key is "+slackapikey)
f.close()


#check email
try:
    subprocess.check_output(['/usr/bin/fetchmail'])
except subprocess.CalledProcessError as e:
    if "Query status=2 (SOCKET)" in str(e.output):
        subprocess.run(['/etc/googleCalendar/fixSSL.sh'])
    elif "No mail for piratemonkscal@gmail.com" in str(e.output):
        print("No New Mail")
    else:
        print("Something else went wrong: "+str(e.output))
        quit()

def openFile ( filePath ):
    try:
        f=open('/etc/googleCalendar/mail/'+filePath, 'r')
        lines = f.readlines()
    except:
        if debugging:
            print("Something went wrong opening the file")
        quit()
    finally:
        f.close()
    return lines

#define function for handling new meetings
def newMeeing ( filePath, groupName ):
    lines = openFile (filePath)
    for line in lines:
        #Match Add to list
        if "Would you like to be added to the distribution" in line:
            #get everything beginning with https:// and ending with '>
            matches = re.findall("https:\/\/.*'>", line)
            link = str(matches[0])[:-2] #Convert to string and strip the last 2 extraneous characters
    headers = {
        'Content-type': 'application/json',
    }
    output="INVITATION to "+groupName+" in mailbox - Click the link to accept: "+link+' - To make this message stop see directions at https://bit.ly/2DoC7gA"}'
    data = '{"text":"%s"}' % (output)
    print(data)
    response = requests.post(slackapikey, headers=headers, data=data)

#Instantiate Google Calendar API
SCOPES = 'https://www.googleapis.com/auth/calendar'
store = file.Storage('token.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
    creds = tools.run_flow(flow, store)
service = build('calendar', 'v3', http=creds.authorize(Http()))


#Load all the email files into memory
messages = os.listdir("/etc/googleCalendar/mail")
for message in messages:
    lines = openFile ( message )
    #Loop through the lines looking for the info.
    Proceed = True; groupName = False; dateString = False; zoomLink = False; ModificatonEmail = False
    for line in lines:
        if "Subject:" in line:
            #This is the subject line.
            #Need to check if it is an invitation to next meeting
            if "Invitation to Next Samson" in line:
                groupName = line.split(': ')[1]
            #Check if this is a modification of an existing meeting
            elif "Samson Meeting Changed" in line:
                groupName = line.split(': ')[1]
                ModificatonEmail = True
                if (debugging):
                    print("This is a Modification Email")
            #Need to check if it is an invitation to the first meeting of a new group
            elif "Your Invitation to Join the Samson Society Group" in line:
                groupName = line.split(': ')[1]
                newMeeing( message, groupName)
                Proceed = False
                break
        if "ur next meeting will be" in line: #This is a next Meeting Email
            #This is the paragraph line
            try:
                dateString = str(re.findall("((Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{2}, \d{4} at \d{2}:\d{2} (AM|PM) \(.*\))",line)[0][0])
            except:
                if debugging:
                    print("No dateString in this email")
                dateString = False
                break
            try:
                zoomLink = str(re.findall("https:\/\/.*'>", line)[0])[:-2]
                if not("zoom" in zoomLink):
                    #link is not a zoom link
                    zoomLink = False
            except:
                if debugging:
                    print("No zoom link found in this email")
                zoomLink = False
                break
    #Validate
    if not(Proceed and dateString and groupName and (ModificatonEmail or zoomLink)):
        #This email does not contain all necessary info.
        #Stop processing this email and move on to the next in the loop
        if debugging:
            print ("Invalid Email, moving on")
            print ("Proceed: "+str(Proceed))
            print ("groupName: "+str(groupName))
            print ("dateString: "+str(dateString))
            print ("zoomLink: "+str(zoomLink))
        os.remove("/etc/googleCalendar/mail/"+message)
        continue
        
    #Regular New Meeting Email:
    
    #Break the dateString into parts
    #Strip the timezone:
    dateTimeStr = (dateString.split("(")[0][:-1]).replace(',', '').replace('at', '') #yields Mar 08 2019  12:00 PM
    startDate = datetime.strptime(dateTimeStr, '%b %d %Y %I:%M %p')
    endDate = startDate + timedelta(hours=1)
    #Determine the timezone
    timezoneStr = dateString.split("(")[1]
    if timezoneStr[-1] == ' ': #Remove trailing space if present
        timezoneStr = timezoneStr[:-1]
        if debugging:
            print("Removed trailing space from time zone string")
    if timezoneStr[-1] == ')':
        timezoneStr = timezoneStr[:-1]
        if debugging:
            print("Removed trailing ) from time zone string")
    #Convert email format timezone to Google format timezoneStr
    #Website to get formats: http://www.timezoneconverter.com/cgi-bin/zonehelp.tzc
    TimezoneDictionary = {
        'Eastern Time': 'America/New_York',
        'Central Time': 'America/Chicago',
        'Alaska': 'America/Anchorage',
        'Amsterdam, Berlin, Bern, Rome, Stockho': 'Europe/Rome',
        'Greenwich Mean Time : London': 'Etc/GMT',
        'Pacific Time': 'America/Los_Angeles',
        'Hawaii': 'Pacific/Honolulu',
        'Arizona': 'America/Phoenix',
        'Beijing, Chongqing, Hong Kong, Urumqi': 'Asia/Shanghai',
        'Seoul':'Asia/Seoul',
        'Mountain Time':'America/Denver'
    }
    timezone = TimezoneDictionary.get(timezoneStr, 'Unknown Timezone')
    if timezone == 'Unknown Timezone':
        headers = {
            'Content-type': 'application/json',
        }
        output="Encountered unknown timezone "+timezoneStr+" in "+groupName
        data = '{"text":"%s"}' % (output)
        response = requests.post(slackapikey, headers=headers, data=data)
        continue

    #convert datetime objects into strings
    startDateStr = startDate.strftime('%Y-%m-%dT%H:%M:00')
    endDateStr = endDate.strftime('%Y-%m-%dT%H:%M:00')
    if not(ModificatonEmail):
        #Not a modification email. Make a new event
        if debugging:
            print("Group Name:\t"+groupName+"\nZoom Link:\t"+zoomLink+"\nStart Date:\t"+startDate.strftime("%b %d, %Y  %I:%M %p")+"\nEnd Date:\t"+endDate.strftime("%b %d, %Y  %I:%M %p")+"\nTimezone:\t"+timezone)
        description = zoomLink+"\nCall In Numbers:\n+1-408-638-0968\n+1-646-558-8656"
        event = {
            'summary': groupName,
            'location': zoomLink,
            'description': description,
            'start': {
                'dateTime': startDateStr,
                'timeZone': timezone,
            },
            'end': {
                'dateTime': endDateStr,
                'timeZone': timezone,
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes':10},
                ],
            },
        }
        os.remove("/etc/googleCalendar/mail/"+message)
        try:
            event = service.events().insert(calendarId='primary', body=event).execute()
            if debugging:
                #Verbose notifications of creation of each event
                headers = {
                    'Content-type': 'application/json',
                }
                output="Event created for: "+groupName
                data = '{"text":"%s"}' % (output)
                response = requests.post(slackapikey, headers=headers, data=data)

        except:
            if debugging:
                print("Error posting the event to Google Calendar")
            e = sys.exc_info()[1]
            input=" - <!channel> EVENT ERROR: "
            error=str(e)
            error=re.sub("<|>", "", error)
            error= error.split("returned",1) #[1]
            error= error.split("\"")[1]
            output=groupName+input+error
            data = '{"text":"%s"}' % (output)
            print(data)
            response = requests.post(slackapikey, headers=headers, data=data)
            #response = requests.post('https://hooks.slack.com/services/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', headers=headers, data=data)
    else:
        #is a modification Email
        #Get the event ID of the matching event
        now = datetime.utcnow().isoformat() + 'Z'
        page_token = None
        while True:
            events = service.events().list(calendarId='primary', timeMin=now, pageToken=page_token).execute()
            for event in events['items']:
                if (debugging):
                    print (event['summary'])
                if (event['summary']).strip() == groupName.strip():
                    #This is the meeting we are looking for
                    myEventID=event['id']
                    if (debugging):
                        print(myEventID)
                        print (event['start'])
                    event['start'] = {'dateTime': startDateStr, 'timeZone': timezone}
                    event['end'] = {'dateTime': endDateStr, 'timeZone': timezone}
                    updatedEvent = service.events().update(calendarId='primary', eventId=myEventID, body=event).execute()
                    os.remove("/etc/googleCalendar/mail/"+message)
                    break
            page_token = events.get('nextPageToken')
            if not page_token:
                if debugging:
                    #Verbose notifications
                    headers = {
                        'Content-type': 'application/json',
                    }
                    output="Update made for: "+groupName
                    data = '{"text":"%s"}' % (output)
                    response = requests.post('https://hooks.slack.com/services/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', headers=headers, data=data)
                break

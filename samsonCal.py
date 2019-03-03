#!/usr/bin/env python3

import os, re, requests, sys, subprocess
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools

debugging = True

#check email
subprocess.run(['/usr/bin/fetchmail'])

def openFile ( filePath ):
    try:
        f=open(filePath, 'r')
        lines = f.readlines()
    except:
        if debugging:
            print("Something went wrong opening the file")
        quit()
    finally:
        f.close()
    return lines

#define function for handling new meetings
def newMeeing ( filePath, groupName):
    lines = openFile (filePath)
    for line in lines:
        #Match Add to list
        if "Would you like to be added to the distribution" in line:
            #get everything beginning with https:// and ending with '>
            matches = re.findall("https:\/\/.*'>", line)
            link = str(matches[0])[:-2] #Convert to string and strip the last 2 extraneous characters
    output="INVITATION to "+groupName+" in mailbox - Click the link to accept: "+link+' - To make this message stop see directions at https://bit.ly/2DoC7gA"}'
    data = '{"text":"%s"}' % (output)
    print(data)
    #response = requests.post('https://hooks.slack.com/services/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', headers=headers, data=data)

#Instantiate Google Calendar API
SCOPES = 'https://www.googleapis.com/auth/calendar'
store = file.Storage('token.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
    creds = tools.run_flow(flow, store)
service = build('calendar', 'v3', http=creds.authorize(Http()))


#Load all the email files into memory
messages = os.listdir("/etc/googCal/mail")
Proceed = True; groupName = False
for message in messages:
    lines = openFile ( message )
    #Loop through the lines looking for the info.
    for line in lines:
        if "Subject:" in line:
            #This is the subject line.
            #Need to check if it is an invitation to next meeting
            if "Invitation to Next Samson" in line:
                groupName = line.split(': ')[1]
            #Need to check if it is an invitation to the first meeting of a new group
            elif "Your Invitation to Join the Samson Society Group" in line:
                groupName = line.split(': ')[1]
                newMeeing( message, groupName)
                Proceed = False
                break
        if "Our next meeting will be" in line:
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
                if not("zoom" in zoomLink)
                    #link is not a zoom link
                    zoomLink = False
            except:
                if debugging:
                    print("No zoom link found in this email")
                zoomLink = False
                break
    
    #Validate
    if not(Proceed and dateString and zoomLink and groupName)
        #This email does not contain all necessary info. 
        #Stop processing this email and move on to the next in the loop
        continue
    
    #Break the dateString into parts
    #Strip the timezone:
    dateTimeStr = (dateString.split("(")[0][:-1]).replace(',', '').replace('at', '') #yields Mar 08 2019  12:00 PM
    startDate = datetime.strptime(dateTimeStr, '%b %d %Y %I:%M %p')
    endDate = startDate + timedelta(hours=1)
    #Determine the timezone
    timezoneStr = dateString.split("(")[1]
    if timezoneStr[-1] == ' ': #Remove trailing space if present
        timezoneStr = timezoneStr[:-1]
    #Convert email format timezone to Google format timezoneStr
    TimezoneDictionary = {
        'Eastern Time': 'America/New_York',
        'Central Time': 'America/Chicago',
        'Alaska': 'America/Anchorage',
        'Amsterdam, Berlin, Bern, Rome, Stockho': 'Europe/Rome',
        'Greenwich Mean Time : London': 'Etc/GMT'
    }
    timezone = TimezoneDictionary.get(timezoneStr, 'Unknown Timezone')
    if debugging:
        print("Group Name:\t"+groupName+"\nZoom Link:\t"+zoomLink+"\nStart Date:\t"+startDate.strftime("%b %d, %Y  %I:%M %p")+"\nEnd Date:\t"+endDate.strftime("%b %d, %Y  %I:%M %p")+"\nTimezone:\t"+timezone)
    event = {
        'summary': groupName,
        'location': zoomLink,
        'description': zoomLink,
        'start': {
            'dateTime': startDate,
            'timeZone': timezone,
        },
        'end': {
            'dateTime': endDate,
            'timeZone': timezone,
        },
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'popup', 'minutes':10},
            ],
        },
    }
    try:
        event = service.events().insert(calendarID='primary', body=event).execute()
    except:
        if debugging:
            print("Error posting the event to Google Calendar")
        e = sys.exc_info()[1]
        input=" - <!channel> EVENT ERROR: "
        error=str(e)
        error=re.sub("<|>", "", error)
        error= error.split("returned",1)[1]
        error= error.split("\"")[1]
        output=groupName+input+error
        data = '{"text":"%s"}' % (output)
        print(data)
        #response = requests.post('https://hooks.slack.com/services/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', headers=headers, data=data)
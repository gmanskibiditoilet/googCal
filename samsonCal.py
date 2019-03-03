#!/usr/bin/env python3

import os 

debugging = True

#Load all the email files into memory
messages = os.listdir("/etc/googCal/mail")
for message in messages:
    try:
        f=open(message, 'r')
        lines = f.readlines()
    except:
        if debugging:
            print("Something went wrong opening the file")
    finally:
        f.close()
    #Get the Subject Line
    #Loop through the lines looking for the info.
    for line in lines:
        


#Check if this is an invitation message


#Get The Meeting Name


#Get the zoom Link


#Get the Date and Time


#Get the Timezone


#Check for missing info (Invalid Email)


#Deal with Time



#Call the API
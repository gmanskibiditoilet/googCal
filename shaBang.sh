#!/bin/bash

/usr/bin/fetchmail 2> /home/rhys/error.txt
if grep -q SSL /home/rhys/error.txt;
then
	sudo ifconfig wlan0 down
	sleep 1
	sudo ifconfig wlan0 up
	sleep 30
	/usr/bin/fetchmail
fi

cd /etc/googleCalendar/
sleep 3
bash /etc/googleCalendar/updateCal.sh

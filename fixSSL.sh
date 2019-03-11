#!/bin/bash

sudo ifconfig wlan0 down
sleep  5
sudo ifconfig wlan0 up
sleep 30
/usr/bin/fetchmail

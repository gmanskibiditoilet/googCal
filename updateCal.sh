#!/bin/bash

#Build an array of the email files
array=()
while IFS=  read -r -d $'\0'; do
    array+=("$REPLY")
done < <(find '/etc/googleCalendar/mail' -iname "*msg*" -not -path "*.grab*" -print0)
#printf '%s\n' "${array[@]}" #Debugging - Print out contents of array

#Begin Catching the specific groups
#Begin the Loop:
arrayLength=${#array[@]}
for (( i=0; i<$arrayLength; i++ ))
do
	thisFileName=${array[$i]}
	#Get the subject line
	subject=$(grep "Subject: " < ${thisFileName})
	#Check if this is an invitation message
	if [[ $subject == *"Your Invitation to Join the Samson Society Group"* ]]
	then
		meetingNameInProg=${subject%:*}
		meetingName=${meetingNameInProg:9}
		paragraph=$(grep http < ${thisFileName})
#		echo $paragraph;echo
		paragraph=${paragraph##*href=\'} #delete everthing infront of and including the last instance of href='
#		echo $paragraph;echo
		joinLink=${paragraph%%\'*} #delete everyting after and including the first '
#		echo $joinLink
		curl -X POST -H 'Content-type: application/json' --data '{"text":"INVITATION to '"$meetingName"' in mailbox - Click the link to accept: '"$joinLink"' - To make this message stop see directions at https://bit.ly/2DoC7gA"}' https://hooks.slack.com/services/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
		break
	fi
	#Check for each group

	if [[ $subject == *"Invitation"* ]]
	then
		#Get the meeting name
		meetingNameInProg=${subject%:*}
		meetingName=${meetingNameInProg:9}
		#get the zoom link
		zoomLine=$(grep "zoom" < ${thisFileName})
		zoomLinkInProg=${zoomLine##*href=\'} #delete everthing infront of and including the last instance of href='
		zoomLink=${zoomLinkInProg%%\'*} #delete everyting after and including the first '
		#Get the date and time
		dateOfEvent=$(cat $thisFileName | grep -E '[a-z|A-Z]{3} [0-9]{2}, [0-9]{4}' -o)
		timeOfEvent=$(cat $thisFileName | grep -E '[0-9]{2}:[0-9]{2} [A|P]M' -o)
		#get the timezone
		timeZone="Undefined"
		#check for Eastern Time
		check=$(cat $thisFileName | grep 'Eastern Time' -o)
		if [[ $check == "Eastern Time" ]]
		then
			timeZone='America/New_York'
		fi
		#check for Central Time
		check=$(cat $thisFileName | grep 'Central Time' -o)
                if [[ $check == "Central Time" ]]
                then
                        timeZone='America/Chicago'
                fi
                #check for Alaska Time
                check=$(cat $thisFileName | grep 'Alaska' -o)
                if [[ $check == *"Alaska"* ]]
                then
                        timeZone='America/Anchorage'
                fi
                #check for Rome Time
                check=$(cat $thisFileName | grep 'Rome' -o)
                if [[ $check == "Rome" ]]
                then
                        timeZone='Europe/Rome'
                fi
		#check  for GMT
		check=$(cat $thisFileName | grep 'Greenwich' -o)
		if [[ $check == "Greenwich" ]]
		then
			timeZone="Etc/GMT"
		fi
		#echo $dateOfEvent #Debugging
		#echo $timeOfEvent #Debugging
		#Validate Info
		if [ -z "$zoomLink" ]
		then
			rm $thisFileName
			break
		fi
		if [ -z "$dateOfEvent" ]
		then
			rm $thisFileName
			break
		fi

		#Get Time Strings

		StartDate=$dateOfEvent
		StartTime=$timeOfEvent

		#Retrieve the Day and Year
		dayOut=${StartDate:4:2}
		yearOut=${StartDate:8:4}

		#Convert Mmm to MM
		month=${StartDate:0:3}
		#echo $month
		case $month in
		Jan)
		  monthOut='01'
		  daysInMonth=31;;
		Feb)
		  monthOut='02'
		  remainder=$(($yearOut % 4))
		  if [ "$remainder" -eq 0 ]
		  then
		    divisible4=1
		  else
		    divisible4=0
		  fi
		  remainder=$(($yearOut % 100))
		  if [ "$remainder" -eq 0 ]
		  then
		    divisible100=1
		  else
		    divisible100=0
		  fi
		  remainder=$(($yearOut % 400))
		  if [ "$remainder" -eq 0 ]
		  then
	  	  divisible400=1
		  else
		    divisible400=0
		  fi
		  if [[ $divisible4 -eq 0 ]]
		  then
		    daysInMonth=28
		  fi
		  if [[ $divisible4 -eq 1 ]] && [[ $divisible100 -eq 0 ]]
		  then
		    daysInMonth=29
		  fi
		  if [[ $divisible4 -eq 1 ]] && [[ $divisible100 -eq 1 ]] && [[ $divisible400 -eq 0 ]]
		  then
		    #not a leap year
		    daysInMonth=28
		  fi
		  if [[ $divisible4 -eq 1 ]] && [[ $divisible100 -eq 1 ]] && [[ $divisible400 -eq 1 ]]
		  then
		    #is a leap year
		    daysInMonth=29
		  fi
		  ;;
		Mar)
		  monthOut='03'
		  daysInMonth=31;;
		Apr)
		  monthOut='04'
		  daysInMonth=30;;
		May)
		  monthOut='05'
		  daysInMonth=31;;
		Jun)
		  monthOut='06'
		  daysInMonth=30;;
		Jul)
		  monthOut='07'
		  daysInMonth=31;;
		Aug)
		  monthOut='08'
		  daysInMonth=31;;
		Sep)
		  monthOut='09'
		  daysInMonth=30;;
		Oct)
		  monthOut='10'
		  daysInMonth=31;;
		Nov)
		  monthOut='11'
		  daysInMonth=30;;
		Dec)
		  monthOut='12'
		  daysInMonth=31;;
		esac #put the leading 0 back if needed
	        #if [[ $dayOut -lt 10 ]]
	        #then
	        #        echo $dayOut
		#	dayOut="0$dayOut"
	        #fi
		 #put the leading 0 back if needed
#	        if [[ $dayOut -lt 10 ]]
#	        then
#	                dayOut="0$dayOut"
#	        fi


		#Build Date Output String
		dateOutput="$yearOut-$monthOut-$dayOut"

		#Convert time to 24 Hour
		aMPM=${StartTime:6:2}
		hour=${StartTime:0:2}
		min=${StartTime:3:2}
		if [ $aMPM == "PM" ]
		then
			#echo "The Time is PM"
			tempFirstDigit=${hour:0:1}
			if [[ $tempFirstDigit == '0' ]]
			then
				#echo "First Digit is 0"
				hour=${hour:1:1}
			fi
			hour=$((12+$hour))
		fi

		if [ $hour == 12 ]
		then
			#it was actually 12 AM and we need to reset to 00:00
			hour=0
		fi
		#check for 12 noon and midnight
		if [ $hour == 24 ]
		then
			#it was actually 12 PM and we need to reset to 12:00
			hour=12
		fi

		#Build Time Output String
		startTimeOutput="T$hour:$min:00"
		#remove leading 0 to prepare for math
		tempFirstDigit=${hour:0:1}
		if [[ $tempFirstDigit == '0' ]]
		then
			#echo "First Digit is 0"
			hour=${hour:1:1}
		fi
		#Add one to hours to create the end time
		hour=$(($hour+1))
		#put the leading 0 back if hour is less than 10
		if [[ $hour -lt 10 ]]
		then
			#echo "hour is less than 10"
			hour="0$hour"
		fi
		startDate="$dateOutput$startTimeOutput"
		#remove leading 0 to prepare for math
                tempFirstDigit=${hour:0:1}
                if [[ $tempFirstDigit == '0' ]]
                then
                        #echo "First Digit is 0"
                        hour=${hour:1:1}
                fi
		#make sure we didn't cross midnight
		if [[ $hour -eq 24 ]]
		then
			hour="00" #reset the hours
			#add one to days
			if [[ ${dayOut:0:1} -eq 0 ]] #remove leading 0 if present
			then
				#remove the 0
				dayOut=${dayOut:1:1}
			fi
			dayOut=$(($dayOut+1)) #add one to the date
			#put the leading 0 back if needed
			if [[ $dayOut -lt 10 ]]
			then
#				echo $dayOut
				dayOut="0$dayOut"
			fi
			#make sure we didn't just cross months... I hate math with time
			if [[ $dayOut -gt $daysInMonth ]]
			then
				if [[ ${monthOut:0:1} -eq 0 ]] #remove leading 0 if present
		        	then
		                	#remove the 0
		                	monthOut=${monthOut:1:1}
		        	fi
				monthOut=$((monthOut+1))
				dayOut='01'
				#since we just added one to the month we better make sure we didn't cross new years
				if [[ $monthOut -eq 13 ]]
				then
					#Happy New Year!!! FML
					monthOut=1
					yearOut=$(($yearOut+1))
				fi
				#put the leading 0 back if needed
				if [[ $monthOut -lt 10 ]]
		                then
		                        monthOut="0$monthOut"
		                fi
			#else
				#echo "no month change"
			fi
			 #put the leading 0 back if hour is less than 10
                	if [[ $hour -lt 10 ]]
               		then
                        	#echo "hour is less than 10"
                	        hour="0$hour"
        	        fi
	                startDate="$dateOutput$startTimeOutput"

			dateOutput="$yearOut-$monthOut-$dayOut"
		fi
		endTimeOutput="T$hour:$min:00"
		#echo $timeOutput
		#Build Output Sting
		endDate="$dateOutput$endTimeOutput"

#		echo "Meeting Name: $meetingName" #Debugging
#		echo "Zoom Link: $zoomLink" #Debugging
#		echo "Start Date/Time: $startDate"
#		echo "End Date/Time: $endDate"
#		echo "Time Zone: $timeZone"


		#Call the API
		link=$(python3 /etc/googleCalendar/createEvent.py "${meetingName}" "${zoomLink}" "${startDate}" "${endDate}" "${timeZone}")
		echo $link
		rm $thisFileName
	fi

done

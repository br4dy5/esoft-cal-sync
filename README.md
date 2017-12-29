# esoft-cal-sync
Synchronizes eSoft Planner events with Google Calendar

## Acquire Google API Credentials
Follow instructions here: https://console.developers.google.com/apis/credentials?project=api-project-1018300270691
This should ultimately result in you storing a client_secret.json file in your working directory. 

## Acquire eSoft Credentials
You will need your eSoft:
* username
* password
* client key
* access key

You will need to run Google Inspect (Ctrl+Shift+i) while you manually login to eSoft. In Inspect, Open the Network tab and proceed to login. Afterward, select the "login.php", probably at the top of the list. In the "Headers" pane, scroll to the bottom under the "Form Data" section. You will see the required credentials. Yes, they were passed in cleartext. 

Add these values following the respective = sign in the config.ini file and make sure it's saved in your working directory. 

## Installation
* Acquire Google API Credentials (see above)
* Acquire eSoft Credentials (see above)
* Update config.ini file with eSoft creds
* pip install -r requirements.txt

## Usage

esoft-cal-sync.py

## Customization

No parameters need to be passed. Account info is provided through config.ini file. Other values can be revised within script which are currently hard-coded, such as:
* Number of months in future to sync (Line 244)
* Event Details (Subject: Line 213, Location: Line 214, Reminders: 231-232)

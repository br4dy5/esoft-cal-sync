# esoft-cal-sync
Synchronizes eSoft Planner events with Google Calendar

## Acquire Google API Credentials
Follow instructions here: https://console.developers.google.com/apis/credentials?project=api-project-1018300270691
This should ultimately result in you storing a client_secret.json file in your working directory. Note, dependent libraries/requirements will also be installed during these steps.

## Acquire eSoft Credentials
You will need your eSoft:
* username
* password
* client key
* access key

You will need to run Google Inspect (Ctrl+Shift+i) while you manually login to eSoft. In Inspect, Open the Network tab and proceed to login. Afterward, select the "login.php", probably at the top of the list. In the "Headers" pane, scroll to the bottom under the "Form Data" section. You will see the required credentials. Yes, they were passed in cleartext. 

Add these values following the respective = sign in the config.ini file and make sure it's saved in your working directory. 

##Usage

esoft-cal-sync.py

No parameters required. 

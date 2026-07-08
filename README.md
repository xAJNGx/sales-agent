Python quickstart

https://developers.google.com/workspace/calendar/api/quickstart/python


Go to the Google Cloud Console.
Select your project.
Go to IAM & Admin → Service Accounts.
Create a service account (or select an existing one).
Open the Keys tab.
Click Add Key → Create new key → JSON.
Download the JSON.
Point settings.google_service_account_json to that file.

Create new calendar 
Open your personal Google Calendar:

Google Calendar
Settings
Settings for newly created  calendars
Share with specific people or groups
Add your service account email
Note to add attendes need 
need Google Calendar invitation emails to be sent automatically, then you must use:

Google Workspace (not a personal Gmail account)
Domain-Wide Delegation enabled on the service account
Impersonation of a Workspace user via:
# epicare-admin (school project)
Admin Pages/Dashboards + Login/Register Pages for epicare [a webapp for persons with intellectual disabilities that suffer from epilepsy]

Template used is the Mantis Bootstrap 5 Admin Template from CodedThemes.

## Features currently completed:
- login/logout
- register
- forgot password mail reset
- user profile (pfp/username) update
- dashboard displays page views by user type (PWID, Caretaker & Admin)
- dashboard displays user count comparison between PWIDs and Caretakers
- dashboard displays total page view count for the year and total user count
- added table for the PWID & Caretaker page with export to csv, excel and print option
- Delete account

## Dependencies:
- flask
- flask_mail
- python-magic-bin
- itsdangerous
- python-dotenv
- Werkzeug  
(may be more that i missed)

## Notes:
#### Make sure to have a .env file with the following format:
MAIL_SERVER=  
MAIL_PORT=587  
MAIL_USE_TLS=True  
MAIL_USERNAME=  
MAIL_PASSWORD=  
MAIL_DEFAULT_SENDER=  

#### Create a file 'page_views.csv'  
timestamp,user_type --> put this in the first row of the file


Note: This repository was recently rebuilt from a working backup.
All current code reflects the latest working version of the project.

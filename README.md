# Habit_Tracker

## A simple CLI app to track daily and weekly habits, monitor streaks and analise progress.

This application is the product of the OOFPP project where I was assigned to create a habit tracking app.

## Installation and setup instructions

first install postgresql from the internet https://get.enterprisedb.com/postgresql/postgresql-17.6-1-windows-x64.exe
follow the prompts of the install wizard
The promts will ask for a password of the superuser (postgres) enter 'warren'
then choose the port 5432
choose the default locale location
complete the install and go int pgAdmin 4
Right click on the Servers cluster and click on register and then server
Name the server MyServer and on the top there are headings. Click on connection and add 'localhost' to the host name, change the password to 'warren'.
After the server has been created a superuser must be created: right click 'MyServer' and click on create then login/group role. Under general give the name of 'tutor' under definition enter 'warren' as the password and under privileges toggle Superuser? on, and save the creation.
now that the setup is complete
go into bash a bash terminal
make sure python is installed v3.14.0 whould work best
git should also be installed and linked to the specific ide
Install psycopg2 (pip install psycopg2)
git clone https://github.com/WarrenOlckers/Habit_Tracker.git

to create the databases run:
python create_db.py for the application database and
python create_test_db.py for the test database
to run the test file: pytest habits_test.py

to start with the main application use python Habit_Tracker2.py -h 
for a list of the commands the user can use
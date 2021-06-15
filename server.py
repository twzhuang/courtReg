from flask import Flask, render_template, redirect, request, session, flash
from mysqlconnection import connectToMySQL
from helper import court_is_full, generate_court
import sys
# from flask_bcrypt import Bcrypt
import re
from datetime import datetime

app = Flask(__name__)
# bcrypt = Bcrypt(app)

app.secret_key = "I am a secret key"

db = "ebc_db"

'''
To Do That I can remember:
1. Need to add timer/clock
2. make html for all courts 
3. style 
4. reset database at a certain time
5. create function that allows admin to reserve court time
6. add court html to admin page and add button next to each name that removes it
7. create admin login check to get to admin page
8. add flash messages to html
'''
"""
information about table: Table is called users and has 4 values. 
first value is an ID (int) for future possible use, 
second value is name(varchar45), 
third value is pin(int), 
fourth value is a"boolean" type (TinyInt) name of column is "onCourt" 
This value is 0 by default and 0 means user is not on a court 
and 1 is when they are on a court. 
Thinking about just changing this value to an int that 
says what court they are currently on but am too lazy currently
"""

num_courts = 8
courts_test = {"court{}".format(num): generate_court() for num in range(1, num_courts+1)}
# print("========== DYNAMICALLY GENERATE COURTS: ========= {}".format(courts_test), file=sys.stderr)

# Dictionary to store all courts and each court is a list of names
courts = {
    "court1": [],
    "court2": [],
    "court3": [],
    "court4": [],
    "court5": [],
    "court6": [],
    "court7": [],
    "court8": [],
}

# This chunk resets all players to not on a court when program starts.
mysql = connectToMySQL(db)
query = "update ebc_db.users set onCourt=0"
mysql.query_db(query)

print('======== COURTS ON STARTUP ========= {}'.format(courts), file=sys.stderr)


@app.route("/")
def main():
    names_of_users = []  # list of users not on a court
    users_to_remove = []  # list of users on a court

    mysql = connectToMySQL(db)  # this is to create list of people not on a court
    query = "Select * FROM ebc_db.users where onCourt = 0;"
    users = mysql.query_db(query)

    mysql = connectToMySQL(db)  # this is to create list of people on a court
    query = "Select first_name FROM ebc_db.users where onCourt = 1;"
    users_on_court = mysql.query_db(query)
    print("========= USERS CURRENTLY ON A COURT FROM INDEX =========== {}".format(users_on_court), file=sys.stderr)

    for user in users:  # makes list of people not on court
        names_of_users.append(user['first_name'])

    for person in users_on_court:  # makes list of people that can removed
        users_to_remove.append(person['first_name'])
    # print("========== COURTS: ========== {}".format(courts_test), file=sys.stderr)
    return render_template('index.html', onCourtUsers=users_to_remove, names_of_users=names_of_users, courts=courts, courts_test=courts_test)


@app.route("/admin")
def admin():
    # add admin login check
    return render_template('admin.html')


# @app.route("/adminlogin", methods=["POST"])
# def adminlogin():

@app.route("/removeUserFromCourt", methods=["POST"])
def remove_user_from_court():
    # checks to see if pin entered matches pin in database
    # if pin matches it goes through courts dictionary and removes name from list and sets onCourt value to 0
    pin_entered = int(request.form['userPinRemove'])
    name_selected = request.form['personNameRemove']
    mysql = connectToMySQL(db)
    query = "Select * FROM ebc_db.users where first_name = " + "'" + name_selected + "'" + ";"
    user = mysql.query_db(query)
    is_valid = True

    if pin_entered < 1:
        flash("This field is required", "userPinAdd")
        is_valid = False
    elif pin_entered != user[0]['pin']:
        flash("Incorrect Pin")
        is_valid = False
    if not is_valid:
        return redirect("/")
    else:
        for court_num, court in courts_test.items():
            for current_or_next, court_info in court.items():
                if name_selected in court_info['players']:
                    court_info['players'].remove(name_selected)
                    mysql = connectToMySQL(db)
                    query = "update ebc_db.users set onCourt=0 where first_name = " + "'" + name_selected + "'" + ";"
                    mysql.query_db(query)
                    print('======== COURTS AFTER REMOVING USER ========= {}'.format(courts), file=sys.stderr)

        # for court in courts:
        #     for person in courts[court]:
        #         print('PERSON: {}'.format(person), file=sys.stderr)
        #         if person == name_selected:
        #             courts[court].remove(person)
        #             mysql = connectToMySQL(db)
        #             query = "update ebc_db.users set onCourt=0 where first_name = " + "'" + person + "'" + ";"
        #             mysql.query_db(query)
        #             print('======== COURTS AFTER REMOVING USER ========= {}'.format(courts), file=sys.stderr)
    return redirect("/")


@app.route("/addUserToCourt", methods=["POST"])
def add_user_to_court():
    """
    Function adds user to a court after checking to see if the correct pin is entered for the user. 
    If it does, it changes user's onCourt value to 0 and adds their name to courts dictionary
    """
    is_valid = True

    # NOTE: Can this be removed?
    mysql = connectToMySQL(db)
    query = "SELECT * FROM ebc_db.users"
    users = mysql.query_db(query)

    pin_entered = int(request.form['userPinAdd'])
    name_selected = request.form['personNameAdd']
    court_entered = request.form['courtNum']
    current_or_next = request.form['current_or_next']
    selected_court_info = courts_test[court_entered]
    mysql = connectToMySQL(db)
    query = "SELECT * FROM ebc_db.users where first_name = " + "'" + name_selected + "'" + ";"
    user = mysql.query_db(query)

    if pin_entered < 1:
        flash("This field is required", "userPinAdd")
        is_valid = False
    elif pin_entered != user[0]['pin']:
        flash("Incorrect Pin")
        is_valid = False
    else:
        # Check if court is currently empty
        # If yes, then user should not be able to select 'next on'
        if (not selected_court_info['current']['players']) and current_or_next == 'next':
            print('Selected court info: {}'.format(selected_court_info), file=sys.stderr)
            print("Cannot add to 'next on' court if court is currently empty", file=sys.stderr)
            flash("Court is currently empty. Please add to current court")
            is_valid = False
        else:
            # check if court is full before adding player to court
            if court_is_full(current_or_next, courts_test[court_entered]):
                print("Court is full", file=sys.stderr)
                flash("This court is currently full. Please choose to be next on the court or choose another court.")
                is_valid = False
            else:
                # if court is empty and court selection is current, add a start time
                if current_or_next == 'current' and not selected_court_info['current']['players']:
                    selected_court_info['current']['start_time'] = datetime.now().strftime("%H:%M:%S")
                    print("SELECTED COURT INFO: {}".format(selected_court_info), file=sys.stderr)
                # Add player to court
                selected_court_info[current_or_next]['players'].append(name_selected)

                mysql = connectToMySQL(db)
                query = "update ebc_db.users set onCourt=1 where first_name = " + "'" + name_selected + "'" + ";"
                mysql.query_db(query)
                print('======== COURTS AFTER ADDING USER ========= {}'.format(courts), file=sys.stderr)
    if not is_valid:
        return redirect("/")

    return redirect("/")


@app.route("/addUser", methods=["POST"])
def add_user():
    """
    This is an admin function to add users to the database.
    Meant for front desk person to check-in people with a name and pin.
    Function checks to see if entered name is unique. pin can be any number
    """
    is_valid = True
    # name not entered
    if len(request.form['addName']) < 1:
        flash("This field is required", "addName")
        is_valid = False
    # name format doesn't match
    elif not (request.form['addName'].isalpha()) or len(request.form['addName']) < 2:
        flash("Name must contain at least two letters and contain only letters", "addName")
        is_valid = False

    # pin not entered
    if len(request.form['userPin']) < 1:
        flash("This field is required", "userPin")
        is_valid = False
    # pin format doesn't match
    elif not (request.form['userPin'].isnumeric()):
        flash("Pin must be a number", "userPin")
        is_valid = False
    else:
        print("CHECKING IF USER ALREADY EXISTS", file=sys.stderr)
        mysql = connectToMySQL(db)
        query = "Select * FROM users WHERE first_name = %(first_name)s;"
        data = {'first_name': request.form['addName']}
        existing_user = mysql.query_db(query, data)
        if existing_user:
            print("User Exists", file=sys.stderr)
            flash("The name you entered has already been taken. Please enter another one.", "email")
            is_valid = False

    if not is_valid:
        return redirect('/admin')
    else:
        print("CREATING NEW USER", file=sys.stderr)
        mysql2 = connectToMySQL(db)
        query = "INSERT INTO USERS(first_name, pin) VALUES (%(un)s, %(up)s)"
        data = {
            'un': request.form['addName'],
            'up': request.form['userPin']
        }
        user = mysql2.query_db(query, data)
        print("USER ADDED TO DB: {}".format(user), file=sys.stderr)
        return redirect("/admin")


# @app.route("/userRegister", methods=["POST"])
# def register():
#    is_valid = True
#    iflen(request.form[''])

if __name__ == '__main__':
    app.run(debug=True)

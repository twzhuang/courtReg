from flask import Flask, render_template, redirect, request, session, flash
from mysqlconnection import connectToMySQL
from helper import (court_is_full, generate_court, remove_user_from_db, calculate_end_time, move_players_on_current_court)
import sys
from datetime import datetime
import logging

app = Flask(__name__)


app.secret_key = "I am a secret key"

db = "ebc_db"


'''
To Do That I can remember:
1. create function that allows admin to reserve court time
2. update user function
3. remove user from database function
'''


num_courts = 8
# Dictionary to store all courts and each court is a list of names
courts_test = {"court{}".format(num): generate_court() for num in range(1, num_courts+1)}


# This chunk resets all players to not on a court when program starts.
mysql = connectToMySQL(db)
query = "update ebc_db.users set onCourt=0"
mysql.query_db(query)


@app.route("/")
def main():
    print("====================== SESSION LINE 57 ====================: {}".format(session), file=sys.stderr)
    names_of_users = []  # list of users not on a court
    users_to_remove = []  # list of users on a court

    mysql = connectToMySQL(db)  # this is to create list of people not on a court
    query = "Select * FROM ebc_db.users where onCourt = 0 ORDER BY first_name;"
    users = mysql.query_db(query)

    mysql = connectToMySQL(db)  # this is to create list of people on a court
    query = "Select first_name FROM ebc_db.users where onCourt = 1 ORDER BY first_name;"
    users_on_court = mysql.query_db(query)

    for user in users:  # makes list of people not on court
        names_of_users.append(user['first_name'])

    for person in users_on_court:  # makes list of people that can removed
        users_to_remove.append(person['first_name'])
    return render_template('index.html', onCourtUsers=users_to_remove, names_of_users=names_of_users, courts_test=courts_test)


@app.route("/clearUserTable")
def clear_user_table():
    if not 'loggedin' in session:
        session['loggedin'] = False
        return redirect('/loginpage')
    mysql = connectToMySQL(db)
    query = "DELETE FROM users"
    mysql.query_db(query)
    global courts_test
    courts_test = {"court{}".format(num): generate_court() for num in range(1, num_courts+1)}
    return redirect("/admin")


@app.route("/admin")
def admin():
    print("====================== SESSION ====================: {}".format(session), file=sys.stderr)
    # add admin login check
    if not 'loggedin' in session:
        print("================INSIDE IF STATEMENT=============", file=sys.stderr)
        session['loggedin'] = False
        return redirect('/loginpage')
    elif session['loggedin'] == True:
        names_of_users = []  # list of users not on a court
        users_to_remove = []  # list of users on a court
        all_users = []

        mysql = connectToMySQL(db)  # this is to create list of people not on a court
        query = "Select * FROM ebc_db.users;"
        all_users_query = mysql.query_db(query)

        mysql = connectToMySQL(db)  # this is to create list of people not on a court
        query = "Select * FROM ebc_db.users where onCourt = 0;"
        users = mysql.query_db(query)

        mysql = connectToMySQL(db)  # this is to create list of people on a court
        query = "Select first_name FROM ebc_db.users where onCourt = 1;"
        users_on_court = mysql.query_db(query)

        for user in users:  # makes list of people not on court
            names_of_users.append(user['first_name'])

        for person in users_on_court:  # makes list of people that can removed
            users_to_remove.append(person['first_name'])
        
        for user in all_users_query:
            all_users.append(user['first_name'])

        return render_template('admin.html', onCourtUsers=users_to_remove, names_of_users=names_of_users, courts_test=courts_test, all_users=all_users)
    else:
        return redirect('/loginpage')

@app.route("/loginpage")
def login_page():
    return render_template('login.html')


@app.route("/login", methods=["POST"])
def login():
    mysql = connectToMySQL(db)
    query = "SELECT * FROM admins WHERE username = %(username)s;"
    data = {'username': request.form['username']}
    existing_user = mysql.query_db(query, data)

    if len(existing_user) > 0:
        # check if password entered matches password in database
        if existing_user[0]['password'] == request.form['password']:
            print(session)
            print("password found")
            session['loggedin'] = True
            return redirect('/admin')
        else:
            print("password incorrect")
            flash("Password incorrect. Please try again.", "pw")
            return redirect('/loginpage')
    else:
        flash("Username not found. Please try again.","loginemail")
        return redirect("/loginpage")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/loginpage")


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
                    remove_user_from_db(db, name_selected)

                    # check if court selection is current
                    if current_or_next == "current":
                        # if not empty update end time
                        if court_info["players"]:
                            court_info['end_time'] = calculate_end_time(
                                len(court_info['players']),
                                datetime.strptime(court_info['start_time'], "%I:%M %p"),
                            )
                        # if empty, reset court and move next on players
                        else:
                            move_players_on_current_court(courts_test[court_num])

    return redirect("/")


@app.route("/adminRemove", methods=["POST"])
def admin_remove():
    name_selected = request.form["player_to_remove"]
    for court_num, court in courts_test.items():
        for current_or_next, court_info in court.items():
            if name_selected in court_info['players']:
                court_info['players'].remove(name_selected)
                remove_user_from_db(db, name_selected)

                if current_or_next == "current":
                    # if not empty update end time
                    if court_info["players"]:
                        court_info['end_time'] = calculate_end_time(
                            len(court_info['players']),
                            datetime.strptime(court_info['start_time'], "%I:%M %p"),
                        )
                    # if empty, reset court and move next on players
                    else:
                        move_players_on_current_court(courts_test[court_num])
    return redirect("/admin")

@app.route("/updateUser", methods=["POST"])
def update_user():
    user_selected = request.form['userToUpdate']
    newPin = request.form['userPin']
    is_valid = True
    # pin not entered
    if len(request.form['userPin']) < 1:
        flash("Pin is required", "userPin")
        is_valid = False
    # pin format doesn't match
    elif not (request.form['userPin'].isnumeric()):
        flash("Pin must be a number", "userPin")
        is_valid = False
    if not is_valid:
        return redirect('/admin')

    mysql = connectToMySQL(db)
    query = "UPDATE users set pin = " + "'" + newPin + "'" + " WHERE first_name = " + "'" + user_selected + "'" + ";"
    mysql.query_db(query)
    return redirect('/admin')

@app.route("/removeUserFromSystem", methods=["POST"])
def remove_user_from_database():
    user_selected = request.form['userToUpdate']
    for court_num, court in courts_test.items():
        for current_or_next, court_info in court.items():
            if user_selected in court_info['players']:
                court_info['players'].remove(user_selected)
    mysql = connectToMySQL(db)
    query = "DELETE from users WHERE first_name = " + "'" + user_selected + "';"  
    mysql.query_db(query)
    return redirect('/admin')

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
    current_court = selected_court_info["current"]

    mysql = connectToMySQL(db)
    query = "SELECT * FROM ebc_db.users where first_name = " + "'" + name_selected + "'" + ";"
    user = mysql.query_db(query)
    print("USER {}".format(user), file=sys.stderr)

    if pin_entered < 1:
        flash("Pin is required", "userPinAdd")
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
                start_time = datetime.now()
                # if court is empty and court selection is current, add a start time and end time
                if current_or_next == 'current':
                    if not current_court['players']:
                        current_court['start_time'] = start_time.strftime("%I:%M %p").lstrip("0")

                    # Calculate end time for court depending on number of players
                    current_court['end_time'] = calculate_end_time(
                        len(current_court["players"]) + 1,
                        start_time
                    )

                # Add player to court
                selected_court_info[current_or_next]['players'].append(name_selected)

                mysql = connectToMySQL(db)
                query = "update ebc_db.users set onCourt=1 where first_name = " + "'" + name_selected + "'" + ";"
                mysql.query_db(query)
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
        flash("Name is required", "addName")
        is_valid = False
    # name format doesn't match
    elif not (request.form['addName'].isalpha()) or len(request.form['addName']) < 2:
        flash("Name must contain at least two letters and contain only letters", "addName")
        is_valid = False

    # pin not entered
    if len(request.form['userPin']) < 1:
        flash("Pin is required", "userPin")
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


@app.route("/updateCourt", methods=["POST"])
def update_court():
    """
    Receive request from js file when court timer is up to update court
    Move "next on" players onto "current" court
    """
    data = request.get_json()
    court_num = data["court_number"]
    court_info = courts_test["court" + str(court_num)]

    # Remove players from the court in db
    for player in court_info["current"]["players"]:
        remove_user_from_db(db, player)

    # Move "next on" players to "currently on"
    court_info["current"] = court_info["next"]
    court_info["next"] = {
        "start_time": "",
        "end_time": "",
        "players": []
    }

    # Set start time and end time for new players on court
    if court_info["current"]["players"]:
        start_time = datetime.now()
        court_info["current"]["start_time"] = start_time.strftime("%I:%M %p").lstrip("0")
        court_info["current"]["end_time"] = calculate_end_time(
            len(court_info["current"]["players"]),
            start_time,
        )
    return redirect("/")


if __name__ == '__main__':
    app.run(debug=True)

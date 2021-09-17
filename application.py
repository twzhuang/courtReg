from flask import Flask, render_template, redirect, request, session, flash
from mysqlconnection import connectToMySQL
from helper import (court_is_full, generate_court, remove_user_from_db, calculate_end_time, move_players_on_current_court, move_players_on_next_on_list)
import sys
from datetime import datetime
import time
import logging

application = Flask(__name__)


application.secret_key = "I am a secret key"

db = "ebc_schema"
# db = "ebc_db"

# challenge court dictionary
challenge_court = {
    "streak": 0,
    #this will be a list of dictionaries containing two player names
    "listofplayers": [] 
}

num_courts = 8
# Dictionary to store all courts and each court is a list of names
courts_test = {"court{}".format(num): generate_court() for num in range(1, num_courts+1)}


# This chunk resets all players to not on a court when program starts.
mysql = connectToMySQL(db)
query = "update {}.users set onCourt=0".format(db)
mysql.query_db(query)

@application.route("/")
def main():
    if not 'loggedin' in session:
        print("================INSIDE IF STATEMENT=============", file=sys.stderr)
        session['loggedin'] = False
        return redirect('/loginpage')
    if session['loggedin']==False:
        return redirect('/loginpage')
    else:
        print("====================== SESSION LINE 57 ====================: {}".format(session), file=sys.stderr)
        names_of_users = []  # list of users not on a court
        users_to_remove = []  # list of users on a court
        playerslist = [] # list of players on challenge court
        mysql = connectToMySQL(db)  # this is to create list of people not on a court
        query = "Select * FROM {}.users where onCourt = 0 ORDER BY first_name;".format(db)
        users = mysql.query_db(query)

        mysql = connectToMySQL(db)  # this is to create list of people on a court
        query = "Select first_name FROM {}.users where onCourt = 1 ORDER BY first_name;".format(db)
        users_on_court = mysql.query_db(query)

        for pairs in challenge_court["listofplayers"]: #makes list of people on challenge court
            for player in pairs:
                playerslist.append(player)

        for user in users:  # makes list of people not on court
            names_of_users.append(user['first_name'])

        for person in users_on_court:  # makes list of people that can removed
            users_to_remove.append(person['first_name'])
        return render_template('index.html', onCourtUsers=users_to_remove, names_of_users=names_of_users, courts_test=courts_test, playerslist = playerslist, challenge=challenge_court)


@application.route("/clearUserTable")
def clear_user_table():
    if not 'admin' in session:
        session['admin'] = False
        return redirect('/loginpage')
    mysql = connectToMySQL(db)
    query = "DELETE FROM users"
    mysql.query_db(query)
    global courts_test
    courts_test = {"court{}".format(num): generate_court() for num in range(1, num_courts+1)}
    global challenge_court
    challenge_court = {
    "streak": 0,
    "listofplayers": [] 
    }
    return redirect("/admin")

@application.route("/checkin")
def checkinpage():
    if not 'admin' in session:
        session['admin'] = False
        return redirect('/loginpage')    
    if session['admin']==False:
        return redirect('/loginpage')
    else:
        return render_template('addUser.html')
    
@application.route("/admin")
def admin():
    print("====================== SESSION ====================: {}".format(session), file=sys.stderr)
    # add admin login check
    if not 'admin' in session:
        print("================INSIDE IF STATEMENT=============", file=sys.stderr)
        session['admin'] = False
        return redirect('/loginpage')
    elif session['admin'] == True:
        names_of_users = []  # list of users not on a court
        users_to_remove = []  # list of users on a court
        all_users = []

        mysql = connectToMySQL(db)  # this is to create list of people not on a court
        query = "Select * FROM {}.users;".format(db)
        all_users_query = mysql.query_db(query)

        mysql = connectToMySQL(db)  # this is to create list of people not on a court
        query = "Select * FROM {}.users where onCourt = 0;".format(db)
        users = mysql.query_db(query)

        mysql = connectToMySQL(db)  # this is to create list of people on a court
        query = "Select first_name FROM {}.users where onCourt = 1;".format(db)
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

@application.route("/loginpage")
def login_page():
    return render_template('login.html')


@application.route("/login", methods=["POST"])
def login():
    mysql = connectToMySQL(db)
    query = "SELECT * FROM admins WHERE username = %(username)s;".format(db)
    data = {'username': request.form['username']}
    existing_user = mysql.query_db(query, data)

    if len(existing_user) > 0:
        # check if password entered matches password in database
        if existing_user[0]['password'] == request.form['password']:
            print(session)
            print("password found")
            session['loggedin'] = True
            if request.form['username']=='ebcadmin':
                session['admin'] = True
                return redirect('/admin')
            return redirect('/')
        else:
            print("password incorrect")
            flash("Password incorrect. Please try again.", "pw")
            return redirect('/loginpage')
    else:
        flash("Username not found. Please try again.","loginemail")
        return redirect("/loginpage")


@application.route("/logout")
def logout():
    session.clear()
    return redirect("/loginpage")


@application.route("/removeUserFromCourt", methods=["POST"])
def remove_user_from_court():
    print("IN REMOVE ROUTE", file=sys.stderr)
    # checks to see if pin entered matches pin in database
    # if pin matches it goes through courts dictionary and removes name from list and sets onCourt value to 0
    pin_entered = int(request.form['userPinRemove'])
    name_selected = request.form['personNameRemove']
    mysql = connectToMySQL(db)
    query = "SELECT * FROM {}.users where first_name = '{}';".format(db, name_selected)
    user = mysql.query_db(query)
    is_valid = True

    if pin_entered < 1:
        flash("This field is required", "removeerror")
        is_valid = False
    elif pin_entered != user[0]['pin']:
        flash("Incorrect Pin", "removeerror")
        is_valid = False
    if not is_valid:
        return redirect("/")
    else:
        break_loop = False
        for court_num, court in courts_test.items():
            print(f"COURT NUM: {court_num}", file=sys.stderr)
            for current_or_next, court_info in court.items():
                print(f"CURRENT OR NEXT: {current_or_next} COURT INFO: {court_info}", file=sys.stderr)
                if current_or_next != "lastrequesttime" and name_selected in court_info['players']:
                    print("PLAYER FOUND", file=sys.stderr)
                    court_info['players'].remove(name_selected)
                    remove_user_from_db(db, name_selected)

                    # check if court selection is current
                    if current_or_next == "current":
                        # if not empty update end time
                        if court_info["players"]:
                            court_info['end_time'] = calculate_end_time(
                                len(court_info['players']),
                                datetime.strptime(court_info['start_time'], "%I:%M:%S %p"),
                            )
                        # if empty, reset court and move next on players
                        else:
                            move_players_on_current_court(courts_test[court_num])

                    #if next is empty, move next next on to up next        
                    elif current_or_next == "next":
                        if not court_info["players"]:
                            move_players_on_next_on_list(courts_test[court_num])
                    print("BREAKING LOOP", file=sys.stderr)
                    break_loop = True
                    break
                if break_loop:
                    break

    return redirect("/")


@application.route("/adminRemove", methods=["POST"])
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
                            datetime.strptime(court_info['start_time'], "%I:%M:%S %p"),
                        )
                    # if empty, reset court and move next on players
                    else:
                        move_players_on_current_court(courts_test[court_num])

                    #if next is empty, move next next on to up next        
                elif current_or_next == "next":
                    if not court_info["players"]:
                        move_players_on_next_on_list(courts_test[court_num])
    return redirect("/admin")

@application.route("/updateUser", methods=["POST"])
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

@application.route("/removeUserFromSystem", methods=["POST"])
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

@application.route("/addUserToCourt", methods=["POST"])
def add_user_to_court():
    """
    Function adds user to a court after checking to see if the correct pin is entered for the user. 
    If it does, it changes user's onCourt value to 0 and adds their name to courts dictionary
    """
    is_valid = True

    # NOTE: Can this be removed?
    mysql = connectToMySQL(db)
    query = "SELECT * FROM {}.users".format(db)
    users = mysql.query_db(query)

    pin_entered = int(request.form['userPinAdd'])
    name_selected = request.form['personNameAdd']
    court_entered = request.form['courtNum']
    current_or_next = request.form['current_or_next']
    selected_court_info = courts_test[court_entered]
    current_court = selected_court_info["current"]

    mysql = connectToMySQL(db)
    query = "SELECT * FROM {}.users where first_name = '{}';".format(db, name_selected)
    user = mysql.query_db(query)
    print("USER {}".format(user), file=sys.stderr)

    if pin_entered < 1:
        flash("Pin is required", "adderror")
        is_valid = False
    elif pin_entered != user[0]['pin']:
        flash("Incorrect Pin", "adderror")
        is_valid = False
    elif selected_court_info["current"]["reserved"]==True:
        flash("Court is Reserved. Please sign up for another court", "adderror")
        is_valid = False
    else:
        # Check if court is currently empty
        # If yes, then user should not be able to select 'next on'
        if (not selected_court_info['current']['players']) and current_or_next == 'next':
            print('Selected court info: {}'.format(selected_court_info), file=sys.stderr)
            print("Cannot add to 'next on' court if court is currently empty", file=sys.stderr)
            flash("Court is currently empty. Please add to current court", "adderror")
            is_valid = False
        elif (not selected_court_info['next']['players']) and current_or_next == 'nextnext':
            print('Selected court info: {}'.format(selected_court_info), file=sys.stderr)
            print("Cannot add to 'next next on' court if court is currently empty", file=sys.stderr)
            flash("Up Next list is currently empty. Please add to the Up Next list", "adderror")
            is_valid = False
        else:
            # check if court is full before adding player to court
            if court_is_full(current_or_next, courts_test[court_entered]):
                print("Court is full", file=sys.stderr)
                flash("This court is currently full. Please choose to be next on the court or choose another court.", "adderror")
                is_valid = False
            else:
                # if court is empty and court selection is current, add a start time and end time
                if current_or_next == 'current':
                    if not current_court['players']:
                        start_time = datetime.utcnow()
                        current_court['start_time'] = start_time.strftime("%I:%M:%S %p").lstrip("0")

                    # Calculate end time for court depending on number of players
                    current_court['end_time'] = calculate_end_time(
                        len(current_court["players"]) + 1,
                        datetime.strptime(current_court['start_time'], "%I:%M:%S %p")
                    )

                # Add player to court
                selected_court_info[current_or_next]['players'].append(name_selected)

                mysql = connectToMySQL(db)
                query = "update {}.users set onCourt=1 where first_name = '{}';".format(db, name_selected)
                mysql.query_db(query)
    if not is_valid:
        return redirect("/")

    return redirect("/")


@application.route("/addUser", methods=["POST"])
def add_user():
    """
    This is an admin function to add users to the database.
    Meant for front desk person to check-in people with a name and pin.
    Function checks to see if entered name is unique. pin can be any number
    """
    is_valid = True
    # name not entered
    if len(request.form['addName']) < 1:
        flash("Name is required", "checkinerror")
        is_valid = False
    # name format doesn't match
    elif len(request.form['addName']) < 2:
        flash("Name must contain at least two letters", "checkinerror")
        is_valid = False

    # pin not entered
    if len(request.form['userPin']) < 1:
        flash("Pin is required", "checkinerror")
        is_valid = False
    # pin format doesn't match
    elif not (request.form['userPin'].isnumeric()):
        flash("Pin must be a number", "checkinerror")
        is_valid = False
    else:
        print("CHECKING IF USER ALREADY EXISTS", file=sys.stderr)
        mysql = connectToMySQL(db)
        query = "Select * FROM users WHERE first_name = %(first_name)s;"
        data = {'first_name': request.form['addName']}
        existing_user = mysql.query_db(query, data)
        if existing_user:
            print("User Exists", file=sys.stderr)
            flash("The name you entered has already been taken. Please enter another one.", "checkinerror")
            is_valid = False

    if not is_valid:
        return redirect('/checkin')
    else:
        print("CREATING NEW USER", file=sys.stderr)
        mysql2 = connectToMySQL(db)
        query = "INSERT INTO users(first_name, pin) VALUES (%(un)s, %(up)s)"
        data = {
            'un': request.form['addName'],
            'up': request.form['userPin']
        }
        user = mysql2.query_db(query, data)
        flash("You have successfully checked in!", "checkinsuccess")
        print("USER ADDED TO DB: {}".format(user), file=sys.stderr)
        return redirect("/checkin")


@application.route("/updateCourt", methods=["POST"])
def update_court():
    """
    Receive request from js file when court timer is up to update court
    Move "next on" players onto "current" court
    """
    data = request.get_json()
    print(data, file=sys.stderr)
    court_num = data["court_number"]
    court_info = courts_test["court" + str(court_num)]
    print("current end time is " + court_info["current"]["end_time"])
    currenttime = time.time()
    if (currenttime - court_info["lastrequesttime"])<=3:
        return redirect("/")
    if court_info["lastrequesttime"]==0:
        court_info["lastrequesttime"]=currenttime
        print(court_info["lastrequesttime"])
    else:
        court_info["lastrequesttime"]=currenttime
    # Remove players from the court in db
        for player in court_info["current"]["players"]:
            remove_user_from_db(db, player)

        # Move "next on" players to "currently on"
        court_info["current"] = court_info["next"]

        if court_info["nextnext"]:
            court_info['next'] = court_info['nextnext']
            court_info["nextnext"] = {
                "start_time": "",
                "end_time": "",
                "players": [],
                "reserved": False
            }
        else:
            court_info["next"] = {
                "start_time": "",
                "end_time": "",
                "players": [],
                "reserved": False
            }

        # Set start time and end time for new players on court
        if court_info["current"]["players"]:
            start_time = datetime.utcnow()
            court_info["current"]["start_time"] = start_time.strftime("%I:%M:%S %p").lstrip("0")
            court_info["current"]["end_time"] = calculate_end_time(
                len(court_info["current"]["players"]),
                start_time,
            )
        return redirect("/")

# @application.route("/challengecourt")
# def challengecourt():
#     if not 'loggedin' in session:
#         session['loggedin'] = False
#         return redirect('/loginpage')
#     if session['loggedin']==False:
#         return redirect('/loginpage')
#     names_of_users = []  # list of users not on a court
#     playerslist = []
#     mysql = connectToMySQL(db)  # this is to create list of people not on a court
#     query = "Select * FROM {}.users where onCourt = 0 ORDER BY first_name;".format(db)
#     users = mysql.query_db(query)
#     for user in users:  # makes list of people not on court
#         names_of_users.append(user['first_name'])
#     for pairs in challenge_court["listofplayers"]:
#         for player in pairs:
#             playerslist.append(player)
#     return render_template('challenger.html', playerslist = playerslist, names_of_users=names_of_users, challenge=challenge_court)

@application.route("/addtochallengecourt", methods=["POST"])
def addtochallenge():
    player1 = request.form ['player1']
    pin1 = int(request.form['player1pin'])
    player2 = request.form['player2']
    pin2 = int(request.form['player2pin'])
    is_valid = True
    mysql = connectToMySQL(db)
    query = "SELECT * FROM {}.users where first_name = '{}';".format(db, player1)
    player1info = mysql.query_db(query)
    mysql = connectToMySQL(db)
    query = "SELECT * FROM {}.users where first_name = '{}';".format(db, player2)
    player2info = mysql.query_db(query)
    if player1==player2:
        flash("Player 1 and Player 2 names must be different", "challengeerror")
        is_valid = False
    elif pin1 < 1:
        flash("Pin is required for Player 1", "challengeerror")
        is_valid = False
    elif pin1 != player1info[0]['pin']:
        flash("Incorrect Pin for Player 1", "challengeerror")
        is_valid = False
    elif pin2 < 1:
        flash("Pin is required for Player 2", "challengeerror")
        is_valid = False
    elif pin2 != player2info[0]['pin']:
        flash("Incorrect Pin for Player 2", "challengeerror")
        is_valid = False
    else:
        playersToAdd=[player1, player2]
        challenge_court["listofplayers"].append(playersToAdd)
        mysql = connectToMySQL(db)
        query = "update {}.users set onCourt=2 where first_name = '{}';".format(db, player1)
        mysql.query_db(query)
        mysql = connectToMySQL(db)
        query = "update {}.users set onCourt=2 where first_name = '{}';".format(db, player2)
        mysql.query_db(query)
    if not is_valid:
        return redirect("/")
    return redirect('/')

@application.route("/champswon", methods=["POST"])
def champswon():
    is_valid = True
    if len(challenge_court["listofplayers"])<1:
        flash("Please wait for more people to sign up", "challengewinnererror")
        is_valid = False 
    if is_valid == False:
        return redirect('/')   
    else:
        if challenge_court["listofplayers"]:
            mysql = connectToMySQL(db)
            query = "update {}.users set onCourt=0 where first_name = '{}';".format(db, challenge_court["listofplayers"][1][0])
            mysql.query_db(query)
            mysql = connectToMySQL(db)
            query = "update {}.users set onCourt=0 where first_name = '{}';".format(db, challenge_court["listofplayers"][1][1])
            mysql.query_db(query)
            challenge_court["listofplayers"].pop(1)
        challenge_court["streak"] = challenge_court["streak"] + 1
    return redirect('/')

@application.route("/challengerswon", methods=["POST"])
def challengerswon():
    is_valid = True
    if len(challenge_court["listofplayers"])<=1:
        flash("Please wait for more people to sign up", "challengewinnererror")
        is_valid = False 
    if is_valid == False:
        return redirect('/') 
    else:
        mysql = connectToMySQL(db)
        query = "update {}.users set onCourt=0 where first_name = '{}';".format(db, challenge_court["listofplayers"][0][0])
        mysql.query_db(query)
        mysql = connectToMySQL(db)
        query = "update {}.users set onCourt=0 where first_name = '{}';".format(db, challenge_court["listofplayers"][0][1])
        mysql.query_db(query)
        challenge_court["streak"] = 1
        challenge_court["listofplayers"].pop(0)
    return redirect('/')

@application.route("/champsretire", methods=["POST"])
def champsretire():
    is_valid = True
    if len(challenge_court["listofplayers"])<1:
        flash("Please wait for more people to sign up", "challengewinnererror")
        is_valid = False 
    if is_valid == False:
        return redirect('/') 
    else:
        mysql = connectToMySQL(db)
        query = "update {}.users set onCourt=0 where first_name = '{}';".format(db, challenge_court["listofplayers"][0][0])
        mysql.query_db(query)
        mysql = connectToMySQL(db)
        query = "update {}.users set onCourt=0 where first_name = '{}';".format(db, challenge_court["listofplayers"][0][1])
        mysql.query_db(query)
        challenge_court["streak"] = 0
        challenge_court["listofplayers"].pop(0)
    return redirect('/')

@application.route("/substituteplayer", methods=["POST"])
def substituteplayer():
    oldplayer = request.form ['oldplayer']
    oldplayerpin = int(request.form['oldplayerpin'])
    newplayer = request.form['newplayer']
    newplayerpin = int(request.form['newplayerpin'])
    is_valid = True
    mysql = connectToMySQL(db)
    query = "SELECT * FROM {}.users where first_name = '{}';".format(db, oldplayer)
    oldplayerinfo = mysql.query_db(query)
    mysql = connectToMySQL(db)
    query = "SELECT * FROM {}.users where first_name = '{}';".format(db, newplayer)
    newplayerinfo = mysql.query_db(query)
    if oldplayerpin < 1:
        flash("Pin is required for Subbed Out Player", "challengesuberror")
        is_valid = False
    elif oldplayerpin != oldplayerinfo[0]['pin']:
        flash("Incorrect Pin for Subbed Out Player", "challengesuberror")
        is_valid = False
    elif newplayerpin < 1:
        flash("Pin is required for Subbed In Player", "challengesuberror")
        is_valid = False
    elif newplayerpin != newplayerinfo[0]['pin']:
        flash("Incorrect Pin for Subbed In Player", "challengesuberror")
        is_valid = False
    if is_valid == False:
        return redirect('/')  
    else:
        for i in range(0, len(challenge_court["listofplayers"])):
            for j in range(0,len(challenge_court["listofplayers"][i])):
                if challenge_court["listofplayers"][i][j]==oldplayer:
                    challenge_court["listofplayers"][i][j]=newplayer
                    mysql = connectToMySQL(db)
                    query = "update {}.users set onCourt=0 where first_name = '{}';".format(db, oldplayer)
                    mysql.query_db(query)
        mysql = connectToMySQL(db)
        query = "update {}.users set onCourt=2 where first_name = '{}';".format(db, newplayer)
        mysql.query_db(query)
    return redirect('/')

@application.route("/deletepair", methods=["POST"])
def deletepair():
    player1 = request.form ['player1']
    pin1 = int(request.form['player1pin'])
    player2 = request.form['player2']
    pin2 = int(request.form['player2pin'])
    is_valid = True
    mysql = connectToMySQL(db)
    query = "SELECT * FROM {}.users where first_name = '{}';".format(db, player1)
    player1info = mysql.query_db(query)
    mysql = connectToMySQL(db)
    query = "SELECT * FROM {}.users where first_name = '{}';".format(db, player2)
    player2info = mysql.query_db(query)
    if player1==player2:
        flash("Player 1 and Player 2 names must be different", "challengedeleteerror")
        is_valid = False
    elif pin1 < 1:
        flash("Pin is required for Player 1", "challengedeleteerror")
        is_valid = False
    elif pin1 != player1info[0]['pin']:
        flash("Incorrect Pin for Player 1", "challengedeleteerror")
        is_valid = False
    elif pin2 < 1:
        flash("Pin is required for Player 2", "challengedeleteerror")
        is_valid = False
    elif pin2 != player2info[0]['pin']:
        flash("Incorrect Pin for Player 2", "challengedeleteerror")
        is_valid = False
    else: 
        for i in range(0, len(challenge_court["listofplayers"])):
            for j in range(0,len(challenge_court["listofplayers"][i])):
                if challenge_court["listofplayers"][i][j] == player1 or challenge_court["listofplayers"][i][j] == player1:
                    if challenge_court["listofplayers"][i][j+1] != player1 and challenge_court["listofplayers"][i][j+1] != player2:
                        flash("Players selected must be partners to be removed.", "challengedeleteerror")
                        return redirect("/")
                    else:
                        mysql = connectToMySQL(db)
                        query = "update {}.users set onCourt=0 where first_name = '{}';".format(db, player1)
                        mysql.query_db(query)
                        mysql = connectToMySQL(db)
                        query = "update {}.users set onCourt=0 where first_name = '{}';".format(db, player2)
                        mysql.query_db(query)
                        challenge_court["listofplayers"].pop(i)
                        if i == 0:
                            challenge_court["streak"] = 0
                        return redirect("/")
    if not is_valid:
        return redirect("/")
    return redirect("/")

@application.route("/reservecourt", methods=["POST"])
def reservecourt():
    court_entered = request.form['courtNum']
    court_info = courts_test[court_entered]
    print("Reserved Court")
    for player in court_info["current"]["players"]:
        remove_user_from_db(db, player)
    for player in court_info["next"]["players"]:
        remove_user_from_db(db, player)
    for player in court_info["nextnext"]["players"]:
        remove_user_from_db(db, player)
    court_info["current"] = {
        "start_time": "",
        "end_time": "",
        "players": [],
        "reserved": True
    }
    court_info["next"] = {
        "start_time": "",
        "end_time": "",
        "players": [],
        "reserved": False
    }
    court_info["nextnext"] = {
        "start_time": "",
        "end_time": "",
        "players": [],
        "reserved": False
    }
    return redirect("/admin")

@application.route("/opencourt", methods=["POST"])
def opencourt():
    court_entered = request.form['courtNum']
    court_info = courts_test[court_entered]
    court_info["current"]["reserved"]=False
    return redirect('/admin')

# @application.route("/addnewlogin")
# def newlogin():
#     mysql = connectToMySQL(db)
#     query = 'insert into admins (username, password) Values ("ebcaccess", "ebc33540");'
#     mysql.query_db(query)
#     print("***************************")
#     return redirect('/')

if __name__ == '__main__':
    application.run(debug=True)

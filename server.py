from flask import Flask, render_template, redirect, request, session, flash
from mysqlconnection import connectToMySQL
#from flask_bcrypt import Bcrypt
import re
from datetime import datetime
app = Flask(__name__)
#bcrypt = Bcrypt(app)

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
#Dictionary to store all courts and each court is a list of names
courts = {
    "court1" : [],
    "court2" : [],
    "court3" : [],
    "court4" : [],
    "court5" : [],
    "court6" : [],
    "court7" : [],
    "court8" : [],
}

#This chunk resets all players to not on a court when program starts. 
mysql = connectToMySQL(db)
query = "update ebc_db.users set onCourt=0"
mysql.query_db(query)

print(courts)
@app.route("/")
def main():
    namesOfUsers = [] #list of users not on a court
    usersToRemove = [] # list of users on a court
    mysql = connectToMySQL(db)#this is to create list of people not on a court
    query = "Select * FROM ebc_db.users where onCourt = 0;"
    users =  mysql.query_db(query)

    mysql = connectToMySQL(db)#this is to create list of people on a court
    query = "Select * FROM ebc_db.users where onCourt = 1;"
    usersOnCourt =  mysql.query_db(query)
    print("users on court")
    print(usersOnCourt)
    for user in users:#makes list of people not on court
        namesOfUsers.append(user['name'])
    for person in usersOnCourt:#makes list of people that can removed
        usersToRemove.append(person['name'])
    return render_template('index.html', onCourtUsers = usersToRemove, namesOfUsers = namesOfUsers, courts=courts)

@app.route("/admin")
def admin():
    #add admin login check
    return render_template('admin.html')

#@app.route("/adminlogin", methods=["POST"])
#def adminlogin():

@app.route("/removeUserFromCourt", methods=["POST"])
def removeUserFromCourt():
    #checks to see if pin entered matches pin in database
    #if pin matches it goes through courts dictionary and removes name from list and sets onCourt value to 0
    pinEntered = int(request.form['userPinRemove'])
    nameSelected = request.form['personNameRemove']
    mysql = connectToMySQL(db)
    query = "Select * FROM ebc_db.users where name = " + "'" + nameSelected + "'"+ ";"
    user =  mysql.query_db(query)
    isValid = True

    if pinEntered < 1:
        flash("This field is required", "userPinAdd")
        isValid = False
    elif pinEntered!=user[0]['pin']:
        flash("Incorrect Pin")
        isValid = False
    if isValid == False:
        return redirect("/")
    else:
        for court in courts:
            for person in courts[court]:
                print(person)
                if person==nameSelected:
                    courts[court].remove(person)
                    mysql = connectToMySQL(db)
                    query = "update ebc_db.users set onCourt=0 where name = "+ "'" + person + "'"+ ";"
                    mysql.query_db(query)
    return redirect("/")

@app.route("/addUserToCourt", methods=["POST"])
def addUserToCourt():
    #checks to see if pin enters matches. If it does it changes users onCourt value to 0 and adds name to courts dictionary
    isValid = True
    mysql = connectToMySQL(db)
    query = "Select * FROM ebc_db.users"
    users =  mysql.query_db(query)

    pinEntered = int(request.form['userPinAdd'])
    nameSelected = request.form['personNameAdd']
    courtEntered = request.form['courtNum']
    mysql = connectToMySQL(db)
    query = "Select * FROM ebc_db.users where name = " + "'" + nameSelected + "'"+ ";"
    user =  mysql.query_db(query)

    if pinEntered < 1:
        flash("This field is required", "userPinAdd")
        isValid = False
    elif pinEntered!=user[0]['pin']:
        flash("Incorrect Pin")
        isValid = False
    else:
        if len(courts[courtEntered])>=8:
            flash("This court is full")
            isValid = False
        else:
            courts[courtEntered].append(nameSelected) 
            mysql = connectToMySQL(db)
            query = "update ebc_db.users set onCourt=1 where name = "+ "'" + nameSelected + "'"+ ";"
            mysql.query_db(query)
            print(courts)
    if isValid == False:
        return redirect("/")


    return redirect("/")

#this is an admin function to add users to database. Meant for front desk person to check in people with a name and pin.
#checks to see if name is unique. pin can be any number
@app.route("/addUser", methods=["POST"])
def addUser():
    isValid = True
     #name not entered
    if len(request.form['addName']) < 1:
        flash("This field is required", "addName")
        isValid = False
    #name format doesn't match
    elif not(request.form['addName'].isalpha()) or len(request.form['addName']) < 2:
        flash("Name must contain at least two letters and contain only letters", "addName")
        isValid = False
    #pin not entered
    if len(request.form['userPin']) < 1:
        flash("This field is required", "userPin")
        isValid = False
    #pin format doesn't match
    elif not(request.form['userPin'].isnumeric()):
        flash("Pin must be a number", "userPin")
        isValid = False
    else:
        mysql = connectToMySQL(db)
        query = "Select * FROM users WHERE name = %(name)s;"
        data = {'name': request.form['addName']}
        existingUser = mysql.query_db(query, data)
        if existingUser:
            print("User Exists")
            flash("The name you entered has already been taken. Please enter another one.", "email")
            isValid = False

    if isValid==False:
        return redirect('/admin')

    else:
        mysql2 = connectToMySQL(db)
        query = "INSERT INTO USERS(name, pin) VALUES (%(un)s, %(up)s)"
        data = {
            'un': request.form['addName'],
            'up': request.form['userPin']
        }
        mysql2 = mysql2.query_db(query,data)
        return redirect("/admin")

#@app.route("/userRegister", methods=["POST"])
#def register():
#    isValid = True
#    iflen(request.form[''])

if __name__ == '__main__':
    app.run(debug=True)

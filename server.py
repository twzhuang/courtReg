from flask import Flask, render_template, redirect, request, session, flash
from mysqlconnection import connectToMySQL
#from flask_bcrypt import Bcrypt
import re
from datetime import datetime
app = Flask(__name__)
#bcrypt = Bcrypt(app)

app.secret_key = "I am a secret key"

db = "ebc_db"
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

mysql = connectToMySQL(db)
query = "update ebc_db.users set onCourt=0"
mysql.query_db(query)

print(courts)
@app.route("/")
def main():
    namesOfUsers = [] 
    usersToRemove = []
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
    print("***********************")
    print(namesOfUsers)
    print(usersToRemove)
    return render_template('index.html', onCourtUsers = usersToRemove, namesOfUsers = namesOfUsers, courts=courts)

@app.route("/admin")
def admin():
    #add admin login check
    return render_template('admin.html')

#@app.route("/adminlogin", methods=["POST"])
#def adminlogin():

@app.route("/removeUserFromCourt", methods=["POST"])
def removeUserFromCourt():
    pinEntered = int(request.form['userPinRemove'])
    nameSelected = request.form['personNameRemove']
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

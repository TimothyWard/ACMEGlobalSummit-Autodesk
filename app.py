from flask import Flask, render_template, request
from flaskext.mysql import MySQL
import re
import MySQLdb
import getpass
import os
import csv
import time

app = Flask(__name__)
mysql = MySQL()

# MySQL configurations
app.config['MYSQL_DATABASE_HOST'] = raw_input("Please enter location of MySQL Server, most likely 'localhost':")
app.config['MYSQL_DATABASE_USER'] = raw_input("Please enter MySQL Username:")
app.config['MYSQL_DATABASE_PASSWORD'] = getpass.getpass(prompt="Please enter associated MySQL User's Password:")
app.config['MYSQL_DATABASE_DB'] = 'ACMESummit'
mysql.init_app(app)


# Routing to the home page
@app.route('/')
def main():
    return render_template('/index.html/')


# Routing to the registration page
@app.route('/register/')
def register():
    return render_template('/register.html/')


# Routing to validate registration info and add to database
@app.route('/submit_registration/', methods=['POST'])
def submit_registration():

    # pull info from form
    first_name = str(request.form['inputFirstName']).strip()
    last_name = str(request.form['inputLastName']).strip()
    company = str(request.form['inputCompanyName']).strip()
    title = str(request.form['inputJobTitle']).strip()
    email = str(request.form['inputEmail']).strip()
    phone = re.sub("\D", "", request.form['inputPhoneNumber'])
    address = str(request.form['inputStreetAddress']).strip()
    city = str(request.form['inputCity']).strip()
    state = str(request.form['inputState']).strip()
    zipcode = str(request.form['inputZip']).strip()
    country = str(request.form['inputCountry']).strip()

    # sanitize inputs
    if not 0 < len(first_name) <= 45:
        msg = "Error: First name is non-existent or greater than 45 characters. Please try again."
    elif not 0 < len(last_name) <= 45:
        msg = "Error: Last name is non-existent or greater than 45 characters. Please try again."
    elif not 0 < len(company) <= 100:
        msg = "Error: Company is non-existent or greater than 100 characters. Please try again."
    elif not 0 < len(title) <= 60:
        msg = "Error: Title is non-existent or greater than 60 characters. Please try again."
    elif not 0 < len(email) <= 60:
        msg = "Error: Email is non-existent or greater than 60 characters. Please try again."
    elif "@" not in email or "." not in email:
        msg = "Error: Email is not valid. Please try again."
    elif not 0 < len(phone) <= 20:
        msg = "Error: Phone Number is non-existent, only non-numeric characters or greater than 20 characters. Please try again."
    elif not 0 < len(address) <= 100:
        msg = "Error: Street Address is non-existent or greater than 100 characters. Please try again."
    elif not 0 < len(city) <= 30:
        msg = "Error: City is non-existent or greater than 30 characters. Please try again."
    elif not 0 < len(state) <= 30:
        msg = "Error: State is non-existent or greater than 30 characters. Please try again."
    elif not 0 < len(zipcode) <= 10:
        msg = "Error: Zip or Postal Code is non-existent or greater than 10 characters. Please try again."
    elif not 0 < len(country) <= 10:
        msg = "Error: Country selection is invalid. Please try again."
    else:

        # add new registration to the database
        try:
            conn = mysql.connect()
            cursor = conn.cursor()
            query_string = (
                "INSERT INTO Registration "
                "(FirstName, LastName, CompanyName, Title, Email, PhoneNumber, "
                "StreetAddress, City, Province, ZipCode, Country) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);")
            cursor.execute(query_string, (first_name, last_name, company, title, email, phone, address, city, state, zipcode, country))

            # save confirmation number from the insert and give it to the user
            cursor.execute("SELECT LAST_INSERT_ID();")
            con_number = cursor.fetchall()[0][0]
            img = "<img src='/static/img/thatsallfolks.jpg' style='width:380px;height:285px;'><br>"
            msg = img+"Registration Successful! Your confirmation number is {}".format(con_number)

        # catch the DB exceptions and tell the use if they tried to duplicate a phone or email
        except (MySQLdb.Error, MySQLdb.Warning) as e:
            if e[0] == 1062:
                msg = "Error: Sorry, this Email or Phone Number is already registered. Please try again."
            else:
                print e

        # close off the database connection
        finally:
            conn.commit()
            cursor.close()
            conn.close()

    # pass the message to the message page and show the user what's up
    return render_template('/message.html/', message=msg)


# Routing to the participant page to look up by confirmation number
@app.route('/participant/')
def participant():
    return render_template('/participant.html/')


# Routing to the lookup function to find confirmation number in the database
@app.route('/lookup/', methods=['POST'])
def lookup():

    # check to make sure the confirmation number is not invalid
    con_number = str(request.form['inputConfNumber']).strip()
    if len(con_number) != 6:
        msg = "Error: Confirmation Number must be exactly 6 characters. Please try again."

    # if the confirmation number was valid, attempt to find the registrant that matches from the database
    else:
        msg = "Error: No individuals are registered with this confirmation number!"
        try:
            conn = mysql.connect()
            cursor = conn.cursor()
            query_string = ("Select * from Registration WHERE ConfirmationNumber = " + con_number + ";")
            success = cursor.execute(query_string)

            # if a registrant was found with the given confirmation number, tell the user the details
            if success:
                rec = cursor.fetchall()
                msg = """Lookup Successful!<br>
                <br>
                Confirmation Number: {}<br>
                First Name: {}<br>
                Last Name: {}<br>
                Company: {}<br>
                Job Title: {}<br>
                Email Address: {}<br>
                Phone Number: {}<br>
                Street Address: {}<br>
                City: {}<br>
                State/Province: {}<br>
                Zip or Postal Code: {}<br>
                Country: {}<br>
                """.format(rec[0][0], rec[0][1], rec[0][2], rec[0][3], rec[0][4], rec[0][5], rec[0][6], rec[0][7],
                           rec[0][8], rec[0][9], rec[0][10], rec[0][11])

        # catch databsae exceptions and print them as errors
        except (MySQLdb.Error, MySQLdb.Warning) as e:
            print(e)

        # close off the database connections
        finally:
            conn.commit()
            cursor.close()
            conn.close()

    # pass the message to the message page and show the user what's up
    return render_template('/message.html/', message=msg)


# routing to the login page for the summit organizer
@app.route('/login/')
def login():
    return render_template('/login.html/')


# check to see if the user is aware of the super secret username and password
@app.route('/authenticate/', methods=['POST'])
def authenticate():
    user = str(request.form['inputUsername']).strip()
    password = str(request.form['inputPassword']).strip()
    if user == "bugsbunny" and password == "whatsupdoc":
        msg = "successful authentication"

        # the user checks out as a conference organizer, so make a new CSV list of registrants for them
        try:

            # connect to the database and create the file location for the CSV
            conn = mysql.connect()
            file_location = "{}/registrants_{}.csv".format(os.getcwd(), time.strftime("%Y%m%d-%H%M%S"))
            cursor = conn.cursor()
            cursor.execute("select * from registration;")

            # this is the right way to do this, however it requires file permissions
            '''
            cursor = conn.cursor()
            query_string = """SELECT * FROM Registration INTO OUTFILE '{}' FIELDS TERMINATED BY ',' ENCLOSED BY '"'
            LINES TERMINATED BY '\\n';""".format(file_location)
            cursor.execute(query_string)
            '''

            # write it to the CSV
            with open(file_location, "wb") as csv_file:
                csv_writer = csv.writer(csv_file)
                csv_writer.writerow([i[0] for i in cursor.description])
                csv_writer.writerows(cursor)

            # tell the user that it is available
            instructions = "<h2>Right Click And Copy Link To Download Local File...</h2><br>"
            msg = instructions + "<a href='file:///{}'> Download CSV of Registrants </a>".format(file_location)

        # catch databsae exceptions and print them as errors
        except (MySQLdb.Error, MySQLdb.Warning) as e:
            print(e)

        # close off the database connections
        finally:
            conn.commit()
            cursor.close()
            conn.close()

    # pass the message to the message page and show the user what's up
    return render_template('/message.html/', message=msg)


if __name__ == "__main__":
    app.run(port=5002)

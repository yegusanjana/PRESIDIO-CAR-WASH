
import os
import bcrypt
from flask import Flask, render_template, request, url_for, redirect, session
import email
from pymongo import MongoClient
import certifi
ca = certifi.where()



app = Flask(__name__)
app.secret_key = "super secret key"
app_root = os.path.abspath(os.path.dirname(__file__))

# <-------- MONGO CONNECTION -------->
cluster = MongoClient(
    "mongodb+srv://carwash:carwash@cluster0.0d7ay.mongodb.net/?retryWrites=true&w=majority", tlsCAFile=ca)
db = cluster["carwash"]
collection_admin = db["admin"]
collection_bookings = db["bookings"]
collection_branches = db["branches"]
collection_services = db["services"]
collection_signup = db["user"]
print("db connected")
# count_signup = collection_signup.count_documents({})


@app.route('/', methods=["GET", "POST"])
def index():
    message = 'Please login to your account'
    if "email" in session:
        return redirect(url_for("logged_in_user"))

    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('your_pass')

        # check if email exists in database
        email_found = collection_signup.find_one({"email": email})
        if email_found:
            email_val = email_found['email']
            passwordcheck = email_found['password']
            # encode the password and check if it matches
            if bcrypt.checkpw(password.encode('utf-8'), passwordcheck):
                session["email"] = email_val
                return redirect(url_for('logged_in_user'))
            else:
                if "email" in session:
                    return redirect(url_for("logged_in_user"))
                message = 'Wrong password'
                return render_template('login.html', message=message)
        else:
            message = 'Email not found'
            return render_template('login.html', message=message)
    return render_template('login.html', message=message)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    # if method post in index
    if "email" in session:
        return redirect(url_for("logged_in_user"))

    if request.method == "POST":
        # keys_signup = ["name", "email", "password"]
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('pass')
        re_pass = request.form.get('re_pass')
        print(name)
        # if found in database showcase that it's found
        user_found = collection_signup.find_one({"name": name})
        email_found = collection_signup.find_one({"email": email})
        print(email_found)
        if user_found:
            message = 'There already is a user by that name'
            return render_template('signup.html', message=message)
        if email_found:
            message = 'This email already exists in database'
            return render_template('signup.html', message=message)
        if password != re_pass:
            message = 'Passwords should match!'
            return render_template('signup.html', message=message)
        else:
            # hash the password and encode it
            hashed = bcrypt.hashpw(re_pass.encode('utf-8'), bcrypt.gensalt())
            # inserting them in a dictionary in key value pairs
            user_input = {'name': name, 'email': email, 'password': hashed}
            # insert it in the record collection
            x = collection_signup.insert_one(user_input)
            print(x)

            # find the new created account and its email
            user_data = collection_signup.find_one({"email": email})
            new_email = user_data['email']
            # if registered redirect to logged in as the registered user
            return redirect(url_for("index"))

    if request.method == "GET":
        return render_template("signup.html")


@app.route("/admin_login", methods=['GET', 'POST'])
def admin_login():
    message = 'Please login to your account'
    if "admin_user" in session:
        return redirect(url_for("logged_in_admin"))

    if request.method == "POST":
        admin_user = request.form.get('admin_user')
        admin_pwd = request.form.get('admin_pwd')

        if admin_user == 'admin' and admin_pwd == 'admin':
            return redirect(url_for('logged_in_admin'))

    return render_template('admin_login.html', message=message)


@app.route('/logged_in_admin', methods=['GET', 'POST'])
def logged_in_admin():
    rows = []
    # rows_status = []
    cursor = collection_bookings.find()
    for document in cursor:
        rows.append(document)
    if request.method == 'POST':
        status = request.form.get('status')
        filter = {'_id': document['_id']}
        user_input = {"$set": {'status': status}}
        x = collection_bookings.update_one(filter, user_input)
        print(x)

    return render_template('logged_in_admin.html', rows=rows)


@app.route('/logged_in_user', methods=['GET', 'POST'])
def logged_in_user():
    rows_service = []
    rows_loc = []                              # define an empty list
    cursor_service = collection_services.find()
    cursor_loc = collection_branches.find()

    for doc_service in cursor_service:
        rows_service.append(doc_service['service'])
    print(rows_service)

    for doc_loc in cursor_loc:
        rows_loc.append(doc_loc['branch_name'])
    print(rows_loc)

    if "email" in session:
        email = session["email"]

        if request.method == 'POST':
            email = request.form.get('email')
            service = request.form.get('service')
            location = request.form.get('location')
            date = request.form.get('date')
            status = "pending"

            user_input = {'email': email, 'service': service,
                          'location': location, 'date': date,
                          'status': status}
            # insert it in the record collection
            x = collection_bookings.insert_one(user_input)
            print(x)

            return render_template('logged_in_user.html', email=email)

        if request.method == "GET":
            return render_template("logged_in_user.html", rows_service=rows_service, rows_loc=rows_loc)


@app.route('/addService', methods=['GET', 'POST'])
def add_service():
    if request.method == 'POST':
        name = request.form.get('name')
        print(name)

        user_input = {'service': name}
        # insert it in the record collection
        x = collection_services.insert_one(user_input)
        print(x)
        return render_template('addServices.html', email=email)

    if request.method == "GET":
        return render_template("addServices.html")


@app.route('/addPlace', methods=['GET', 'POST'])
def add_place():
    if request.method == 'POST':
        name = request.form.get('name')
        address = request.form.get('address')
        print(name)

        user_input = {'branch_name': name, "address": address}
        # insert it in the record collection
        x = collection_branches.insert_one(user_input)
        print(x)
        return render_template("addPlaces.html")

    if request.method == "GET":
        return render_template("addPlaces.html")


@app.route("/logout", methods=["POST", "GET"])
def logout():
    if "email" in session:
        session.pop("email", None)
        return render_template("signout.html")
    else:
        return render_template('signout.html')


@app.route('/user_booking')
def user_booking():
    if "email" in session:
        email = session["email"]
    rows = []
    query = {'email': email}
    # rows_status = []
    cursor = collection_bookings.find(query)
    for document in cursor:
        rows.append(document)

        return render_template('view.html', rows=rows)
    else:
        return redirect(url_for("/"))


if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, render_template, request, url_for, redirect, session
import pymongo
import bcrypt
from fpdf import FPDF
#set app as a Flask instance 
app = Flask(__name__)
#encryption relies on secret keys so they could be run
app.secret_key = "testing"
#connoct to your Mongo DB database
client = pymongo.MongoClient(port=27017)

#get the database name
db = client.get_database('AutoQuGen')
#get the particular collection that contains the data
UserRecord = db.users
QuesRecord = db.questions
class PDF(FPDF):
     pass 
#assign URLs to have a particular route 
@app.route("/", methods=['post', 'get'])
def index():
    message = ''
    #if method post in index
    if "email" in session:
        return redirect(url_for("logged_in"))
    if request.method == "POST":
        user = request.form.get("name")
        email = request.form.get("email")
        password1 = request.form.get("password")
        # password2 = request.form.get("password2")
        #if found in database showcase that it's found 
        user_found = UserRecord.find_one({"name": user})
        email_found = UserRecord.find_one({"email": email})
        if user_found:
            message = 'There already is a user by that name'
            return render_template('index.html', message=message)
        if email_found:
            message = 'This email already exists in database'
            return render_template('index.html', message=message)
        # if password1 != password2:
        #     message = 'Passwords should match!'
        #     return render_template('index.html', message=message)
        else:
            #hash the password and encode it
            hashed = bcrypt.hashpw(password1.encode('utf-8'), bcrypt.gensalt())
            #assing them in a dictionary in key value pairs
            user_input = {'name': user, 'email': email, 'password': hashed}
            #insert it in the record collection
            UserRecord.insert_one(user_input)
            
            #find the new created account and its email
            user_data = UserRecord.find_one({"email": email})
            new_email = user_data['email']
            #if registered redirect to logged in as the registered user
        return render_template('logged_in.html', email=new_email)
    return render_template('index.html')



@app.route("/login", methods=["POST", "GET"])
def login():
    message = 'Please login to your account'
    if "email" in session:
        return redirect(url_for("logged_in"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        #check if email exists in database
        email_found = UserRecord.find_one({"email": email})
        if email_found:
            email_val = email_found['email']
            passwordcheck = email_found['password']
            #encode the password and check if it matches
            if bcrypt.checkpw(password.encode('utf-8'), passwordcheck):
                session["email"] = email_val
                return redirect(url_for('logged_in'))
            else:
                if "email" in session:
                    return redirect(url_for("logged_in"))
                message = 'Wrong password'
                return render_template('login.html', message=message)
        else:
            message = 'Email not found'
            return render_template('login.html', message=message)
    return render_template('login.html', message=message)

@app.route('/logged_in')
def logged_in():
    if "email" in session:
        email = session["email"]
        return render_template('logged_in.html', email=email)
    else:
        return redirect(url_for("login"))
@app.route('/add',methods=['POST','GET'])
def add():
    if "email" in session:
        email = session["email"]
        if request.method == "POST":
            question = request.form.get("question")
            answer = request.form.get("answer")
            mark = request.form.get("marks")
            challenge = request.form.get("challenge")
            #insert the question and answer in the database
            QuesRecord.insert_one({"question": question, "answer": answer, "marks": mark, "challenge": challenge})
            return redirect(url_for('add'))
        return render_template('add.html', email=email)
    else:
        return redirect(url_for("login"))

@app.route('/generate', methods=['POST','GET'])
def generate():
    if "email" in session:
        email = session["email"]
        if request.method == "POST":
            pdf = PDF(orientation='P', unit='mm', format='A4')
            pdf.add_page()
            pdf.output('test.pdf','F')
        return render_template('generate.html', email=email)
    else:
        return redirect(url_for("login"))

@app.route("/logout", methods=["POST", "GET"])
def logout():
    if "email" in session:
        session.pop("email", None)
        return render_template("signout.html")
    else:
        return render_template('index.html')



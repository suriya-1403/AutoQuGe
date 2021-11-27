from datetime import time
from os import name
from re import A
from flask import Flask, render_template, request, url_for, redirect, session
import pymongo
import bcrypt
from fpdf import FPDF
import multiprocessing as mp
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from configparser import ConfigParser

pool = mp.Pool(mp.cpu_count())
print(" * Number of CPU Available: ",mp.cpu_count())
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
CourseRecord = db.subject
class PDF(FPDF):
     pass 
def pdfgen(q1,q2,q3,subject,subject_code,time,branch,paperName):
    pdf = PDF(orientation='P', format='A4')
    pdf.add_page()
    pdf.set_font("Arial",'b', size=14)
    pdf.cell(200,10,"Vellore Institute Of Technology, Chennai", ln=1, align="C")
    pdf.set_font("Arial", size=13)
    pdf.cell(200,10,branch+" ("+"5th"+" Semester ("+"2020-2021"+"))", ln=1, align="C")
    pdf.set_font("Arial",'b', size=14)
    pdf.cell(200,10,paperName+" Examination", ln=1, align="C")
    pdf.set_font("Arial",'b', size=13)
    pdf.cell(200,10,subject+"("+subject_code+")", ln=1, align="C")
    pdf.set_font("Times", size=10)
    pdf.cell(167,10,"Max Marks : 30", align="left")
    pdf.cell(100,10,"Time : "+time,ln=1, align="right")
    pdf.set_font("Times", size=10)
    pdf.cell(100,10,"Note: There are three Questions in this paper . All Questions are compulsory.",ln=1, align="left")
    # pdf.set_font("Arial",'b', size=13)
    # pdf.cell(134,10,"Section A", align="left")
    pdf.set_font("Arial",'i', size=11)
    pdf.cell(100,10,"Max marks for all Question are 10",ln=1, align="left")
    pdf.set_font("Arial",'b', size=10)
    pdf.cell(100,10,"Attempt ALL Questions.",ln=1, align="left")
    pdf.set_font("Arial",'b', size=13)
    pdf.multi_cell(140,10,"Question 1: "+q1, align="left")
    pdf.ln()
    pdf.set_font("Arial",'b', size=13)
    # q2.decode('latin-1')
    pdf.multi_cell(140,10,"Question 2: "+str(q2), align="left")
    pdf.ln()
    pdf.set_font("Arial",'b', size=13)
    pdf.multi_cell(140,10,"Question 3: "+q3, align="left")
    pdf.output('test.pdf','F')
    mailing()

def mailing():
    body = '''Good Morning,
    This is a Confidential Mail
    sincerely yours,
    Exam Committee
    '''
    file ='config.ini'
    config = ConfigParser()
    config.read(file)
    sender = config['Gmail']['mailID']
    password = config['Gmail']['Password']
    # put your email here
    
    # get the password in the gmail (manage your google account, click on the avatar on the right)
    # then go to security (right) and app password (center)
    # insert the password and then choose mail and this computer and then generate
    # copy the password generated here
    # put the email of the receiver here
    receiver = 'suriya@outlook.in'
    
    #Setup the MIME
    message = MIMEMultipart()
    message['From'] = sender
    message['To'] = receiver
    message['Subject'] = 'This email has an attacment, a pdf file'
    
    message.attach(MIMEText(body, 'plain'))
    
    pdfname = 'test.pdf'
    
    # open the file in bynary
    binary_pdf = open(pdfname, 'rb')
    
    payload = MIMEBase('application', 'octate-stream', Name=pdfname)
    # payload = MIMEBase('application', 'pdf', Name=pdfname)
    payload.set_payload((binary_pdf).read())
    
    # enconding the binary into base64
    encoders.encode_base64(payload)
    
    # add header with pdf name
    payload.add_header('Content-Decomposition', 'attachment', filename=pdfname)
    message.attach(payload)
    
    #use gmail with port
    session = smtplib.SMTP('smtp.gmail.com', 587)
    
    #enable security
    session.starttls()
    
    #login with mail_id and password
    session.login(sender, password)
    
    text = message.as_string()
    session.sendmail(sender, receiver, text)
    session.quit()
    print('Mail Sent')
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
            subjectCode = request.form.get("subject")
            module = request.form.get('Module')
            #insert the question and answer in the database
            QuesRecord.insert_one({"question": question, "answer": answer, "marks": mark, "challenge": challenge, "subjectCode": subjectCode, "module": module})
            return redirect(url_for('add'))
        return render_template('add.html', email=email)
    else:
        return redirect(url_for("login"))

@app.route('/generate', methods=['POST','GET'])
def generate():
    if "email" in session:
        email = session["email"]
        if request.method == "POST":
            ts = time.time()
            branch = request.form.get("branch")
            subject = request.form.get("subject")
            module = request.form.get("Modules")
            Name = request.form.get("PaperName")
            duration = request.form.get('time')
            a = "Moderate"
            # CourseRecord.insert_one({"SubjectName" : "Parallel Distribution System", "Code" : "CSE4001"})
            for x in QuesRecord.find({"challenge":"Moderate"}):
                q1 = x['question']
                # print(q1)
            for x in QuesRecord.find({"challenge":"Easy"}):
                q2 = x['question']
                # print(q2)
            for x in QuesRecord.find({"challenge":"Hard"}):
                q3 = x['question']
                # print(q3)
            for x in CourseRecord.find({"Code":subject}):
                # print(x)
                subjectNa = x['SubjectName']
            # print(subjectNa)
            pool.apply_async(pdfgen(q1,q2,q3,subjectNa,subject,duration,branch,Name))
            pool.close()
            pool.join()
            print("time in parallel:",time.time()-ts)
            # pdfgen(q1,q2,q3,subjectNa,subject,duration,branch,Name)
            # print("time in serial:",time.time()-ts)
            
                # print(x['question'])
            # pdf = PDF(orientation='P', unit='mm', format='A4')
            # pdf.add_page()
            # pdf.output('test.pdf','F')
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



from flask import Flask, render_template, request, redirect, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from accountsUser import User, Picture
from textReader import readText
from werkzeug.utils import secure_filename
import os
from os import listdir
import re

from app import app
import urllib.request

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///keys.db'
app.config['SQLALCHEMY_TRACK_MODIFICATION'] = False
app.config['SECRET_KEY'] = 'fdgdfgdfggf786hfg6hfg6h7f'
db = SQLAlchemy(app)

user = User("")
image = Picture("")

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


def convertText(text, path):
    file = open(path, 'r')
    dataPattern = file.read().split(';')
    wordsInPattern = {}
    for word in dataPattern:
        elementOutriggerWords = {word: ''}
        wordsInPattern.update(elementOutriggerWords)
    for data in wordsInPattern:
        if data.lower() in text.lower():
            result = re.search(data.lower(), text.lower())
            text = text.replace(text[:result.end()], '')
            placeTrigger = findFirstKey(text, path)
            wordsInPattern[data] = text[:placeTrigger].replace('\n', " ").replace(':', '').strip()
        else:
            return "Empty"
    return wordsInPattern


def findFirstKey(text, path):
    minPos = len(text)
    file = open(path, 'r')
    tiggerWords = file.read().split(';')
    for data in tiggerWords:
        if data.lower() in text.lower():
            result = re.search(data.lower(), text.lower())
            if minPos > result.start():
                minPos = result.start()
    return minPos


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


class Patterns(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    path = db.Column(db.String(), nullable=False)


class Accounts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(), nullable=False, unique=True)
    password = db.Column(db.String(), nullable=False)

    def __repr__(self):
        return self.login


def getPatterns(trigger):
    files = listdir('static/patterns/' + user.login)
    if trigger:
        files.append('Without pattern')
    return files



@app.route('/')
def index():
    if user.login == '':
        return redirect('/signIn')
    else:
        return render_template('index.html', data=user.login, CARCASSES=getPatterns(True))


@app.route('/upload', methods=['POST', 'GET'])
def upload():
    if request.method == 'POST':
        file = request.files['filePath']
        readedFile = readText(file).strip()
        return render_template('index.html', data=user.login, text=readedFile)


@app.route('/deletePattern', methods=['POST', 'GET'])
def deletePattern():
    if request.method == "POST":
        numberPattern = int(request.form.get('pattern')) - 1
        path = 'static/patterns/' + user.login + '/' + getPatterns(False)[numberPattern]
        flash('Pattern "' + getPatterns(False)[numberPattern] + '" deleted')
        os.remove(path)
    return render_template('pattern.html', data=user.login, CARCASSES=getPatterns(False))

@app.route('/', methods=['POST', 'OPTIONS', 'GET'])
def upload_image():
    if 'filePath' not in request.files:
        # flash('No file part')
        return redirect(request.url)
    file = request.files['filePath']
    if file.filename == '':
        # flash('No image selected for uploading')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join('static/uploads/', filename))
        readedFile = readText(file).strip()
        # print('upload_image filename: ' + filename)
        # flash('Image successfully uploaded and displayed below')
        numberPattern = int(request.form.get('pattern')) - 1
        path = 'static/patterns/' + user.login + '/' + getPatterns(True)[numberPattern]
        if getPatterns(True)[numberPattern] != 'Without pattern':
            convertedText = convertText(readedFile, path)
        else:
            convertedText = readedFile
        return render_template('index.html', filename=filename, text=convertedText, data=user.login, CARCASSES=getPatterns(True))
    else:
        flash('Allowed image types are -> png, jpg, jpeg, gif')
        return redirect(request.url)


@app.route('/display/<filename>')
def display_image(filename):
    # print('display_image filename: ' + filename)
    return redirect(url_for('static', filename='uploads/' + filename), code=301)


@app.route('/pattern',  methods=['POST', 'GET'])
def pattern():
    if user.login == '':
        return redirect('/signIn')
    else:
        if request.method == "POST":
            dataFromPattern = request.form['textForPattern']
            name = dataFromPattern[0:dataFromPattern.find(';')]
            my_file = open('static/patterns/' + user.login+'/'+name + '.txt', "w+")
            my_file.write(dataFromPattern[dataFromPattern.find(';')+1:])
            flash('Pattern created successfully')
        return render_template('pattern.html', data=user.login, CARCASSES=getPatterns(False))


@app.route('/signUn', methods=['POST', 'GET'])
def signUn():
    if request.method == "POST":
        login = request.form['login']
        password = request.form['password']

        account = Accounts(login=login, password=password)

        try:
            db.session.add(account)
            db.session.commit()
            flash('Account registered successfully')
            return redirect('/signIn')
        except:
            return render_template('signUn.html')
    else:
        return render_template('signUn.html')


@app.route('/signIn', methods=['POST', 'GET'])
def signIn():
    logins = Accounts.query.all()
    newlogins = list(map(str, logins))
    if request.method == "POST":
        login = request.form['login']
        password = request.form['password']
        if login in newlogins:
            user.login = login
            if not os.path.exists('static/patterns/' + login):
                os.mkdir('static/patterns/' + login)
            return redirect('/')
        else:
            flash('Incorrect username or password')
    return render_template('signIn.html')


if __name__ == '__main__':
    app.run(debug=True)

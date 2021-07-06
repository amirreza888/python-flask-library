from os import name
from flask import Flask, session, redirect, url_for, escape, request, render_template, Response

import pymongo
import hashlib

app = Flask(__name__)
app.secret_key = 'secret'

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["library"]

CustomerModel = mydb["customers"]
BookModel = mydb["books"]


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        name = request.form['name']
        lastname = request.form['lastname']
        data = {"username": username, "password": password, "email": email, "name": name, "lastname": lastname}
        CustomerModel.insert_one(data)
        return Response("you are registered successfully\n <a href=\"/login\">login</a>", status=200)

    if request.method == 'GET':
        return render_template('register.html')


@app.route('/login', methods=['POST', 'get'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        customer = CustomerModel.find_one(
            {"username": username, 'password': password},
            {"_id": 1, "username": 1, "email": 1, "name": 1, "lastname": 1}
        )
        if customer:
            session['username'] = username
            return redirect("/profile", code=302)
        return Response("your pass or user name is incorrect", status=400)

    elif request.method == 'GET':
        return render_template('login.html')


@app.route('/logout', methods=['GET'])
def logout():
    session.pop('username', None)
    return Response("session cleared <a href=\"/login\">login</a>", status=200)


@app.route('/profile', methods=['GET'])
def profile():
    if session.get('username'):
        result = CustomerModel.find_one({"username": session.get('username')},
                                        {"_id": 1, "username": 1, "email": 1, "name": 1, "lastname": 1})

        if request:
            return render_template('profile.html', result=result)

    return Response("permission denied <a href=\"/login\">first login</a>", status=403)



@app.route('/books', methods=['GET'])
def profile():
    query = {}
    book_name = request.args.get('name', None)
    if book_name:
        query['name'] = { "$regex": "^" + book_name }
    books = BookModel.find(query)
    return render_template('books.html', result=books)




if __name__ == '__main__':
    app.run()

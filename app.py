from os import name

from bson import ObjectId
from flask import Flask, session, redirect, url_for, escape, request, render_template, Response

import pymongo
import hashlib

app = Flask(__name__)
# app.config["DEBUG"] = True
app.secret_key = 'secret'

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["library"]

CustomerModel = mydb["customers"]
BookModel = mydb["books"]
OrderModel = mydb["orders"]


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


@app.route('/books', methods=['GET', 'POST'])
def book_list():
    if session.get('username'):
        if request.method == 'GET':
            query = {"count": {"$gt": 0}}
            book_name = request.args.get('name', None)
            if book_name:
                query['name'] = {"$regex": "^" + book_name}
            books = BookModel.find(query,
                                   {
                                       "_id": 1,
                                       "name": 1,
                                       "description": 1,
                                       "publication_date": 1,
                                       "rate": 1,
                                       "count": 1
                                   })
            return render_template('books.html', books=books)

        if request.method == 'POST':
            if session.get('username'):
                user = CustomerModel.find_one({"username": session.get('username')},
                                              {"_id": 1, "username": 1, "email": 1, "name": 1, "lastname": 1})
                book_id = request.form.get('book_id')
                book = BookModel.find_one({"_id": ObjectId(book_id)})
                OrderModel.insert_one({"book_id": book["_id"], "customer_id": user["_id"]})
                myquery = {"_id": ObjectId(book["_id"])}
                newvalues = {"$set": {"count": book['count'] - 1}}
                BookModel.update_one(myquery, newvalues)
                return redirect("/books", code=302)
    else:
        return Response("permission denied <a href=\"/login\">first login</a>", status=403)


@app.route('/borrowed-books', methods=['GET', 'POST'])
def costumer_book_list():
    if session.get('username'):
        if request.method == 'GET':
            pipeline = [
                {
                    "$lookup":
                        {
                            "from": "books",
                            "localField": "book_id",
                            "foreignField": "_id",
                            "as": "book"
                        }
                },
                {"$unwind": "$book"},
                {
                    "$lookup":
                        {
                            "from": "customers",
                            "localField": "customer_id",
                            "foreignField": "_id",
                            "as": "customer"
                        }
                },
                {"$unwind": "$customer"},
                {
                    "$match": {
                        "customer.username": session.get('username')
                    }
                }
            ]
            book_name = request.args.get('name', None)

            # if book_name:
            #     pipeline.append(
            #         {
            #             "$match": {
            #                 "name": book_name
            #             }
            #         }
            #     )
            orders = OrderModel.aggregate(pipeline)
            import pprint
            # for i in orders:
            #     print(i)
            return render_template('costumer_books.html', orders=orders)

        if request.method == 'POST':
            if session.get('username'):
                user = CustomerModel.find_one({"username": session.get('username')},
                                              {"_id": 1, "username": 1, "email": 1, "name": 1, "rate": 1})
                order_id = request.form.get('order_id')
                order = OrderModel.find_one({"_id": ObjectId(order_id)})
                if order:
                    myquery = {"_id": order["book_id"]}
                    newvalues = {"$inc": {"count": 1}}
                    BookModel.update_one(myquery, newvalues)
                    OrderModel.delete_one({"_id": ObjectId(order_id)})
                return redirect("/borrowed-books", code=302)
    else:
        return Response("permission denied <a href=\"/login\">first login</a>", status=403)


app.run()

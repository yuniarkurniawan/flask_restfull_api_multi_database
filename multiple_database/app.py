from flask import Flask, request, jsonify, make_response
import sqlite3
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import fields
from sqlalchemy import func, String


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///default_book.sqlite'
app.config['SQLALCHEMY_BINDS'] = {
    "second_book" : 'sqlite:///second_book_db.sqlite'
}


db = SQLAlchemy(app)

class Book(db.Model):

    __tablename__ = 'book'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(255))

    def __init__(self, **kwargs)-> None:
        self.title = kwargs['title']
        self.year = kwargs['year']
        self.description = kwargs['description']


class BookLite(db.Model):
    __bind_key__ = 'second_book'
    __tablename__ = 'second_book'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(255))

    def __init__(self, **kwargs)-> None:
        self.title = kwargs['title']
        self.year = kwargs['year']
        self.description = kwargs['description']


db.create_all()
MODELS = {"default_book": {"Book": Book}, "second_book": {"Book": BookLite}}


@app.route("/api/v1/<db_name>/delete_book/<int:id>", methods=['DELETE'])
def delete_book(db_name, id):

    book = MODELS[db_name]["Book"]
    get_book = book.query.get_or_404(id)

    db.session.delete(get_book)
    db.session.commit()
    return make_response(jsonify(
        {
            "message": "success",
            "code": 204
        }
    ), 204)


@app.route("/api/v1/<db_name>/update_book/<int:id>", methods=['PUT'])
def update_book(db_name, id):

    book = MODELS[db_name]["Book"]
    get_book = book.query.get_or_404(id)

    data = request.get_json()
    if data.get('title'): get_book.title = data['title']
    if data.get('year'): get_book.year = int(data['year'])
    if data.get('description'): get_book.description = data['description']
    db.session.commit()

    result = {
            "id": get_book.id,
            "title": get_book.title,
            "year": get_book.year,
            "description": get_book.description
        }

    return make_response(jsonify(
        {
            "data": result,
            "message": "success",
            "code": 201
        }
    ), 201)


@app.route("/api/v1/<db_name>/list_book", methods=['GET'])
def get_list_book(db_name):

    book = MODELS[db_name]["Book"]

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 5, type=int)
    search = request.args.get('search', type=str)
    fetch_book = book.query.filter(func.lower(book.title)
                                        .like('%'+search+'%')
                                        | func.lower(book.description)
                                        .like('%'+search+'%')
                                        | func.cast(book.year, String).like('%'+search+'%'))\
            .order_by(book.id.desc())\
            .paginate(page=page, per_page=per_page)

    list_books = list()
    for data in fetch_book.items:
        dict_data = {}
        dict_data['id'] = data.id
        dict_data['title'] = data.title
        dict_data['year'] = data.year
        dict_data['description'] = data.description
        list_books.append(dict_data)

    pagination = {
            "page": fetch_book.page,
            'pages': fetch_book.pages,
            'total_count': fetch_book.total,
            'prev_page': fetch_book.prev_num,
            'next_page': fetch_book.next_num,
            'has_next': fetch_book.has_next,
            'has_prev': fetch_book.has_prev,
        }

    return make_response(jsonify(
            {
                "data": list_books,
                "message": "success",
                "code": 200,
                "pagination": pagination
            }
        ), 200)


@app.route("/api/v1/<db_name>/insert_book", methods=['POST'])
def insert_book(db_name):
    try:
        data = request.get_json()
        title = data['title']
        year = int(data['year'])
        description = data['description']

        book = MODELS[db_name]["Book"](title=title, year=year, description=description)
        db.session.add(book)
        db.session.commit()

        result = {
            "id": book.id,
            "title": book.title,
            "year": book.year,
            "description": book.description
        }

        return make_response(jsonify(
            {
                "data": result,
                "message": "success",
                "code": 201
            }
        ), 201)

    except Exception as e:
        return make_response(jsonify({"message": str(e)}), 401)


if __name__ == '__main__':
    app.run(port=5000, host="0.0.0.0", use_reloader=False)

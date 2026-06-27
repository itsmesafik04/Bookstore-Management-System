from flask import Flask, request, jsonify
from config import Config
from models import db, Book
from flask import render_template
from flask import (
    Flask,
    request,
    jsonify,
    render_template,
    redirect,
    url_for,
    flash
)

app = Flask(__name__)
app.config.from_object(Config)

app.secret_key = "bookstore_secret_key"

db.init_app(app)


# Home Route
@app.route("/")
def home():
    return redirect(url_for("books_page"))


# -------------------------
# CREATE BOOK
# -------------------------
@app.route("/api/books", methods=["POST"])
def add_book():
    data = request.get_json()

    required_fields = [
        "title",
        "author",
        "category",
        "isbn",
        "price",
        "quantity",
        "published_year"
    ]

    for field in required_fields:
        if field not in data:
            return jsonify({
                "error": f"{field} is required"
            }), 400

    existing_book = Book.query.filter_by(
        isbn=data["isbn"]
    ).first()

    if existing_book:
        return jsonify({
            "error": "ISBN already exists"
        }), 409

    new_book = Book(
        title=data["title"],
        author=data["author"],
        category=data["category"],
        isbn=data["isbn"],
        price=data["price"],
        quantity=data["quantity"],
        published_year=data["published_year"]
    )

    db.session.add(new_book)
    db.session.commit()

    return jsonify({
        "message": "Book added successfully",
        "book": new_book.to_dict()
    }), 201


# -------------------------
# GET ALL BOOKS
# -------------------------
@app.route("/api/books", methods=["GET"])
def get_books():

    query = Book.query

    # Search
    search = request.args.get("search")

    if search:
        query = query.filter(
            Book.title.ilike(f"%{search}%") |
            Book.author.ilike(f"%{search}%")
        )

    # Category Filter
    category = request.args.get("category")

    if category:
        query = query.filter(
            Book.category.ilike(category)
        )

    # Sorting
    sort_by = request.args.get("sort_by", "id")
    order = request.args.get("order", "asc")

    sortable_fields = {
        "title": Book.title,
        "price": Book.price,
        "year": Book.published_year,
        "id": Book.id
    }

    if sort_by in sortable_fields:

        if order == "desc":
            query = query.order_by(
                sortable_fields[sort_by].desc()
            )
        else:
            query = query.order_by(
                sortable_fields[sort_by].asc()
            )

    # Pagination
    page = request.args.get(
        "page",
        1,
        type=int
    )

    per_page = 9

    pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    books = pagination.items

    return jsonify({
        "total_books": pagination.total,
        "current_page": page,
        "total_pages": pagination.pages,
        "books": [
            book.to_dict()
            for book in books
        ]
    })


# -------------------------
# GET SINGLE BOOK
# -------------------------
@app.route("/api/books/<int:id>", methods=["GET"])
def get_book(id):

    book = Book.query.get(id)

    if not book:
        return jsonify({
            "error": "Book not found"
        }), 404

    return jsonify(book.to_dict())


# -------------------------
# UPDATE BOOK
# -------------------------
@app.route("/api/books/<int:id>", methods=["PUT"])
def update_book(id):

    book = Book.query.get(id)

    if not book:
        return jsonify({
            "error": "Book not found"
        }), 404

    data = request.get_json()

    book.title = data.get("title", book.title)
    book.author = data.get("author", book.author)
    book.category = data.get("category", book.category)
    book.price = data.get("price", book.price)
    book.quantity = data.get("quantity", book.quantity)
    book.published_year = data.get(
        "published_year",
        book.published_year
    )

    db.session.commit()

    return jsonify({
        "message": "Book updated successfully",
        "book": book.to_dict()
    })


# -------------------------
# DELETE BOOK
# -------------------------
@app.route("/api/books/<int:id>", methods=["DELETE"])
def delete_book(id):

    book = Book.query.get(id)

    if not book:
        return jsonify({
            "error": "Book not found"
        }), 404

    db.session.delete(book)
    db.session.commit()

    return jsonify({
        "message": "Book deleted successfully"
    })

@app.route("/books")
def books_page():

    search = request.args.get("search", "")
    category = request.args.get("category", "")

    query = Book.query

    if search:
        query = query.filter(
            Book.title.ilike(f"%{search}%") |
            Book.author.ilike(f"%{search}%")
        )

    if category:
        query = query.filter(
            Book.category == category
        )

    # Sorting
    sort_by = request.args.get("sort_by", "id")
    order = request.args.get("order", "asc")

    if sort_by == "title":
        if order == "desc":
            query = query.order_by(Book.title.desc())
        else:
            query = query.order_by(Book.title.asc())

    elif sort_by == "price":
        if order == "desc":
            query = query.order_by(Book.price.desc())
        else:
            query = query.order_by(Book.price.asc())

    elif sort_by == "year":
        if order == "desc":
            query = query.order_by(Book.published_year.desc())
        else:
            query = query.order_by(Book.published_year.asc())

    else:
        query = query.order_by(Book.id.asc())

    pagination = query.paginate(
        page=request.args.get("page", 1, type=int),
        per_page=9,
        error_out=False
    )

    total_books = Book.query.count()

    total_quantity = db.session.query(
        db.func.sum(Book.quantity)
    ).scalar() or 0

    categories = db.session.query(
        Book.category
    ).distinct().all()

    categories = [c[0] for c in categories]

    return render_template(
        "index.html",
        books=pagination.items,
        pagination=pagination,
        total_books=total_books,
        total_quantity=total_quantity,
        categories=categories,
        selected_category=category
    )


@app.route("/books/add", methods=["GET", "POST"])
def add_book_page():

    if request.method == "POST":

        title = request.form["title"].strip()
        author = request.form["author"].strip()
        category = request.form["category"].strip()
        isbn = request.form["isbn"].strip()
        price = request.form["price"]
        quantity = request.form["quantity"]
        published_year = request.form["published_year"]

        # Validation
        if not title:
            flash("Title is required")
            return redirect(url_for("add_book_page"))

        if not author:
            flash("Author is required")
            return redirect(url_for("add_book_page"))

        if not category:
            flash("Category is required")
            return redirect(url_for("add_book_page"))

        if not isbn:
            flash("ISBN is required")
            return redirect(url_for("add_book_page"))

        if not isbn.isdigit():
            flash("ISBN must contain only numbers")
            return redirect(url_for("add_book_page"))

        if float(price) <= 0:
            flash("Price must be greater than 0")
            return redirect(url_for("add_book_page"))

        if int(quantity) < 0:
            flash("Quantity cannot be negative")
            return redirect(url_for("add_book_page"))

        if not published_year:
            flash("Published Year is required")
            return redirect(url_for("add_book_page"))

        # Create book after validation
        book = Book(
            title=title,
            author=author,
            category=category,
            isbn=isbn,
            price=float(price),
            quantity=int(quantity),
            published_year=int(published_year)
        )

        db.session.add(book)
        db.session.commit()

        flash("Book Added Successfully")

        return redirect(url_for("books_page"))

    return render_template("add_book.html")


@app.route("/books/edit/<int:id>", methods=["GET", "POST"])
def edit_book_page(id):

    book = Book.query.get_or_404(id)

    if request.method == "POST":

        title = request.form["title"].strip()
        author = request.form["author"].strip()
        category = request.form["category"].strip()
        isbn = request.form["isbn"].strip()
        price = request.form["price"]
        quantity = request.form["quantity"]
        published_year = request.form["published_year"]

        # Validation
        if not title:
            flash("Title is required")
            return redirect(url_for("edit_book_page", id=id))

        if not author:
            flash("Author is required")
            return redirect(url_for("edit_book_page", id=id))

        if not category:
            flash("Category is required")
            return redirect(url_for("edit_book_page", id=id))

        if not isbn:
            flash("ISBN is required")
            return redirect(url_for("edit_book_page", id=id))

        if not isbn.isdigit():
            flash("ISBN must contain only numbers")
            return redirect(url_for("edit_book_page", id=id))

        if float(price) <= 0:
            flash("Price must be greater than 0")
            return redirect(url_for("edit_book_page", id=id))

        if int(quantity) < 0:
            flash("Quantity cannot be negative")
            return redirect(url_for("edit_book_page", id=id))

        if not published_year:
            flash("Published Year is required")
            return redirect(url_for("edit_book_page", id=id))

        # Update book after validation
        book.title = title
        book.author = author
        book.category = category
        book.isbn = isbn
        book.price = float(price)
        book.quantity = int(quantity)
        book.published_year = int(published_year)

        db.session.commit()

        flash("Book Updated Successfully")

        return redirect(url_for("books_page"))
        
    return render_template(
        "edit_book.html",
        book=book
    )

@app.route("/books/delete/<int:id>")
def delete_book_page(id):

    book = Book.query.get_or_404(id)

    db.session.delete(book)

    db.session.commit()

    flash("Book Deleted Successfully")

    return redirect(url_for("books_page"))


@app.errorhandler(404)
def page_not_found(error):

    return render_template(
        "404.html"
    ), 404

@app.errorhandler(500)
def internal_server_error(error):

    return render_template(
        "500.html"
    ), 500



if __name__ == "__main__":
    app.run(debug=True)
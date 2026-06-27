from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Book(db.Model):
    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(255), nullable=False)

    author = db.Column(db.String(255), nullable=False)

    category = db.Column(db.String(100), nullable=False)

    isbn = db.Column(db.String(20), unique=True, nullable=False)

    price = db.Column(db.Float, nullable=False)

    quantity = db.Column(db.Integer, nullable=False)

    published_year = db.Column(db.Integer, nullable=False)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "category": self.category,
            "isbn": self.isbn,
            "price": self.price,
            "quantity": self.quantity,
            "published_year": self.published_year,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }
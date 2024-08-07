from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_marshmallow import Marshmallow

db = SQLAlchemy()
ma = Marshmallow()

class User(db.Model):
    __tablename__ = 'user' 
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    lastname = db.Column(db.String(100))
    photo = db.Column(db.String(150), default='default.jpg')
    email = db.Column(db.String(120), unique=True)
    telephone = db.Column(db.String(20), unique=True, nullable=False)
    nationality = db.Column(db.String(100)) 
    location = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float)
    role = db.Column(db.String(50), default='farmer', nullable=False)
    longitude = db.Column(db.Float) 
    gender = db.Column(db.String(10))
    date_of_birth = db.Column(db.Date)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    def update_details(self, name, telephone, group_name, location, land_size, crop, last_yield, bank):
        self.name = name
        self.telephone = telephone
        self.group_name = group_name
        self.location = location
        self.land_size = land_size
        self.crop = crop
        self.last_yield = last_yield
        self.bank_account = bank

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    


    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on': role
    }
    
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'photo': self.photo,
            'telephone': self.telephone,
            'group_name': self.group_name,
            'nationality': self.nationality,
            'location': self.location,
            'land_size': self.land_size,
            'crop': self.crop,
            'last_yield': self.last_yield,
            'bank_account': self.bank_account,
            'gender': self.gender,
            'date_of_birth': str(self.date_of_birth),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    __table_args__ = (
        db.UniqueConstraint('telephone', name='uq_user_telephone'),
        db.UniqueConstraint('email', name='uq_user_email'),
    )
    
class Issue(db.Model):
    __tablename__ = 'issues'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('issues', lazy=True))
    issue_text = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text)
    status = db.Column(db.String(50), default='Open') 
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'issue_text': self.issue_text,
            'response': self.response,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('orders', lazy=True))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    product_name = db.Column(db.String(150), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'product_name': self.product_name,
            'quantity': self.quantity,
            'price': self.price,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'price': self.price,
            'status': self.status
        }
    

class Farmer(User):
    __tablename__ = 'farmer'
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    nin = db.Column(db.String(20), unique=True, nullable=False)
    group_name = db.Column(db.String(100))
    land_size = db.Column(db.Float)
    crop = db.Column(db.String(100))
    last_yield = db.Column(db.Float)
    bank_account = db.Column(db.Boolean, default=False)

    __mapper_args__ = {
        'polymorphic_identity': 'farmer',
        'inherit_condition': (id == User.id)
    }


class Admin(User):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    admin_id = db.Column(db.String(100))


    __mapper_args__ = {
        'polymorphic_identity': 'admin',
        'inherit_condition': (id == User.id)
    }


class Supplier(User):
    __tablename__ = 'suppliers'
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    nin = db.Column(db.String(20), unique=True, nullable=False)
    company_name = db.Column(db.String(100))
    products = db.relationship('Product', backref='supplier', lazy=True)
    contact_person = db.Column(db.String(100))

    __mapper_args__ = {
        'polymorphic_identity': 'supplier',
        'inherit_condition': (id == User.id)
    }

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'photo': self.photo,
            'products': [product.to_dict() for product in self.products]
        }


class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(200), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(200), nullable=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category.name if self.category else None,
            'price': self.price,
            'image_url': self.image_url,
            'supplier': self.supplier.to_dict() if self.supplier else None
        }

class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=True)
    products = db.relationship('Product', backref='category', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'products': [product.to_dict() for product in self.products]
        }
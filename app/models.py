from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    photo = db.Column(db.LargeBinary)
    email = db.Column(db.String(120), unique=True, nullable=False)
    telephone = db.Column(db.String(20), unique=True, nullable=False)
    group_name = db.Column(db.String(100))
    nationality = db.Column(db.String(100)) 
    location = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float)
    role = db.Column(db.String(50), default='Farmer', nullable=False)
    longitude = db.Column(db.Float) 
    land_size = db.Column(db.Float)
    crop = db.Column(db.String(100))
    last_yield = db.Column(db.Float)
    bank_account = db.Column(db.Boolean, default=False)
    gender = db.Column(db.String(10))
    date_of_birth = db.Column(db.Date)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    def update_detials(self, name, telephone, group_name, location, land_size, crop, last_yield, bank):
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
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('orders', lazy=True))
    product_name = db.Column(db.String(100), nullable=False)
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
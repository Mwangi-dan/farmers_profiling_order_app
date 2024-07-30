import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

ISSUE_STATUS = ['Open', 'In Progress', 'Resolved', 'Closed']
ORDER_STATUS = ['Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled']
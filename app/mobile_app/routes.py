from flask import jsonify, request
from . import mobile_app_bp
from app import db
from app.models import (
    User, Farmer, Product, Order, Farmer, Supplier, Category)


@mobile_app_bp.route('/categories', methods=['GET'])
def get_categories():
    categories = Category.query.all()
    categories_data = [{"id": category.id, "name": category.name} for category in categories]
    return jsonify(categories_data)


@mobile_app_bp.route('/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify([product.to_dict() for product in products])
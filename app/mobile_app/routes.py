from flask import jsonify, request
from . import mobile_app_bp
from app import db
from app.models import (
    User, Farmer, Product, Order, Farmer, Supplier)


@mobile_app_bp.route('/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify([product.to_dict() for product in products])


@mobile_app_bp.route('/featured-products', methods=['GET'])
def get_featured_products():
    products = Product.query.filter_by(featured=True).all()
    return jsonify([product.to_dict() for product in products])


@mobile_app_bp.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get(product_id)
    return jsonify(product.to_dict())


@mobile_app_bp.route('/product-categories', methods=['GET'])
def get_product_categories():
    categories = Product.query.with_entities(Product.category).distinct().all()
    print(categories)
    return jsonify([category[0] for category in categories])
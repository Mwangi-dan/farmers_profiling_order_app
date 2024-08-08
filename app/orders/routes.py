from flask import Blueprint, request, jsonify
from app.models import db, Order

orders_bp = Blueprint('orders', __name__)


@orders_bp.route('/orders', methods=['GET'])
@orders_bp.route('/', methods=['GET'])
def get_orders():
    orders = Order.query.all()
    return jsonify([order.to_dict() for order in orders])


@orders_bp.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json()

    if not data or not all(key in data for key in ('user_id', 'product_id', 'quantity', 'total_price')):
        return jsonify({"error": "Missing data"}), 400
    

    new_order = Order(
        user_id=data['user_id'],
        product_id=data['product_id'],
        quantity=data['quantity'],
        total_price=data['total_price'],
        status='pending'
    )
    db.session.add(new_order)
    db.session.commit()
    return jsonify(new_order.to_dict()), 201


@orders_bp.route('/orders/<int:id>', methods=['GET'])
def get_order(id):
    order = Order.query.get_or_404(id)
    return jsonify(order.to_dict())


@orders_bp.route('/orders/<int:id>', methods=['PUT'])
def update_order(id):
    order = Order.query.get_or_404(id)
    data = request.get_json()

    if 'status' not in data:
        return jsonify({"error": "Missing status field"}), 400
    

    order.status = data['status']
    db.session.commit()
    return jsonify(order.to_dict())


@orders_bp.route('/orders/<int:id>', methods=['DELETE'])
def delete_order(id):
    order = Order.query.get_or_404(id)
    db.session.delete(order)
    db.session.commit()
    return '', 204


@orders_bp.route('/orders/user/<int:user_id>', methods=['GET'])
def get_user_orders(user_id):
    orders = Order.query.filter_by(user_id=user_id).all()
    return jsonify([order.to_dict() for order in orders])

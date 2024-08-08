from flask import Blueprint, request, jsonify
from app.models import db, Product, Supplier
from app.utils.image_helper import save_image

products_bp = Blueprint('products', __name__)


@products_bp.route('/products', methods=['GET'])
@products_bp.route('/', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify([product.to_dict() for product in products])


@products_bp.route('/products', methods=['POST'])
def create_product():
    data = request.form
    image = request.files.get('image')
    image_url = save_image(image) if image else None

    supplier_id = data.get('supplier_id')
    supplier = Supplier.query.get(supplier_id) if supplier_id else None

    new_product = Product(
        name=data.get('name'),
        description=data.get('description'),
        price=data.get('price'),
        image_url=image_url,
        supplier=supplier
    )
    db.session.add(new_product)
    db.session.commit()
    return jsonify(new_product.to_dict()), 201


@products_bp.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    product = Product.query.get_or_404(id)
    return jsonify(product.to_dict())


@products_bp.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    product = Product.query.get_or_404(id)
    data = request.form
    image = request.files.get('image')
    image_url = save_image(image) if image else product.image_url

    supplier_id = data.get('supplier_id')
    supplier = Supplier.query.get(supplier_id) if supplier_id else None

    product.name = data.get('name')
    product.description = data.get('description')
    product.price = data.get('price')
    product.image_url = image_url
    product.supplier = supplier

    db.session.commit()
    return jsonify(product.to_dict())


@products_bp.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return '', 204
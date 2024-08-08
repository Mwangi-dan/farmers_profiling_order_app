from flask import Blueprint, request, jsonify
from app.models import db, Supplier, Product
from app.utils.image_helper import save_image

suppliers_bp = Blueprint('suppliers', __name__)


@suppliers_bp.route('/suppliers', methods=['GET'])
@suppliers_bp.route('/', methods=['GET'])
def get_suppliers():
    suppliers = Supplier.query.all()
    return jsonify([supplier.to_dict() for supplier in suppliers])


@suppliers_bp.route('/suppliers', methods=['POST'])
def create_supplier():
    data = request.form
    first_name = data.get('fname')
    last_name = data.get('lname')
    nin = data.get('nin')
    company_name = data.get('company_name')
    contact_person = data.get('contact_person')
    telephone = data.get('telephone')
    email = data.get('email')
    location = data.get('location')
    image = request.files.get('image')
    image_url = save_image(image) if image else None

    new_supplier = Supplier(
        name=first_name,
        lastname=last_name,
        nin=nin,
        company_name=company_name,
        contact_person=contact_person,
        telephone=telephone,
        email=email,
        location=location,
        photo=image_url
    )
    db.session.add(new_supplier)
    db.session.commit()
    return jsonify(new_supplier.to_dict()), 201


@suppliers_bp.route('/suppliers/<int:id>', methods=['GET'])
def get_supplier(id):
    supplier = Supplier.query.get_or_404(id)
    return jsonify(supplier.to_dict())

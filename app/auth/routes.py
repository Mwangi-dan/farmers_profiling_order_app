from flask import Blueprint, request, jsonify, flash, redirect, render_template, url_for, make_response, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required, get_jwt_identity,
    set_access_cookies, set_refresh_cookies, unset_jwt_cookies
)
from flask_uploads import UploadSet, IMAGES
from werkzeug.utils import secure_filename
from app import db
from app.models import User, Farmer, Supplier, Admin
from flask import current_app
from flask_wtf.csrf import CSRFError
from app.forms import (
    RegistrationForm, LoginForm, 
    FarmerRegistrationForm, SupplierRegistrationForm
    )

auth = Blueprint('auth', __name__)

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    print("signing up")
    form = RegistrationForm()
    if form.validate_on_submit():
        print("here now")
        hashed_password = generate_password_hash(form.password.data)
        user = Admin(
            name=form.name.data,
            lastname=form.lastname.data,
            email=form.email.data,
            gender=form.gender.data,
            telephone=format_number(form.nationality.data, form.telephone.data),
            nationality=form.nationality.data,
            role=form.role.data,
            location=form.location.data,
            latitude=form.latitude.data,
            longitude=form.longitude.data,
            password_hash=hashed_password,
            date_of_birth=form.date_of_birth.data
        )
        db.session.add(user)
        db.session.commit()
        print("Account created succesfully")
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('auth.login'))
    else:
        print("Form did not validate")
        for field, errors in form.errors.items():
            for error in errors:
                print(f"Error in {field}: {error}")
    google_maps_api_key = current_app.config['GOOGLE_MAPS_API_KEY']
    return render_template('signup.html', form=form, google_maps_api_key=google_maps_api_key)


@auth.route('/signup_farmer', methods=['GET', 'POST'])
def signup_farmer():
    form = FarmerRegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        farmer = Farmer(
            name=form.name.data,
            email=form.email.data,
            telephone=format_number(form.country.data, form.telephone.data),
            location=form.location.data,
            latitude=form.latitude.data,
            longitude=form.longitude.data,
            role='farmer',
            nin=form.nin.data,
            group_name=form.group_name.data,
            land_size=form.land_size.data,
            crop=form.crop.data,
            last_yield=form.last_yield.data,
            bank_account=form.bank_account.data,
            gender=form.gender.data,
            date_of_birth=form.date_of_birth.data,
            password_hash=hashed_password
        )
        db.session.add(farmer)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('auth.login'))
    return render_template('signup_farmer.html', form=form)


@auth.route('/signup_supplier', methods=['GET', 'POST'])
def signup_supplier():
    form = SupplierRegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        supplier = Supplier(
            name=form.name.data,
            email=form.email.data,
            telephone=format_number(form.country.data, form.telephone.data),
            location=form.location.data,
            latitude=form.latitude.data,
            longitude=form.longitude.data,
            role='supplier',
            company_name=form.company_name.data,
            nin = form.nin.data,
            products=form.products.data,
            contact_person=form.contact_person.data,
            password_hash=hashed_password
        )
        db.session.add(supplier)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('auth.login'))
    return render_template('signup_supplier.html', form=form)



@auth.route('/login', methods=['GET', 'POST'])
@auth.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(telephone=form.telephone.data, role='admin').first()
        if user and check_password_hash(user.password_hash, form.password.data):
            access_token = create_access_token(identity={'telephone': user.telephone})
            refresh_token = create_refresh_token(identity={'telephone': user.telephone})
            response = make_response(redirect(url_for('admin.dashboard')))
            set_access_cookies(response, access_token)
            set_refresh_cookies(response, refresh_token)
            return response
        else:
            flash('Login Unsuccessful. Please check telephone and password', 'danger')
    return render_template('login.html', form=form)


@auth.route('/logout')
@jwt_required()
def logout():
    response = make_response(redirect(url_for('auth.login')))
    unset_jwt_cookies(response)
    return response


@auth.route('/token/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    response = jsonify({'refresh': True})
    set_access_cookies(response, access_token)
    return response, 200



@auth.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    user = User.query.filter_by(telephone=data.get('telephone')).first()

    if user and check_password_hash(user.password_hash, data.get('password')):
        access_token = create_access_token(identity={'telephone': user.telephone, 'role': user.role})
        refresh_token = create_refresh_token(identity={'telephone': user.telephone, 'role': user.role})

        return jsonify({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "name": user.name,
                "email": user.email,
                "telephone": user.telephone,
                "role": user.role
            }
        }), 200
    else:
        return jsonify({"message": "Invalid phone number or password"}), 401




def format_number(country, number):
    if country == 'Kenya':
        if number.startswith('0'):
            number = '+254' + number[1:]
    elif country == 'Uganda':
        if number.startswith('0'):
            number = '+256' + number[1:]
    else:
        number=number

    return number
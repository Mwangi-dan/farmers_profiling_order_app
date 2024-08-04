from flask import Blueprint, request, jsonify, flash, redirect, render_template, url_for, make_response, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required, get_jwt_identity,
    set_access_cookies, set_refresh_cookies, unset_jwt_cookies
)
from app import db
from app.models import User
from flask_wtf.csrf import CSRFError
from app.forms import RegistrationForm, LoginForm

auth = Blueprint('auth', __name__)

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    print("signing up")
    form = RegistrationForm()
    if form.validate_on_submit():
        print("here now")
        hashed_password = generate_password_hash(form.password.data)
        user = User(
            name=form.name.data,
            email=form.email.data,
            gender=form.gender.data,
            telephone=form.telephone.data,
            nationality=form.nationality.data,
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


@auth.route('/login', methods=['GET', 'POST'])
@auth.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(telephone=form.telephone.data).first()
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

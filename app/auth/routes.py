from flask import Blueprint, request, jsonify, flash, redirect, render_template, url_for, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required
from app import db
from app.models import User
from app.forms import RegistrationForm, LoginForm

auth = Blueprint('auth', __name__)

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user = User(name=form.name.data, telephone=form.telephone.data, location=form.location.data, password_hash=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('auth.login'))
    return render_template('signup.html', form=form)


@auth.route('/login', methods=['GET', 'POST'])
@auth.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(telephone=form.telephone.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            access_token = create_access_token(identity={'telephone': user.telephone})
            response = make_response(redirect(url_for('admin.dashboard')))
            response.set_cookie('access_token', access_token, httponly=True)
            flash('You have been logged in!', 'success')
            return response
        else:
            flash('Login Unsuccessful. Please check telephone and password', 'danger')
    return render_template('login.html', form=form)

@auth.route('/logout')
@jwt_required()
def logout():
    response = make_response(redirect(url_for('auth.login')))
    response.set_cookie('access_token', '', expires=0)
    flash('You have been logged out!', 'success')
    return response
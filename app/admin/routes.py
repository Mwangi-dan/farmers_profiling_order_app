from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, make_response, send_file
from flask_jwt_extended import (
    create_access_token, create_refresh_token, set_access_cookies, 
    jwt_required, get_jwt_identity, set_refresh_cookies, verify_jwt_in_request
)
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash
from app.models import User, Issue, Order
import csv
from io import StringIO, BytesIO
from app import db
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from config import ISSUE_STATUS, ORDER_STATUS
from app.forms import RegistrationForm, LoginForm
from datetime import datetime, timedelta

admin = Blueprint('admin', __name__)

csrf = CSRFProtect()



@admin.route('/login', methods=['GET', 'POST'])
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
            flash('You have been logged in!', 'success')
            return response
        else:
            flash('Login Unsuccessful. Please check telephone and password', 'danger')
    return render_template('login.html', form=form)


@admin.route('/register', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        telephone = request.form['telephone']
        password = request.form['password']
        location = request.form['location']
        new_user = User(name=name, telephone=telephone, location=location)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('admin.login'))
    return render_template('signup.html')


@admin.before_request
def before_request():
    verify_jwt_in_request(optional=True)
    token = request.cookies.get('access_token')
    if token:
        request.headers['Authorization'] = f'Bearer {token}'


@admin.route('/dashboard')
@jwt_required()
def dashboard():
    # add a check if user is authenticated or not
    if not get_jwt_identity():
        return redirect(url_for('admin.login'))

    current_user_identity = get_jwt_identity()
    current_user = User.query.filter_by(telephone=current_user_identity['telephone']).first()
    users = User.query.all()
    issues = Issue.query.all()
    orders = Order.query.all()

    # Calculate the start of today and the start of this week
    today = datetime.utcnow().date()
    start_of_week = today - timedelta(days=today.weekday())

    # Query for today's orders
    orders_today = Order.query.filter(Order.created_at >= today).count()

    # Query for this week's orders
    orders_this_week = Order.query.filter(Order.created_at >= start_of_week).count()

    return render_template(
        'dashboard.html',
        current_user=current_user,
        users=users,
        user_count=len(users),
        issues=issues, 
        orders=orders,
        issue_count=len(issues),
        orders_today=orders_today,
        orders_this_week=orders_this_week
        )


@admin.route('/issues/<int:issue_id>/status', methods=['PUT'])
@jwt_required()
def update_issue_status(issue_id):
    issue = Issue.query.get(issue_id)
    if not issue:
        return jsonify({'error': 'Issue not found'}), 404

    new_status = request.json.get('status')
    if new_status not in ISSUE_STATUS:
        return jsonify({'error': 'Invalid status'}), 400

    issue.status = new_status
    db.session.commit()
    return jsonify(issue.serialize()), 200


@admin.route('/orders/<int:order_id>/status', methods=['PUT'])
@jwt_required()
def update_order_status(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404

    new_status = request.json.get('status')
    if new_status not in ORDER_STATUS:
        return jsonify({'error': 'Invalid status'}), 400

    order.status = new_status
    db.session.commit()
    return jsonify(order.serialize()), 200


@admin.route('/users/add', methods=['GET', 'POST'])
@jwt_required()
def add_user():
    if request.method == 'POST':
        name = request.form['name']
        telephone = request.form['telephone']
        password = request.form['password']
        location = request.form['location']
        new_user = User(name=name, telephone=telephone, location=location)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('admin.get_users'))
    return render_template('add_user.html')

@admin.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@jwt_required()
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    print("Route accessed")
    if request.method == 'POST':
        print("Form submitted")
        user.name = request.form['name']
        user.gender = request.form['gender']
        user.telephone = request.form['telephone']
        user.location = request.form['location']
        print(f"Updated data: Name={user.name}, Gender={user.gender}, Telephone={user.telephone}, Location={user.location}")
        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('admin.get_users'))
    return render_template('edit_users.html', user=user)

@admin.route('/users/delete/<int:user_id>', methods=['POST'])
@jwt_required()
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('admin.get_users'))

@admin.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    current_user_identity = get_jwt_identity()
    current_user = User.query.filter_by(telephone=current_user_identity['telephone']).first()
    users = User.query.all()
    return render_template('users.html', users=users, current_user=current_user)


# page to view more info of users
@admin.route('/view_user/<int:user_id>', methods=['GET'])
@jwt_required()
def view_user(user_id):
    current_user_identity = get_jwt_identity()
    current_user = User.query.filter_by(telephone=current_user_identity['telephone']).first()
    user = User.query.get_or_404(user_id)
    return render_template('view_user.html', user=user, current_user=current_user)


@admin.route('/issues')
@jwt_required()
def get_issues():
    issues = Issue.query.all()
    current_user_identity = get_jwt_identity()
    current_user = User.query.filter_by(telephone=current_user_identity['telephone']).first()
    return render_template('issues.html', issues=issues, current_user=current_user)


@admin.route('/orders')
@jwt_required()
def get_orders():
    orders = Order.query.all()
    current_user_identity = get_jwt_identity()
    current_user = User.query.filter_by(telephone=current_user_identity['telephone']).first()
    return render_template('orders.html', orders=orders, current_user=current_user)


@admin.route('/api/users', methods=['GET'])
@jwt_required()
def api_get_users():
    users = User.query.all()
    return jsonify([user.serialize() for user in users])


@admin.route('/api/issues', methods=['GET'])
@jwt_required()
def api_get_issues():
    issues = Issue.query.all()
    return jsonify([issue.serialize() for issue in issues])


@admin.route('/profile/<int:user_id>', methods=['GET', 'POST'])
@jwt_required()
def profile(user_id):
    active = active
    current_user_identity = get_jwt_identity()
    current_user = User.query.filter_by(telephone=current_user_identity['telephone']).first()
    user = User.query.get_or_404(user_id)
    return render_template('profile.html', user=user, current_user=current_user, active=active)


# Edit profile route
@admin.route('/edit_profile/<int:user_id>', methods=['POST'])
@jwt_required()
# @csrf.protect()
def edit_profile(user_id):
    csrf.generate_csrf()
    user = User.query.get_or_404(user_id)
    
    if 'photo' in request.files:
        photo = request.files['photo']
        if photo.filename != '':
            user.photo = photo.read()  # Read and store the binary data
    
    user.name = request.form['name']
    user.telephone = request.form['telephone']
    user.location = request.form['location']
    user.group_name = request.form['group_name']
    user.land_size = request.form.get('land_size', type=float)
    user.crop = request.form['crop']
    user.last_yield = request.form.get('last_yield', type=float)
    user.bank_account = request.form.get('bank_account') == 'True'
    user.gender = request.form['gender']
    user.date_of_birth = request.form.get('date_of_birth', type=lambda d: datetime.strptime(d, '%Y-%m-%d'))

    db.session.commit()
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('admin.profile', user_id=user.id))

@admin.route('/api/orders', methods=['GET'])
@jwt_required()
def api_get_orders():
    orders = Order.query.all()
    return jsonify([order.serialize() for order in orders])


@admin.route('/export/users/csv')
@jwt_required()
def export_users_csv():
    users = User.query.all()

    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID', 'Name', 'Telephone', 'Location'])
    for user in users:
        cw.writerow([user.id, user.name, user.telephone, user.location])

    response = make_response(si.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=users.csv'
    response.headers['Content-type'] = 'text/csv'
    return response


@admin.route('/export/issues/csv')
@jwt_required()
def export_issues_csv():
    issues = Issue.query.all()

    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID', 'User ID', 'Issue Text', 'Status'])
    for issue in issues:
        cw.writerow([issue.id, issue.user_id, issue.issue_text, issue.status])

    response = make_response(si.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=issues.csv'
    response.headers['Content-type'] = 'text/csv'
    return response


@admin.route('/export/orders/csv')
@jwt_required()
def export_orders_csv():
    orders = Order.query.all()

    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID', 'User ID', 'Product Name', 'Quantity', 'Status'])
    for order in orders:
        cw.writerow([order.id, order.user_id, order.product_name, order.quantity, order.status])

    response = make_response(si.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=orders.csv'
    response.headers['Content-type'] = 'text/csv'
    return response


@admin.route('/export/users/pdf')
@jwt_required()
def export_users_pdf():
    users = User.query.all()

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    c.drawString(100, height - 40, 'Users Report')
    y = height - 60

    c.drawString(30, y, 'ID')
    c.drawString(100, y, 'Name')
    c.drawString(200, y, 'Telephone')
    c.drawString(300, y, 'Location')

    y -= 20

    for user in users:
        c.drawString(30, y, str(user.id))
        c.drawString(100, y, user.name)
        c.drawString(200, y, user.telephone)
        c.drawString(300, y, user.location)
        y -= 20
        if y < 40:  # Check for page overflow
            c.showPage()
            y = height - 40
            c.drawString(30, y, 'ID')
            c.drawString(100, y, 'Name')
            c.drawString(200, y, 'Telephone')
            c.drawString(300, y, 'Location')
            y -= 20

    c.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name='users_report.pdf', mimetype='application/pdf')



@admin.route('/export/issues/pdf')
@jwt_required()
def export_issues_pdf():
    issues = Issue.query.all()

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    c.drawString(100, height - 40, 'Issues Report')
    y = height - 60

    c.drawString(30, y, 'ID')
    c.drawString(100, y, 'User ID')
    c.drawString(200, y, 'Issue Text')
    c.drawString(400, y, 'Status')

    y -= 20

    for issue in issues:
        c.drawString(30, y, str(issue.id))
        c.drawString(100, y, str(issue.user_id))
        c.drawString(200, y, issue.issue_text)
        c.drawString(400, y, issue.status)
        y -= 20
        if y < 40:  # Check for page overflow
            c.showPage()
            y = height - 40
            c.drawString(30, y, 'ID')
            c.drawString(100, y, 'User ID')
            c.drawString(200, y, 'Issue Text')
            c.drawString(400, y, 'Status')
            y -= 20

    c.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name='issues_report.pdf', mimetype='application/pdf')


@admin.route('/export/orders/pdf')
@jwt_required()
def export_orders_pdf():
    orders = Order.query.all()

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    c.drawString(100, height - 40, 'Orders Report')
    y = height - 60

    c.drawString(30, y, 'ID')
    c.drawString(100, y, 'User ID')
    c.drawString(200, y, 'Product Name')
    c.drawString(300, y, 'Quantity')
    c.drawString(400, y, 'Status')

    y -= 20

    for order in orders:
        c.drawString(30, y, str(order.id))
        c.drawString(100, y, str(order.user_id))
        c.drawString(200, y, order.product_name)
        c.drawString(300, y, str(order.quantity))
        c.drawString(400, y, order.status)
        y -= 20
        if y < 40:  # Check for page overflow
            c.showPage()
            y = height - 40
            c.drawString(30, y, 'ID')
            c.drawString(100, y, 'User ID')
            c.drawString(200, y, 'Product Name')
            c.drawString(300, y, 'Quantity')
            c.drawString(400, y, 'Status')
            y -= 20

    c.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name='orders_report.pdf', mimetype='application/pdf')


@admin.route('/logout')
def logout():
    response = make_response(redirect(url_for('admin.login')))
    response.set_cookie('access_token', '', expires=0)
    return response
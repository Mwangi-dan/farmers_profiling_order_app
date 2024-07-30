from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, make_response, send_file
from flask_jwt_extended import create_access_token, set_access_cookies, jwt_required, get_jwt_identity, verify_jwt_in_request
from werkzeug.security import check_password_hash
from app.models import User, Issue, Order
import csv
from io import StringIO, BytesIO
from app import db
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from config import ISSUE_STATUS, ORDER_STATUS

admin = Blueprint('admin', __name__)

@admin.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        telephone = request.form.get('telephone')
        password = request.form.get('password')
        user = User.query.query.filter_by(telephone=telephone).first()

        if user and check_password_hash(user.password, password):
            access_token = create_access_token(identity={'telephone':user.telephone})
            response = redirect(url_for(admin.dashboard))
            set_access_cookies(response, access_token)
            return response
        else:
            flash('Invalid telephone number or password')
    return render_template('login.html')


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
        request.headers = {'Authorization': f'Bearer {token}'}


@admin.route('/dashboard')
@jwt_required()
def dashboard():
    # add a check if user is authenticated or not
    if not get_jwt_identity():
        return redirect(url_for('admin.login'))

    current_user = get_jwt_identity()
    users = User.query.all()
    issues = Issue.query.all()
    orders = Order.query.all()

    user_labels = [user.name for user in users]
    user_counts = [1 for _ in users]  # Example: Count 1 per user

    issue_labels = [issue.status for issue in issues]
    issue_counts = [issue_labels.count(status) for status in set(issue_labels)]

    order_labels = [order.status for order in orders]
    order_counts = [order_labels.count(status) for status in set(order_labels)]


    return render_template(
        'dashboard.html', 
        users=users, 
        issues=issues, 
        orders=orders,
        user_labels=user_labels,
        user_counts=user_counts,
        issue_labels=issue_labels,
        issue_counts=issue_counts,
        order_labels=order_labels,
        order_counts=order_counts)


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

@admin.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@jwt_required()
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.name = request.form['name']
        user.telephone = request.form['telephone']
        user.location = request.form['location']
        if request.form['password']:
            user.set_password(request.form['password'])
        db.session.commit()
        return redirect(url_for('admin.get_users'))
    return render_template('edit_user.html', user=user)

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
    users = User.query.all()
    return render_template('users.html', users=users)


@admin.route('/issues')
@jwt_required()
def get_issues():
    issues = Issue.query.all()
    return render_template('issues.html', issues=issues)

@admin.route('/orders')
@jwt_required()
def get_orders():
    orders = Order.query.all()
    return render_template('orders.html', orders=orders)


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
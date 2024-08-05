import io
from flask import Blueprint, g, render_template, request, redirect, url_for, flash, jsonify, make_response, send_file
from flask_jwt_extended import (
    create_access_token, create_refresh_token, set_access_cookies, 
    jwt_required, get_jwt_identity, set_refresh_cookies, verify_jwt_in_request
)
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash, generate_password_hash
from app.models import User, Issue, Order, Admin, Farmer, Supplier
import csv
from io import StringIO, BytesIO
from app import db
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from config import ISSUE_STATUS, ORDER_STATUS, allowed_file
from app.forms import (
    LoginForm, EditProfileForm, ReportGenerationForm,
    EditUserForm ,ChangePasswordForm
    )
from datetime import datetime, timedelta
from flask_uploads import UploadSet, IMAGES
from werkzeug.utils import secure_filename
from flask import current_app

import os

admin = Blueprint('admin', __name__)

csrf = CSRFProtect()

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
        role = request.form['role']
        new_user = role.capitalize()(name=name, telephone=telephone, location=location)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('admin.get_users'))
    return render_template('add_user.html')

@admin.route('/edit_user/<int:user_id>', methods=['POST'])
@jwt_required()
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = EditUserForm(obj=user)

    if form.validate_on_submit():
        user.name = form.name.data
        user.gender = form.gender.data
        user.telephone = form.telephone.data
        user.location = form.location.data

        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('admin.get_users'))

    flash('Error updating user.', 'danger')
    return redirect(url_for('admin.get_users'))

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
    current_user_identity = get_jwt_identity()
    current_user = User.query.filter_by(telephone=current_user_identity['telephone']).first()
    form = EditProfileForm(obj=current_user)
    user = User.query.get_or_404(user_id)
    return render_template('profile.html', user=user, current_user=current_user, form=form)


# Edit profile route
photos = UploadSet('photos', IMAGES)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@admin.route('/edit_profile/<int:user_id>', methods=['GET', 'POST'])
@jwt_required()
def edit_profile(user_id):
    current_user_identity = get_jwt_identity()
    current_user = User.query.filter_by(telephone=current_user_identity['telephone']).first()

    user = User.query.get_or_404(user_id)
    form = EditProfileForm(obj=user)
    
    if form.validate_on_submit():
        user.name = form.name.data
        user.email = form.email.data
        user.gender = form.gender.data
        user.telephone = form.telephone.data
        user.location = form.location.data
        user.date_of_birth = form.date_of_birth.data
        
        if 'photo' in request.files:
            photo = request.files['photo']
            if photo and allowed_file(photo.filename):
                filename = secure_filename(photo.filename)
                upload_folder = current_app.config['UPLOAD_FOLDER']
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

                if user.photo and user.photo != 'default.jpg':
                    old_photo_path = os.path.join(upload_folder, user.photo)
                    if os.path.exists(old_photo_path):
                        os.remove(old_photo_path)

                photo.save(filepath)
                user.photo = filename  # Save the filename to the database
            else:
                flash('File type not allowed. Allowed types are png, jpg, jpeg', 'danger')
                return redirect(url_for('admin.profile', user_id=user.id, current_user=current_user))
        else:
            flash('No file uploaded or file size exceeds limit.', 'danger')
            return redirect(url_for('admin.profile', user_id=user.id, current_user=current_user))
        
        db.session.commit()
        flash('Profile updated successfully!', 'success-profile')
        return redirect(url_for('admin.profile', user_id=user.id, current_user=current_user))
    
    return render_template('profile.html', form=form, user=user, current_user=user)



@admin.route('/change_password', methods=['GET', 'POST'])
@jwt_required()
def change_password():
    current_user_identity = get_jwt_identity()
    current_user = User.query.filter_by(telephone=current_user_identity['telephone']).first()
    user = current_user
    form = ChangePasswordForm(obj=user)
    if form.validate_on_submit():
        
        if check_password_hash(user.password_hash, form.current_password.data):
            user.password_hash = generate_password_hash(form.new_password.data)
            db.session.commit()
            flash('Your password has been updated!', 'success')
            return redirect(url_for('admin.profile', user_id=user.id))
        else:
            flash('Current password is incorrect.', 'danger')
    return render_template('change_password.html', form=form, current_user=current_user, user=user)




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


@admin.route('/report_generation', methods=['GET', 'POST'])
@jwt_required()
def report_generation():
    current_user_identity = get_jwt_identity()
    current_user = User.query.filter_by(telephone=current_user_identity['telephone']).first()
    form = ReportGenerationForm()
    if form.validate_on_submit():
        report_type = form.report_type.data
        start_date = form.start_date.data
        end_date = form.end_date.data

        # Generate the report based on the selected criteria
        report_data = generate_report(report_type, start_date, end_date)

        # Optionally, provide the report for download as a CSV file
        output = io.StringIO()
        writer = csv.writer(output)
        if report_type == 'users':
            writer.writerow(['ID', 'Name', 'Email', 'Telephone', 'Location', 'Date of Birth'])
            for user in report_data:
                writer.writerow([user.id, user.name, user.email, user.telephone, user.location, user.date_of_birth])
        elif report_type == 'orders':
            writer.writerow(['ID', 'User', 'Product', 'Price', 'Status'])
            for order in report_data:
                writer.writerow([order.id, order.user_id, order.product_name, order.price, order.status])
        elif report_type == 'issues':
            writer.writerow(['ID', 'User', 'Issue', 'Status', 'Created At'])
            for issue in report_data:
                writer.writerow([issue.id, issue.user_id, issue.description, issue.status, issue.created_at])

        response = make_response(output.getvalue())
        response.headers['Content-Disposition'] = 'attachment; filename=report.csv'
        response.headers['Content-type'] = 'text/csv'
        return response

    return render_template('report_generation.html', form=form, current_user=current_user)


def generate_report(report_type, start_date, end_date):
    if report_type == 'users':
        return User.query.filter(User.created_at.between(start_date, end_date)).all()
    elif report_type == 'orders':
        return Order.query.filter(Order.created_at.between(start_date, end_date)).all()
    elif report_type == 'issues':
        return Issue.query.filter(Issue.created_at.between(start_date, end_date)).all()
    return []


@admin.route('/logout')
def logout():
    response = make_response(redirect(url_for('admin.login')))
    response.set_cookie('access_token', '', expires=0)
    return response



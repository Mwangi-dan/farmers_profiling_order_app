import io
from flask import Blueprint, g, render_template, request, redirect, url_for, flash, jsonify, make_response, send_file
from flask_jwt_extended import (
    create_access_token, create_refresh_token, set_access_cookies, 
    jwt_required, get_jwt_identity, set_refresh_cookies, verify_jwt_in_request
)
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash, generate_password_hash
from app.models import User, Issue, Order, Admin, Farmer, Supplier, Product, Category
import csv
from io import StringIO, BytesIO
from app import db
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from config import ISSUE_STATUS, ORDER_STATUS, allowed_file
from app.forms import (
    LoginForm, EditProfileForm, ReportGenerationForm,
    EditUserForm ,ChangePasswordForm, NewProductForm
    )
from datetime import datetime, timedelta
from flask_uploads import UploadSet, IMAGES
from werkzeug.utils import secure_filename
from flask import current_app
from app.utils.image_helper import save_image

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
    products = Product.query.all()

    # Calculate the start of today and the start of this week
    today = datetime.utcnow().date()
    start_of_week = today - timedelta(days=today.weekday())

    # Query for today's orders
    orders_today = Order.query.filter(Order.created_at >= today).count()

    # Query for this week's orders
    orders_this_week = Order.query.filter(Order.created_at >= start_of_week).count()

    # Recent products listed
    recent_products = Product.query.order_by(Product.created_at.desc()).limit(5).all()

    return render_template(
        'dashboard.html',
        current_user=current_user,
        users=users,
        user_count=len(users),
        issues=issues, 
        orders=orders,
        issue_count=len(issues),
        orders_today=orders_today,
        orders_this_week=orders_this_week,
        products=recent_products
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

@admin.route('/edit_user/<int:user_id>', methods=['POST', 'GET'])
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
    user = User.query.get_or_404(user_id)
    form = EditProfileForm(obj=user)
    
    if form.validate_on_submit():
        user.name = form.name.data
        user.lastname = form.lastname.data
        user.email = form.email.data
        user.gender = form.gender.data
        user.telephone = form.telephone.data
        user.location = form.location.data
        user.date_of_birth = form.date_of_birth.data
        db.session.commit()
        flash('Profile updated successfully!', 'success-profile')
        
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
                db.session.commit()
            else:
                flash('File type not allowed. Allowed types are png, jpg, jpeg', 'danger')
                return redirect(url_for('admin.profile', user_id=user.id, current_user=current_user()))
            
            return redirect(url_for('admin.profile', user_id=user.id, current_user=current_user()))
    
        else:
            flash('No file uploaded or file size exceeds limit.', 'danger')
            return redirect(url_for('admin.profile', user_id=user.id, current_user=current_user()))
        
 
        
    else:
        print(form.errors)
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

def current_user():
    current_user_identity = get_jwt_identity()
    current_user = User.query.filter_by(telephone=current_user_identity['telephone']).first()
    return current_user

############### SUPPLIERS ####################

@admin.route('/suppliers', methods=['GET'])
@jwt_required()
def admin_suppliers():
    suppliers = Supplier.query.all()
    return render_template('suppliers/suppliers.html', suppliers=suppliers, current_user=current_user())

@admin.route('/suppliers/new', methods=['GET'])
def new_supplier():
    return render_template('create_supplier.html')

@admin.route('/suppliers/new', methods=['POST'])
def create_supplier():
    data = request.form
    first_name = data.get('fname')
    last_name = data.get('lname')
    nin = data.get('nin')
    gender= data.get('gender')
    company_name = data.get('company_name')
    contact_person = data.get('contact_person')
    telephone = data.get('telephone')
    country = data.get('country')
    email = data.get('email')
    location = data.get('location')
    image = request.files.get('image')
    image_url = save_image(image) if image else None


    try:
        supplier = Supplier.query.filter_by(telephone=telephone, nin=nin, email=email).first()
        if supplier:
            flash('Supplier already exists!', 'danger')
            return redirect(url_for('admin.admin_suppliers'))
        else:
            new_supplier = Supplier(
            name=first_name,
            lastname=last_name,
            nin=nin,
            gender=gender,
            company_name=company_name,
            contact_person=contact_person,
            telephone=format_number(country, telephone),
            email=email,
            nationality=country,
            location=location,
            photo=image_url,
            role='supplier',
            password_hash=generate_password_hash('password')
             )
            db.session.add(new_supplier)
            db.session.commit()
            flash('Supplier created successfully!', 'success-supplier')
    except Exception as e:
        flash(f'Error creating supplier!\n {e}', 'danger-supplier')
        return redirect(url_for('admin.admin_suppliers'))
    
    return redirect(url_for('admin.admin_suppliers'))
    

@admin.route('/suppliers/edit/<int:id>', methods=['GET'])
def edit_supplier(id):
    supplier = Supplier.query.get_or_404(id)
    return render_template('suppliers/edit_supplier.html', supplier=supplier, current_user=current_user())

@admin.route('/suppliers/edit/<int:id>', methods=['POST'])
@jwt_required()
def update_supplier(id):
    supplier = Supplier.query.get_or_404(id)
    data = request.form
    image = request.files.get('image')
    image_url = save_image(image) if image else supplier.photo

    supplier.name = data.get('name')
    supplier.lastname = data.get('lname')
    supplier.nin = data.get('nin')
    supplier.gender = data.get('gender')
    supplier.company_name = data.get('company_name')
    supplier.contact_person = data.get('contact_person')
    supplier.telephone = data.get('telephone')
    supplier.email = data.get('email')
    supplier.location = data.get('location')
    supplier.photo = image_url

    db.session.commit()
    flash('Supplier updated successfully!', 'success-supplier')
    return redirect(url_for('admin.edit_supplier', id=supplier.id))

@admin.route('/suppliers/delete/<int:id>', methods=['POST'])
def delete_supplier(id):
    supplier = Supplier.query.get_or_404(id)
    db.session.delete(supplier)
    db.session.commit()
    flash('Supplier deleted successfully!', 'success-supplier')
    return redirect(url_for('admin.admin_suppliers'))



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



################# PRODUCTS ####################
@admin.route('/products', methods=['GET'])
@jwt_required()
def admin_products():
    products = Product.query.all()
    return render_template('products/products.html', products=products, current_user=current_user())


@admin.route('/products/<int:id>', methods=['GET'])
@jwt_required()
def view_product(id):
    product = Product.query.get_or_404(id)
    user = current_user()
    nationality = user.nationality
    return render_template('products/view_product.html', product=product, current_user=current_user(), price=currency_conversion(nationality, product.price, product))



@jwt_required()
@admin.route('/new_product', methods=['GET', 'POST'])
def new_product():
    form = NewProductForm()
    if form.validate_on_submit():
        # Check if a new supplier was entered
        if form.new_supplier.data:
            supplier = Supplier(name=form.new_supplier.data)
            db.session.add(supplier)
            db.session.commit()
        else:
            supplier = Supplier.query.get(form.supplier.data)

        # Create the new product
        new_product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            quantity=form.quantity.data,
            image_url=form.image.data.filename if form.image.data else None,
            # category_id=category.id,
            supplier_id=supplier.id
        )

        # Save the product image if uploaded
        if form.image.data:
            photo = request.files['image']
            if photo and allowed_file(photo.filename):
                filename = secure_filename(photo.filename)
                upload_folder = current_app.config['PRODUCT_UPLOAD_FOLDER']
                filepath = os.path.join(upload_folder, filename)
                photo.save(filepath)
                new_product.image_url = filename

        db.session.add(new_product)
        db.session.commit()

        flash('Product added successfully!', 'success')
        return redirect(url_for('admin.admin_products'))
    else:
        print(form.errors)
    return render_template('products/create_product.html', form=form, current_user=current_user())


@admin.route('/products/edit/<int:id>', methods=['GET', 'POST'])
@jwt_required()
def edit_product(id):
    product = Product.query.get_or_404(id)
    sup = Supplier.query.get(product.supplier_id)
    form = NewProductForm(obj=product)

    form.submit.label.text = "Edit Product"

    if form.validate_on_submit():
        # Check if a new supplier was entered
        if form.new_supplier.data:
            supplier = Supplier(name=form.new_supplier.data)
            db.session.add(supplier)
            db.session.commit()
        else:
            supplier = Supplier.query.get(form.supplier.data)

        product.name = form.name.data
        product.description = form.description.data
        product.price = form.price.data
        product.quantity = form.quantity.data
        product.image_url = form.image.data.filename if form.image.data else product.image_url
        product.category = form.category.data
        product.supplier = supplier
        product.featured = form.featured.data
        product.currency = form.currency.data

        # Save the product image if uploaded
        if form.image.data:
            photo = request.files['image']
            if photo and allowed_file(photo.filename):
                filename = secure_filename(photo.filename)
                upload_folder = current_app.config['PRODUCT_UPLOAD_FOLDER']
                filepath = os.path.join(upload_folder, filename)

                if product.image_url and product.image_url != 'default.jpg':
                    old_photo_path = os.path.join(upload_folder, product.image_url)
                    if os.path.exists(old_photo_path):
                        os.remove(old_photo_path)

                photo.save(filepath)
                product.image_url = filename
            
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('admin.view_product', id=product.id))
    else:
        flash('Error updating product.', 'danger')
    return render_template('products/edit_product.html', form=form, product=product, current_user=current_user(), supplier=sup)


@admin.route('/products/delete/<int:id>', methods=['POST'])
@jwt_required()
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('admin.admin_products'))


@admin.route('/toggle_feature/<int:id>/<string:action>', methods=['GET', 'POST'])
@jwt_required()
def toggle_feature(id, action):
    product = Product.query.get_or_404(id)
    
    if action == 'feature':
        product.featured = True
        flash('Product has been featured!', 'success')
    elif action == 'unfeature':
        product.featured = False
        flash('Product has been unfeatured!', 'success')
    
    db.session.commit()
    return redirect(url_for('admin.admin_products'))


@admin.route('/toggle_feature/product/<int:id>/<string:action>', methods=['GET', 'POST'])
@jwt_required()
def product_page_toggle(id, action):
    product = Product.query.get_or_404(id)
    
    if action == 'feature':
        product.featured = True
        flash('Product has been featured!', 'success')
    elif action == 'unfeature':
        product.featured = False
        flash('Product has been unfeatured!', 'success')
    
    db.session.commit()
    return redirect(url_for('admin.view_product', id=product.id))




def currency_conversion(nationality, price, product):
    if 'kenya' in nationality.lower():
        if product.currency == 'KES':
            return f'KES {price}'
    elif 'uganda' in nationality.lower():
        if product.currency == 'KES':
            nprice = price * 28.84
            return f'UGX {nprice}'
    else:
        return price
            
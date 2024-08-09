from app.models import db, User, Farmer, Order, Product
from datetime import datetime
from werkzeug.security import generate_password_hash

def process_ussd_input(session_id, service_code, phone_number, text):
    response = ""
    user = User.query.filter_by(telephone=format_number(phone_number)).first() or User.query.filter_by(telephone=phone_number).first()

    steps = text.split('*') if text else [""]
    last_step = steps[-1]

    # Configuring navigation in the menus
    if user is None:
        response = handle_registration(steps, last_step)
    else:
        response = handle_existing_user_menu(user, steps, last_step)

    return response

def handle_registration(steps, last_step):
    global text
    if last_step == "99":
        steps = [""]
        text = ""
    elif last_step == "0":
        steps.pop()
        text = "*".join(steps)
        steps = text.split("*") if text else [""]
    else:
        steps = text.split("*") if text else [""]

    if len(steps) == 1:
        response = "CON Welcome to ShambaBora!\nEnter your FIRST and LAST name:\nPut * at the end\n\n0. Back  99. Home\n"
    elif len(steps) == 2:
        response = "CON Select your country:\n1. Kenya\n2. Uganda\n\n0. Back  99. Home\n"
    elif len(steps) == 3:
        response = "CON Enter your Gender:\n1. Male\n2. Female\n\n0. Back  99. Home\n"
    elif len(steps) == 4:
        response = "CON Enter your National ID Number:\n\n0. Back  99. Home\n"
    elif len(steps) == 5:
        response = "CON Enter your Date of Birth (DDMMYYYY):\n"
    elif len(steps) == 6:
        response = "CON Do you have a bank account?\n1. Yes\n2. No\n\n0. Back  99. Home\n"
    elif len(steps) == 7:
        response = "CON Enter your County/Province:\n\n0. Back  99. Home\n"
    elif len(steps) == 8:
        response = confirm_registration_details(steps)
    elif len(steps) == 9:
        response = finalize_registration(steps)
    else:
        response = "CON Invalid input!!!\n\n0. Back  99. Home\n"
    
    return response

def confirm_registration_details(steps):
    name = steps[0].split(" ")
    first_name = name[0]
    last_name = name[1]
    country_choice = steps[2]
    country = "Kenya" if country_choice == "1" else "Uganda"
    gender = "Male" if steps[3] == "1" else "Female"
    nin = steps[4]
    dob = datetime.strptime(steps[5], "%d%m%Y").strftime("%Y-%m-%d")
    bank_account = "True" if steps[6] == "1" else "False"
    location = steps[7]

    response = "CON Confirm your details:\n"
    response += f"Name: {first_name} {last_name}\n"
    response += f"Country: {country}\n"
    response += f"Sex: {gender} ID: {nin}\n"
    response += f"DOB: {dob}\n"
    response += f"Bank Account: {bank_account}\n"
    response += f"Location: {location}\n\n"
    response += "1. Confirm\n0. Back\n99. Home\n"
    
    return response

def finalize_registration(steps):
    name = steps[0].split(" ")
    first_name = name[0]
    last_name = name[1]
    country_choice = steps[2]
    country = "Kenya" if country_choice == "1" else "Uganda"
    gender = "Male" if steps[3] == "1" else "Female"
    nin = steps[4]
    dob = datetime.strptime(steps[5], "%d%m%Y").strftime("%Y-%m-%d")
    bank_account = True if steps[6] == "1" else False
    location = steps[7]

    user = Farmer(
        name=str(first_name),
        lastname=str(last_name),
        telephone=format_number(steps[1]),
        nationality=country,
        gender=gender,
        nin=nin,
        date_of_birth=dob,
        bank_account=bank_account,
        password_hash=generate_password_hash("1234"),
        role="farmer",
        location = location,
    )

    db.session.add(user)
    db.session.commit()

    return "END Registration successful! Welcome to ShambaBora."

def main_menu():
    response = "CON Welcome to ShambaBora!\nSelect an option:\n1. Order\n2. Track Order\n3. View Profile\n\n99. Home\n"
    return response

def handle_existing_user_menu(user, steps, last_step):
    if last_step == "99" or last_step == "":
        response = main_menu()
    elif last_step == "1":
        response = order_menu(user, steps)
    elif last_step == "2":
        response = track_order_menu(user, steps)
    elif last_step == "3":
        response = view_profile_menu(user, steps)
    else:
        response = "END Invalid input!/!"
    
    return response

def order_menu(user, steps):
    response = ""
    if len(steps) == 2:
        response = "CON Select category:\n1. Vegetables\n2. Fruits\n\n0. Back 99. Home\n"
    elif len(steps) == 3:
        category_choice = steps[2]
        response = view_products(category_choice)
    elif len(steps) == 4:
        product_choice = int(steps[3])
        products = get_products_by_category(steps[2])
        product = products[product_choice - 1]
        response = f"CON Enter quantity for {product.name}:\n\n0. Back 99. Home\n"
    elif len(steps) == 5:
        product_choice = int(steps[3])
        quantity = int(steps[4])
        products = get_products_by_category(steps[2])
        product = products[product_choice - 1]
        total_price = product.price * quantity
        response = f"CON Confirm order for {quantity} {product.name} at KES {total_price}\n1. Confirm\n0. Back 99. Home\n"
    elif len(steps) == 6 and steps[5] == "1":
        product_choice = int(steps[3])
        quantity = int(steps[4])
        products = get_products_by_category(steps[2])
        product = products[product_choice - 1]
        total_price = product.price * quantity
        new_order = Order(
            user_id=user.id,
            product_id=product.id,
            product_name=product.name,
            quantity=quantity,
            price=total_price,
            status='Pending'
        )
        db.session.add(new_order)
        db.session.commit()
        response = "END Order placed successfully!"
    else:
        response = "CON Invalid input\n0. Back 99. Home\n"
    
    return response

def view_products(category_choice):
    products = get_products_by_category(category_choice)
    response = "CON Select product:\n"
    for i, product in enumerate(products):
        response += f"{i+1}. {product.name} - KES {product.price}\n"
    response += "\n0. Back 99. Home\n"
    return response

def get_products_by_category(category_choice):
    category = "Vegetables" if category_choice == "1" else "Fruits"
    return Product.query.filter_by(category=category).all()

def track_order_menu(user, steps):
    user_orders = Order.query.filter_by(user_id=user.id).all()
    response = ""
    if len(steps) == 2:
        if user_orders:
            response = "CON Track Order\n"
            for i, order in enumerate(user_orders):
                response += f"{i+1}. {order.product_name} - {order.status}\n"
            response += "\n0. Back 99. Home\n"
        else:
            response = "CON You have no orders yet.\n0. Back 99. Home\n"
    elif len(steps) == 3:
        order_index = int(steps[2]) - 1
        order = user_orders[order_index]
        response = f"CON Order Details:\nProduct: {order.product_name}\nQuantity: {order.quantity}\nStatus: {order.status}\n\n1. Cancel Order\n0. Back 99. Home\n"
    elif len(steps) == 4:
        order_index = int(steps[2]) - 1
        order = user_orders[order_index]
        if steps[3] == "1":
            db.session.delete(order)
            db.session.commit()
            response = "END Order cancelled successfully!"
        else:
            response = "CON Invalid input\n0. Back 99. Home\n"

    return response

def view_profile_menu(user, steps):
    response = ""

    if len(steps) == 2:
        response = f"CON Name: {user.name} {user.lastname}\n"
        response += f"Telephone: {format_number(user.telephone)}\n"
        response += f"Location: {user.location}\n"
        response += f"Gender: {user.gender}\n"
        response += f"DOB: {user.date_of_birth}\n"
        response += "1. Edit Profile\n99. Home\n"
    elif len(steps) == 3:
        if steps[2] == "1":
            response = edit_profile(user)
        else:
            response = "CON Invalid input\n0. Back 99. Home\n"

    return response

def edit_profile(user):
    response = "CON Edit Profile\n"
    response += "1. Name\n"
    response += "2. Location\n"
    response += "3. Email\n"
    response += "4. Farm and company details\n"
    response += "5. Change Password\n"
    response += "0. Back 99. Home\n"
    return response

def format_number(phone_number):
    if phone_number.startswith("+254"):
        tel_number = phone_number.replace("+254", "0")
    elif phone_number.startswith("+256"):
        tel_number = phone_number.replace("+256", "0")
    else:
        tel_number = phone_number

    return tel_number

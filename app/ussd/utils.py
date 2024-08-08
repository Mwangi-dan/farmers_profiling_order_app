from app.models import db, User, Farmer, Order
from datetime import datetime
from werkzeug.security import generate_password_hash

def process_ussd_input(session_id, service_code, phone_number, text):
    """"
    :Returns: response
    """
    response = ""
    user = User.query.filter_by(telephone=phone_number).first()

    steps = text.split('*') if text else [""]
    last_step = steps[-1]

    # Configuring navigation in the menus
    if user is None:
        # New User registration
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
            response = "CON Welcome to ShambaBora!\n"
            response += "Enter your FIRST and LAST name:\nPut * at the end\n\n0. Back  99. Home\n"
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
            
        elif len(steps) == 9:
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
                telephone=phone_number,
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

            response = "END Registration successful! Welcome to ShambaBora."
        else:
            response = "CON Invalid input!\n\n0. Back  99. Home\n"
            last_step = steps[-1]

    # Existing users menu
    else:
        user = User.query.filter_by(telephone=phone_number).first()

        if text == "" or last_step == "99":
            response = main_menu()
        elif last_step == "1":
            response = order_menu(user)
        elif last_step == "2":
            response = track_order_menu(user)
        elif last_step == "3":
            response = view_profile(user)
        else:
            response = "END Invalid input"

    return response
        



def main_menu():
    response = "CON Welcome to ShambaBora FMS\n"
    response += "1. Make Order\n"
    response += "2. Track Order\n"
    response += "3. View Profile \n99. Home"
    return response


def order_menu(user):
    response = "CON Make Order\n"
    response += "1. View Products\n"
    response += "2. View Cart\n"
    response += "3. Checkout\n"
    response += "4. Cancel Order\n"
    response += "\n99. Home"
    return response


def track_order_menu(user):
    user_orders = Order.query.filter_by(user_id=user.id).all()
    if user_orders:
        response = "CON Track Order\n"
        for order in user_orders:
            response += f"{order.id}. {order.status}\n"
        response += "\n99. Home"
    else:
        response = "CON You have no orders yet.\n99. Home"

    return response


def view_profile(user):
    response = f"CON Name: {user.name} {user.lastname}\n"
    response += f"Telephone: {user.telephone}\n"
    response += f"Location: {user.location}\n"
    response += f"Gender: {user.gender}\n"
    response += f"DOB: {user.date_of_birth}\n"
    response += " * * * * * * * * \n"

    response += "1. Edit Profile\n"
    response += "\n99. Home"

    return response


def edit_profile(user):
    response = "CON Edit Profile\n"
    response += "1. Name\n"
    response += "2. Location\n"
    response += "3. Email\n"
    response += "4. Farm and company details\n"
    response += "5. Change Password\n"

    response += "\n99. Home"

    return response

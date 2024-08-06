from flask import jsonify
from app.models import db, User, Farmer, Order
from datetime import datetime


def process_ussd_input(session_id, service_code, phone_number, text):
    """"
    :Returns: JSON response
    """
    response = ""
    user = User.query.filter_by(telephone=phone_number).first()

    steps = text.split('*') if text else ['']
    last_step = steps[-1]

    # Configuring navigation in the menus
    if user is None:
        # New User registration
        if last_step == "99":
            steps = [""]
        elif last_step == "0":
            steps.pop()
            text = "*".join(steps)
            steps = text.split("*") if text else [""]
        else:
            steps = text.split("*") if text else [""]


        if len(steps) == 1:
            response = "CON Welcome to ShambaBora!\n"
            response += "Please enter your first and last name:\n0. Back\n99. Home\n"
        elif len(steps) == 2:
            response = "CON Select your country:\n1. Kenya\n2. Uganda\n0. Back\n99. Home\n"
        elif len(steps) == 3:
            response = "CON Enter your Gender:\n1. Male\n2. Female\n0. Back\n99. Home\n"
        elif len(steps) == 4:
            reponse = "CON Enter your National ID Number:\n0. Back\n99. Home\n"
        elif len(steps) == 5:
            response = "CON Enter your date of birth (ddmmyyy):\n0. Back\n99. Home\n"
        elif len(steps) == 6:
            response = "CON Do you have a bank account?\n1. Yes\n2. No\n0. Back\n99. Home\n"
        elif len(steps) == 7:
            name = steps[1].split(" ")
            first_name = name[0]
            last_name = name[1]
            country_choice = steps[2]
            country = "Kenya" if country_choice == "1" else "Uganda"
            gender = "Male" if steps[3] == "1" else "Female"
            nin = steps[4]
            dob = steps[5]
            bank_account = "True" if steps[6] == "1" else "False"

            user = Farmer(
                name=first_name,
                lastname=last_name,
                telephone=phone_number,
                nationality=country,
                gender=gender,
                nin=nin,
                date_of_birth=datetime.strptime(dob, "%d%m%Y"),
                bank_account=bank_account
            )

            db.session.add(user)
            db.session.commit()

            response = "END Registration successful! Welcome to ShambaBora."
        else:
            response = "END Invalid input"

    # Existing users menu
    else:
        if text == "" or last_step == "99":
            response = "CON Welcome back to ShambaBora!\n"
            response += "1. Make Order\n"
            response += "2. Track Order\n"
        elif last_step == "1":
            response = "END Feature coming soon"
        elif last_step == "2":
            response = "END Feature coming soon"
        else:
            response = "END Invalid input"

    return jsonify(
        {
            "response": response}
    )
        



def main_menu():
    response = "CON Welcome to ShambaBora FMS\n"
    response += "1. Make Order\n"
    response += "2. Track Order \n99. Home"
    return jsonify({"response": response})
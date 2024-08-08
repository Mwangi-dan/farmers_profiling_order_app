from flask import Blueprint, request
from .utils import process_ussd_input
from app import csrf

ussd = Blueprint('ussd', __name__)

@ussd.route('/ussd', methods=['POST'])
@ussd.route('/', methods=['POST'])
@csrf.exempt
def usd():
    global response
    if request.method == 'POST':
        session_id = request.form.get('sessionId')
        service_code = request.form.get('serviceCode')
        phone_number = request.form.get('phoneNumber')
        text = request.form.get('text')

        response = process_ussd_input(session_id, service_code, phone_number, text)

    return response
   
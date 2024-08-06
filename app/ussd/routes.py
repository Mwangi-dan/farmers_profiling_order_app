from flask import Blueprint, request, jsonify
from .utils import process_ussd_input

ussd = Blueprint('ussd', __name__)

@ussd.route('/ussd', methods=['POST'])
def ussd_calls():
    session_id = request.form.get('sessionId')
    service_code = request.form.get('serviceCode')
    phone_number = request.form.get('phoneNumber')
    text = request.form.get('text')

    response = process_ussd_input(session_id, service_code, phone_number, text)
    return response

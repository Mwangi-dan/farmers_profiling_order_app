import os
from werkzeug.utils import secure_filename
from flask import current_app

PRODUCT_UPLOAD_FOLDER = 'static/images/product_uploads'

def save_image(image):
    filename = secure_filename(image.filename)
    filepath = os.path.join(current_app.config['PRODUCT_UPLOAD_FOLDER'], filename)
    image.save(filepath)
    return filename
from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, SubmitField, BooleanField, 
    SelectField, HiddenField, DateField, FileField, FloatField
    )
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional
from flask_wtf.file import FileAllowed
from app.models import User

class RegistrationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=50)])
    lastname = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    telephone = StringField('Telephone', validators=[DataRequired(), Length(min=10, max=15)])
    nationality = StringField('Nationality', validators=[DataRequired(), Length(min=2, max=100)])
    location = StringField('Location', validators=[DataRequired(), Length(min=2, max=100)])
    date_of_birth = DateField('Date of Birth', format='%Y-%m-%d', validators=[DataRequired()])
    gender = SelectField('Gender', choices=[('', 'Select Gender'),('Male', 'Male'), ('Female', 'Female'), ('Other', 'Prefer not to say')], validators=[DataRequired()])
    role = SelectField('Role', choices=[('', 'Select Role'),('admin', 'admin'), ('farmer', 'farmer'), ('supplier', 'supplier')], validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    latitude = HiddenField('Latitude')  # Add hidden field for latitude
    longitude = HiddenField('Longitude')  # Add hidden field for longitude
    submit = SubmitField('Sign Up')

    def validate_telephone(self, telephone):
        user = User.query.filter_by(telephone=telephone.data).first()
        if user:
            raise ValidationError('That telephone is already registered.')
        

class LoginForm(FlaskForm):
    telephone = StringField('Telephone', validators=[DataRequired(), Length(min=10, max=15)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class EditProfileForm(FlaskForm):
    name = StringField('Full Name', validators=[Optional()])
    lastname = StringField('Last Name', validators=[Optional()])
    email = StringField('Email', validators=[Optional(), Email()])
    gender = SelectField('Gender', choices=[('Male', 'Male'), ('Female', 'Female')], validators=[Optional()])
    telephone = StringField('Telephone', validators=[Optional()])
    location = StringField('Location', validators=[Optional()])
    latitude = StringField('Latitude', validators=[Optional()])
    longitude = StringField('Longitude', validators=[Optional()])
    date_of_birth = DateField('Date of Birth', validators=[Optional()])
    photo = FileField('Profile Image', validators=[Optional(), FileAllowed(['jpg', 'png'], 'Images only!')])
    submit = SubmitField('Save Changes')

class ReportGenerationForm(FlaskForm):
    report_type = SelectField('Report Type', choices=[('users', 'Users'), ('orders', 'Orders'), ('issues', 'Issues')], validators=[DataRequired()])
    start_date = DateField('Start Date', format='%Y-%m-%d', validators=[DataRequired()])
    end_date = DateField('End Date', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('Generate Report')


class FarmerRegistrationForm(RegistrationForm):
    nin = StringField('National Identification Number', validators=[DataRequired(), Length(min=7, max=14)])
    group_name = StringField('Group Name')
    land_size = FloatField('Land Size (acres)')
    crop = StringField('Crop Being Grown')
    last_yield = FloatField('Last Yield (tons)')
    bank_account = BooleanField('Bank Account')
    gender = SelectField('Gender', choices=[('Male', 'Male'), ('Female', 'Female')])
    date_of_birth = DateField('Date of Birth')


class SupplierRegistrationForm(RegistrationForm):
    nin = StringField('National Identification Number', validators=[DataRequired(), Length(min=7, max=14)])
    company_name = StringField('Company Name', validators=[DataRequired()])
    products = StringField('Products or Services', validators=[DataRequired()])
    contact_person = StringField('Contact Person', validators=[DataRequired()])


class EditUserForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    gender = SelectField('Gender', choices=[('Male', 'Male'), ('Female', 'Female')], validators=[DataRequired()])
    telephone = StringField('Telephone', validators=[DataRequired(), Length(min=10, max=20)])
    location = StringField('Location', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Save Changes')


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('new_password', message='Passwords must match')
    ])
    submit = SubmitField('Change Password')
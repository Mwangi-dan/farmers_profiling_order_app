from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, HiddenField, DateField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from app.models import User

class RegistrationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    telephone = StringField('Telephone', validators=[DataRequired(), Length(min=10, max=15)])
    nationality = StringField('Nationality', validators=[DataRequired(), Length(min=2, max=100)])
    location = StringField('Location', validators=[DataRequired(), Length(min=2, max=100)])
    date_of_birth = DateField('Date of Birth', format='%Y-%m-%d', validators=[DataRequired()])
    gender = SelectField('Gender', choices=[('', 'Select Gender'),('Male', 'Male'), ('Female', 'Female'), ('Other', 'Prefer not to say')], validators=[DataRequired()])
    role = SelectField('Role', choices=[('', 'Select Role'),('Admin', 'Admin'), ('Farmer', 'Farmer')], validators=[DataRequired()])
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

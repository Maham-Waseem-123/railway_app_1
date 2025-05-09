from flask_wtf import FlaskForm
from wtforms import (
    StringField, SelectField, PasswordField, DateField,
    IntegerField, SubmitField
)
from wtforms.validators import DataRequired, Email, EqualTo, NumberRange

class SearchForm(FlaskForm):
    departure_city = StringField('Departure City', validators=[DataRequired()])
    arrival_city = StringField('Arrival City', validators=[DataRequired()])
    travel_date = DateField('Travel Date', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('Search Trains')

class UserRegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', 
                                   validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class PassengerForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired()])
    age = IntegerField('Age', validators=[DataRequired(), NumberRange(min=1, max=100)])
    gender = SelectField('Gender', choices=[
        ('Male', 'Male'), 
        ('Female', 'Female'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    cnic = StringField('CNIC', validators=[DataRequired()])
    phone = StringField('Phone Number', validators=[DataRequired()])
    address = StringField('Address', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Add Passenger')

class BookingForm(FlaskForm):
    passenger_id = SelectField('Select Passenger', coerce=int, validators=[DataRequired()])
    ticket_category = SelectField('Seat Class', choices=[
        ('economy', 'Economy Class'),
        ('economy_birth', 'Economy Birth'),
        ('ac_business', 'AC Business'),
        ('ac_standard', 'AC Standard'),
        ('ac_sleeper', 'AC Sleeper')
    ], validators=[DataRequired()])
    submit = SubmitField('Confirm Booking')
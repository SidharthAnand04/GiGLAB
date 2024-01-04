from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import (PasswordField, StringField, SubmitField, TextAreaField,
                     validators)


class ContactForm(FlaskForm):
    name = StringField('Your Name', validators=[validators.InputRequired()])
    email = StringField('Your Email', validators=[validators.InputRequired(), validators.Email()])
    message = TextAreaField('Your Message', validators=[validators.InputRequired()])
    submit = SubmitField('Submit')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[validators.InputRequired()])
    password = PasswordField('Password', validators=[validators.InputRequired()])
    error = None  # Error message field


class SignupForm(FlaskForm):
    username = StringField('Username', validators=[validators.InputRequired()])
    password = PasswordField('Password', [
        validators.InputRequired()
    ])
    confirm_password = PasswordField('Confirm Password')
    name = StringField('Name', validators=[validators.InputRequired()])
    description = TextAreaField('Description', validators=[validators.InputRequired()])
    role = StringField('Role', validators=[validators.InputRequired()])
    affiliation = StringField('Affiliation', validators=[validators.InputRequired()])
    submit = SubmitField('Signup')
    error = None  # Error message field
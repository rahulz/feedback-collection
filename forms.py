from flask_wtf import Form
from wtforms import StringField, PasswordField, SubmitField, validators
from wtforms.validators import Email, DataRequired


class SignupForm(Form):
    domain = StringField('Domain', [validators.DataRequired()])
    name = StringField('Name', [validators.DataRequired()])
    email = StringField('Email Address', [validators.DataRequired(), validators.Email()])
    password = PasswordField('New Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')


class SigninForm(Form):
    email = StringField('Email Address', [validators.DataRequired(), validators.Email()])
    password = PasswordField('New Password', [
        validators.DataRequired(),
    ])


class CsrfForm(Form):
    pass

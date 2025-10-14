import re
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, DateField, IntegerField, SelectField
from wtforms.validators import DataRequired, Length, ValidationError, Optional
from app.models import User, Employee

class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(message='Обязательное поле'), Length(min=2, max=20)])
    password = PasswordField('Пароль', validators=[DataRequired(message='Обязательное поле')])
    remember = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(message='Обязательное поле'), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(message='Обязательное поле'), Length(max=120)])
    password = PasswordField('Пароль', validators=[DataRequired(message='Обязательное поле')])
    submit = SubmitField('Зарегистрироваться')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Это имя пользователя уже занято. Пожалуйста, выберите другое.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Этот email уже зарегистрирован. Пожалуйста, используйте другой.')
        
        if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email.data):
            raise ValidationError('Пожалуйста, введите корректный email адрес.')

class EmployeeForm(FlaskForm):
    full_name = StringField('ФИО', validators=[DataRequired(message='Обязательное поле'), Length(max=100)])
    position = StringField('Должность', validators=[DataRequired(message='Обязательное поле'), Length(max=50)])
    hire_date = DateField('Дата приема', validators=[DataRequired(message='Обязательное поле')])
    salary = IntegerField('Зарплата', validators=[DataRequired(message='Обязательное поле')])
    boss_id = SelectField('Руководитель', coerce=int, validators=[Optional()])
    submit = SubmitField('Сохранить')
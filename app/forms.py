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
    position = SelectField('Должность', validators=[DataRequired(message='Обязательное поле')], choices=[])
    hire_date = DateField('Дата приема', validators=[DataRequired(message='Обязательное поле')])
    salary = IntegerField('Зарплата', validators=[DataRequired(message='Обязательное поле')])
    boss_id = SelectField('Руководитель', coerce=int, validators=[Optional()])
    submit = SubmitField('Сохранить')
    
    def __init__(self, *args, **kwargs):
        super(EmployeeForm, self).__init__(*args, **kwargs)
        # Динамически загружаем должности при создании формы
        self.position.choices = self.get_position_choices()
    
    def get_position_choices(self):
        """Получает список должностей из базы и добавляет опцию для новой должности"""
        positions = Employee.get_unique_positions()
        choices = [(pos, pos) for pos in positions]
        choices.append(('', '-- Выберите должность --'))  # Пустая опция по умолчанию
        choices.append(('__new__', '+ Добавить новую должность'))  # Опция для добавления новой
        return choices

class EmployeeFormWithCustomPosition(FlaskForm):
    """Альтернативная форма с возможностью ввода новой должности"""
    full_name = StringField('ФИО', validators=[DataRequired(message='Обязательное поле'), Length(max=100)])
    position_select = SelectField('Выберите должность', validators=[Optional()], choices=[])
    position_custom = StringField('Или введите новую должность', validators=[Optional(), Length(max=50)])
    hire_date = DateField('Дата приема', validators=[DataRequired(message='Обязательное поле')])
    salary = IntegerField('Зарплата', validators=[DataRequired(message='Обязательное поле')])
    boss_id = SelectField('Руководитель', coerce=int, validators=[Optional()])
    submit = SubmitField('Сохранить')
    
    def __init__(self, *args, **kwargs):
        super(EmployeeFormWithCustomPosition, self).__init__(*args, **kwargs)
        # Загружаем существующие должности
        positions = Employee.get_unique_positions()
        self.position_select.choices = [('', '-- Выберите из списка --')] + [(pos, pos) for pos in positions]
    
    def validate(self, **kwargs):
        # Кастомная валидация - должна быть выбрана либо существующая должность, либо введена новая
        if not super().validate(**kwargs):
            return False
        
        if not self.position_select.data and not self.position_custom.data:
            self.position_select.errors.append('Необходимо выбрать должность из списка или ввести новую')
            return False
        
        if self.position_select.data and self.position_custom.data:
            self.position_custom.errors.append('Выберите должность из списка ИЛИ введите новую, но не оба варианта')
            return False
        
        return True
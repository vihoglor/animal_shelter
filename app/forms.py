from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, IntegerField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, Regexp
from app.models import User
import phonenumbers

class RegistrationForm(FlaskForm):
    name = StringField('Имя', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Length(max=100)])
    phone = StringField('Телефон', validators=[
        DataRequired(),
        Regexp(regex=r'^(\+7|8)?[\s\-]?\(?[0-9]{3}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$',
               message='Введите номер в формате: +7 (999) 123-45-67 или 89123456789')
    ])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Подтвердите пароль', 
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Зарегистрироваться')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Этот email уже зарегистрирован')
    
    def validate_phone(self, phone):
        # Проверка, что номер существует
        try:
            # Очищаем номер от пробелов и скобок
            cleaned = ''.join(filter(lambda x: x.isdigit() or x == '+', phone.data))
            parsed = phonenumbers.parse(cleaned, 'RU')
            if not phonenumbers.is_valid_number(parsed):
                raise ValidationError('Неверный формат номера телефона')
        except:
            raise ValidationError('Введите корректный номер телефона')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(max=100)])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

class AnimalForm(FlaskForm):
    name = StringField('Кличка', validators=[DataRequired(), Length(max=100)])
    species = SelectField('Вид', choices=[('собака', 'Собака'), ('кошка', 'Кошка'), ('другое', 'Другое')], validators=[DataRequired()])
    breed = StringField('Порода', validators=[Length(max=100)])
    gender = SelectField('Пол', choices=[('male', 'Мужской'), ('female', 'Женский')], validators=[DataRequired()])
    age = IntegerField('Возраст (лет)', validators=[DataRequired()])
    color = StringField('Окрас', validators=[Length(max=100)])
    description = TextAreaField('Описание', validators=[DataRequired()])
    status = SelectField('Статус', choices=[
        ('Ищет дом'),
        ('Пристроен'),
        ('На лечении'),
        ('На передержке')
    ], validators=[DataRequired()])
    photo = FileField('Добавить фото', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Только изображения!')])
    submit = SubmitField('Сохранить')

class ActivityForm(FlaskForm):
    action_type = SelectField('Действие', choices=[
        ('feeding', 'Кормление'),
        ('walking', 'Выгул'),
        ('cleaning', 'Уборка')
    ], validators=[DataRequired()])
    comment = TextAreaField('Комментарий')
    submit = SubmitField('Отметить')
from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    email = input('Email администратора: ')
    name = input('Имя администратора: ')
    password = input('Пароль: ')
    
    admin = User.query.filter_by(email=email).first()
    if admin:
        print('Пользователь с таким email уже существует')
    else:
        admin = User(email=email, name=name, role='admin')
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        print(f'Администратор {email} успешно создан!')
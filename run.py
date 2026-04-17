from app import create_app, db
from app.models import User

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Создать администратора по умолчанию, если его нет
        admin = User.query.filter_by(email='admin@gmail.com').first()
        if not admin:
            admin = User(
                email='admin@gmail.com',
                name='Администратор',
                role='admin'
            )
            admin.set_password('admin')
            db.session.add(admin)
            db.session.commit()
            print('Создан администратор: admin@gmail.com / admin')
    
    app.run(debug=True, host='0.0.0.0', port=5000)

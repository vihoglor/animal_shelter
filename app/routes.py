import os
from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.utils import secure_filename
from app import db
from app.models import User, Animal, AnimalPhoto, Activity, AdoptionRequest, Fundraiser, Donation
from app.forms import RegistrationForm, LoginForm, AnimalForm, ActivityForm

def register_routes(app):
    
    # ============ АВТОРИЗАЦИЯ ============
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('catalog'))
        
        form = RegistrationForm()
        if form.validate_on_submit():
            user = User(
                email=form.email.data,
                name=form.name.data,
                phone=form.phone.data,
                role='user'  # Обычный пользователь, НЕ волонтёр!
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('Регистрация успешна! Теперь вы можете войти.', 'success')
            return redirect(url_for('login'))
        
        return render_template('register.html', form=form)
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('catalog'))
        
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and user.check_password(form.password.data):
                login_user(user)
                flash(f'Добро пожаловать, {user.name}!', 'success')
                return redirect(url_for('catalog'))
            else:
                flash('Неверный email или пароль', 'danger')
        
        return render_template('login.html', form=form)
    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('Вы вышли из системы', 'info')
        return redirect(url_for('catalog'))
    
    # ============ ПУБЛИЧНЫЙ КАТАЛОГ ============
    
    @app.route('/')
    @app.route('/catalog')
    def catalog():
        animals = Animal.query.order_by(Animal.created_at.desc()).all()
        return render_template('catalog.html', animals=animals)
    
    @app.route('/animal/<int:id>')
    def animal_card(id):
        animal = Animal.query.get_or_404(id)
        activities = Activity.query.filter_by(animal_id=id).order_by(Activity.created_at.desc()).all()
        form = ActivityForm()
        return render_template('animal_card.html', animal=animal, activities=activities, form=form)
    
    # ============ ВОЛОНТЁРСКАЯ АКТИВНОСТЬ ============
    
    @app.route('/volunteer/activity/<int:animal_id>', methods=['POST'])
    @login_required
    def log_activity(animal_id):
        # Проверяем, что пользователь имеет права волонтёра или администратора
        if not (current_user.is_volunteer() or current_user.is_admin()):
            flash('Доступ запрещён. Только волонтёры могут отмечать активность.', 'danger')
            return redirect(url_for('animal_card', id=animal_id))
        
        animal = Animal.query.get_or_404(animal_id)
        form = ActivityForm()
        
        if form.validate_on_submit():
            activity = Activity(
                animal_id=animal_id,
                user_id=current_user.id,
                action_type=form.action_type.data,
                comment=form.comment.data
            )
            db.session.add(activity)
            db.session.commit()
            action_name = dict(form.action_type.choices).get(form.action_type.data)
            flash(f'Действие "{action_name}" отмечено!', 'success')
        
        return redirect(url_for('animal_card', id=animal_id))
    
    # ============ АДМИНИСТРИРОВАНИЕ ============
    
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']
    
    @app.route('/admin')
    @login_required
    def admin_dashboard():
        if not current_user.is_admin():
            flash('Доступ запрещён. Требуются права администратора.', 'danger')
            return redirect(url_for('catalog'))
        
        animals = Animal.query.order_by(Animal.created_at.desc()).all()
        users = User.query.all()
        return render_template('admin_dashboard.html', animals=animals, users=users)

    @app.route('/admin/users/promote/<int:id>')
    @login_required
    def promote_user(id):
        if not current_user.is_admin():
            flash('Доступ запрещён.', 'danger')
            return redirect(url_for('catalog'))
        
        user = User.query.get_or_404(id)
        if user.role == 'user':
            user.role = 'volunteer'
            db.session.commit()
            flash(f'Пользователь "{user.name}" повышен до волонтёра', 'success')
        else:
            flash('Пользователь уже имеет права волонтёра или администратора', 'warning')
        
        return redirect(url_for('admin_dashboard'))
    
    @app.route('/admin/animals/create', methods=['GET', 'POST'])
    @login_required
    def create_animal():
        if not current_user.is_admin():
            flash('Доступ запрещён. Требуются права администратора.', 'danger')
            return redirect(url_for('catalog'))
        
        form = AnimalForm()
        if form.validate_on_submit():
            animal = Animal(
                name=form.name.data,
                species=form.species.data,
                breed=form.breed.data,
                gender=form.gender.data,
                age=form.age.data,
                color=form.color.data,
                description=form.description.data,
                status=form.status.data,  # Добавлено поле статуса
                created_by=current_user.id
            )
            db.session.add(animal)
            db.session.commit()
            
            # Сохранение фото
            if form.photo.data:
                file = form.photo.data
                if file and allowed_file(file.filename):
                    filename = secure_filename(f"animal_{animal.name}_{animal.id}")
                    upload_folder = current_app.config['UPLOAD_FOLDER']
                    file_path = os.path.join(upload_folder, filename)
                    file.save(file_path)
                    
                    animal_photo = AnimalPhoto(
                        animal_id=animal.id,
                        file_path=f"uploads/{filename}",
                        is_main=True
                    )
                    db.session.add(animal_photo)
                    db.session.commit()
                else:
                    animal_photo = AnimalPhoto(
                        animal_id=animal.id,
                        file_path=f"uploads/placeholder.png",
                        is_main=True
                    )
                    db.session.add(animal_photo)
                    db.session.commit()
                
            
            flash(f'Животное "{animal.name}" успешно добавлено!', 'success')
            return redirect(url_for('admin_dashboard'))
        
        return render_template('create_animal.html', form=form)
    
    @app.route('/admin/animals/delete/<int:id>')
    @login_required
    def delete_animal(id):
        if not current_user.is_admin():
            flash('Доступ запрещён.', 'danger')
            return redirect(url_for('catalog'))
        
        animal = Animal.query.get_or_404(id)
        db.session.delete(animal)
        db.session.commit()
        flash(f'Животное "{animal.name}" удалено', 'warning')
        return redirect(url_for('admin_dashboard'))
    
    @app.route('/admin/users/delete/<int:id>')
    @login_required
    def delete_user(id):
        if not current_user.is_admin():
            flash('Доступ запрещён.', 'danger')
            return redirect(url_for('catalog'))
        
        user = User.query.get_or_404(id)
        if user.id == current_user.id:
            flash('Нельзя удалить самого себя', 'danger')
            return redirect(url_for('admin_dashboard'))
        
        db.session.delete(user)
        db.session.commit()
        flash(f'Пользователь "{user.name}" удалён', 'warning')
        return redirect(url_for('admin_dashboard'))

    # ============ ЗАЯВКИ НА ПРИСТРОЙСТВО ============

    @app.route('/adoption-request/<int:animal_id>', methods=['GET', 'POST'])
    def adoption_request(animal_id):
        animal = Animal.query.get_or_404(animal_id)
        
        if request.method == 'POST':
            full_name = request.form.get('full_name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            experience = request.form.get('experience')
            message = request.form.get('message')
            
            # Валидация обязательных полей
            if not full_name or not email:
                flash('Пожалуйста, заполните имя и email', 'danger')
                return render_template('adoption_request.html', animal=animal)
            
            adoption_req = AdoptionRequest(
                user_id=current_user.id if current_user.is_authenticated else None,
                animal_id=animal_id,
                full_name=full_name,
                email=email,
                phone=phone,
                experience=experience,
                message=message,
                status='new'
            )
            db.session.add(adoption_req)
            db.session.commit()
            
            flash('Ваша заявка отправлена! Администратор свяжется с вами в ближайшее время.', 'success')
            return redirect(url_for('catalog'))
        
        return render_template('adoption_request.html', animal=animal)


    @app.route('/admin/adoption-requests')
    @login_required
    def admin_adoption_requests():
        if not current_user.is_admin():
            flash('Доступ запрещён.', 'danger')
            return redirect(url_for('catalog'))
        
        requests = AdoptionRequest.query.order_by(AdoptionRequest.created_at.desc()).all()
        return render_template('admin_adoption_requests.html', requests=requests)


    @app.route('/admin/adoption-requests/approve/<int:id>')
    @login_required
    def approve_adoption_request(id):
        if not current_user.is_admin():
            flash('Доступ запрещён.', 'danger')
            return redirect(url_for('catalog'))
        
        adoption_req = AdoptionRequest.query.get_or_404(id)
        adoption_req.status = 'approved'
        
        # Меняем статус животного на "Пристроен"
        animal = Animal.query.get(adoption_req.animal_id)
        if animal:
            animal.status = 'adopted'
        
        db.session.commit()
        flash(f'Заявка на пристройство {animal.name} одобрена', 'success')
        return redirect(url_for('admin_adoption_requests'))


    @app.route('/admin/adoption-requests/reject/<int:id>')
    @login_required
    def reject_adoption_request(id):
        if not current_user.is_admin():
            flash('Доступ запрещён.', 'danger')
            return redirect(url_for('catalog'))
        
        adoption_req = AdoptionRequest.query.get_or_404(id)
        adoption_req.status = 'rejected'
        db.session.commit()
        flash('Заявка отклонена', 'warning')
        return redirect(url_for('admin_adoption_requests'))


    # ============ ПОЖЕРТВОВАНИЯ ============

    @app.route('/donate/<int:fundraiser_id>', methods=['GET', 'POST'])
    def donate(fundraiser_id):
        fundraiser = Fundraiser.query.get_or_404(fundraiser_id)
        
        if request.method == 'POST':
            amount = request.form.get('amount')
            comment = request.form.get('comment')
            
            if not amount or float(amount) <= 0:
                flash('Введите корректную сумму пожертвования', 'danger')
                return render_template('donate.html', fundraiser=fundraiser)
            
            donation = Donation(
                user_id=current_user.id if current_user.is_authenticated else None,
                fundraiser_id=fundraiser_id,
                amount=float(amount),
                comment=comment
            )
            db.session.add(donation)
            
            # Обновляем собранную сумму в сборе
            fundraiser.collected_amount += float(amount)
            db.session.commit()
            
            flash(f'Спасибо за пожертвование {amount} руб.!', 'success')
            return redirect(url_for('catalog'))
        
        return render_template('donate.html', fundraiser=fundraiser)
    # ============ РЕДАКТИРОВАНИЕ ЖИВОТНОГО (АДМИНИСТРАТОР) ============

    @app.route('/admin/animals/edit/<int:id>', methods=['GET', 'POST'])
    @login_required
    def edit_animal(id):
        if not current_user.is_admin():
            flash('Доступ запрещён. Требуются права администратора.', 'danger')
            return redirect(url_for('catalog'))
        
        animal = Animal.query.get_or_404(id)
        form = AnimalForm(obj=animal)  # Заполняем форму текущими данными
        
        if form.validate_on_submit():
            # Обновляем поля животного
            animal.name = form.name.data
            animal.species = form.species.data
            animal.breed = form.breed.data
            animal.gender = form.gender.data
            animal.age = form.age.data
            animal.color = form.color.data
            animal.description = form.description.data
            animal.status = form.status.data
            
            # Обработка новой фотографии (если загружена)
            if form.photo.data and form.photo.data.filename:
                file = form.photo.data
                if file and allowed_file(file.filename):
                    filename = secure_filename(f"animal_{animal.name}_{animal.id}")
                    upload_folder = current_app.config['UPLOAD_FOLDER']
                    file_path = os.path.join(upload_folder, filename)
                    file.save(file_path)
                    
                    # Если это первое фото, делаем его главным
                    is_main = len(animal.photos) == 0
                    
                    animal_photo = AnimalPhoto(
                        animal_id=animal.id,
                        file_path=f"uploads/{filename}",
                        is_main=is_main
                    )
                    db.session.add(animal_photo)
            
            db.session.commit()
            flash(f'Карточка животного "{animal.name}" успешно обновлена!', 'success')
            return redirect(url_for('admin_dashboard', id=animal.id))
        
        return render_template('edit_animal.html', form=form, animal=animal)


    @app.route('/admin/animals/photo/set-main/<int:photo_id>')
    @login_required
    def set_main_photo(photo_id):
        if not current_user.is_admin():
            flash('Доступ запрещён.', 'danger')
            return redirect(url_for('catalog'))
        
        photo = AnimalPhoto.query.get_or_404(photo_id)
        animal = photo.animal
        
        # Сбрасываем флаг is_main у всех фото этого животного
        for p in animal.photos:
            p.is_main = False
        
        # Устанавливаем новое главное фото
        photo.is_main = True
        db.session.commit()
        
        flash('Главное фото обновлено', 'success')
        return redirect(url_for('edit_animal', id=animal.id))


    @app.route('/admin/animals/photo/delete/<int:photo_id>')
    @login_required
    def delete_photo(photo_id):
        if not current_user.is_admin():
            flash('Доступ запрещён.', 'danger')
            return redirect(url_for('catalog'))
        
        photo = AnimalPhoto.query.get_or_404(photo_id)
        animal_id = photo.animal_id
        
        # Удаляем файл с диска
        file_path = os.path.join(current_app.root_path, 'static', photo.file_path)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        db.session.delete(photo)
        db.session.commit()
        
        flash('Фотография удалена', 'success')
        return redirect(url_for('edit_animal', id=animal_id))
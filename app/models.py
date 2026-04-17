from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    created_animals = db.relationship('Animal', back_populates='creator', foreign_keys='Animal.created_by')
    activities = db.relationship('Activity', back_populates='user')
    adoption_requests = db.relationship('AdoptionRequest', back_populates='user')
    created_fundraisers = db.relationship('Fundraiser', back_populates='creator')
    donations = db.relationship('Donation', back_populates='user')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_volunteer(self):
        return self.role == 'volunteer'
    
    def __repr__(self):
        return f'<User {self.email}>'


class Animal(db.Model):
    __tablename__ = 'animals'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    species = db.Column(db.String(50), nullable=False)
    breed = db.Column(db.String(100))
    gender = db.Column(db.String(10))
    age = db.Column(db.Integer)
    color = db.Column(db.String(100))
    status = db.Column(db.String(50), default='looking')
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    
    # Relationships
    photos = db.relationship('AnimalPhoto', back_populates='animal', cascade='all, delete-orphan')
    activities = db.relationship('Activity', back_populates='animal', cascade='all, delete-orphan')
    adoption_requests = db.relationship('AdoptionRequest', back_populates='animal')
    fundraisers = db.relationship('Fundraiser', back_populates='animal')
    creator = db.relationship('User', back_populates='created_animals', foreign_keys=[created_by])
    
    def get_main_photo(self):
        main = AnimalPhoto.query.filter_by(animal_id=self.id, is_main=True).first()
        if main:
            return main.file_path
        first = AnimalPhoto.query.filter_by(animal_id=self.id).first()
        return first.file_path if first else None
    
    @property
    def active_fundraiser(self):
        return Fundraiser.query.filter_by(animal_id=self.id, status='active').first()
    
    def __repr__(self):
        return f'<Animal {self.name}>'


class AnimalPhoto(db.Model):
    __tablename__ = 'animal_photos'
    
    id = db.Column(db.Integer, primary_key=True)
    animal_id = db.Column(db.Integer, db.ForeignKey('animals.id', ondelete='CASCADE'), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    is_main = db.Column(db.Boolean, default=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    animal = db.relationship('Animal', back_populates='photos')


class Activity(db.Model):
    __tablename__ = 'activities'
    
    id = db.Column(db.Integer, primary_key=True)
    animal_id = db.Column(db.Integer, db.ForeignKey('animals.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    action_type = db.Column(db.String(50), nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    animal = db.relationship('Animal', back_populates='activities')
    user = db.relationship('User', back_populates='activities')


class AdoptionRequest(db.Model):
    __tablename__ = 'adoption_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    animal_id = db.Column(db.Integer, db.ForeignKey('animals.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(50), default='new')
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    experience = db.Column(db.Text)
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='adoption_requests')
    animal = db.relationship('Animal', back_populates='adoption_requests')


class Fundraiser(db.Model):
    __tablename__ = 'fundraisers'
    
    id = db.Column(db.Integer, primary_key=True)
    animal_id = db.Column(db.Integer, db.ForeignKey('animals.id', ondelete='SET NULL'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    goal_amount = db.Column(db.Numeric(10, 2), nullable=False)
    collected_amount = db.Column(db.Numeric(10, 2), default=0)
    status = db.Column(db.String(20), default='active')
    photo = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    
    # Relationships
    donations = db.relationship('Donation', back_populates='fundraiser', cascade='all, delete-orphan')
    animal = db.relationship('Animal', back_populates='fundraisers')
    creator = db.relationship('User', back_populates='created_fundraisers')
    
    def get_progress_percentage(self):
        if self.goal_amount and self.goal_amount > 0:
            return float(self.collected_amount) / float(self.goal_amount) * 100
        return 0
    
    def __repr__(self):
        return f'<Fundraiser {self.title}>'


class Donation(db.Model):
    __tablename__ = 'donations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    fundraiser_id = db.Column(db.Integer, db.ForeignKey('fundraisers.id', ondelete='CASCADE'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='donations')
    fundraiser = db.relationship('Fundraiser', back_populates='donations')
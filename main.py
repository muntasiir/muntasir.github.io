import os
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, session, redirect, url_for, flash, current_app
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from wtforms import SelectField, StringField, PasswordField, BooleanField, SubmitField, validators
from wtforms.validators import DataRequired, Length, Email, EqualTo
from flask_login import logout_user
from flask_login import login_required
import random

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'Flare' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:muntasir1234@localhost/5.0db' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'index'


# Define models
class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(256))  # Increased length for password hash
    phone_number = db.Column(db.String(10))
    
    purchasedservices = db.relationship('PurchasedService', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class PurchasedService(db.Model):
    __tablename__ = 'pos2'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    service_type = db.Column(db.String(20))
    service_number = db.Column(db.String(10))

    def __repr__(self):
        return f'<PurchasedService {self.id}>'

# Define forms
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    phone_number = StringField('Phone Number', validators=[DataRequired(), Length(max=10)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, max=128)])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class PurchaseForm(FlaskForm):
    service_type = SelectField('Service Type', choices=[('BYOD', 'BYOD'), ('Fiber', 'Fiber')], validators=[validators.DataRequired()])
    service_number = SelectField('Serial Number', choices=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('500', '500'), ('1.0', '1.0'), ('3.0', '3.0')], validators=[validators.DataRequired()])
    submit = SubmitField('Purchase')



@app.route('/', methods=['GET', 'POST'])
def index():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None:
            flash('Seems like you are not registered. Please register.')
            return redirect(url_for('register'))
        if not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('index'))
        login_user(user, remember=form.remember_me.data)
        next_page = session.get('next_page', None)
        session.pop('next_page', None)
        return redirect(next_page) if next_page else redirect(url_for('profile'))
    
    
    
    # Pass the form and the random phone numbers to the template
    return render_template('index.html', form=form)





@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    phone_numbers = []  # Initialize the list of phone numbers
    
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, phone_number=form.phone_number.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('shop'))
    
    # Generate 5 random phone numbers only on GET request
    if request.method == 'GET':
        phone_numbers = [generate_random_phone_number() for _ in range(5)]
    
    return render_template('register.html', form=form, phone_numbers=phone_numbers)

# Random phone number generation function
def generate_random_phone_number():
    area_code = random.choice(['647', '416', '437'])
    exchange_code = random.randint(100, 999)
    subscriber_number = random.randint(1000, 9999)
    return f"({area_code})-{exchange_code}-{subscriber_number}"

# Endpoint to generate a single random phone number
@app.route('/random_phone_number')
def random_phone_number():
    phone_number = generate_random_phone_number()
    return jsonify({"phone_number": phone_number})



@app.route('/shop', methods=['GET', 'POST'])
@login_required
def shop():
    # Query to check if the user already bought services
    user_purchased_services = PurchasedService.query.filter_by(user_id=current_user.id).all()

    # Check if the user already bought BYOD or Fiber service
    has_byod_service = any(service.service_type == 'BYOD' for service in user_purchased_services)
    has_fiber_service = any(service.service_type == 'Fiber' for service in user_purchased_services)

    # Instantiate the purchase form
    form = PurchaseForm()

    # Filter out choices based on existing purchases
    if has_byod_service:
        form.service_type.choices = [('Fiber', 'Fiber')]  # User already has BYOD, so only Fiber can be chosen
    elif has_fiber_service:
        form.service_type.choices = [('BYOD', 'BYOD')]  # User already has Fiber, so only BYOD can be chosen

    if form.validate_on_submit():
        # Check if the user already purchased a service of the selected type
        if form.service_type.data == 'BYOD' and has_byod_service:
            flash('You can only buy one BYOD service.', 'error')
            return redirect(url_for('shop'))
        elif form.service_type.data == 'Fiber' and has_fiber_service:
            flash('You can only buy one Fiber service.', 'error')
            return redirect(url_for('shop'))

        # Check for allowed service numbers based on service type
        if (form.service_type.data == 'BYOD' and form.service_number.data not in ['1', '2', '3', '4']) or \
           (form.service_type.data == 'Fiber' and form.service_number.data not in ['500', '1.0', '3.0']):
            flash('Invalid service type and number match.', 'error')
            return redirect(url_for('shop'))

        # Purchase the service
        purchased_service = PurchasedService(
            user_id=current_user.id,
            service_type=form.service_type.data,
            service_number=form.service_number.data
        )
        db.session.add(purchased_service)
        db.session.commit()
        flash('Service purchased successfully!', 'success')
        return redirect(url_for('profile'))

    # Load the shop template with the purchase form
    return render_template('shop3.html', form=form)



@app.route('/profile')
@login_required
def profile():
    purchasedservices = PurchasedService.query.filter_by(user_id=current_user.id).all()

    # Assuming you have dictionaries for service descriptions
    byod_descriptions = {
        '1': '$29 for 20 GB in 4G speed, unlimited Canada-wide calling and texting',
        '2': '$34 for 50 GB in 4G speed, unlimited Canada-wide calling and texting',
        '3': '$39 for 60 GB in 5G speed, unlimited Canada-wide calling and texting',
        '4': '$50 for 60 GB in 5G speed, unlimited Canada & US-wide calling and texting'
    }

    fiber_descriptions = {
        '500': '500 mbps of internet speed upload & download',
        '1.0': '1 gbps of internet speed upload & download',
        '3.0': '3.0 gbps of internet speed upload & download'
    }

    return render_template('profile.html', purchasedservices=purchasedservices,
                           byod_descriptions=byod_descriptions, fiber_descriptions=fiber_descriptions)



@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.')
    return redirect(url_for('index'))


@app.route('/support')
@login_required
def support():
    return render_template('support.html')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=80)  # Listen on all available network interfaces on port 80

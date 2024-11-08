from datetime import datetime

from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, \
    logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length

from model import predict_iris

app = Flask(__name__)
app.config[
    'SECRET_KEY'] = 'your_secret_key'  # Change this to a more secure key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # Database URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Define the route for login page


# Create user registration and login forms using Flask-WTF

class RegisterForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=4, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password',
                             validators=[DataRequired(), Length(min=8)])
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


# User model for SQLAlchemy (storing user credentials and login sessions)
class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    predictions = db.relationship('PredictionHistory', backref='user',
                                  lazy=True)  # Establish relationship with PredictionHistory


class PredictionHistory(db.Model):
    __tablename__ = 'prediction_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),
                        nullable=False)  # Foreign key referencing User table
    sepal_length = db.Column(db.Float, nullable=False)
    sepal_width = db.Column(db.Float, nullable=False)
    petal_length = db.Column(db.Float, nullable=False)
    petal_width = db.Column(db.Float, nullable=False)
    prediction = db.Column(db.String(50),
                           nullable=False)  # Store model's prediction (e.g., 'Setosa')
    timestamp = db.Column(db.DateTime,
                          default=datetime.utcnow)  # Timestamp of prediction


# Load user from session
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Route for Home Page
@app.route('/')
def home():
    return render_template('home.html')


# Route for Register Page
@app.route('/register', methods=['GET', 'POST'])
def register():
    # redirect to profile if user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
    form = RegisterForm()
    print(form.username.data, form.email.data, form.password.data)
    if form.validate_on_submit():
        # Check if user already exists
        existing_user = User.query.filter_by(
            username=form.username.data).first()
        if existing_user:
            flash('Username already exists!', 'danger')
            return redirect(url_for('register'))

        # Create new user
        hashed_password = generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, email=form.email.data,
                        password=hashed_password)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Account created successfully!', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Error: ' + str(e), 'danger')
    else:
        if request.method == 'POST':
            flash(form.errors, 'danger')

    return render_template('register.html', form=form)


# Route for Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    # redirect to profile if user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('profile'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html', form=form)


# Route for Logout
@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))


# Route for Profile Page (Only accessible to logged-in users)
@app.route('/profile')
@login_required
def profile():
    # Query the database for the current user's prediction history
    history = PredictionHistory.query.filter_by(
        user_id=current_user.id).order_by(
        PredictionHistory.timestamp.desc()).all()
    return render_template('profile.html', user=current_user, history=history)


# Route for Input Page (Only accessible to logged-in users)
@app.route('/input', methods=['GET', 'POST'])
@login_required
def input_page():
    if request.method == 'POST':
        # Retrieve data from form
        sepal_length = float(request.form.get('sepal_length'))
        sepal_width = float(request.form.get('sepal_width'))
        petal_length = float(request.form.get('petal_length'))
        petal_width = float(request.form.get('petal_width'))

        # Make prediction using the ML model
        prediction = predict_iris(sepal_length, sepal_width, petal_length,
                                  petal_width)

        # Save prediction data to database
        new_prediction = PredictionHistory(
            user_id=current_user.id,
            sepal_length=sepal_length,
            sepal_width=sepal_width,
            petal_length=petal_length,
            petal_width=petal_width,
            prediction=prediction
        )
        db.session.add(new_prediction)
        db.session.commit()

        flash('Prediction made successfully!', 'success')
        return redirect(url_for('result', prediction=prediction))

    return render_template('input.html')


# Route for Result Page (After prediction)
@app.route('/result')
@login_required
def result():
    # Retrieve the prediction result passed as a query parameter
    prediction = request.args.get('prediction', 'Unknown')
    return render_template('result.html', prediction=prediction)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', title="Page Not Found",
                           error_message="404 - Page Not Found"), 404


@app.errorhandler(403)
def unauthorized(e):
    return render_template('error.html', title="Unauthorized",
                           error_message="403 - Unauthorized Access"), 403


# Run the app
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Creates the database tables
    app.run(debug=True, host='0.0.0.0')

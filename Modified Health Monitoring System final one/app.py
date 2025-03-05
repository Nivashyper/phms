from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, current_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import io
import base64
import matplotlib.pyplot as plt
import joblib
import numpy as np
import pandas as pd

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.secret_key = '35816d3b5542d2c486cdc0932b08c5bd'

# Initialize database and login manager
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Use Agg backend for Matplotlib to avoid GUI issues
import matplotlib
matplotlib.use('Agg')


# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    health_data = db.relationship('HealthData', back_populates='user')


# Health Data Model
class HealthData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pulse = db.Column(db.Integer, nullable=False)
    blood_pressure = db.Column(db.String(50), nullable=False)
    weight = db.Column(db.Float, nullable=False)
    activity_level = db.Column(db.String(100), nullable=False)
    recommendation = db.Column(db.String(255), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates="health_data")


# Login Manager
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# Home Route
@app.route('/')
def index():
    return render_template('index.html')


# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))

        return 'Invalid username or password'
    return render_template('login.html')


# Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))
    return render_template('register.html')


# Load trained models
try:
    knn_model = joblib.load('knn_model.pkl')
    rf_model = joblib.load('rf_model.pkl')
    scaler = joblib.load('scaler.pkl')
except Exception as e:
    knn_model = None
    rf_model = None
    scaler = None
    print(f"Error loading models: {e}")


# Function to generate health recommendations using ML
def generate_recommendation(pulse, blood_pressure, weight, activity_level):
    if not knn_model or not rf_model or not scaler:
        return "Machine Learning models are not available. Please check system configuration."

    # Convert activity level to numeric value
    activity_map = {'Low': 0, 'Moderate': 1, 'High': 2}
    activity_numeric = activity_map.get(activity_level, 1)

    # Prepare input for ML model
    input_data = pd.DataFrame([[pulse, blood_pressure, weight, activity_numeric]],
                              columns=['pulse', 'blood_pressure', 'weight', 'activity_level'])
    input_scaled = scaler.transform(input_data)

    # Predict recommendation using KNN
    knn_prediction = knn_model.predict(input_scaled)[0]

    # Predict health trend using Random Forest
    rf_prediction = rf_model.predict(input_data)[0]

    print(f"KNN Suggestion: {knn_prediction} | Health Trend: {rf_prediction}")
    return knn_prediction


# Add Health Data Route
@app.route('/add_data', methods=['GET', 'POST'])
@login_required
def add_data():
    if request.method == 'POST':
        pulse = int(request.form['pulse'])
        blood_pressure = request.form['blood_pressure']
        weight = float(request.form['weight'])
        activity_level = request.form['activity_level']

        recommendation = generate_recommendation(pulse, blood_pressure, weight, activity_level)

        new_data = HealthData(
            pulse=pulse,
            blood_pressure=blood_pressure,
            weight=weight,
            activity_level=activity_level,
            recommendation=recommendation,
            user_id=current_user.id
        )
        db.session.add(new_data)
        db.session.commit()

        return redirect(url_for('dashboard'))

    return render_template('add_data.html')


# Dashboard Route
@app.route('/dashboard')
@login_required
def dashboard():
    health_data = HealthData.query.filter_by(user_id=current_user.id).all()
    latest_recommendation = health_data[-1].recommendation if health_data else "No recommendations yet."
    
    return render_template('dashboard.html', health_data=health_data, latest_recommendation=latest_recommendation)


# Health Data Plot Route
@app.route('/health_data_plot', methods=['GET'])
@login_required
def health_data_plot():
    health_data = HealthData.query.filter_by(user_id=current_user.id).all()
    activity_level_counts = {'Low': 0, 'Moderate': 0, 'High': 0}

    for data in health_data:
        if data.activity_level in activity_level_counts:
            activity_level_counts[data.activity_level] += 1

    labels = list(activity_level_counts.keys())
    sizes = list(activity_level_counts.values())

    # Handle empty data
    if sum(sizes) == 0:
        return "No activity data available for plotting", 400

    plt.figure(figsize=(6, 6))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.title('Activity Levels Distribution')

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)

    return send_file(img, mimetype='image/png')


# Logout Route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# Run the app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  
app.secret_key = '35816d3b5542d2c486cdc0932b08c5bd'
db = SQLAlchemy(app)


# User Model
class User(db.Model):
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


# Function to display all records from all tables
def display_all_records():
    # Query all records from the User table
    users = User.query.all()
    print("\nAll Users:")
    for user in users:
        print(f"ID: {user.id}, Username: {user.username}")

    # Query all records from the HealthData table
    health_data_records = HealthData.query.all()
    print("\nAll Health Data Records:")
    for record in health_data_records:
        print(f"ID: {record.id}, Pulse: {record.pulse}, Blood Pressure: {record.blood_pressure}, Weight: {record.weight}, "
              f"Activity Level: {record.activity_level}, Recommendation: {record.recommendation}")


# Main block to display the records
if __name__ == "__main__":
    with app.app_context():
        # Create tables if they don't exist yet 
        db.create_all()

        # Display all records
        display_all_records()

    app.run(debug=False)

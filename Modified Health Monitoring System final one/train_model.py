import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
import joblib

df=pd.read_csv('health_data_5000.csv')

# Encode activity levels
activity_map = {'Low': 0, 'Moderate': 1, 'High': 2}
df['activity_level'] = df['activity_level'].map(activity_map)

# Define features and labels
X = df[['pulse', 'blood_pressure', 'weight', 'activity_level']]
y = df['recommendation']

# Split data into training/testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Standardize features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train K-Nearest Neighbors Model
knn = KNeighborsClassifier(n_neighbors=3)
knn.fit(X_train, y_train)
knn_pred = knn.predict(X_test)
knn_accuracy = accuracy_score(y_test, knn_pred)

# Train Random Forest model
rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X_train, y_train)
rf_pred = rf.predict(X_test)
rf_accuracy = accuracy_score(y_test, rf_pred)

# Display accuracies
print(knn_accuracy, rf_accuracy)


# Save models
joblib.dump(knn, 'knn_model.pkl')
joblib.dump(rf, 'rf_model.pkl')
joblib.dump(scaler, 'scaler.pkl')

print("Models trained and saved successfully!")

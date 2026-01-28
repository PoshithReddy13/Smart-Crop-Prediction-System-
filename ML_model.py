import pandas as pd
import pickle
import seaborn as sns
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score

# Load data
df = pd.read_csv("Plant_Parameters.csv")

# Drop unused columns
df.drop(columns=['Urea', 'T.S.P', 'M.O.P'], inplace=True)
df.dropna(inplace=True)

# Rename columns
df.rename(columns={
    'pH': 'ph',
    'Soil EC': 'soil_ec',
    'Phosphorus': 'P',
    'Potassium': 'K',
    'Moisture': 'humidity',
    'Temperature': 'temperature'
}, inplace=True)

# Add rainfall feature
df["rainfall"] = 100.0

X = df[['ph', 'soil_ec', 'P', 'K', 'humidity', 'temperature', 'rainfall']]
y = df['Plant Type']

# Encode target
le = LabelEncoder()
y_enc = le.fit_transform(y)

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y_enc, test_size=0.2, stratify=y_enc, random_state=42
)

# Scale
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# Train
model = GradientBoostingClassifier(n_estimators=200, learning_rate=0.05)
model.fit(X_train, y_train)

# Evaluate
print("Accuracy:", accuracy_score(y_test, model.predict(X_test)))

# Save
pickle.dump(model, open("crop_model.pkl", "wb"))
pickle.dump(scaler, open("scaler.pkl", "wb"))
pickle.dump(le, open("label_encoder.pkl", "wb"))

print("✅ Model, scaler, encoder saved")

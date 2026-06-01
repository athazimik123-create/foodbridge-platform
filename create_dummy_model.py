import numpy as np
import pandas as pd
import joblib
from xgboost import XGBClassifier
from sklearn.preprocessing import LabelEncoder

# 1. Define food categories aligned with seed_data.py
food_types = ["Bakery", "Prepared Meals", "Produce", "Dairy", "Seafood", "Grains", "Fruits", "Snacks", "Mixed"]

# 2. Fit and save the food encoder
food_encoder = LabelEncoder()
food_encoder.fit(food_types)
joblib.dump(food_encoder, "food_encoder.pkl")
print("Saved food_encoder.pkl with classes:", food_encoder.classes_)

# 3. Fit and save the label encoder
label_encoder = LabelEncoder()
label_encoder.fit(["Fresh", "Spoiled"])
joblib.dump(label_encoder, "label_encoder.pkl")
print("Saved label_encoder.pkl with classes:", label_encoder.classes_)

# 4. Generate some simulated training data to train a simple XGBoost model
np.random.seed(42)
num_samples = 200

# Random features
temp = np.random.uniform(10, 45, num_samples)
humidity = np.random.uniform(30, 95, num_samples)
mq2 = np.random.uniform(20, 400, num_samples)
mq4 = np.random.uniform(20, 400, num_samples)
mq135 = np.random.uniform(20, 500, num_samples)
mq136 = np.random.uniform(10, 300, num_samples)
food_encoded = np.random.choice(len(food_types), num_samples)

df = pd.DataFrame({
    'Temperature': temp,
    'Humidity': humidity,
    'MQ2': mq2,
    'MQ4': mq4,
    'MQ135': mq135,
    'MQ136': mq136,
    'Food': food_encoded
})

# Make target label depend roughly on temperature, humidity, and gas sensor levels (MQ135 / MQ136)
# Higher temperature/humidity/gas levels -> higher chance of spoilage
spoilage_prob = (
    0.2 * (temp > 30) + 
    0.2 * (humidity > 75) + 
    0.3 * (mq135 > 250) + 
    0.3 * (mq136 > 150)
)
y = (spoilage_prob + np.random.normal(0, 0.15, num_samples) > 0.5).astype(int)

# Ensure both classes are present
if len(np.unique(y)) < 2:
    y[0] = 0
    y[1] = 1

# 5. Train the XGBoost model
xgb_model = XGBClassifier(
    n_estimators=50,
    max_depth=3,
    learning_rate=0.1,
    random_state=42,
    use_label_encoder=False,
    eval_metric='logloss'
)
xgb_model.fit(df, y)

# 6. Save the XGBoost model
joblib.dump(xgb_model, "xgboost_model.pkl")
print("Saved xgboost_model.pkl successfully!")

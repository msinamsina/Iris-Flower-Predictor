# model.py
import joblib
import numpy as np

# Load the trained model
model = joblib.load('iris_model.pkl')


# Define a function to make predictions
def predict_iris(sepal_length, sepal_width, petal_length, petal_width):
    # Prepare the data in the format the model expects
    features = np.array(
        [[sepal_length, sepal_width, petal_length, petal_width]])
    prediction = model.predict(features)

    # Map the prediction to the class name
    iris_types = {0: 'Setosa', 1: 'Versicolor', 2: 'Virginica'}
    return iris_types[prediction[0]]

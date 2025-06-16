from PIL import Image
import numpy as np
import random
from sklearn.linear_model import LinearRegression
import pandas as pd
from linear_regression import *

# List of image paths
IMAGE_PATHS = [f"sometimes food/img{i}.jpg" for i in range(10)]

class Food:
    def __init__(self, path, calories, predicted_fat=None, is_healthy=None):
        self.path = path if path is not None else random.choice(IMAGE_PATHS)
        self.calories = calories if calories is not None else random.randint(100, 700)
        
        # Load model and predict fat content
        model = load_model()
        self.predicted_fat = predicted_fat if predicted_fat is not None else model.predict([[self.calories]])[0]
        
        # Set is_healthy based on predicted fat threshold
        self.is_healthy = is_healthy if is_healthy is not None else self.predicted_fat < 20
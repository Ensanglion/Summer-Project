import pandas as pd
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import numpy as np

original_df = pd.read_csv('Nutrition_Value_Dataset.csv')
filtered_df = original_df[['Energy (kCal)', 'Total Fat (g)']].dropna()

# Filter out high-calorie outliers
filtered_df = filtered_df[filtered_df['Energy (kCal)'] <= 700]

X = filtered_df[['Energy (kCal)']] # calories
y = filtered_df['Total Fat (g)'] # fat
model = LinearRegression()
model.fit(X, y)

# Print model coefficients and score
print(f"\nModel coefficients:")
print(f"Slope: {model.coef_[0]:.4f}")
print(f"Intercept: {model.intercept_:.4f}")
print(f"R-squared score: {model.score(X, y):.4f}")

# Create scatter plot with regression line
plt.figure(figsize=(10, 6))
plt.scatter(X, y, alpha=0.5, label='Actual Data')
plt.plot(X, model.predict(X), color='red', label='Regression Line')
plt.xlabel('Energy (kCal)')
plt.ylabel('Total Fat (g)')
plt.title('Energy vs Total Fat with Linear Regression (Calories ≤ 700)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()

# Test some example predictions
test_calories = [50, 100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650]
print("\nPredictions and actual values:")
for calories in test_calories:
    # Create a proper DataFrame for prediction
    test_df = pd.DataFrame([[calories]], columns=['Energy (kCal)'])
    predicted_fat = model.predict(test_df)[0]
    print(f"\nFor {calories} calories:")
    print(f"Predicted fat: {predicted_fat:.2f} grams")
    
    # Find actual values within ±50 calories
    actual_values = filtered_df[
        (filtered_df['Energy (kCal)'] >= calories - 50) & 
        (filtered_df['Energy (kCal)'] <= calories + 50)
    ]
    if not actual_values.empty:
        avg_fat = actual_values['Total Fat (g)'].mean()
        print(f"Average actual fat in this range: {avg_fat:.2f} grams")
    else:
        print("No actual values found in this range")
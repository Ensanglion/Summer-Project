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
print(f"\nLinear equation: Fat = {model.coef_[0]:.4f} * Calories {'-' if model.intercept_ < 0 else '+'} {abs(model.intercept_):.4f}")

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
import pandas as pd
from sklearn.linear_model import LinearRegression

# Load the dataset, then intialize and train the model
def load_model():
    original_df = pd.read_csv('Nutrition_Value_Dataset.csv')
    filtered_df = original_df[['Energy (kCal)', 'Total Fat (g)']].dropna()

    # Filter out high-calorie outliers
    filtered_df = filtered_df[filtered_df['Energy (kCal)'] <= 700]

    X = filtered_df[['Energy (kCal)']] # calories
    y = filtered_df['Total Fat (g)'] # fat
    model = LinearRegression()
    model.fit(X, y)

    return model

import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# Initialize session state for storing meal data if not exists
if 'meals' not in st.session_state:
    st.session_state.meals = []

st.title("Nutrient & Calorie Tracker")

# Function to fetch food data from OpenFoodFacts API
def get_food_data(food_name):
    url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={food_name}&json=1"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data['products']:
            product = data['products'][0]
            return {
                'name': food_name,
                'calories': product.get('nutriments', {}).get('energy-kcal', 0),
                'protein': product.get('nutriments', {}).get('proteins', 0),
                'carbs': product.get('nutriments', {}).get('carbohydrates', 0),
                'fat': product.get('nutriments', {}).get('fat', 0)
            }
    return None

# Input form for meals
with st.form("meal_form"):
    food_name = st.text_input("Enter food name")
    portion_size = st.number_input("Portion size (grams)", min_value=0)
    meal_time = st.selectbox("Meal time", ["Breakfast", "Lunch", "Dinner", "Snack"])
    submit_button = st.form_submit_button("Add Meal")

if submit_button and food_name and portion_size:
    food_data = get_food_data(food_name)
    if food_data:
        # Scale nutrients based on portion size
        scaling_factor = portion_size / 100  # API usually returns per 100g
        meal_entry = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'food_name': food_name,
            'portion': portion_size,
            'meal_time': meal_time,
            'calories': food_data['calories'] * scaling_factor,
            'protein': food_data['protein'] * scaling_factor,
            'carbs': food_data['carbs'] * scaling_factor,
            'fat': food_data['fat'] * scaling_factor
        }
        st.session_state.meals.append(meal_entry)
        st.success("Meal added successfully!")
    else:
        st.error("Food not found in database")

# Display daily summary
st.subheader("Today's Summary")
today = datetime.now().strftime('%Y-%m-%d')
today_meals = [meal for meal in st.session_state.meals if meal['date'] == today]

if today_meals:
    daily_totals = {
        'calories': sum(meal['calories'] for meal in today_meals),
        'protein': sum(meal['protein'] for meal in today_meals),
        'carbs': sum(meal['carbs'] for meal in today_meals),
        'fat': sum(meal['fat'] for meal in today_meals)
    }
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Calories", f"{daily_totals['calories']:.1f} kcal")
    col2.metric("Protein", f"{daily_totals['protein']:.1f}g")
    col3.metric("Carbs", f"{daily_totals['carbs']:.1f}g")
    col4.metric("Fat", f"{daily_totals['fat']:.1f}g")

# Weekly summary visualization
st.subheader("Weekly Summary")
end_date = datetime.now()
start_date = end_date - timedelta(days=7)
weekly_meals = [meal for meal in st.session_state.meals 
                if start_date.strftime('%Y-%m-%d') <= meal['date'] <= end_date.strftime('%Y-%m-%d')]

if weekly_meals:
    df = pd.DataFrame(weekly_meals)
    df['date'] = pd.to_datetime(df['date'])
    daily_stats = df.groupby('date').agg({
        'calories': 'sum',
        'protein': 'sum',
        'carbs': 'sum',
        'fat': 'sum'
    }).reset_index()
    
    # Display line chart for calories
    st.line_chart(daily_stats.set_index('date')['calories'])
    
    # Display bar chart for macronutrients
    st.bar_chart(daily_stats.set_index('date')[['protein', 'carbs', 'fat']])
else:
    st.info("No data available for the past week")

# Display recent meals
st.subheader("Recent Meals")
if st.session_state.meals:
    recent_meals_df = pd.DataFrame(st.session_state.meals[-5:])
    st.table(recent_meals_df[['date', 'meal_time', 'food_name', 'portion', 'calories']])
else:
    st.info("No meals recorded yet")

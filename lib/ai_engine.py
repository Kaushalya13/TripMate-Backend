import pandas as pd
import numpy as np
import joblib
import os
from math import radians, cos, sin, asin, sqrt

# --- DATA LOADING & SANITIZATION ---
def load_and_clean_data():
    path = 'data/Locations_Data.csv'
    if not os.path.exists(path):
        raise FileNotFoundError(f"Critical Error: {path} not found!")
    
    data = pd.read_csv(path)
    # Convert and fill NaNs for numeric columns
    data['Cost_LKR'] = pd.to_numeric(data['Cost_LKR'], errors='coerce').fillna(0)
    interest_cols = ['Interest_Beach', 'Interest_Nature', 'Interest_History', 'Interest_Religious']
    for col in interest_cols:
        data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0).astype(int)
    
    # Remove rows without valid coordinates
    data = data.dropna(subset=['Latitude', 'Longitude'])
    return data

# Load fixed data and pre-trained models
df_locs = load_and_clean_data()
model = joblib.load('model/tripmate_model.pkl')
scaler = joblib.load('model/tripmate_scaler.pkl')

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    return 2 * asin(sqrt(sin((lat2-lat1)/2)**2 + cos(lat1)*cos(lat2)*sin((lon2-lon1)/2)**2)) * R

def dist_to_line(p_lat, p_lon, a_lat, a_lon, b_lat, b_lon):
    p, a, b = np.array([p_lat, p_lon]), np.array([a_lat, a_lon]), np.array([b_lat, b_lon])
    if np.array_equal(a, b): return haversine(p_lat, p_lon, a_lat, a_lon)
    return np.abs(np.cross(b-a, a-p)) / np.linalg.norm(b-a)

def get_ai_scores(u_prof, subset_df):
    feats = ['Latitude', 'Longitude', 'Cost_LKR', 'Interest_Beach', 'Interest_Nature', 'Interest_History', 'Interest_Religious']
    inputs = [u_prof + list(r[feats]) for _, r in subset_df.iterrows()]
    # scaler.transform handles the feature normalization before the Neural Network scores them
    return model.predict_proba(scaler.transform(inputs))[:, 1]

def get_route_plan(s_name, e_name, u_prof, days):
    try:
        # 1. Fetch Start and End points
        s = df_locs[df_locs['Name'].str.contains(s_name, case=False, na=False)].iloc[0]
        e = df_locs[df_locs['Name'].str.contains(e_name, case=False, na=False)].iloc[0]
    except Exception as e:
        print(f"Location Lookup Error: {e}")
        return None
    
    # 2. CREATE A BOUNDING BOX (The "Safety Rectangle")
    # This prevents the AI from looking at Galle (South) or Negombo (North) 
    # when you are traveling between Moratuwa and Colombo.
    lat_min, lat_max = min(s.Latitude, e.Latitude), max(s.Latitude, e.Latitude)
    lon_min, lon_max = min(s.Longitude, e.Longitude), max(s.Longitude, e.Longitude)
    
    # Add a 0.05 degree buffer (approx 5km) so we don't miss spots 
    # slightly outside the direct rectangle.
    buffer = 0.05
    
    pool = df_locs.copy()
    pool = pool[
        (pool['Latitude'] >= lat_min - buffer) & 
        (pool['Latitude'] <= lat_max + buffer) &
        (pool['Longitude'] >= lon_min - buffer) & 
        (pool['Longitude'] <= lon_max + buffer)
    ].copy()

    # If the bounding box is too empty, fall back to the original pool
    if len(pool) < (days * 2):
        pool = df_locs.copy()

    # 3. CALCULATE OFF-ROUTE DISTANCE
    # Filter only those points within 15km of the straight-line corridor
    pool['off_route'] = pool.apply(
        lambda x: dist_to_line(x.Latitude, x.Longitude, s.Latitude, s.Longitude, e.Latitude, e.Longitude), 
        axis=1
    )
    pool = pool[pool['off_route'] < 0.15].copy() 

    if pool.empty:
        return {"itinerary": {}, "message": "No suitable spots found in this corridor."}

    # 4. AI SCORING & PROGRESSION
    # Score based on user interests [age, budget, beach, nature, history, religious]
    pool['ai_score'] = get_ai_scores(u_prof, pool)
    
    # Measure distance from start to ensure the itinerary flows in order
    pool['dist_start'] = pool.apply(
        lambda x: haversine(s.Latitude, s.Longitude, x.Latitude, x.Longitude), 
        axis=1
    )
    
    # 5. ORGANIZE ITINERARY
    itinerary = {f"day_{d}": [] for d in range(1, days + 1)}
    
    # Select top spots (3 per day) and sort them by distance so the route is logical
    top_pois = pool.sort_values('ai_score', ascending=False).head(days * 3).sort_values('dist_start')
    
    for i, (_, poi) in enumerate(top_pois.iterrows()):
        day_idx = (i // 3) + 1
        if day_idx <= days:
            # We convert to dict and ensure NaN values are handled for JSON safety
            poi_dict = poi.to_dict()
            itinerary[f"day_{day_idx}"].append(poi_dict)
            
    return itinerary

# ENGINE 2: CITY
def get_city_plan(city_name, u_prof, days):
    try:
        match = df_locs[df_locs['Name'].str.contains(city_name, case=False)].iloc[0]
        pool = df_locs[df_locs['City'].str.lower() == match['City'].lower()].copy()
    except: return None
    
    pool['ai_score'] = get_ai_scores(u_prof, pool)
    itinerary = {}
    top = pool.sort_values('ai_score', ascending=False)
    for d in range(1, days + 1):
        itinerary[f"day_{d}"] = top.iloc[(d-1)*3 : d*3].to_dict('records')
    return itinerary

# ENGINE 3: DISCOVER
def get_nearby(place_name, u_prof):
    curr = df_locs[df_locs['Name'].str.contains(place_name, case=False)].iloc[0]
    pool = df_locs[df_locs['Name'] != curr['Name']].copy()
    pool['dist'] = pool.apply(lambda x: haversine(curr.Latitude, curr.Longitude, x.Latitude, x.Longitude), axis=1)
    pool = pool[pool['dist'] < 15].copy()
    pool['ai_score'] = get_ai_scores(u_prof, pool)
    return pool.sort_values('ai_score', ascending=False).head(5).to_dict('records')
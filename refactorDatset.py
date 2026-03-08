import pandas as pd
df = pd.read_csv('data.CSV')
df['POI_ID'] = range(1, len(df) + 1)
import os
os.makedirs('data', exist_ok=True)
df.to_csv('data/Locations_Data.csv', index=False)
print("✅ data/Locations_Data.csv created with correct IDs.")
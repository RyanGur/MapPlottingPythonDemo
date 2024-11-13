import pandas as pd
from shapely.geometry import Point
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import geopandas as gpd  # For reading shapefiles
import matplotlib.pyplot as plt
from geopy.distance import geodesic

# Load data from CSV
data = pd.read_csv('data/farmers_customers_warehouses.csv')

# Separate data by type
farmers = data[data['type'] == 'farmer']
homeless = data[data['type'] == 'homeless']
warehouses = data[data['type'] == 'warehouse']

# Load Minneapolis neighborhood boundaries shapefile
# Ensure this shapefile has Minneapolis city boundary and/or neighborhood boundaries
neighborhoods = gpd.read_file('data/minneapolis_neighborhoods.shp')

# Initialize a map of the region around Minneapolis with Cartopy
fig = plt.figure(figsize=(12, 12))
ax = plt.axes(projection=ccrs.PlateCarree())
ax.set_extent([-93.5, -93.0, 44.7, 45.2], crs=ccrs.PlateCarree())  # Intermediate zoom level

# Add state borders with distinct styling
state_borders = cfeature.NaturalEarthFeature(
    category='cultural', scale='10m', facecolor='none',
    name='admin_1_states_provinces_lines')

ax.add_feature(state_borders, edgecolor='blue', linewidth=1.5, linestyle='--', label="State Border")

# Add other map features for context
ax.add_feature(cfeature.BORDERS, linestyle=':', edgecolor='gray')
ax.add_feature(cfeature.COASTLINE, linestyle=':')
ax.add_feature(cfeature.STATES, edgecolor='black')
ax.add_feature(cfeature.LAND, color='lightgray', alpha=0.5)
ax.add_feature(cfeature.LAKES, color='lightblue')

# Plot Minneapolis neighborhoods with color
neighborhoods = neighborhoods.to_crs(epsg=4326)  # WGS84 latitude-longitude format
neighborhoods.plot(ax=ax, color='lightyellow', edgecolor='black', linewidth=0.5, alpha=0.3)

# Function to count nearby points within a distance (in km) from a central point
def count_nearby_points(center, points, distance_km):
    count = 0
    for _, row in points.iterrows():
        point = (row['latitude'], row['longitude'])
        if geodesic(center, point).km <= distance_km:
            count += 1
    return count

# Define a search radius (e.g., 1 km)
search_radius_km = 4
max_total_count = 0
highlighted_warehouse = None

# Determine which warehouse has the most farmers and homeless within its radius
warehouse_counts = []  # Store each warehouse’s counts for later plotting
for _, warehouse in warehouses.iterrows():
    center = (warehouse['latitude'], warehouse['longitude'])
    warehouse_point = Point(warehouse['longitude'], warehouse['latitude'])
    
    # Count farmers and homeless locations within the radius
    num_farmers = count_nearby_points(center, farmers, search_radius_km)
    num_homeless = count_nearby_points(center, homeless, search_radius_km)
    total_count = num_farmers + num_homeless
    
    # Check if this warehouse has the highest total count
    if total_count > max_total_count:
        max_total_count = total_count
        highlighted_warehouse = warehouse
    
    # Store count info for plotting
    warehouse_counts.append((warehouse_point, num_farmers, num_homeless, total_count))

# Plot each warehouse with a distinct color for the one with the most farmers and homeless shelters
for warehouse_point, num_farmers, num_homeless, total_count in warehouse_counts:
    # Determine if this is the highlighted warehouse
    is_highlighted = (total_count == max_total_count)
    
    # Plot warehouse as a blue square
    ax.plot(warehouse_point.x, warehouse_point.y, 'bs', markersize=8, transform=ccrs.PlateCarree(), label='Warehouse')
    
    # Create a circular buffer around the warehouse
    buffer = warehouse_point.buffer(search_radius_km / 111)  # Approx 1 degree ~ 111 km
    x, y = buffer.exterior.xy
    buffer_color = 'red' if is_highlighted else ('purple' if num_farmers > num_homeless else 'orange')
    ax.fill(x, y, alpha=0.3, transform=ccrs.PlateCarree(),
            color=buffer_color,
            label=f"Radius: {search_radius_km} km\nFarmers: {num_farmers}\nHomeless: {num_homeless}")

# Plot Farmers and Homeless locations with different colors
for idx, row in farmers.iterrows():
    ax.plot(row['longitude'], row['latitude'], 'go', markersize=6, transform=ccrs.PlateCarree(), label='Farmer' if idx == farmers.index[0] else "")

for idx, row in homeless.iterrows():
    ax.plot(row['longitude'], row['latitude'], 'ro', markersize=6, transform=ccrs.PlateCarree(), label='Homeless' if idx == homeless.index[0] else "")

# Add a custom legend to specify the state line and categories
plt.legend(loc='upper left')
plt.title("Warehouse Coverage in Minneapolis: Farmers (Supply) and Homeless (Customers)")
plt.xlabel("Longitude")
plt.ylabel("Latitude")

# Show plot
plt.show()

#For the plot, the red sphere is to indicate the warehouse with the most number of total farmers and homeless
#Purple is to indicate it has more farmers than homeless, and Orange for more homeless than farmers
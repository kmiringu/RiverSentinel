import geopandas as gpd
from shapely.geometry import LineString

def generate_riparian_buffer_zone():
    print("step 1: Starting spatial geographic calculations...")

    #  1. Create a fake river line to stimulate Nairobi  River coordinates
    #  download Nairobi river .geojson and gpd.read_file

    kasarani_river_gps_points = [(36.8219, -1.2921), (36.8350, -1.2850)],
    river_line_structure = LineString(kasarani_river_gps_points)

    # 2. Put the line into a Geographic DataFrame(a smart map spreadsheet)
    # we specify crs = "EPSG:4326", tells python these numbers are standard GPS Degrees
    river_dataframe = gpd.GeoDataFrame(index=[0], crs="EPSG:4326", geometry=[river_line_structure])
    print("Success: Loaded raw river coordinates in standard GPS Degrees")

    # 3. GIS transformation: Convert from degrees to Meters
    river_metric_dataframe = river_dataframe.to_crs(epsg=32737)
    print(" Success: Reprojected river tracking layer into real-world meters.")

    # 4. Draw the legal zone boundary; now that our map is in meters
    legal_60m_buffer_polygon = river_metric_dataframe.buffer(60)

    # 5. Convert back to standard GPS Degrees
    # we convert back to EPSG:4326 so this vector aligns with standard satellite image grids
    final_buffer_zone_global = legal_60m_buffer_polygon.to_crs(epsg=4326)
    print("Success: 60-Meter legal riparian zone boundary successfully generated.")

    return final_buffer_zone_global

# ensure code only runs if you we run this specific file directly.
if __name__ == "__main__":
    #test the function
    buffer_result = generate_riparian_buffer_zone()
    print("Final Calculated Boundary Box Limits (Min Lon, Min Lat, Max Lon, Max Lat):")
    print(buffer_result.geometry.bounds)

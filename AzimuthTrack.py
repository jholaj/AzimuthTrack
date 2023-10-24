import datetime
from pysolar.solar import get_azimuth
import googlemaps
import polyline
from geopy.distance import great_circle
from geopy import distance
import math
#############
from config import api_key


# Latitude, Longtitude, Sunrise, Sunset, Time, Timezone

# 0°     NORTH
# 90°    EAST
# 180°   SOUTH 
# 270°   WEST 

gmaps = googlemaps.Client(key=api_key) 

# Liberec
start_latitude = 50.76711
start_longtitude = 15.05619

# Hradec
end_latitude = 50.210361
end_longtitude = 15.825211

date_time = datetime.datetime(2023, 10, 24, 9, 30, 30, tzinfo=datetime.timezone.utc)

start_location = {
    "latitude": start_latitude,
    "longtitude": start_longtitude,
}

start_point = (start_location['latitude'], start_location['longtitude'])


end_location = {
    "latitude": end_latitude,
    "longtitude": end_longtitude,
}

###################################################################

def calc_sun_azimuth_percentage(latitude, longitude, date_time, start_latitude, start_longitude):
    # calc distance from start to current point
    distance = great_circle((start_latitude, start_longitude), (latitude, longitude)).meters
    print(f"Zkontrolováno na {distance} metrech")
    
    azimuth_degrees = get_azimuth(latitude, longitude, date_time)
    
    bearing = calculate_bearing(start_point, (latitude, longitude))

    # diff between bearing of route and azimuth
    angle_difference = abs(bearing - azimuth_degrees)

    if angle_difference < 90 or angle_difference > 270:
        return True
    else:
        return False

###################################################################

def calculate_bearing(point1, point2):
    
    # calc bearing of route 
    lat1, lon1 = point1
    lat2, lon2 = point2

    delta_lon = lon2 - lon1

    #calc azimuth
    y = math.sin(math.radians(delta_lon)) * math.cos(math.radians(lat2))
    x = math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) - math.sin(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.cos(math.radians(delta_lon))
    
    # calc angle between y and x
    initial_bearing = math.atan2(y, x)
    initial_bearing = math.degrees(initial_bearing)
    #0 - 360°
    compass_bearing = (initial_bearing + 360) % 360

    return compass_bearing

###################################################################

def calc_percentage_for_data(data, date_time):
    left_counter = 0
    right_counter = 0
    total_count = len(data)
    
    start_latitude, start_longitude = data[0]

    for i, (latitude, longitude) in enumerate(data):
        azimuth_info = calc_sun_azimuth_percentage(latitude, longitude, date_time, start_latitude, start_longitude)
        print(f"Bod {i + 1}: {azimuth_info}")
        
        if azimuth_info == True:
            left_counter += 1
        else:
            right_counter += 1
    
    left_percentage = (left_counter / total_count) * 100
    right_percentage = (right_counter / total_count) * 100

    return left_percentage, right_percentage

###################################################################

directions_result = gmaps.directions((start_location['latitude'], start_location['longtitude']), (end_location['latitude'], end_location['longtitude']), mode="driving")
route = directions_result[0]['overview_polyline']['points']

decoded_route = polyline.decode(route)

result = calc_percentage_for_data(decoded_route, date_time)
length = directions_result[0]['legs'][0]['distance']['text']

print(f"Délka trasy: {length}")
print(f"Procento trasy se sluncem nalevo: {result[0]}%")
print(f"Procento trasy se sluncem napravo: {result[1]}%")

if result[0] > result[1]:
    print("Preferovaná strana: VPRAVO")
else:
    print("Preferovaná strana: VLEVO")

###################################################################



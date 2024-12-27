import datetime
from dataclasses import dataclass
import logging
from pathlib import Path
import os
from dotenv import load_dotenv

import openrouteservice
from pysolar.solar import get_azimuth, get_altitude
import math
import gmplot


load_dotenv()

# Setting up the logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class Coordinates:
    latitude: float
    longitude: float

    def validate(self) -> bool:
        """Validate coordinates."""
        return (-90 <= self.latitude <= 90) and (-180 <= self.longitude <= 180)

class RouteCalculator:
    def __init__(self, api_key: str):
        """
        Initialize the route calculator.

        Args:
            api_key: OpenRouteService API key
        """
        self.api_key = api_key
        self.client = self._initialize_client()

    def _initialize_client(self) -> openrouteservice.Client:
        try:
            return openrouteservice.Client(key=self.api_key)
        except Exception as e:
            logger.error(f"Error initializing client: {e}")
            raise

    def calculate_bearing(self, point1: Coordinates, point2: Coordinates) -> float:
        """
        Calculate the bearing between two points.

        Returns:
            float: Bearing in degrees (0-360)
        """
        delta_lon = point2.longitude - point1.longitude

        y = math.sin(math.radians(delta_lon)) * math.cos(math.radians(point2.latitude))
        x = (math.cos(math.radians(point1.latitude)) * math.sin(math.radians(point2.latitude)) -
             math.sin(math.radians(point1.latitude)) * math.cos(math.radians(point2.latitude)) *
             math.cos(math.radians(delta_lon)))

        initial_bearing = math.atan2(y, x)
        return (math.degrees(initial_bearing) + 360) % 360

    def get_route(self, start: Coordinates, end: Coordinates) -> list[tuple[float, float]]:
        """
        Get a route from OpenRouteService with error handling.

        Returns:
            List of route points
        """
        try:
            if not (start.validate() and end.validate()):
                raise ValueError("Invalid coordinates")

            route = self.client.directions(
                profile='driving-car',
                format='geojson',
                coordinates=[(start.longitude, start.latitude),
                             (end.longitude, end.latitude)]
            )
            return [(point[1], point[0]) for point in
                    route['features'][0]['geometry']['coordinates']]
        except Exception as e:
            logger.error(f"Error getting route: {e}")
            raise

class SunCalculator:
    def __init__(self, date_time: datetime.datetime):
        self.date_time = date_time

    def calculate_sun_trajectory(self, location: Coordinates, num_points: int = 100) -> list[Coordinates]:
        """
        Calculate the sun's trajectory.

        Returns:
            List of sun trajectory points
        """
        trajectory = []

        for i in range(num_points):
            time = self.date_time + datetime.timedelta(minutes=i*15)
            azimuth = get_azimuth(location.latitude, location.longitude, time)
            altitude = get_altitude(location.latitude, location.longitude, time)

            if altitude > 0:
                distance_factor = 0.1
                sun_lat = location.latitude + distance_factor * math.cos(math.radians(azimuth))
                sun_lon = location.longitude + distance_factor * math.sin(math.radians(azimuth))
                trajectory.append(Coordinates(sun_lat, sun_lon))

        return trajectory

    def is_sun_on_left(self,
                       current: Coordinates,
                       bearing: float) -> bool:
        """Determine if the sun is to the left of the route."""
        azimuth = get_azimuth(current.latitude, current.longitude, self.date_time)
        angle_diff = abs(bearing - azimuth)
        return angle_diff < 90 or angle_diff > 270

class MapVisualizer:
    def __init__(self, start: Coordinates, zoom: int = 13):
        self.gmap = gmplot.GoogleMapPlotter(start.latitude, start.longitude, zoom)

    def plot_route(self,
                   route_points: list[Coordinates],
                   sun_calc: SunCalculator,
                   route_calc: RouteCalculator) -> None:
        """Plot the route with colors based on the sun's position."""
        for i in range(len(route_points) - 1):
            start_point = route_points[i]
            end_point = route_points[i + 1]

            bearing = route_calc.calculate_bearing(start_point, end_point)
            color = 'blue' if sun_calc.is_sun_on_left(start_point, bearing) else 'green'

            self.gmap.plot([start_point.latitude, end_point.latitude],
                           [start_point.longitude, end_point.longitude],
                           color=color, edge_width=3)

    def plot_sun_trajectory(self,
                            trajectory: list[Coordinates],
                            ray_length: float = 0.1) -> None:
        """Plot the sun's trajectory and rays."""
        # Trajectory
        self.gmap.plot([p.latitude for p in trajectory],
                       [p.longitude for p in trajectory],
                       color='yellow', edge_width=3)

        # Rays
        for point in trajectory:
            azimuth = get_azimuth(point.latitude, point.longitude,
                                  datetime.datetime.now(datetime.timezone.utc))
            ray_lat = point.latitude + ray_length * math.cos(math.radians(azimuth))
            ray_lon = point.longitude + ray_length * math.sin(math.radians(azimuth))
            self.gmap.plot([point.latitude, ray_lat],
                           [point.longitude, ray_lon],
                           color='orange', edge_width=2)

    def add_markers(self, start: Coordinates, end: Coordinates) -> None:
        """Add markers for start and end points."""
        self.gmap.marker(start.latitude, start.longitude,
                         title="Start: Liberec", color='red')
        self.gmap.marker(end.latitude, end.longitude,
                         title="End: Hradec", color='red')

    def save(self, filename: str) -> None:
        """Save the map to a file."""
        output_path = Path(filename)
        self.gmap.draw(str(output_path))
        logger.info(f"Map saved to: {output_path.absolute()}")

def main():
    # Configuration
    start = Coordinates(50.76711, 15.05619)  # Liberec
    end = Coordinates(50.210361, 15.825211)  # Hradec
    date_time = datetime.datetime.now(datetime.timezone.utc)

    # Initialize calculators
    API_KEY = os.getenv('OPENROUTESERVICE_API_KEY')

    if not API_KEY:
        raise ValueError("API key is missing from the .env file")

    route_calc = RouteCalculator(API_KEY)
    sun_calc = SunCalculator(date_time)

    # Get the route
    route_points = [Coordinates(lat, lon) for lat, lon in
                    route_calc.get_route(start, end)]

    # Calculate the sun's trajectory
    sun_trajectory = sun_calc.calculate_sun_trajectory(start)

    # Visualization
    visualizer = MapVisualizer(start)
    visualizer.plot_route(route_points, sun_calc, route_calc)
    visualizer.plot_sun_trajectory(sun_trajectory)
    visualizer.add_markers(start, end)
    # Save map to HTML file
    visualizer.save("route_map_with_sun.html")

    logger.info("Route visualization was successfully created!")

if __name__ == "__main__":
    main()

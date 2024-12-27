# Route and Sun Trajectory Visualizer

This project calculates a driving route between two points and visualizes the sun's trajectory along that route. It uses the OpenRouteService API to obtain routing data and the PySolar library to compute the sun's position based on geographic coordinates and time.

## Features

- Calculate driving routes using OpenRouteService API.
- Compute the sun's trajectory for a given location and time.
- Visualize the route and sun trajectory on an interactive map.
- Color-code the route segments based on the sun's position relative to the route.

## Requirements
- Python 3.7 or higher
- Libraries listed in *requirements.txt*

## Installation

1. Clone this repository:
```bash
git clone https://github.com/jholaj/RouteSunVisualizer.git
cd RouteSunVisualizer
```
2. Install the required packages:
```bash
pip install -r requirements.txt
```
3. Create a `.env` file in the root directory of the project and add your OpenRouteService API key:
```bash
cp .env_example .env
```

## Example
![Example No. 1](https://imgur.com/bapPzri.png)

## Notes
- Current version has hardcoded Start & Destination & Time
- Saves output to .html file


## Acknowledgments
- [OpenRouteService](https://openrouteservice.org/) for routing services.
- [PySolar](https://pysolar.readthedocs.io/) for solar calculations.
- [gmplot](https://github.com/gmplot/gmplot) for Google Maps visualization.

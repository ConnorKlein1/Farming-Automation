import random
from shapely.geometry import Polygon

# Generates a random shapely::Polygon
class RandomPolygon(Polygon):
    def __init__(self, num_vertices=5, min_coord=0, max_coord=500):
        self.num_vertices = num_vertices
        self.min_coord = min_coord
        self.max_coord = max_coord
        self.polygon = self.generate_polygon()

    def generate_polygon(self):
        while True:
            # Generate random points within a square
            points = [(random.uniform(self.min_coord, self.max_coord),
                       random.uniform(self.min_coord, self.max_coord))
                      for i in range(self.num_vertices)]

            # Create a polygon from the random points
            polygon = Polygon(points)

            # Check if the polygon is valid (i.e., not self-intersecting)
            if polygon.is_valid:
                return polygon
            
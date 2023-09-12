# Library
import numpy as np
from shapely.geometry import LineString, MultiPolygon, box
from shapely import affinity

# This is not a factory method, instead it produces rectangles that descibe a shapely::Polygon
class RectangleFactory():
    def __init__(self, polygon, toolSize):
        self.rectangles, self.centroid, self.angle, self.translate = self.CreateRects(polygon, toolSize)
        
    def VerticalAt(self, polygon):
        """
        Helper function to define if a polygon starts by traveling vertically

        Args:
            x: point to compare
            polygon: polygon to test verticalness at lower bound

        Returns: 
            Bool descibing if rectangle starts vertically
        """
        tolerance = 0.01
        coords = list(polygon.exterior.coords)
        occurrences = [i for i, point in enumerate(coords) if abs(point[0] - polygon.bounds[0]) < tolerance]
        
        # is not strait line becuase only one point
        if len(occurrences) < 2:
            return False
        
        # checking if they are next to eachother
        for i in range(len(occurrences) - 1):
            if abs(occurrences[i] - occurrences[i+1]) == 1:
                return True
        
        return False
    
    def RotateForLongestEdge(self, polygon):
        """
        Rotates Polygon so that longest side starts at the lowest left corner. This is an inital try
        at decreasing area of which the rectangles do not overlap the ploygon. Also allows for
        mathematics to be easier later on with vertical rects.

        Args:
            polygon (Shapely::Polygon)

        Returns: 
            A roated copy of a Shapely::Polygon
            The angle of rotation
            The translation needed to get the lowest left corner to (0,0)
        """
        longest_edge = None
        max_length = 0

        for i in range(len(polygon.exterior.coords) - 1):
            p1 = polygon.exterior.coords[i]
            p2 = polygon.exterior.coords[i + 1]
            edge = LineString([p1, p2])
            length = edge.length

            if length > max_length:
                max_length = length
                longest_edge = edge

        dx = longest_edge.coords[1][0] - longest_edge.coords[0][0]
        dy = longest_edge.coords[1][1] - longest_edge.coords[0][1]
        angle = np.math.atan2(dy, dx)
        
        rotatedAngle = np.pi / 2 - angle
        
        initalRotate = affinity.rotate(polygon, rotatedAngle, use_radians=True, origin=polygon.centroid)
        
        if not self.VerticalAt(initalRotate):
            initalRotate = affinity.rotate(initalRotate, np.pi, use_radians=True, origin=polygon.centroid)
            rotatedAngle += np.pi
        
        # Gets minimum y distance so can translate into +x
        min_y = initalRotate.bounds[1]
        
        if min_y >= 0:
            translated = 0
        else:
            translated = -min_y
            initalRotate = affinity.translate(initalRotate, yoff=translated)
            
        return initalRotate, rotatedAngle, translated
    
    def ContourToPoints(self, contour):
        
        # A contour starts and ends at the same point, want to remove it if that is was is passed in
        contour = list(contour)
        if contour[0][0] == contour[0][-1]:
            contour[0].pop()
            contour[1].pop()
            
        points = [[x, y] for x, y in zip(contour[0], contour[1])]
        minIndexX = points.index(min(points, key=lambda p: p[0]))
        # Sorting so that min x point is used
        return points[minIndexX:] + points[:minIndexX]
    
    def FillLines(self, points, toolSize):
        """
        Fills a set of lines with many points for animation later.

        Args:
            points ([[x1,y1], [x2,y2], ...])

        Returns: 
            Map of Shapely::Linstring to the points contained in that linestring.
            *right now a list, maybe should be a map but unsure what is more efficient.
        """
        # ensuring that we have a complete contour
        if points[0] != points[-1]:
            points.append(points[0])

        # Doing this right now for the MultiLineString API
        lineList = [LineString([points[i], points[i+1]]) for i in range(len(points)-1)]
        
        # lets see if this works
        relativeMap = [i for i in range(len(lineList))]
        
        minX = min(points, key=lambda p: p[0])[0]
        maxX = max(points, key=lambda p: p[0])[0] + toolSize
        minY = min(points, key=lambda p: p[1])[1]
        maxY = max(points, key=lambda p: p[1])[1]
        
        x = minX
        
        # yes, super inefficent
        while x < maxX:
            
            # making this line very high, should just do max height and min height
            line_string = LineString([[x, minY], [x, maxY]])
            
            for index, line in enumerate(lineList):
                # check if it crosses and if it is the same line
                if line.crosses(line_string) and not line_string.contains(line):
                    # therefore there is only one intersection
                    intersection = line.intersection(line_string)
                    
                    if intersection not in points:
                        
                        # finally insert the point
                        points.insert(relativeMap[index]+1, [intersection.x, intersection.y])
                        
                        # update the map
                        for i in range(index+1, len(relativeMap)):
                            relativeMap[i] += 1
                                
            x += toolSize    
                
        return points

    def DefineRect(self, point, x, toolSize):
        """
        Helper function to define if a point should be in the created rectangle.

        Args:
            point: ([x1,y1])
            x: point to compare
            toolSize: Size of rectangle

        Returns: 
            Bool descibing if point shoul dbe in rectangle
        """
        if point[0] <= (x + toolSize):
            return True
        else:
            return False
        
    def BuildRectsFromPoints(self, points, toolSize):
        """
        Given a set of points, construct rectangles that are of width of the given toolSize

        Args:
            point: ([[x1,y1], [x2,y2], ...])
            toolSize: Width of rectangle

        Returns: 
            Rectangles that descibe the points
        """
        rects = []
        points.sort(key = lambda x: x[0])
        
        while len(points):
            x = points[0][0]
            r = []

            # All the points within a certain x + distance
            pointsInRange = [point for point in points if self.DefineRect(point, x, toolSize)]

            # Checking if any points greater than x, don't need to make an empty rect if only one point
            xplusPointTest = [point for point in pointsInRange if point[0] > (x)]
            if len(xplusPointTest) == 0:
                break 

            y_min = min([r[1] for r in pointsInRange])
            y_max = max([r[1] for r in pointsInRange])

            points = [point for point in points if point[0] >= (x + toolSize)]

            rects.append(box(x, y_min, x+toolSize, y_max, ccw = True))
            
        return rects
        
    def CreateRects(self, polygon, toolSize):
        """Constructs a set of rectangles that best describe a complex Polygon

        Args:
            polygon (Shapely::Polygon): collection of points describing the outline of an area
            toolSize (float): thickness of the tool; how large the rectangles can be

        Returns: Shapely::MultiPolygon
        """
        polygons = []
        centroid = polygon.centroid
        
        # Rotating the polygon so that the longest edge is vertical
        polygon, angle, translation = self.RotateForLongestEdge(polygon)
        contour = polygon.exterior.coords.xy
        
        points = self.FillLines(self.ContourToPoints(contour), toolSize)
        polygons = self.BuildRectsFromPoints(points, toolSize)

        # return affinity.rotate(MultiPolygon(polygons), -angle, centroid, use_radians=True)
        # lets carry the angle of rotation to later for similicity, yes we can;t make this simple then
        return MultiPolygon(polygons), centroid, angle, translation
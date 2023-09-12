# Library
import numpy as np
from shapely.geometry import LineString

class ToolPath():
    def __init__(self, toolSize, toolLength, rectangles, pointsInEachPath):
        """
        Constructs a tool path given a set of rectangles.

        Args:
            toolSize (float): Width of rectangle
            toolLength (float): length of trailing object
            rectangles (shapely::MultiPolygon): set of vertical rectangles that the toolpath with descibe
            pointsInEachPath (int): points to be in each seperate path object

        Returns: 
            tool path that follows the rectangles
        """
        self.min_x, self.min_y, self.max_x, self.max_y = rectangles.bounds
        self.normalizedPts = int(np.ceil(toolLength / ((self.max_y - self.min_y) / pointsInEachPath)))
        
        self.path = self.CreatePath(toolSize, toolLength, rectangles, pointsInEachPath)
        
    def GetMidLinePointsFrom(self, shape):
        """
        Returns a line bisecting a rectangle.

        Args:
            shape (Shapely::Polygon): starting rectangle of beizer curve

        Returns: 
            [[topX, topY], [bottomX, bottomY]]
        """
        topDiff = [(shape[2][0] - shape[1][0]) / 2 , (shape[2][1] - shape[1][1]) / 2]
        bottomDiff = [(shape[3][0] - shape[0][0]) / 2, (shape[3][1] - shape[0][1]) / 2]
        
        topPoint = [(shape[2][0] - topDiff[0]) , (shape[2][1] - topDiff[1])]
        bottomPoint = [(shape[3][0] - bottomDiff[0]), (shape[3][1] - bottomDiff[1])]
        
        return [topPoint, bottomPoint]
    
    def InterpolatePoints(self, startPt, endPt, num):
        """
        Given a start and end point, creates a set of points linearly between them.
        Does not include the starting point in line
        
        Args:
            startPt (x,y)
            endPt (x,y)
            num (int): number of points to add

        Returns: 
            [[x1, y1], ... [endPtX, endPtY]]
        """
        x = np.linspace(startPt[0], endPt[0], num+1)
        y = np.linspace(startPt[1], endPt[1], num+1)
        
        x = x[1:]
        y = y[1:]
        
        return np.column_stack((x, y))
    
    def NonIntersectingCurve(self, rect1, rect2, toolSize, toolLength, numPoints, up):
        """
        Constructs a beizer curve connecting two rectangles.

        Args:
            toolSize (float): Width of rectangle
            toolLength (float): length of trailing object
            rect1 (Shapely::Polygon): starting rectangle of beizer curve
            rect2 (Shapely::Polygon): destination rectangle of beizer curve
            numPoints (int): points to be in a curve
            up (bool): Whether the curve should face upwards or downwards 

        Returns: 
            tool path that follows the rectangles
        """
        tolerance = toolSize / 10
        ctrBegin = (self.max_x - self.min_x) / (self.max_y - self.min_y)
        ctrIncrease = (self.max_x - self.min_x) / (self.max_y - self.min_y)
        
        if up:
            point1, _ = self.GetMidLinePointsFrom(rect1.exterior.coords)
            point2, _ = self.GetMidLinePointsFrom(rect2.exterior.coords)
            
            if ((point1[1] + toolLength) <= point2[1]):
                # this is the point where the curve cannot cross
                rectMinX = rect2.exterior.coords[3][0]
                rectMaxY = rect2.exterior.coords[1][1]
                no_touching_pt = [rectMinX + tolerance - (toolSize/2), rectMaxY]

                # initaling bezizer control points, p0 and p3 always remain the same
                # change p1 and p2
                p0 = [point1[0], point1[1] + toolLength]
                p3 = point2
                
                # time is +x
                diff_multipler = 1
            else:
                # this is the point where the curve cannot cross
                rectMaxX = rect1.exterior.coords[0][0]
                rectMaxY = rect1.exterior.coords[1][1]
                no_touching_pt = [rectMaxX - tolerance + (toolSize/2), rectMaxY] # This makes sense(Y)

                # initaling bezizer control points, p0 and p3 always remain the same
                # change p1 and p2
                p0 = point2
                p3 = [point1[0], point1[1] + toolLength]
                
                # time is -x
                diff_multipler = -1
        # Now where going down, were gathering timber    
        else:
            toolLength *= -1
            ctrBegin *= -1
            ctrIncrease *= -1
            _, point1 = self.GetMidLinePointsFrom(rect1.exterior.coords)
            _, point2 = self.GetMidLinePointsFrom(rect2.exterior.coords)
                
            # If the starting point is less than the end point
            if( (point1[1] + toolLength) >= point2[1]):
                
                # this is the point where the curve cannot cross
                rectMinX = rect2.exterior.coords[3][0]
                rectMinY = rect2.exterior.coords[3][1]
                no_touching_pt = [rectMinX + tolerance - (toolSize/2), rectMinY]

                # initaling bezizer control points, p0 and p3 always remain the same
                # change p1 and p2
                p0 = [point1[0], point1[1] + toolLength]
                p3 = point2
                
                # +x
                diff_multipler = 1
            else:
                # this is the point where the curve cannot cross
                rectMaxX = rect1.exterior.coords[0][0]
                rectMinY = rect1.exterior.coords[0][1]
                no_touching_pt = [rectMaxX - tolerance + (toolSize/2), rectMinY] # This makes sense(Y)

                # initaling bezizer control points, p0 and p3 always remain the same
                # change p1 and p2
                p0 = point2
                p3 = [point1[0], point1[1] + toolLength]
                
                # -x
                diff_multipler = -1


        # offset it a vertical point from p0 and p3 respectively so we have tanget lines
        p1 = [p0[0], p0[1] + ctrBegin]
        p2 = [p3[0], p3[1] + ctrBegin]

        points = []
        points.extend(self.InterpolatePoints(point1, [point1[0], point1[1] + toolLength], self.normalizedPts))

        # So it doesn't go on forever
        counter = 0
        while counter < 100:
            # these are the orders of n in the 3rd order poly equation that I am trying to solve
            ord0 = p0[1] - no_touching_pt[1]
            ord1 = -3 * p0[1] + 3*p1[1]
            ord2 = 3*p0[1] - 6*p1[1] + 3*p2[1]
            ord3 = -1*p0[1] + 3*p1[1] - 3*p2[1] + p3[1]

            # getting the t where the top of the box is for out curve to check if the x is too close
            # ts_at_y = np.roots([ord0, ord1, ord2, ord3])
            ts_at_y = np.roots([ord3, ord2, ord1, ord0])
            
            # finds if any of the t is before halfway. returns a index corralating to ts_at_y
            # Error when it sees its at 1 (or like .9999)
            condition = (ts_at_y < 0.999) & (ts_at_y > 0)
            
            if not np.any(condition):
                # This catches if the box + the length is the same height
                print("the first box is taller than the second")
                break
            
            t_at_y = np.where(condition)
            
            # if it is more than one we have problems so just getting the first one and iterating
            if len(t_at_y[0]) > 1:
                t_at_y = ts_at_y[t_at_y[0][0]]
            elif len(t_at_y[0]) == 1:
                t_at_y = ts_at_y[t_at_y[0]]
            
            # calcuating the x using t in our beizer curve equ
            x_at_y = (1-t_at_y)**3 * p0[0] + 3*(1-t_at_y)**2 * t_at_y * p1[0] + 3*(1-t_at_y) * t_at_y**2 * p2[0] + t_at_y**3 * p3[0]

            # if there is no overlap, break the cycle
            # if there is, increase the y, should only do this for the first point but you know
            diff = diff_multipler * (no_touching_pt[0] - x_at_y)
            if (diff) >= 0:
                break
            else:
                p1 = [p1[0], p1[1] + ctrIncrease]
                # Maybe one day I'll increase both?
                # p2 = [p2[0], p2[1] + offset_to_increase]
                
            counter += 1

        # construct our curve
        T = [(t/numPoints) for t in range(numPoints)]
        
        # when first box is taller than the second (without the increase), the line is constructed going -x,
        # need to reverse this
        if diff_multipler == -1:
            T.reverse()
        
        for t in T:
            Bx = (1-t)**3 * p0[0] + 3*(1-t)**2 * t * p1[0] + 3*(1-t) * t**2 * p2[0] + t**3 * p3[0]
            By = (1-t)**3 * p0[1] + 3*(1-t)**2 * t * p1[1] + 3*(1-t) * t**2 * p2[1] + t**3 * p3[1]
            points.append([Bx, By])

        
        return points

    def CreatePath(self, toolSize, toolLength, rects, numPoints):
        """
        Constructs the path.

        Args:
            toolSize (float): Width of rectangle
            toolLength (float): length of trailing object
            rects (shapely::MultiPolygon): set of vertical rectangles that the toolpath with descibe
            numPoints (int): points to be in each seperate path object

        Returns: 
            tool path that follows the rectangles
        """
        lines = []
        
        for i in range(len(rects.geoms)):
            
            if i % 2 == 0:
                endPoint, startPoint = self.GetMidLinePointsFrom(rects.geoms[i].exterior.coords)
                
                # On first pass only line in the midpoint   
                if i != 0:
                    lines.extend(self.NonIntersectingCurve(rects.geoms[i-1], rects.geoms[i], toolSize, toolLength, numPoints, up = False))
                else:
                    lines.append(startPoint)
                    
                lines.extend(self.InterpolatePoints(startPoint, endPoint, numPoints).tolist())
                
            else:
                lines.extend(self.NonIntersectingCurve(rects.geoms[i-1], rects.geoms[i], toolSize, toolLength, numPoints, up = True))
                
                startPoint, endPoint = self.GetMidLinePointsFrom(rects.geoms[i].exterior.coords)
                lines.extend(self.InterpolatePoints(startPoint, endPoint, numPoints).tolist())
        
        
        return LineString(lines)
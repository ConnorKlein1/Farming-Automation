# Local
from Plotter import Plotter
from RandomPolygon import RandomPolygon
from Rectangles import RectangleFactory
from ToolPath import ToolPath

# Library
from shapely import affinity

def main():
    
    toolSize = 1
    toolLength = 1
    
    P = Plotter()
    
    # generate a random polygon with 5 sides
    rp = RandomPolygon(5, max_coord=toolSize*10)
    polygon = rp.polygon
    
    # Constructing Reactangles from shape
    RectangleObject = RectangleFactory(polygon, toolSize)
    
    Rects = RectangleObject.rectangles
    centroid = RectangleObject.centroid
    angle = RectangleObject.angle
    translate = RectangleObject.translate
    
    toolPath = ToolPath(toolSize, toolLength, Rects, 20).path
    
    # Drawing Rectangles to show path
    Rects = affinity.rotate(Rects, angle = -angle, use_radians = True, origin=centroid)
    Rects = affinity.translate(Rects, yoff = -translate)
    # P.AddShapes(Rects)
    
    # Drawing inital shape
    P.AddShapes(polygon, color = 'green')
    
    # Unrotating toolPath
    toolPath = affinity.translate(toolPath, yoff=-translate)
    toolPath = affinity.rotate(toolPath, angle = -angle, use_radians = True, origin=centroid)
    P.AddShapes(toolPath)

    P.Animate(toolPath.xy[0], toolPath.xy[1])
    
    P.Plot()
    
if __name__ == '__main__': main()
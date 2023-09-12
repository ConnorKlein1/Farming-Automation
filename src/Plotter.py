import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from shapely.geometry import Polygon, MultiPolygon, MultiLineString, LineString

SHAPE_KEY = 'shape'
POINT_KEY = 'point'

# Wrapper for matplotlib::plot(), for easier implementation with these use cases.
# Allows for adding plotting elements in the shapely library.
class Plotter:
    def __init__(self):
        """
        initializes first pyplot and initalizes a list for history
        """
        self.fig, self.ax = plt.subplots()
        self.history = list()
        
    def Plot(self):
        """
        Shows the plot and initizes new plot with memory from old plot
        This is needed as on completion of show the plt is emptied
        """
        plt.show()
        
        self.fig, self.ax = plt.subplots()
        for history in self.history:
            if history[0] is SHAPE_KEY:
                self.ax.fill(*(history[1]), history[2])
            if history[0] is POINT_KEY:
                self.ax.scatter(*(history[1]), marker='x', c=history[2])
            
    
    # since overloads don't exist in python, this is the public function 
    def AddShapes(self, *args, color = 'black'):
        """
        Addes a figure to the active plot
        Params:
            one to two arguments to unpack into the x, y
        Raises:
            TypeError: only 2D currently
        """
        if len(args) == 1:
            if isinstance(args[0], Polygon):
                self.AddShapes(args[0].exterior.xy, color = color)
                return
            if isinstance(args[0], MultiPolygon):
                self.__AddPolygons(args[0], color = color)
                return
            if isinstance(args[0], LineString):
                self.__AddLineString(args[0], color = color)
                return
            if isinstance(args[0], MultiLineString):
                self.__AddLineStrings(args[0], color = color)
                return
            else:
                x, y = args[0]
        elif len(args) == 2:
            x, y = args
        else:
            raise TypeError("Add() takes 1 or 2 positional arguments")
        
        self.ax.fill(x, y, color = color)
        self.history.append([SHAPE_KEY, (x,y), color])
    
    # if you only put two points in will assume its x,y's not pairs
    def AddPoints(self, *args, connected = False, color = ''):
        """
        Addes points to the active plot in either xy pairings or [x], [y]
        Params:
            one to two arguments to unpack into the x, y
        Raises:
            TypeError: only 2D currently
        """
        if len(args) == 1:
            try:
                x, y = args[0]
            except ValueError:
                points = args[0]
                x, y = zip(*points)
        elif len(args) == 2:
            x, y = args
        else:
            raise TypeError("AddPoints() takes 1 or 2 positional arguments")
        
        if not connected:
            self.ax.scatter(x, y, zorder=10, marker='x')
            
            if len([x]) == 1:
                self.history.append([POINT_KEY, (x,y), color])
            else:
                for i, X in enumerate(x):
                    self.history.append([POINT_KEY, (X,y[i]), color])
        else:
            self.ax.plot(x,y)
            
            for i, X in enumerate(x):
                self.history.append([SHAPE_KEY, (X,y[i]), color])
    
    def ClearHistory(self):
        """
        Clears the history of the plot
        """
        self.history.clear()
    
    # def Animate(self, init_ft, animate_ft, frames, blit = True):
    def Animate(self, x_coords, y_coords, init_ft = None, blit = True, frames=None):
        ln, = self.ax.plot([], [], 'ro')
        if frames is None:
            frames = len(x_coords)
        
        def init():
            nonlocal init_ft
            if init_ft is None:
                init_ft = lambda : None
            init_ft()
            return ln,
        
        def update(frame):
            x = x_coords[frame]
            y = y_coords[frame]
            ln.set_data(x, y)
            return ln,
        
        animation = FuncAnimation(self.fig, update, init_func=init, frames=frames, blit=blit, repeat=False)
        plt.show()
    
    def get_ax(self):
        return self.ax
    
    def __AddPolygons(self, polygons, color = ''):
        """
        Converts multipolygon into plotted polygons
        Args:
            polygons (MultiPolygons)
        """
        for polygon in polygons.geoms:
            self.AddShapes(polygon.exterior.xy, color = color)
            
    def __AddLineString(self, lineString, color = ''):
        self.AddPoints(lineString.xy, connected = True, color = color)
                
    def __AddLineStrings(self, multiLineString, color = ''):
        for line in multiLineString.geoms:
            self.__AddLineString(line, color = color)
class ToursVisualizer:
    """
    Class used to visualize the computed complex of tours. 
    
    'tours': an array whose element are the single tours of the agents.
    'length': total length. Sum of the lengths of all the single tours.
    'distances': matrix of distances between the nodes
    """
    def __init__(self, tours, length, distances):
        self.tours = tours
        self.length = length
        self.distances = distances
    
    def __get_distance(self, i, j):
        return self.distances[i][j]
        
    
    def draw(self, radius = 1):
        """
        Draw the whole tour spreading the nodes on a circle according to their relative distances.
        Color differently the single tours to understand the divisions between different agents.
        INPUT:    "radius" is the radius of the circle
        
        """
        
        # setup colors of the drawing
        plt.gca().set_prop_cycle(plt.cycler('color', plt.cm.gist_ncar(np.linspace(0, 0.95, len(self.tours)))))
        
        # add coordinate of first point
        coordinates = [(0,0)]
        
        theta = - math.pi/2 # first point is at six o'clock
        for tour in self.tours:
            for i in range(1,len(tour)):
                d = self.__get_distance(tour[i-1], tour[i])
                delta_theta = d / self.length * 2 * math.pi
                theta += delta_theta
                x = radius * math.cos(theta)
                y = radius * math.sin(theta) + radius

                coordinates.append((x,y))

            xs, ys = zip(*coordinates)
            plt.plot(xs, ys, label="tour n° " + str(self.tours.index(tour)))
            plt.plot(xs, ys, 'k+') # black pluses represeting nodes
        
        plt.plot(0,0,'ro') # a red dot to show the starting point
        plt.legend(loc='center')
        plt.axis('off')
        return plt.gca()
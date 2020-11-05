import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import RegularPolygon


class JerkBoard(): 
    """ This object acts as the environemnt for a Minesweeper game.  
        An agent can interface with the game using the following functions: 
            board.user_select(i, j)  
                Right click a cell.  Returns -1 if mine or minecount of cell 
            board.user_flag(i, j)
                Toggles mine on a cell 
            board.check_gameover_conditions()
                Returns boolean to check if game is over.  If true, board.score 
                is populated 
            board.score 
                Get score of the game following gameover conditions are met 

    The following blog post was used as reference for the visualization commponent 
    of this object.      
    https://jakevdp.github.io/blog/2012/12/06/minesweeper-in-matplotlib/  
    """
    
    count_colors = ['none', 'blue', 'green', 'red', 'darkblue',
                    'darkred', 'darkgreen', 'black', 'black']
    
    flag_vertices = np.array([[0.25, 0.2], [0.25, 0.8],
                              [0.75, 0.65], [0.25, 0.5]])



    
    def __init__(self, dim=15, num_mines=45, fog_probability=0.2):
        self.dim = dim
        self.num_mines = num_mines 
        
        # fog probability is the chance that the board will not return the hint 
        #  to the agent.  It will instead return a integer value of -2, signifying that 
        #  a hint was not provided.  
        self.fog_probability = fog_probability

        # grid of cells of the board.  Shows mines (-1) and minecounts  
        self.cells = np.zeros((dim, dim))
        
        # grid of bools.  True if agent has excavated the cell at i, j 
        self.excavated = np.zeros((dim, dim), dtype=bool) 
        
        # grid of bools.  True if agent has placed a flag at i, j
        self.flags = np.zeros((dim, dim), dtype=object)


        # Boolean marking if game is complete 
        self.gameover = False 
        # Score value will be populated to this attribute upon gameover 
        self.score = None 
        
        # Create the figure and axes 
        self.fig = plt.figure(figsize=((dim + 2) / 3., (dim + 2) / 3.))
        self.ax = self.fig.add_axes((0.05, 0.05, 0.9, 0.9),
                                    aspect='equal', frameon=False,
                                    xlim=(-0.05, dim + 0.05),
                                    ylim=(-0.05, dim + 0.05))
        for axis in (self.ax.xaxis, self.ax.yaxis):
            axis.set_major_formatter(plt.NullFormatter())
            axis.set_major_locator(plt.NullLocator())


        # Create the grid of squares
        self.squares = np.array([[RegularPolygon((i + 0.5, j + 0.5),
                                                 numVertices=4,
                                                 radius=0.5 * np.sqrt(2),
                                                 orientation=np.pi / 4,
                                                 ec='black',
                                                 fc='lightgray')
                                  for j in range(dim)]
                                 for i in range(dim)])
        [self.ax.add_patch(sq) for sq in self.squares.flat]
        
        
        self.place_mines() 
        self.assign_mine_counts()
        
        # Event hook for mouse clicks
        self.fig.canvas.mpl_connect('button_press_event', self._button_press)       
        
       
            
    def place_mines(self): 
        """Randomly places self.num_mines across the grid.
            Mines are denoted by (-1) 
        """
        for mine_idx in range(self.num_mines): 
            not_placed=True 

            while(not_placed): 
                i, j = np.random.randint(0, self.dim, 2)

                if self.cells[i, j] != -1: 
                    # Place mine 
                    self.cells[i, j] = -1
                    not_placed=False 
        return 
    
    
    
    def assign_mine_counts(self):
        """Assigns adjacentcy mine counts too all non-mine cells of the grid.  
            Mine counts can be [0, 8] and are written to self.cells   
        """
        
        for i in range(self.dim):
            for j in range(self.dim): 
                
                mine_count = 0 
                
                # if (i,j) is not mine  
                if self.cells[i, j] != -1: 
                    
                    # Neighbors in 8 directions (cardinal plus diagonal)
                    neighbors = [(i+1, j), 
                                (i, j+1), 
                                (i-1, j), 
                                (i, j-1), 
                                (i+1, j+1), 
                                (i+1, j-1), 
                                (i-1, j+1), 
                                (i-1, j-1), 
                                ]

                    for neighbor in neighbors: 
                        
                        # Check if neighbor is on the board 
                        if (0 <= neighbor[0] < self.dim) and (0 <= neighbor[1] < self.dim):
                            
                            # Increment mine count for (i,j) if mine exists in neighbor 
                            if self.cells[neighbor[0], neighbor[1]] == -1: 
                                mine_count += 1

                    # Assign minecount to cell[i, j]
                    self.cells[i, j] = mine_count 

        return 
    
    
    def user_select(self, i, j): 
        """  User function for selecting cell (i, j).

                If the cell has already been excavated: do nothing 
                If the cell has a flag on it: do nothing 
                If the cell has a mine: reveal the mine 
                Otherwise: reveal the cell's mine count  

            Returns -1 on mine or mine count integer value 
        """
        
        # If the cell is excavated, do nothing 
        if self.excavated[i, j]: 
            return None 
        
        
        # If the cell is flagged, do nothing 
        if self.flags[i, j]:
            return None 
        
        
        # If the cell is a mine, essplode 
        if self.cells[i, j] == -1: 
            self.excavated[i, j] = True 
            self._draw_exploded_mine(i, j)
            return -1 
        
        # Otherwise, this is a regular safe cell. 
        self.excavated[i, j] = True 

        # Sample for to see if the fog clouds the hint for the agent 
        roll = np.random.uniform()
        if roll <= self.fog_probability: 
            # The fog wins.  Agent is not given the hint 
            self._draw_mine_count_value(i, j, fog=True)
            return -2  

        else: 
            # The agent is given the hint  
            self._draw_mine_count_value(i, j)
            return int(self.cells[i, j])

    
    def user_flag(self, i, j): 
        """ User function for placing flag at cell (i, j)

        """
        
        # If the cell has already been excavated, do nothing 
        if self.excavated[i, j]: 
            return 

        else: 
            # Otherwise, toggle flag.  The helper function applies changes 
            #   to self.flags and adds/removes flag to self.ax + applies draw() 
            self._toggle_flag(i, j)





    def check_gameover_conditions(self): 
        """ Checks if end-game conditions are met.  
            flag_count + excavated_count == total cells on board 
        """

        flag_count = sum([bool(cell) for cell in self.flags.flatten()])
        excavated_count = sum(sum(self.excavated))


        if self.dim**2 == (flag_count + excavated_count):
            self.gameover = True 
            # Calculate score 
            self._calculate_score()
            return True 

        else: 
            return False 



    def _reveal_board(self):
        """ Reveals all cells of the board.  WARNING: flag state is removed 
        """

        for i in range(self.dim): 
            for j in range(self.dim): 

                # remove flag if present 
                if self.flags[i, j]: 
                    self._toggle_flag(i, j)

                # if mine, draw mine 
                if self.cells[i, j] == -1: 
                    self._draw_mine(i, j)

                else: 
                    self._draw_mine_count_value(i, j)
        return 


    def _button_press(self, event): 
        """ Event hook for catching mouse clicks 
            Pipes left and right click actions to user_select() and user_flag() 
        """
        
        # Get coordinates of cell clicked on 
        i, j = map(int, (event.xdata, event.ydata))
        if (i < 0 or j < 0 or i >= self.dim or j >= self.dim):
            return

        # Left Mouse Click.  button == 1
        #  Pipe to user_select  
        if event.button == 1:
            self.user_select(i, j)


        # Right Mouse Click.  button == 3
        #  Pipe to user_place_flag 
        if event.button == 3: 
            self.user_flag(i, j)

        # Redraw canvas 
        self.fig.canvas.draw()
      



    def _calculate_score(self): 
        """ Calculates the current point value according to the state of the board

                For each correctly placed flag, one point is earned.  
                Uses self.flag and self.cells as global truth of the state of the game 
        """

        correct = 0 
        incorrect = 0 

        for i in range(self.dim):
            for j in range(self.dim): 

                # cell (i, j) has a flag and has a mine 
                if (bool(self.flags[i, j])) and (self.cells[i, j] == -1):
                    correct += 1

                # cell has a flag and no mine 
                if (bool(self.flags[i, j])) and (self.cells[i, j] != -1):
                    incorrect += 1



        self.score = (correct - incorrect) / self.num_mines 



    def _draw_mine_count_value(self, i, j, fog=False): 
        """Draws colored mine count value at cell @ i, j
        """
        self.squares[i, j].set_facecolor('white')

        # If fog applies, then print a '?' to represent that the agent dont know 
        if fog: 
            self.ax.text(i + 0.5, j + 0.5, '?',
                         color='purple',
                         ha='center', va='center', fontsize=18,
                         fontweight='bold')
            return 


        self.ax.text(i + 0.5, j + 0.5, str(int(self.cells[i, j])),
                     color=self.count_colors[int(self.cells[i, j])],
                     ha='center', va='center', fontsize=18,
                     fontweight='bold')


    def _draw_mine(self, i, j): 
        """ Draws mine at cell @ i, j.  Mine is black and gray 
        """
        self.squares[i, j].set_facecolor('white')
        self.ax.add_patch(plt.Circle((i + 0.5, j + 0.5), radius=0.25,
                                     ec='black', fc='gray'))
    
    
    def _draw_exploded_mine(self, i, j):
        """ Draws exploded mine at cell @ i, j.  Mine is black and red.  
        """
        self.squares[i, j].set_facecolor('white')
        self.ax.add_patch(plt.Circle((i + 0.5, j + 0.5), radius=0.25,
                                     ec='black', fc='orangered'))

            
        
    def _toggle_flag(self, i, j):
        """ Toggles flag image on cell at i, j
        """
        if self.flags[i, j]:
            self.ax.patches.remove(self.flags[i, j])
            self.flags[i, j] = None
        else:
            self.flags[i, j] = plt.Polygon(self.flag_vertices + [i, j],
                                            fc='red', ec='black', lw=2)
            self.ax.add_patch(self.flags[i, j])
        self.fig.canvas.draw()

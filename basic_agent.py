import numpy as np 
import board as board 
from time import sleep 


class Cell(): 
    covered = True 
    mine = None 
    mine_count = None 
    flag = None 
    safe = None 
    total_neighbors = 8 
    hidden_neighbors = 8 
    safe_neighbors_identified = 0 

    def __str__(self):
        
        if self.flag: 
            return "F"
            
        if self.covered: 
            return "?"

        if self.mine_count is not None: 
            return str(self.mine_count)
        

        if self.mine: 
            return 'M' 

        else: 
            return "err"

    def __repr__(self): 
        return self.__str__() 



class BasicAgent():
    """Basic agent for solving minesweeper.  
    """



    def __init__(self, board): 
        
        # Environment/board attribute of agent.  
        self._board = board 
        #   The only allowed interfaces to this object are: 
        #       .user_select(i, j)
        #       .user_flag(i, j)
        #       .check_gameover_conditions()
        #       .score 
        #       .dim 
        #       .num_mines 
        #   Other attribute or functions accesses are illegal and cheating  
        #    e.g The agent cannot access board.cells or board.excavated   



        # store board metadata locally 
        self.dim = self._board.dim 
        self.num_mines = self._board.num_mines 

        # Initialize agent's internal model of the board  
        self.cells = np.zeros((self.dim, self.dim), dtype=Cell)

        for i in range(self.dim): 
            for j in range(self.dim): 
                self.cells[i, j] = Cell() 

                # Edge cells have 5 neighbors 
                if (i == 0) or (j == 0) or (i == self.dim-1) or (j == self.dim-1): 
                    self.cells[i, j].hidden_neighbors = 5
                    self.cells[i, j].total_neighbors = 5 


                # Corner cells have 3 neighbors 
                if (i == 0 and j == 0) or \
                   (i == self.dim-1 and j == 0) or \
                   (i == 0 and j == self.dim-1) or \
                   (i == self.dim-1 and j == self.dim-1):
                    self.cells[i, j].hidden_neighbors = 3
                    self.cells[i, j].total_neighbors = 3 


        # Metric for random clicks done 
        self.random_clicks = 0 


    def toggle_flag(self, i, j):
        """ Places flag on cell at (i, j).  
        Sends user_flag() command to board and updates internal structures
        """

        self._board.user_flag(i, j)
        
        # Flag currently present 
        if self.cells[i, j].flag: 
            self.cells[i, j].flag = False     

        # Flag currently not present 
        else: 
            self.cells[i, j].flag = True 




    def excavate_cell(self, i, j, log=False): 
        """Digs up the cell at (i, j).  
        Sends user_select() command to board and updates internal structures with 
          what is returned. 

        Returns true on successful excavation 
        """

        # If flagged, cannot excavate 
        if self.cells[i, j].flag: 
            return False 

        value = self._board.user_select(i, j)
        self.cells[i, j].covered = False    

        # Hit a mine 
        if value == -1: 
            self.cells[i, j].mine = True 
            self.cells[i, j].safe = False 
            if log: print("Excavated a mine at ({}, {})".format(i, j))
        
        else: 
        # Did not hit a mine 
            self.cells[i, j].mine_count = value
            if log: print("Excavated ({}, {})".format(i, j))


            # Decrement hidden_neighbors count for all neighbors 
            #   and increment safe_neighbors count for all neighbors  
            neighbors = [(i+1, j+1), (i+1, j), (i, j+1), (i-1, j+1), \
                         (i-1, j-1), (i-1, j), (i, j-1), (i+1, j-1)]
            for neighbor in neighbors: 
                # The neighbor is within bounds of the board 
                if (0 <= neighbor[0] < self.dim) and (0 <= neighbor[1] < self.dim): 
                    self.cells[neighbor].hidden_neighbors -= 1
                    self.cells[neighbor].safe_neighbors_identified += 1


        return True 



    def surrounding_safe(self, i, j, log=False): 
        """If, for a given cell, the total number of safe neighbors (8 - clue) 
        minus the number of revealed safe neighbors is the number of hidden 
        neighbors, every hidden neighbor is safe.

        In this case, all hidden_neighbors of (i, j) are marked .safe=True 

        Returns True if all surrounding hidden cells can be marked as safe.  
        False otherwise.  
        """

        cell = self.cells[i, j]

        if cell.flag: 
            return False 

        if cell.mine: 
            return False 


        made_progress = False 
        total_safe_neighbors = cell.total_neighbors - cell.mine_count 
        remaining_safe_neighbors = total_safe_neighbors - cell.safe_neighbors_identified

        # If the remaining uncovered neighbor count == number of safe neighbrs left 
        #   then all remaining uncovered neighbors are safe.  
        if remaining_safe_neighbors == cell.hidden_neighbors: 

            neighbors = [(i+1, j+1), (i+1, j), (i, j+1), (i-1, j+1), \
                         (i-1, j-1), (i-1, j), (i, j-1), (i+1, j-1)]

            for neighbor in neighbors: 
                # The neighbor is within bounds of the board 
                if (0 <= neighbor[0] < self.dim) and (0 <= neighbor[1] < self.dim): 

                    # The neighbor is covered 
                    if self.cells[neighbor].covered == True: 

                        # This cell is safe.  Mark it as safe 
                        self.cells[neighbor].safe = True 
                        if log: print("Cell ({}, {}) deemed safe using ({}, {}).".format(neighbor[0], neighbor[1], i, j))
                        made_progress = True 

            return made_progress 
        return False 



    def surrounding_mines(self, i, j, log=False): 
        """If, for a given cell, the total number of mines (the clue) minus the 
        number of revealed mines is the number of hidden neighbors, every 
        hidden neighbor is a mine

        In this case, all hidden_neighbors of (i, j) are flagged.

        Returns True if all surrounding hidden cells are identified as mines.
        False otherwise. 
        """

        cell = self.cells[i, j]
        made_progress = False 

        if cell.hidden_neighbors == cell.mine_count: 


            neighbors = [(i+1, j+1), (i+1, j), (i, j+1), (i-1, j+1), \
                         (i-1, j-1), (i-1, j), (i, j-1), (i+1, j-1)]

            for neighbor in neighbors: 
                # The neighbor is within bounds of the board 
                if (0 <= neighbor[0] < self.dim) and (0 <= neighbor[1] < self.dim): 

                    # The neighbor is covered 
                    if self.cells[neighbor].covered == True: 

                        # This is a mine.
                        #   Set it to flagged in agent's data structures 
                        self.cells[neighbor].flag = True 
                        self.cells[neighbor].covered = False 

                        #   Set it to a mine in the game board
                        self._board.user_flag(neighbor[0], neighbor[1])

                        if log: print("Cell ({}, {}) deduced to be a mine using ({}, {})".format(neighbor[0], neighbor[1], i, j))
                        made_progress = True 

            return made_progress
        return False 




    def uncover_all_safe_cells(self, log=False):
        """ Loop through all cells on the board and excavate any uncovered 
           cell marked safe

           Returns True if any of the excavate_cell calls was successful 
        """

        success = False 

        for i in range(self.dim): 
            for j in range(self.dim): 

                if self.cells[i, j].covered and self.cells[i, j].safe: 
                    ret = self.excavate_cell(i, j, log) 
                    if ret: 
                        success = True 

        return success 




    def mark_safe_cells(self, log=False): 
        """ Loop through all uncovered cells and mark their neighbors as safe 
            if all neighbors are safe 

            Returns True if any of the surrounding_safe calls was successful 
        """

        success = False 

        for i in range(self.dim): 
            for j in range(self.dim): 

                if not self.cells[i, j].covered: 
                    ret = self.surrounding_safe(i, j, log) 
                    if ret: 
                        success = True 
        return success



    def mark_mine_cells(self, log=False): 
        """ Loop through all uncovered cells and flag their neighbors 
            if all neighbors are identified as mines 

            Returns True if any of the surrounding_mines calls was successful 
        """

        success = False 

        for i in range(self.dim): 
            for j in range(self.dim): 

                if not self.cells[i, j].covered: 
                    ret = self.surrounding_mines(i, j, log) 
                    if ret: 
                        success = True 
        return success




    def solve(self, interactive=False, log=False, delay=0): 


        self.excavate_cell(0, 0)

        while(True):

            if interactive:
                input("Press Enter to continue...")

            safe_check = self.mark_safe_cells(log)
            mine_check = self.mark_mine_cells(log)
            uncover_try = self.uncover_all_safe_cells(log)


            if(self._board.check_gameover_conditions()): 
                return self._board.score 

            # If nothing was accomplished on this iteration, reveal some 
            #  random cell 
            if not safe_check and not mine_check and not uncover_try: 
                done = False 
                while (not done): 

                    i, j = np.random.randint(0, self.dim, size=2)
                    if self.cells[i, j].covered: 
                        if log: print("\tRandomly selected ({}, {}) to uncover.".format(i, j))
                        self.excavate_cell(i, j) 
                        self.random_clicks += 1 
                        done = True 



            self._board.fig.canvas.draw()

            # delay so that we can watch on the GUI 
            sleep(delay) 


        return self._board.score
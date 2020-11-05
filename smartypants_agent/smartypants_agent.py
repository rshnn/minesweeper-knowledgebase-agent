import numpy as np 
from time import sleep 
from .utils import Variable, Clause, CellClauses, KnowledgeBase, neighbors


class Cell(): 
    covered = True 
    mine = None 
    mine_count = None 
    flag = None 
    safe = None 

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



class SmartypantsAgent(): 


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


        # Initialize a knowledgebase object for each cell.  
        self.kb = np.zeros((self.dim, self.dim), dtype=CellClauses)

        for i in range(self.dim): 
            for j in range(self.dim): 

                self.kb[i, j] = CellClauses([])
                self.kb[i, j].center_cell = (i, j)



        # Initialize agent's internal knowlege of cells. 
        #   This is the same as that used in the basic agent 
        self.cells = np.zeros((self.dim, self.dim), dtype=Cell)
        for i in range(self.dim): 
            for j in range(self.dim): 
                self.cells[i, j] = Cell() 


        # Metric for counting random clicks 
        self.random_clicks = 0 



    def excavate_cell(self, i, j, log=False): 
        """ Agent digs up cell at (i, j). 
        Sends user_select() command to the board and updates internal data structs.

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

            # update knowledgebase
            #  Loop through all clauses in knowledgebase 
            #    if conflicting literal exists in clause, remove clause 
            #    conflicting literal is (-M(i, j))

            total_removed = 0 
            for i_ in range(self.dim): 
                for j_ in range(self.dim): 
                    removed = self.kb[i_, j_].remove_mine_variable(i, j)
                    if removed: 
                        total_removed += removed

            if log: print("Removed {} clauses with -M({}, {})".format(total_removed, i, j))


        else: 
        # Did not hit a mine.  Got a mine_count (stored in value) 

            self.cells[i, j].mine_count = value 
            self.cells[i, j].safe = True 
            if log: print("Excavated ({}, {})".format(i, j))

            # Update knowledgebase 

            # Add information to knowledgebase regarding the mine_count 
            added = self.kb[i, j].generate_clauses_from_minecount(i, j, value, self.dim)
            if log: print("Added {} clauses to KB for cell ({}, {})".format(added, i, j))


            #  Loop through all clauses in the knowledgebase 
            #    if conflicting literal exists in clause, remove clause 
            #    conflicting literal is (M(i, j))
            total_removed = 0
            for i_ in range(self.dim): 
                for j_ in range(self.dim): 
                    removed = self.kb[i_, j_].remove_safe_variable(i, j)
                    if removed: 
                        total_removed += removed
            if log: print("Removing {} clauses with M({}, {})".format(total_removed, i, j))

        return True 




    def toggle_flag(self, i, j, log=False): 
        """ Places flag on cell at (i, j).  
        Sends user_flag() command to board and updates internal structures
        """


        self._board.user_flag(i, j)
        if log: print("Toggled flag at ({}, {})".format(i, j))

        # Flag was already present
        if self.cells[i, j].flag: 
            self.cells[i, j].flag = False 
            # update knowledge base? TODO 

        # Flag wasnt present 
        else: 
            self.cells[i, j].flag = True 
            
            # Update knowledgebase.
            #  Cell at (i, j) is deemed a mine. 
            #  Loop through all clauses in knowledgebase 
            #    if conflicting literal exists in clause, remove clause 
            #    conflicting literal is (-M(i, j))

            total_removed = 0 
            for i_ in range(self.dim): 
                for j_ in range(self.dim): 
                    removed = self.kb[i_, j_].remove_mine_variable(i, j)
                    if removed: 
                        total_removed += removed

            if log: print("Removed {} clauses with -M({}, {})".format(total_removed, i, j))




    def learn_from_singleton_clauses(self, log=False):
        """ If any cellclause in the knowledge base has only 1 clause in it, 
            then that clause is True.  The literals that comprise it are true.
            Update .cells datastructure's safe field accordingly.  
        """

        successful = False 

        # Find any singleton clauses 
        for i in range(self.dim): 
            for j in range(self.dim): 

                if len(self.kb[i, j].clauses) == 1: 

                    successful = True   
                    for literal in self.kb[i, j].clauses[0].literals:
                        
                        if literal.mine:
                            # Literal's cell is a mine 
                            r = literal.i
                            c = literal.j

                            self.cells[r, c].safe = False 

                        else: 
                            # Literal's cell is not a mine                             
                            r = literal.i
                            c = literal.j

                            self.cells[r, c].safe = True 

                    if log: print("Learned from clauses at ({}, {})".format(i, j))
                    # Remove the clause when done
                    self.kb[i, j].clauses = []

        return successful



    def uncover_all_safe_cells(self, log=False): 
        """ Loop through all cells on the board and excavate any covered 
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



    def mark_all_mine_cells(self, log=False): 
        """ Loop through all the cells on the board and flag any covered cells 
            marked as not safe.  

            Returns True if any of the toggle_flag calls was successful 
        """

        success = False 

        for i in range(self.dim): 
            for j in range(self.dim): 

                if self.cells[i, j].covered and (self.cells[i, j].safe == False) and (not self.cells[i, j].flag):
                    self.toggle_flag(i, j, log)
                    success = True 

        return success




    def refresh_knowledgebase(self, log=True): 
        """ Update all clauses to remove known mines and safe cells 
        """

        success = False 

        for i in range(self.dim):
            for j in range(self.dim): 


                # Covered and Flagged --> mine 
                if self.cells[i, j].covered and self.cells[i, j].flag: 
                    # Update knowledgebase. Cell at (i, j) is deemed a mine. 
                    #  Loop through all clauses in knowledgebase 
                    #    if conflicting literal exists in clause, remove clause 
                    #    conflicting literal is (-M(i, j))

                    total_removed = 0 
                    for i_ in range(self.dim): 
                        for j_ in range(self.dim): 
                            removed = self.kb[i_, j_].remove_mine_variable(i, j)
                            if removed: 
                                total_removed += removed
                                success = True 

                    if log: print("Removed {} clauses with -M({}, {})".format(total_removed, i, j))

                # Uncovered and safe --> not mine 
                if self.cells[i, j].covered == False and self.cells[i, j].safe: 


                    # Update knowledgebase 
                    #  DOnt need to add to KB.  This is done on excavating and flagging
                    # # Add information to knowledgebase regarding the mine_count 
                    # value = self.cells[i, j].mine_count
                    # added = self.kb[i, j].generate_clauses_from_minecount(i, j, value, self.dim)
                    # if log: print("Added {} clauses to KB for cell ({}, {})".format(added, i, j))


                    #  Loop through all clauses in the knowledgebase 
                    #    if conflicting literal exists in clause, remove clause 
                    #    conflicting literal is (M(i, j))
                    total_removed = 0
                    for i_ in range(self.dim): 
                        for j_ in range(self.dim): 
                            removed = self.kb[i_, j_].remove_safe_variable(i, j)
                            if removed: 
                                total_removed += removed
                                success = True 
                    if log: print("Removing {} clauses with M({}, {})".format(total_removed, i, j))



        return success




    def solve(self, interactive=False, log=False, delay=0):

        self.excavate_cell(0, 0, log=log)

        while(True): 


            if interactive: 
                input("Press Enter to continue...")

            learned = self.learn_from_singleton_clauses(log=log) 
            uncover = self.uncover_all_safe_cells(log=log)
            mark = self.mark_all_mine_cells(log=log)
            refresh = self.refresh_knowledgebase(log=log)


            if (self._board.check_gameover_conditions()):
                return self._board.score


            # If nothing was accomplished on this iteration, reveal some 
            #   random cell.             
            if not learned and not uncover and not mark and not refresh: 
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




    def solve_one_iteration(self, log=False): 
        
        learned = self.learn_from_singleton_clauses(log=log) 
        uncover = self.uncover_all_safe_cells(log=log)
        mark = self.mark_all_mine_cells(log=log)
        refresh = self.refresh_knowledgebase(log=log)


        if (self._board.check_gameover_conditions()):
            return self._board.score


        # If nothing was accomplished on this iteration, reveal some 
        #   random cell.             
        if not learned and not uncover and not mark and not refresh: 
            done = False 
            while (not done): 

                i, j = np.random.randint(0, self.dim, size=2)
                if self.cells[i, j].covered: 
                    if log: print("\tRandomly selected ({}, {}) to uncover.".format(i, j))
                    self.excavate_cell(i, j) 
                    done = True 



        self._board.fig.canvas.draw()


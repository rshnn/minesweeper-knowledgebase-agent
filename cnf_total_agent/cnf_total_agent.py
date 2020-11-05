import numpy as np 
from time import sleep 
from .utils import Variable, Clause, KnowledgeBase 


class Cell(): 
    covered = True 
    mine = None 
    mine_count = None 
    flag = None 
    safe = None 
    idx = None 

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


class CNF_Total_Agent(): 


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
        

        # attributes used for managing the total mines left constraint 
        self.mines_left = self.num_mines 
        self.unknown = set()


        # Initialize agent's internal knowlege of cells. 
        #   This is the same as that used in the basic agent 
        self.cells = np.zeros((self.dim, self.dim), dtype=Cell)
        counter = 1 
        for i in range(self.dim): 
            for j in range(self.dim): 
                self.cells[i, j] = Cell()
                self.cells[i, j].idx = counter 

                # set of covered cells for total mines constraint
                self.unknown.add((i, j, counter))

                counter += 1



        # Initialize the agent's knowledgebase 
        self.kb = KnowledgeBase([])

        # Metric for random clicks done 
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
        self.unknown.remove((i, j, self.cells[i, j].idx))


        # Hit a mine 
        if value == -1: 
            self.cells[i, j].mine = True 
            self.cells[i, j].safe = False 
            self.mines_left -= 1
            if log: print("Excavated a mine at ({}, {})".format(i, j))


            # Update the knowledgebase.
            #  Discovered that Cell(i, j) is a mine. 
            #  Create a literal that represents this knowledge and add it to KB 
            idx = self.cells[i, j].idx 
            literal = Variable(i=i, j=j, idx=idx, mine=True)
            self.kb.add_literal(literal)
            if log: print("Added {} to knowledgebase.".format(literal))

            # # Add new total mines remaining constraint to KB
            # self.kb.add_total_mines_constraint(self.mines_left, list(self.unknown))
            # if log: print("Added total mines clauses to knowledgebase. {}/{}".format(self.mines_left, self.num_mines))




        else: 
        # Did not hit a mine.  GOt a mine_count (stored in value) 


            self.cells[i, j].mine_count = value 
            self.cells[i, j].safe = True 
            if log: print("Excavated ({}, {})".format(i, j))


            # Update knowledgebase 
            #  Two things.. 
            #   (1) Discovered (i, j) is not a mine 
            #   (2) Discovered a mine count 

            #  (1) 
            #  Discovered that Cell(i, j) is not a mine. 
            #  Create a literal that represents this knowledge and add it to KB 
            idx = self.cells[i, j].idx 
            literal = Variable(i=i, j=j, idx=idx, mine=False)
            self.kb.add_literal(literal)
            if log: print("Added {} to knowledgebase.".format(literal))



            # (2) 
            # Discovered a mine_count for (i, j) 
            #   Generate unknown_neighbors idx list.
            #   Figure out how many unknown mines there are 
            #   Tell KB to generate mine clauses 
            #   Tell KB to generate not mine clauses 
            unknown_neighbors = self.get_unknown_neighbors_idx(i, j)
            unknown_mine_count = self.get_unknown_mine_count(i, j)

            self.kb.generate_mine_clauses(unknown_mine_count, unknown_neighbors)
            self.kb.generate_not_mine_clauses(unknown_mine_count, unknown_neighbors)

            #   If value==0:  all neighbors are safe
            #   If value==len(unknown_neighbors), all neighbors are mines 
            #   The above generate_* functions handle these cases 
            if log: print("Generating clauses at ({}, {}, {}). {} mines, {} neighbors".format(i, j, idx, value, len(unknown_neighbors))) 

        return True 




    def toggle_flag(self, i, j, log=False): 
        """ Places flag on cell at (i, j).  
        Sends user_flag() command to board and updates internal structures
        """

        # Send toggle_flag command to board 
        self._board.user_flag(i, j)
        if log: print("Toggled flag at ({}, {})".format(i, j))

        # Flag was already present
        if self.cells[i, j].flag: 
            self.cells[i, j].flag = False 
            # update knowledge base? This situation should never happen.

        # Flag wasnt present 
        else: 
            self.cells[i, j].flag = True 
            self.mines_left -= 1
            self.unknown.remove((i, j, self.cells[i, j].idx))

            # Update knowledgebase.
            #   Identified a mine at (i, j)
            #   Create a literal that represents this knowledge and add it to KB 
            idx = self.cells[i, j].idx 
            literal = Variable(i=i, j=j, idx=idx, mine=True)
            self.kb.add_literal(literal)
            if log: print("Added {} to knowledgebase.".format(literal))

            # Add new total mines remaining constraint to KB
            # self.kb.add_total_mines_constraint(self.mines_left, list(self.unknown))
            # if log: print("Added total mines clauses to knowledgebase. {}/{}".format(self.mines_left, self.num_mines))



    def learn_from_unit_clauses(self, log=False): 
        """ Loops through the knowledgebase for unit clauses (1 literal long clauses) 
             These clauses represent facts of mine cells or safe cells.  
             Mark internal data structures as safe or not safe.  
        """

        success = False 

        for cl in self.kb.clauses: 

            # If clause has one literal in it 
            if len(cl) == 1: 
                literal = cl[0]
                i = literal.i
                j = literal.j

                
                # Already know about this unit clause, go to next iteration 
                #   If the cell is uncovered 
                #   If the cell has a flag 
                if (not self.cells[i, j].covered): 
                    continue 

                if self.cells[i, j].flag:
                    continue 

                # Learning about an covered, unflagged cell 
                success = True 

                # It is a mine 
                if literal.mine: 

                    self.cells[i, j].safe = False 
                    if log: print("Learned ({}, {}) is a mine via unit clause.".format(i, j))

                # It is safe 
                else:
                    self.cells[i, j].safe = True 
                    if log: print("Learned ({}, {}) is safe via unit clause.".format(i, j))

        return success



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



    def get_unknown_neighbors_idx(self, i, j):
        """ Returns a list of tuples that are valid, unknown neighbors of (i, j)
             Tuples are of the form:  (i, j, idx) 
        """


        neighbors = [(i+1, j+1), (i+1, j), (i, j+1), (i-1, j+1), \
                (i-1, j-1), (i-1, j), (i, j-1), (i+1, j-1)]

        out = []

        for neighbor in neighbors: 
            # The neighbor is within bounds of the board 
            if (0 <= neighbor[0] < self.dim) and (0 <= neighbor[1] < self.dim): 

                # The neighbor is covered and not a flag 
                if self.cells[neighbor].covered and not self.cells[neighbor].flag: 
                    out.append((neighbor[0], neighbor[1], self.cells[neighbor].idx)) 
                
        return out 


    def get_unknown_mine_count(self, i, j): 
        """ Returns the number of unknown mines surrounding (i, j).

            This will be the mine_count of (i, j) minus any flags or 
             excavated mines. 
        """

        value = self.cells[i, j].mine_count
        excavated_mine_count = 0
        flagged_mine_count = 0 

        neighbors = [(i+1, j+1), (i+1, j), (i, j+1), (i-1, j+1), \
                (i-1, j-1), (i-1, j), (i, j-1), (i+1, j-1)]


        for neighbor in neighbors: 
            # The neighbor is within bounds of the board 
            if (0 <= neighbor[0] < self.dim) and (0 <= neighbor[1] < self.dim): 

                # The neighbor is an excavated mine
                if self.cells[neighbor].mine == True and self.cells[neighbor].safe == False: 
                    excavated_mine_count += 1 


                # The neighbor is a flagged mine 
                if self.cells[neighbor].flag == True:  
                    flagged_mine_count += 1


        return value - excavated_mine_count - flagged_mine_count




    def query_negative_literals(self, log=False): 
        """ Queries KB for -M(i, j).
            
             If KB and -M(i, j) is unsatisfiable, then (i, j) is a mine 
        """

        success = False 

        # Iterate through all cells 
        for i in range(self.dim): 
            for j in range(self.dim): 

                # If unknown cells 
                if self.cells[i, j].covered and not self.cells[i, j].flag: 

                    # Create literal and run query against KB 
                    literal = Variable(i, j, self.cells[i, j].idx, False)
                    response = self.kb.query(literal)

                    if response == 'UNSAT':
                        # It is unsat. Thus, (i, j) is a mine 
                        self.cells[i, j].safe = False 
                        success = True 
                        if log: print("Learned ({}, {}) is a mine via negative query.".format(i, j))


        return success 



    def query_positive_literal(self, log=False): 
        """ Queries KB for M(i, j).
            
             If KB and M(i, j) is unsatisfiable, then (i, j) is safe  
        """

        success = False 

        # Iterate through all cells 
        for i in range(self.dim): 
            for j in range(self.dim): 

                # If unknown cells 
                if self.cells[i, j].covered and not self.cells[i, j].flag: 

                    # Create literal and run query against KB 
                    literal = Variable(i, j, self.cells[i, j].idx, True)
                    response = self.kb.query(literal)

                    if response == 'UNSAT':
                        # It is unsat. Thus, (i, j) is safe  
                        self.cells[i, j].safe = True  
                        success = True 
                        if log: print("Learned ({}, {}) is safe via positive query.".format(i, j))


        return success 



    def query_total_mines_clauses(self, log=False): 
        """ Asks KB to generate total mines clauses annd queries the KB + total mines 
             clauses.  THis is a very very expensive operation since the total mines 
             clauses list is huge.  
        """

        # Add new total mines remaining constraint to KB
        if log: print("Attempting to add total mines to knowledgebase. {}/{}".format(self.mines_left, self.num_mines))
        check = self.kb.generate_total_mines_constraint(self.mines_left, list(self.unknown))
        if log: print("Added total mines clauses to knowledgebase. {}/{}".format(self.mines_left, self.num_mines))


        # query postiive 
        positive = False 

        # Iterate through all cells 
        for i in range(self.dim): 
            for j in range(self.dim): 

                # If unknown cells 
                if self.cells[i, j].covered and not self.cells[i, j].flag: 

                    # Create literal and run query against KB 
                    literal = Variable(i, j, self.cells[i, j].idx, True)
                    response = self.kb.query_with_global(literal)

                    if response == 'UNSAT':
                        # It is unsat. Thus, (i, j) is safe  
                        self.cells[i, j].safe = True  
                        positive = True 
                        if log: print("**Learned ({}, {}) is safe via positive query on totalmines.".format(i, j))



        # query negative 
        negative = False 

        # Iterate through all cells 
        for i in range(self.dim): 
            for j in range(self.dim): 

                # If unknown cells 
                if self.cells[i, j].covered and not self.cells[i, j].flag: 

                    # Create literal and run query against KB 
                    literal = Variable(i, j, self.cells[i, j].idx, False)
                    response = self.kb.query_with_global(literal)

                    if response == 'UNSAT':
                        # It is unsat. Thus, (i, j) is a mine 
                        self.cells[i, j].safe = False 
                        negative = True 
                        if log: print("**Learned ({}, {}) is a mine via negative query on totalmines.".format(i, j))


        if positive or negative: 
            return True

        else: 
            return False 




    def solve(self, interactive=False, log=False, delay=0, total_mines_clause=False): 

        self.excavate_cell(0, 0, log=log)

        while(True): 

            if interactive: 
                input("Press Enter to continue...")


            # Check endgame conditions.  Return score if end 
            if (self._board.check_gameover_conditions()):
                return self._board.score

            # Draw the canvas on this iteration 
            self._board.fig.canvas.draw()

            # delay so that we can watch on the GUI 
            sleep(delay) 


            # (1) Check for unit clauses in the KB
            #    i.e M(i, j) or -M(i, j) clauses in the KB
            #    if one exists, learn from it, take action, and continue to next iter
            unit_clause_check = self.learn_from_unit_clauses(log=log)

            if unit_clause_check:
                self.uncover_all_safe_cells(log=log)
                self.mark_all_mine_cells(log=log)
                continue  

            # (2) Query for -M(i, j)  
            #      If KB and -M(i, j) is unsatisfiable, (i, j) is a mine 
            negative_query_check = self.query_negative_literals(log=log)

            if negative_query_check: 
                self.mark_all_mine_cells(log=log)
                continue  


            # (3) Query for M(i, j)  
            #      If KB and M(i, j) is unsatisfiable, (i, j) is safe  
            positive_query_check = self.query_positive_literal(log=log)

            if positive_query_check:
                self.uncover_all_safe_cells(log=log)
                continue  


            # (3.1) Query KB with total mines clauses  
            #  Retry positive and negative queries 
            #  If successful, uncover and mark over the board 
            total_mines_query = self.query_total_mines_clauses(log=log)

            if total_mines_query: 
                self.uncover_all_safe_cells(log=log)
                self.mark_all_mine_cells(log=log)
                continue  


            # (4) Uncover random unknown cell 
            done = False 
            while (not done): 
                i, j = np.random.randint(0, self.dim, size=2)
                if self.cells[i, j].covered and not self.cells[i, j].flag: 
                    if log: print("\tRandomly selected ({}, {}) to uncover.".format(i, j))
                    self.excavate_cell(i, j, log=log) 
                    self.random_clicks += 1
                    done = True 




    def solve_one_iteration(self, log=False): 

        # Check endgame conditions.  Return score if end 
        if (self._board.check_gameover_conditions()):
            return self._board.score

        # Draw the canvas on this iteration 
        self._board.fig.canvas.draw()



        # (1) Check for unit clauses in the KB
        #    i.e M(i, j) or -M(i, j) clauses in the KB
        #    if one exists, learn from it, take action, and continue to next iter
        unit_clause_check = self.learn_from_unit_clauses(log=log)

        if unit_clause_check:
            self.uncover_all_safe_cells(log=log)
            self.mark_all_mine_cells(log=log)

            self._board.fig.canvas.draw()
            return  

        # (2) Query for -M(i, j)  
        #      If KB and -M(i, j) is unsatisfiable, (i, j) is a mine 
        negative_query_check = self.query_negative_literals(log=log)

        if negative_query_check: 
            self.mark_all_mine_cells(log=log)
            self._board.fig.canvas.draw()
            return  


        # (3) Query for M(i, j)  
        #      If KB and M(i, j) is unsatisfiable, (i, j) is safe  
        positive_query_check = self.query_positive_literal(log=log)

        if positive_query_check:
            self.uncover_all_safe_cells(log=log)
            self._board.fig.canvas.draw()
            return  


        # (3.1) Query KB with total mines clauses  
        #  Retry positive and negative queries 
        #  If successful, uncover and mark over the board 
        total_mines_query = self.query_total_mines_clauses(log=log)

        if total_mines_query: 
            self.uncover_all_safe_cells(log=log)
            self.mark_all_mine_cells(log=log)
            self._board.fig.canvas.draw()
            return  


        # (4) Uncover random unknown cell 
        done = False 
        while (not done): 
            i, j = np.random.randint(0, self.dim, size=2)
            if self.cells[i, j].covered and not self.cells[i, j].flag: 
                if log: print("\tRandomly selected ({}, {}) to uncover.".format(i, j))
                self.excavate_cell(i, j, log=log) 
                done = True      


        self._board.fig.canvas.draw()
        return  




    def check_knowledgebase_consistency(self):
        """ This function is for debugging only.
             Runs dual queries on the KB to see if both return unsat. 
             If both return UNSAT, the KB is flawed.  Time to panic  

             Returns True if everything is okay 
             Returns False if KB is flawed 
        """


        for i in range(self.dim): 
            for j in range(self.dim): 
                # If unknown cells 
                if self.cells[i, j].covered and not self.cells[i, j].flag: 
                    
                    true_sat = False
                    false_sat = False

                    # M(i, j) Create literal and run query against KB 
                    literal = Variable(i, j, self.cells[i, j].idx, True)
                    response = self.kb.query(literal)

                    if response == 'UNSAT':
                        true_sat = True 

                        
                    # -M(i, j) Create literal and run query against KB 
                    literal = Variable(i, j, self.cells[i, j].idx, False)
                    response = self.kb.query(literal)

                    if response == 'UNSAT':
                        false_sat = True 
                        
                    
                    if true_sat and false_sat: 
                        print("KB flawed for query using ({}, {})".format(i, j))
                        return False 

        return True 
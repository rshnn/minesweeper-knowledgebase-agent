import numpy as np
import itertools
import pycosat 



class Variable():
    """ A Variable represents a literal.  They take the form of M(i, j).
          M(i, j) means cell i, j has a mine. 
          -M(i, j) means cell i, j is safe.  

        The .mine attribute stores the truth value 
        The .idx attribute signifies Cell i, j's integer ID for cnf solving 

    """
    
    # Coordinates of this Variable on the board 
    i = None 
    j = None 
    coords = None 
    

    # idx is the index number used in pycosat solver.  It is this Variable's unique ID 
    #   This ID should be the same across the agent's knowledgebase 
    idx = None 
    
    # Truth value of the Variable.  M(i, j) == is the cell at i, j a mine?
    mine = None

    
    def __init__(self, i, j, idx, mine=None): 
        self.i = i
        self.j = j
        self.coords = (i, j)
        self.idx = idx 
        self.mine = mine 
        
        

    def get_idx_representation(self): 
        if self.mine == True: 
            return self.idx 
        elif self.mine == False: 
            return self.idx * -1 
        else: 
            raise ValueError("Variable does not have a truth assignment.")
    
    
    def __repr__(self): 
        
        sign = ""
        if not self.mine: 
            sign = "-"
        return "{}M({}, {}, idx:{})".format(sign, self.i, self.j, self.idx)
    
    
    def __str__(self): 
        return self.__repr__()
    




class Clause(list):
    """ A Clause represents a disjunction of literals (variables) 
         E.g.   [M(1, 1), -M(1, 2), ... ]
         The elements of a clause are assumed to be OR'ed together 

    """
       
    def __init__(self, l):
        super().__init__(l)
        
    def append(self, literal): 
        super().append(literal)
        
        
    def get_idx_represention(self): 
        out = list()
        for i in self: 
            out.append(i.get_idx_representation())
        return out 




class KnowledgeBase(): 
    """ A KnowledgeBase represents a conjunction of clauses. 
    That is, it is a conjunction of disjunctions of literals.  It will always 
     be in conjunctive normal form (CNF) and will utilize the pycosat library 
     to solve for satisfiability. 


    The .clauses attribute is a list of the KB's Clause objects 
    the .idx_representation attribute is a list of idx representations of clauses.
      This attribute is designed to be interpretable by the pycosat library.   
    """
    
    clauses = list()
    idx_representation = list()
    literals = set() 
    
    # for managing total mines clauses 
    total_mines_clauses = list() 
    total_mines_idx_representation = list() 

    
    def __init__(self, clause_list):
        self.clauses = list()
        self.idx_representation = list() 

        for cl in clause_list: 
            self.append(cl)
        
    def __repr__(self): 
        return str(self.clauses)
    
    def __str__(self): 
        return self.__repr__()
    
        
    def append(self, clause): 
        """ Append a new clause object to the datastructure. 
             The clauses list and idx_representations list are both updated 
        """
        self.clauses.append(clause)
        self.idx_representation.append(clause.get_idx_represention())

        for literal in clause: 
            self.literals.add((literal.i, literal.j))

        


    def add_literal(self, literal): 
        """ Adds a clause that contains a single literal to the KB.

             This will be used to tell the KB when a safe cell or a mine has 
              been discovered.  (i.e. A single literal representing the fact
              will be added as a clause.)
        """
        cl = Clause([literal])
        self.append(cl)



    def generate_mine_clauses(self, count, unknown_neighbors): 
        """ For any (len(unkn_neighbors)-count+1) neighbors out of 
             total unknown_neighbors, at least one is a mine.  

             unknown_neighbors must be a list of tuples: 
                 [(i, j, idx), ...] 

        """

        choose = (len(unknown_neighbors) - count + 1)
        combos = itertools.combinations(unknown_neighbors, choose)

        for combo in combos: 
            # A combo represents a clause. A clause is a bunch of literals 
            literals = []

            # Build up the variables in the clause 
            for literal in combo: 
                # A combo is made up of several Variables/literals 
                #  For this clause, all the truth values are True.  
                v = Variable(i=literal[0], j=literal[1], idx=literal[2], mine=True)
                literals.append(v)

            # Join the variables into a Clause 
            clause = Clause(literals)
            
            # Add the clause to self's datastructures 
            self.append(clause)


        # Return True on success 
        #   This represents the conjunction of all the disjunctions
        #     Each clause is a disjuntion of literals 
        return True 





    def generate_not_mine_clauses(self, count, unknown_neighbors): 
        """ For any (count+1) nneighbors out of total unkown_neighbors, 
             at least one is not a mine.
             
              unknown_neighbors must be a list of tuples: 
                 [(i, j, idx), ...] 

        """

        choose = count+1 
        combos = itertools.combinations(unknown_neighbors, choose) 

        for combo in combos: 
            # A combo represents one clause.  A clause is made up of choose # of literals 
            literals = []

            for literal in combo: 

                # Build up the Variable/literal
                #   For this clause, all the truth values are False 
                v = Variable(i=literal[0], j=literal[1], idx=literal[2], mine=False)
                literals.append(v)

            # Join the variables together into a Clause 
            clause = Clause(literals)
            
            # Add the clause to self's datastructures 
            self.append(clause)

        # Return True on success 
        #   This represents the conjunction of all the disjunctions
        #     Each clause is a disjuntion of literals 
        return True 

    
    def generate_total_mines_constraint(self, mines_left, unknown_neighbors):
        """ Exactly Q of the total unknown_neighbors contain mines. 
             These clauses are separete from the rest of the clauses.
             They are managed in two list attributes on self. 
                .total_mines_clauses and .total_mines_idx_rep 
             On each invocation of this function, those lists are flushed and 
                repopulated.  This is because the total mines clauses list is 
                gigantic.      
        """

        # Refresh the list 
        self.total_mines_clauses = list()
        self.total_mines_idx_representation = list()



        # (1) Add mine clauses 
        choose = (len(unknown_neighbors) - mines_left + 1)
        combos = itertools.combinations(unknown_neighbors, choose)

        for combo in combos: 
            # A combo represents a clause. A clause is a bunch of literals 
            literals = []

            # Build up the variables in the clause 
            for literal in combo: 
                # A combo is made up of several Variables/literals 
                #  For this clause, all the truth values are True.  
                v = Variable(i=literal[0], j=literal[1], idx=literal[2], mine=True)
                literals.append(v)

            # Join the variables into a Clause 
            clause = Clause(literals)
            
            # Add the clause to self's total mines clause list  
            self.total_mines_clauses.append(clause)
            self.total_mines_idx_representation.append(clause.get_idx_represention())
            for literal in clause: 
                self.literals.add((literal.i, literal.j))



        # (2) Add not mine clauses 
        choose = mines_left + 1 
        combos = itertools.combinations(unknown_neighbors, choose) 

        for combo in combos: 
            # A combo represents one clause.  A clause is made up of choose # of literals 
            literals = []

            for literal in combo: 

                # Build up the Variable/literal
                #   For this clause, all the truth values are False 
                v = Variable(i=literal[0], j=literal[1], idx=literal[2], mine=False)
                literals.append(v)

            # Join the variables together into a Clause 
            clause = Clause(literals)
            
            # Add the clause to self's datastructures 
            self.total_mines_clauses.append(clause)
            self.total_mines_idx_representation.append(clause.get_idx_represention())
            for literal in clause: 
                self.literals.add((literal.i, literal.j))

        return True 

    
    
    def query(self, literal): 
        """ Query the KB to see if literal is satisfiable with it
            Returns solution (list of assignments) if (KB and literal) is satisfiable 
            Returns "UNSAT" if (KB AND literal) is unsatisfiable 
            Returns "UNKNOWN" if pycosat cannot determine a solution 
        
            If KB and M(i, j) is unsatisfiable, then cell (i. j) is not a mine 
            If KB and not M(i, j) is unsatisfiable, then cell (i. j) is a mine 
                
            Note that the literal itself will have the truth value in it's .mine field. 
        """

        # If knowledgebase doesnt know about this literal, return IDK 
        if (literal.i, literal.j) not in self.literals: 
            return "IDK" 

        
        # Create a copy of the KB to query against. 
        query_cnf = list.copy(self.idx_representation)

        # Add the query literal to the copy 
        query_cnf.append([literal.get_idx_representation()])


        # Is the copy of the KB satisfiable?  
        return pycosat.solve(query_cnf)
    



    def query_with_global(self, literal): 

            # If knowledgebase doesnt know about this literal, return IDK 
            if (literal.i, literal.j) not in self.literals: 
                return "IDK" 

            
            # Create a copy of the KB to query against. 
            query_cnf = list.copy(self.idx_representation)

            # Add the total mines clauses to the copy KB 
            total_mines_copy = list.copy(self.total_mines_idx_representation)
            query_cnf = query_cnf + total_mines_copy 

            # Add the query literal to the copy 
            query_cnf.append([literal.get_idx_representation()])

            # Is the copy of the KB satisfiable?  
            return pycosat.solve(query_cnf)
        


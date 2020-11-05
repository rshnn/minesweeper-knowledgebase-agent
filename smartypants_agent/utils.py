import numpy as np
import itertools



class Variable():
    
    coords = None 
    mine = None
    
    def __init__(self, i, j, mine=None): 
        self.i = i
        self.j = j 
        self.mine = mine 
        
    def __repr__(self):
        if self.mine: 
            return "M({}, {})".format(self.i, self.j)
        elif self.mine is None: 
            return "?M({}, {})".format(self.i, self.j)
        else: 
            return "-M({}, {})".format(self.i, self.j)

        
    def __str__(self): 
        return self.__repr__()
    
    
    def __eq__(self, other): 
        if self.i == other.i and self.j == other.j: 
            return True 
        else: 
            return False 
    
    def evaluate(self): 
        return mine 





class Clause(): 
    """ A clause is a conjunction of Literals (Variables).
         It is represented as a list of Variables in which each 
         element of the list is assumed to be AND'ed together 
    """
    
    literals = list()
    contains = set()
    
    def __init__(self, var_list): 
        self.literals = var_list
        
    def add_variable(self, var):
        self.literals.append(var)
        coords = (var.i, var.j)
        self.contains.add(coords)
        
    
    def evaluate(self):
        """ Perform logical AND over all elements in the list 
        """
        return all([literal.evaluate() for literal in self.literals])
    
    
    def __repr__(self):
        
        if len(self.literals) == 0:
            return "Nil" 
        
        
        out = str(self.literals[0])

        for lit in self.literals[1:]: 
            out = "".join([out, " AND ", str(lit)])
        
        return out 
    
    
    def __str__(self): 
        return self.__repr__()
    
    



class CellClauses():
    """ A CellClauses is a disjunction of clauses.
         It is represented as a list of clauses in which each 
         element of the list is assume to be OR'ed together 
    """
    
    clauses = list()
    center_cell = None 
    contains = set()  
    
    def __init__(self, clause_list): 
        self.clauses = clause_list
        
    def add_clause(self, clause): 
        self.clauses.append(clause) 
        

    def query(self, query_variable): 
        pass
    
    
    def  __repr__(self): 
        
        if len(self.clauses) == 0: 
            return "Nil" 
        
        out = "(" + str(self.clauses[0]) + ")"
        
        for cl in self.clauses[1:]:
            out = "".join([out, "\n OR ", "(", str(cl), ")"])
            
        return out 
    
    
    def __str__(self):
        return self.__repr__()
    
    
    
    def generate_clauses_from_minecount(self, i, j, mine_count, dim): 
      
        src_bools = list()
        neighs = neighbors(i, j, dim)


        for dummy in range(len(neighs)):
            if dummy < mine_count: 
                src_bools.append(True)
            else: 
                src_bools.append(False)

        bools = list(set(itertools.permutations(src_bools)))

        self.center_cell = (i, j)

        for claws_idx in range(len(bools)):

            c = Clause([])

            for lit_idx in range(len(neighs)):

                coords = neighs[lit_idx]
                v = Variable(coords[0], coords[1], bools[claws_idx][lit_idx])
                c.add_variable(v)

            self.add_clause(c)

        self.contains = set.copy(c.contains)
        
        return len(bools)
        
    
        
    def remove_safe_variable(self, i, j, log=False):
        """ Found out that (i, j) is not a mine.  
             Remove all clauses which assume that (i, j) is a mine (M(i j))
        """
        
        if (i, j) not in self.contains: 
            return False 
        
        
        v = Variable(i, j)
        clauses_to_remove = []
        
        for clause in self.clauses:            
            found = False 
            for literal in clause.literals: 
                
                if found: 
                    break 
                
                if literal == v: 
                    if literal.mine:
                        # Remove this clause 
                        if log: print("Removing this clause, " + str(clause))
                        clauses_to_remove.append(clause)
                        found = True 
                
                
        for cl in clauses_to_remove: 
            self.clauses.remove(cl)
            
            
        return len(clauses_to_remove)
    
    
    
    def remove_mine_variable(self, i, j, log=False): 
        """ Found out that (i, j) is a mine. 
             Remov all clauses which assume that (i, j) is not a mine (-M(i, j))
        """
            
        
        if (i, j) not in self.contains: 
            return False 
        
        
        v = Variable(i, j)
        clauses_to_remove = []
        
        for clause in self.clauses:            
            found = False 
            for literal in clause.literals: 
                
                if found: 
                    break 
                
                if literal == v: 
                    if not literal.mine:
                        # Remove this clause 
                        if log: print("Removing this clause, " + str(clause))
                        clauses_to_remove.append(clause)
                        found = True 
                
                
        for cl in clauses_to_remove: 
            self.clauses.remove(cl)
            
            
        return len(clauses_to_remove)
    


class KnowledgeBase(): 
    """The knowledge base is a conjunction of CellClauses.
        It is represented as a list of cellclauses in which 
        each is assumed to be AND'ed together.  
    
    """
    
    cellclauses = []
    
    def __init__(self, cellclauses):
        self.cellclauses = cellclauses
        
        
        
    def __repr__(self): 
        
        if len(self.cellclauses) == 0: 
            return "" 
        
        out = "(" + str(self.cellclauses[0]) + ")"
        
        for cl in self.cellclauses[1:]:
            out = "".join([out, "\n AND ", "(", str(cl), ")"])
            
        return out 
        
        


def neighbors(i, j, dim): 
    
    neighbors = [(i+1, j+1), (i+1, j), (i, j+1), (i-1, j+1), \
             (i-1, j-1), (i-1, j), (i, j-1), (i+1, j-1)]

    out = []
    
    for neighbor in neighbors: 
        # The neighbor is within bounds of the board 
        if (0 <= neighbor[0] < dim) and (0 <= neighbor[1] < dim): 
            out.append(neighbor) 
            
    return out 

    
    
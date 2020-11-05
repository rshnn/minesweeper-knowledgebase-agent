import numpy as np

import board as board
import jerk_board as jerk_board

import basic_agent
import smartypants_agent
import cnf_agent
import cnf_bonus_agent

import matplotlib.pyplot as plt




def generate_score_vs_density_list(dim, runs_per_x, x_interval=1, agent_type='basic'):
    """ Generates a list of performance vs mine count for analysis 
    
        Agents supported are:  'basic', 'smarty', 'cnf'

    """

    # Determine what kind of agent we are assessing 
    if agent_type.lower() == 'basic':
        def new_agent(brd): 
            return basic_agent.BasicAgent(brd)
    elif agent_type.lower() == 'smarty':
        def new_agent(brd): 
            return smartypants_agent.SmartypantsAgent(brd)
    elif agent_type.lower() == 'cnf':
        def new_agent(brd): 
            return cnf_agent.CNF_Agent(brd) 
    else: 
        ValueError('Did not recognize agent type {}'.format(agent_type))


    out = []
    counts = np.arange(1, dim**2-1)
    counts = counts[::x_interval]

    for mine_count in counts: 
        
        density_score = 0
        random_clicks = 0 
        
        for i in range(runs_per_x): 
        
            brd = board.Board(dim, mine_count) 
            agent = new_agent(brd) 
            agent.solve()
            
            density_score += brd.score
            random_clicks += agent.random_clicks 
        
        out.append((mine_count, density_score/runs_per_x, random_clicks/runs_per_x))

    return out 



def generate_score_vs_prob_list(dim, mine_count, num_x=10, runs_per_x=1):
    """ Generates al ist of performance vs fog_probability for analysis.
        This is for the bonus section 

        The only agent currently supported is the CNF_Bonus_Agent 
    """


    out = []
    probs = np.linspace(0, 1, num_x)

    for prob in probs: 
        density_score = 0
        random_clicks = 0 
        
        for i in range(runs_per_x): 
        
            brd = jerk_board.JerkBoard(dim, mine_count, prob) 
            agent = cnf_bonus_agent.CNF_Bonus_Agent(brd) 
            agent.solve()
            
            density_score += brd.score
            random_clicks += agent.random_clicks 
        
        out.append((prob, density_score/runs_per_x, random_clicks/runs_per_x))

    return out 


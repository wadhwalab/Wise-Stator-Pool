# Stochastic simulation and analytic solution for stator binding/unbinding kinetics.
# Imported by gillespie-sim.ipynb and mechanosensing-plots.ipynb.
import numpy as np
import matplotlib.pyplot as plt
import math
import random

def gillespie(cycles,steps,p):
    '''
    cycles = number of times to run simulation
    steps = number of steps to run each simulation for
    p = parameters of simulation. Should be an array with N_max,N_0, P_0, k_0, gamma, es ,eb, eT

    returns 
    N[i,j] - number of stators as an array     i -> cycle #      ||     j -> time
    N_ave[j] - averaged number of stators over all cycles               j -> time
    t[i,j] - times as an array                 i -> cycle #      ||     j -> time
    t_ave[j] - times as an array for averaged data                      j -> time
    '''
    #Initialize simulation:
    N_max = p[0]
    N_0 = p[1]
    P_0 = p[2]
    k_0 = p[3]
    gamma = p[4]
    es = p[5]
    eb = p[6]
    eT = p[7]
    k_off = k_0 * math.exp(eb - eT)
    k_on = k_0 * gamma * math.exp(es)
    t = np.zeros((cycles, steps+1)) #time
    N = np.zeros((cycles, steps+1)) #number of stators
    P = np.zeros((cycles, steps+1)) #number of stators in the pool
    N[:,0] = N_0 #initialize
    P[:,0] = P_0

    #run simulation
    for i in range(cycles):
        for j in range (steps):
            R = k_on * (N_max - N[i,j]) * P[i,j] + k_off * N[i,j] #total rate = on * empty sites * number of stators in pool + off * number of occupied sites
            u = random.uniform(0,1) #get random number
            tau = math.log(1/u) / R #get time until next rxn
            t[i, j+1] = t[i,j] + tau
            kf = k_on * (N_max - N[i,j]) * P[i,j] / R
            
            v = random.uniform(0,1)
            if v < kf and N[i,j] < N_max:
                N[i,j+1] = N[i,j] + 1
                P[i,j+1] = P[i,j] - 1
            elif v > kf and N[i,j] > 0:
                N[i,j+1] = N[i,j] - 1
                P[i,j+1] = P[i,j] + 1
            else:
                N[i,j+1] = N[i,j] 
                P[i,j+1] = P[i,j]

    # Set up average arrays
    ave_steps = 100
    tmax = np.percentile(t[:,-1], 95)

    t_ave = np.linspace(0, tmax, ave_steps+1)
    N_ave = np.zeros(ave_steps+1)
    P_ave = np.zeros(ave_steps+1)

    for i, current_time in enumerate(t_ave):

        N_sum = 0
        P_sum = 0

        for j in range(cycles):

            idx = np.searchsorted(t[j], current_time)

            if idx == 0:
                idx = 0
            elif idx >= steps:
                idx = steps
            else:
                idx -= 1

            N_sum += N[j,idx]
            P_sum += P[j,idx]

        N_ave[i] = N_sum / cycles
        P_ave[i] = P_sum / cycles

    return(N,N_ave,t,t_ave)

def analytic_sol(p,t_max=4000):
    '''
    p - parameters array (see gillespie)
    t_max = last time point (default 4000s)
    returns analytic solution
    N(t)
    t
    '''
    N_max = p[0]
    N_0 = p[1]
    P_0 = p[2]
    k_0 = p[3]
    gamma = p[4]
    es = p[5]
    eb = p[6]
    eT = p[7]
    k_off = k_0 * math.exp(eb - eT)
    
    times = np.arange(t_max - 1)
    N = np.zeros(t_max) 
    N[0] = N_0
    P = P_0
    def get_k_on(P):
        k_on = k_0 * gamma * math.exp(es) * P
        return k_on
    for t in times:
        dN = k_0 * gamma * math.exp(es) * P * (N_max - N[t]) - k_off * N[t]
        N[t+1] = N[t] + dN
        P -= dN
    times = np.arange(t_max)
    return N, times
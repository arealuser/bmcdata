# Learning-Augmented Dynamic Power Management with Multiple States via New Ski Rental Bounds 对比实验
import os
import time
import pandas as pd
from sklearn.metrics import accuracy_score
from datetime import datetime
import numpy as np
from scipy.special import lambertw
import random
import subprocess
import re
import networkx as nx

def get_cpu_usage():
    cmd = "mpstat -P ALL 1 1 | awk '/平均时间:/ && $2 ~ /^[0-9]+$/ {print 100-$NF}'"
    output = subprocess.check_output(cmd, shell=True).decode()
    
    usage = [float(line) for line in output.strip().splitlines() if line]
    
    return usage if usage else [0] * 128  

######Algorithms in Learning-Augmented Dynamic Power Management with Multiple States via New Ski Rental Bounds########################
RHO = 1.1596  # default value of rho
RHO_LIMIT = 1.1596

POWER_CONSUMPTIONS = [1., 0.47, 0.105, 0]
WAKE_UP_COSTS = [0, 0.12, 0.33, 1.] # assume all are interesting at some point

def FTP(requests, pred):
  res = [0] * len(requests)
  for t, req in enumerate(requests):
     res[t] = 0 if pred[t]>=1 else requests[t]+1000
  return res

def ClassicRandom(requests, pred=[]):
  res = [0] * len(requests)
  for t, req in enumerate(requests):
    buy = np.log(1+np.random.rand()*(np.expm1(1)))
    res[t] = buy
  return res


# buying time at time 0 in many cases
def g0(mu,tp):
  return tp*mu
  
# density of two parts of the CDF
def g1(mu,rho,tp,t):
  return (rho-1-mu+mu*tp)*np.exp(t)
def g2(rho,t):
  return rho*np.exp(t-1)
# integral of the density
def G1(mu,rho,tp,end):
  return max(0,(rho-1-mu+mu*tp)*(np.exp(end)-1))
def G2(rho,start,end):
  return max(0, rho*(np.exp(end-1)-np.exp(start-1)))

# first case: the CDF is first flat, then follows an exponential
def CDF_flat(mu, rho, tp, t):
  p0 = tp*(rho-1)/(1-tp)
  p1 = min(mu, 1-p0)
  tlim = 1+np.log((rho-1+p0+p1)/rho)
  if t < tlim:
    return p0
  else:
    return p0 + G2(rho, tlim, min(t,1))


# second case: the CDF follows two exponential
def CDF_2exp(mu, rho, tp, t):
  p0 = g0(mu,tp)
  p1 = min(mu, 1-p0)
  tlim = 1+np.log((rho-1+p0+p1+G1(mu,rho,tp,tp))/rho)
  if t < tlim:
    return min(1-p1, p0 + G1(mu,rho,tp, min(tp,t)))
  else:
    return min(1-p1, p0 + G1(mu,rho,tp,tp) + G2(rho, tlim, min(t,1)))

# third case: the predicted time is larger than 1
def CDF_big(mu, rho, tp, t):
  temp = g0(mu,tp) + G1(mu,rho,tp,t)
  ref = g0(mu,tp) + G1(mu,rho,tp,tp-1)
  if (ref > 1):
    return min(1, temp) # subcase where the exponential grows until a buying probability of 1
  if (t < tp-1):
    return temp # the required time belongs to the exponential growth
  if (ref > 1-mu):
    return ref # the required time is after the exponential growth, which stopped at the buying probability
  return min(temp, 1-mu) # the exponential growth stopped at 1-mu


def CDF(mu, rho, tp, t):
  if (tp >= 1):
    return CDF_big(mu, rho, tp, t)
  if (g1(mu,rho,tp,0) <= 0):
    return CDF_flat(mu, rho, tp, t)
  return CDF_2exp(mu, rho, tp, t)

# best mu in function of rho (for all prediction times)
def ParetoMu(rho):
  if(rho>1.1596):
    return (1-rho*(np.exp(1)-1)/np.exp(1))/np.log(2)
  else:
    W = lambertw(-np.sqrt((rho-1)/(4*rho)))
    return (rho-1)/(2*W)*(1+1/(2*W))

def RhoMu_paretomu(requests, pred, rho = RHO_LIMIT):
  res = [0] * len(requests)
  mu = ParetoMu(rho)
  for t, req in enumerate(requests):
    p = np.random.rand()
    if (CDF(mu,rho,pred[t],1) <= p):
      res[t] = requests[t]
    else:
      buy = inverse(lambda x: CDF(mu,rho,pred[t], x)) (p)
      res[t] = buy
  return res

def binary_search(f, y, lo, hi, delta):
    while lo <= hi:
        x = (lo + hi) / 2
        if f(x) < y:
            lo = x + delta
        elif f(x) > y:
            hi = x - delta
        else:
            return x;
    return hi if (f(hi) - y < y - f(lo)) else lo

def inverse(f, delta=1/1024.):
    def f_1(y):
        return binary_search(f, y, 0, 1, delta)
    return f_1



# this is to compute EMD flow:
def compute_switch_probs(old_probs, new_probs, cur_alg):
  n = len(old_probs)

  G = nx.DiGraph()

  for i in range(n):
    G.add_node(i)
    G.add_node(n+i)

  for i in range(n):
    for j in range(n):
      if i == j:
        G.add_edge(i,n+j, capacity=1, weight=0)
      else:
        G.add_edge(i, n + j, capacity=1, weight=1)

  source = 2*n+1
  target = 2*n+2
  G.add_node(source) #source
  G.add_node(target) #target

  for i in range(n):
    G.add_edge(source,i, capacity=old_probs[i], weight=0)
    G.add_edge(n+i, target, capacity=new_probs[i], weight=0)

  flow = nx.algorithms.max_flow_min_cost(G,source, target)
  switch_probs = [ flow[cur_alg][n+i] for i in range(n) ]
  return switch_probs

def compute_switch_probs_with_precision(old_probs, new_probs, cur_alg):
  # implementation via bipartite flows sometimes fails to find the optimimum solution and breaks down.
  # In such case, I decrease the number of precision bits and try again with less precise numbers.
  precision = 53
  while precision > 0:
    N = 2**precision
    sig1 = [ round(N*p)/N for p in old_probs ]
    sig2 = [ round(N*p)/N for p in new_probs ]
    try:
      switch_probs = compute_switch_probs(sig1, sig2, cur_alg)
    except:
      precision = precision - 1
      if precision < 20:
        print("WARNING: Could not find EMD flow for\n{}\n{}, decreasing precision to {} bits".format(sig1, sig2, precision))
    else:
      break
  assert precision > 0, "Could not find EMD flow"
  total = sum(switch_probs)
  # total mass in switch_probs should be equal to the probability of staying in cur_alg state
  # this may slightly differ due to precision issues.
  # Therefore, I normalize by "total" to make sure that the probabilities sum up to 1
  switch_probs = [p / total for p in switch_probs]
  return switch_probs  

def Combine_rand(requests, pred, algs, epsilon=0.1):
  diameter = 0.5
  beta = 1.0 - 0.5 * epsilon
  
  istep = 0.1
  histories = list(map(lambda x: x(requests, pred), algs))
  weights = [1] * len(algs)
  probs = [1/len(algs)] * len(algs)
  history = []
  cur_alg = random.randrange(0,len(algs))
  loss = [0] * len(algs)
  count = 0
  
  for t, request in enumerate(requests):
    previ = 0
    #应该是每时每刻都预测，预测结果记录下来，我们正式使用的时候，应始终保持所有历史，或者一段历史，传给这个函数，当预测成功，就立即退出
    count += 1
    # the time is discretized in steps of size 0.1
    for i in np.arange(0,requests[t]+1,istep):
      
      # compute the new probabilities in function of the loss and the new algorithm to follow
      new_weights = [w*(beta)**(l/diameter) for w,l in zip(weights,loss)]
      total_weights = sum(new_weights)
      new_probs = [w / total_weights for w in new_weights]
      switch_probs = compute_switch_probs_with_precision(probs, new_probs, cur_alg)
      #中途有可能切换算法
      cur_alg = np.random.choice(np.arange(0, len(algs)), p=switch_probs)
      probs = new_probs
      weights = new_weights
      weights = probs # prevents floating point errors: always normalize the weights

      # the round stops before the next i
      if (histories[cur_alg][t] < i+istep or requests[t] < i+istep):
        # save the loss to update the algorithms at the next iteration
        loss = [requests[t]-previ if x[t]>=requests[t] else 0 if x[t] < previ else 1+x[t]-previ for x in histories]
        if (requests[t] < histories[cur_alg][t]):
          history.append(requests[t]+1000) # cur_alg did not buy
          break
        else:
          history.append(max (i, histories[cur_alg][t]) ) # cur_alg buys between i and the following i
          break

      loss = [i-previ if x[t]>=i else 0 if x[t] < previ else 1+x[t]-previ for x in histories]
      previ = i

  return history


def RobustRhoMu(requests, pred):
  sb = Combine_rand(requests, pred, [
      FTP,
      lambda r, p : RhoMu_paretomu(r, p, 1.1),
      lambda r, p : RhoMu_paretomu(r, p, 1.1596),
      lambda r, p : RhoMu_paretomu(r, p, 1.3),
      lambda r, p : RhoMu_paretomu(r, p, 1.4),
      lambda r, p : RhoMu_paretomu(r, p, 1.5),
      ClassicRandom,])
  return sb

######End of Algorithms in Learning-Augmented Dynamic Power Management with Multiple States via New Ski Rental Bounds########################


IDLE_THRESHOLD = 0.1 
SLEEP_TIME = 10.0 
MIN_GROUP_SIZE = 16 

idle_periods = [[] for _ in range(128)]
idle_predict = [[] for _ in range(128)]
idle_flags = [1] * 128
dt = datetime.now()


while True:
    time.sleep(SLEEP_TIME)

    cpu_usages = get_cpu_usage()
    
    print("cpu usage:", cpu_usages)
    
    current_time = datetime.now()
    span = (current_time - dt).total_seconds()
    dt = current_time

    selected_p_cores = []
    selected_e_cores = []

    
    for i in range(128):
        core_usage = cpu_usages[i]
        
        if core_usage > IDLE_THRESHOLD:
            idle_flags[i] = 1
            selected_p_cores.append(i)
        else:
            if idle_flags[i] == 1:
                
                idle_periods[i].append(span / SLEEP_TIME)
                idle_flags[i] = 0
            else:
                idle_periods[i][-1] += span / SLEEP_TIME
    

    
    for i in range(128):
        
        if i not in selected_p_cores:
            if len(idle_predict[i]) == 0:
              idle_predict[i] = idle_periods[i]
            
            if len(idle_predict[i]) < len(idle_periods[i]):
              idle_predict[i].append(idle_periods[i][-1])
            
            idle_periods[i] = idle_periods[i][:100]  
            idle_predict[i] = idle_predict[i][:100]  

            idle_predict[i] = RobustRhoMu(idle_periods[i], idle_predict[i])
            
            predict = idle_predict[i][-1]
            if predict > 1000:
              pass
            else:
              # Switch to power saving mode, such as lowering the frequency
              selected_e_cores.append(i)
              pass
            pass
        print(f"request for core {i}: ", idle_periods[i])
        print(f"prediction for core {i}: ", idle_predict[i])
        print("ecore:", selected_e_cores)
        print("pcores:", selected_p_cores)
    
    for group in range(0, 128, MIN_GROUP_SIZE):
        val_e = sum(1 for core in range(group, group + MIN_GROUP_SIZE) if core in selected_e_cores)
        val_p = sum(1 for core in range(group, group + MIN_GROUP_SIZE) if core in selected_p_cores)
        utility_p = sum(cpu_usages[core] for core in range(group, group + MIN_GROUP_SIZE) if core in selected_p_cores)
        print(f"compare: {val_e}, {val_p}")
        
        if val_e/2 > val_p and utility_p < IDLE_THRESHOLD * MIN_GROUP_SIZE:
           print(f"cpupower -c {group} frequency-set frequency-set -g powersave")
           subprocess.call(f"cpupower -c {group} frequency-set frequency-set -g powersave", shell=True)
           pass
        elif val_p/2 > val_e:
           print(f"cpupower -c {group} frequency-set frequency-set -g performance")
           subprocess.call(f"cpupower -c {group} frequency-set frequency-set -g performance", shell=True)
           pass

import random

def generate_test_case(n, k):
    arr = [random.randint(0, k*100//n) for _ in range(n)]
    total_load = sum(arr)
    arr = [load * (k*100) // total_load for load in arr]
    return arr

def calculate_cost(arr1, arr2):
    cost = 0
    for i in range(0, len(arr2)):
        if arr2[i] == 0 :
            cost += arr1[i]
    return cost

def generate_cost_matrix(num_cores, numasize, groupsize):
    n_group = num_cores // groupsize
    cost = [[0 for _ in range(num_cores)] for _ in range(num_cores)]
    half_cores = num_cores // 2
    for i in range(num_cores):
        for j in range(num_cores):
            cost[i][j] = abs(i // groupsize - j //groupsize)
            if i // numasize == j // numasize:
                cost[i][j] = 0
            if i < half_cores and j >= half_cores:
                cost[i][j] += 1
            elif i >= half_cores and j < half_cores:
                cost[i][j] += 1

    return cost


def calculate_cost_numa(arr1, arr2, cost_matrix):
    effective_cores = sum(arr2)
    cost = 0
    for i in range(len(arr2)):
        if arr2[i] == 0:
            for j in range(len(arr2)):
                if arr2[j] == 1:
                    cost += arr1[i] * cost_matrix[i][j] // effective_cores
    return cost



def genetic_algorithm(n, m, arr, groupsize, numasize):

    population_size = n // groupsize
    generations = 20

    num_cores = n
    num_targetcpus = m

    costmatrix = generate_cost_matrix(num_cores, numasize, groupsize)

    def generate_population(pop_size):
        n_group = num_cores // groupsize
        n_sel_group = round(num_targetcpus / groupsize)
        temparr = [1]*n_sel_group + [0]*(n_group - n_sel_group)
        population = []
        for _ in range(pop_size):
            individual = temparr.copy()
            random.shuffle(individual)
            population.append(individual)
        return population

    def fitness(individual):
        n_group = num_cores // groupsize
        individual_arr = []
        for i in range(n_group):
            if individual[i] == 1:
                individual_arr = individual_arr + [1]*groupsize
            else:
                individual_arr = individual_arr + [0]*groupsize
        
        return calculate_cost_numa(arr, individual_arr, costmatrix)

    def convert_to_weights(fitness_values):
        max_fitness = max(fitness_values)
        weights = [max_fitness - fitness + 1 for fitness in fitness_values]
        return weights

    def roulette_wheel_selection(population, fitness_values):
        total_fitness = sum(fitness_values)
        probabilities = [fitness / total_fitness for fitness in fitness_values]
        return random.choices(population, weights=probabilities, k=len(population))

    def crossover(parent1, parent2):
        sumparent = sum(parent1)
        crossover_point = random.randint(1, min(len(parent1), len(parent2)) - 1)
        child1 = parent1[:crossover_point] + parent2[crossover_point:]
        child2 = parent2[:crossover_point] + parent1[crossover_point:]
        if sum(child1) != sumparent or sum(child2) != sumparent: 
            child1 = parent1
            child2 = parent2
        return child1, child2

    def mutate(individual):
        one_indices = [i for i, gene in enumerate(individual) if gene == 1]
        zero_indices = [i for i, gene in enumerate(individual) if gene == 0]

        if len(one_indices) > 0 and len(zero_indices) > 0:
            one_index = random.choice(one_indices)
            zero_index = random.choice(zero_indices)
            individual[one_index] = 0
            individual[zero_index] = 1

        return individual

    def run_genetic_algorithm(pop_size, generations):
        population = generate_population(pop_size)
        best_individual_ever = None
        best_fitness_ever = float('inf')

        for _ in range(generations):
            fitness_values = [fitness(individual) for individual in population]

            best_fitness_current = min(fitness_values)
            best_individual_current = population[fitness_values.index(best_fitness_current)]
            if best_fitness_current < best_fitness_ever:
                best_individual_ever = best_individual_current
                best_fitness_ever = best_fitness_current

            weights = convert_to_weights(fitness_values)
            selected_population = roulette_wheel_selection(population, weights)

            offspring = []
            for i in range(0, pop_size, 2):
                child1, child2 = crossover(selected_population[i], selected_population[i+1])
                offspring.extend([child1, child2])

            for individual in offspring:
                if random.random() < 0.2:
                    mutate(individual)

            population = offspring

            if fitness(best_individual_current) > fitness(best_individual_ever):
                worst_individual_index = fitness_values.index(max(fitness_values))
                population[worst_individual_index] = best_individual_ever
            
        best_individual = min(population, key=fitness)
        return best_individual

    new_bitarr = run_genetic_algorithm(population_size, generations)

    n_group = num_cores // groupsize
    target_arr = []
    for i in range(n_group):
        if new_bitarr[i] == 1:
            target_arr = target_arr + [1]*groupsize
        else:
            target_arr = target_arr + [0]*groupsize


    # print("cost: " + str(calculate_cost_numa(arr, target_arr, costmatrix)))
    
    return target_arr

def greedy_algorithm(n, m, arr, groupsize):
    num_cores = n
    num_targetcpus = m

    n_group = num_cores // groupsize
    n_sel_group = round(num_targetcpus / groupsize)
    temparr = [0]*n_group

    group_loads = [sum(arr[i*groupsize:(i+1)*groupsize]) for i in range(n_group)]
    sorted_groups = sorted(range(n_group), key=lambda k: group_loads[k], reverse=True)

    for i in range(n_sel_group):
        temparr[sorted_groups[i]] = 1

    target_arr = []
    for i in range(n_group):
        if temparr[i] == 1:
            target_arr = target_arr + [1]*groupsize
        else:
            target_arr = target_arr + [0]*groupsize
    
    return target_arr


if __name__ == "__main__":
    # adjust pCPUs in P-Zone from n to m
    n = 128  
    m = 32   

    test_case = generate_test_case(n, m - 1)
    print("initial workload list: ", test_case)
    print(f"total workload: {sum(test_case)}")

    new_load = genetic_algorithm(n, m, test_case, 16, 8)
    print("after deprovision, workload bitmap: ", new_load)

    r = 0.6  # A coefficient to adjust the expected CPU usage.
    total_load = sum(test_case) * r
    print("expected average cpu usage: ", round(total_load/m, 2))

    greedyresult = greedy_algorithm(n, m, test_case, 16)
    print(f"greedy algorithm result: {greedyresult}")

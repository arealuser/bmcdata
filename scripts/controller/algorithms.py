import random

def generate_test_case(n, k):
    # Randomly generate CPU load for n cores
    arr = [random.randint(0, k*100//n) for _ in range(n)]
    # Ensure total load equals k*100
    total_load = sum(arr)
    arr = [load * (k*100) // total_load for load in arr]
    return arr

def calculate_cost(arr1, arr2):
    # Calculate migration cost from arr1 to arr2
    cost = 0
    for i in range(0, len(arr2)):
        if arr2[i] == 0 :
            cost += arr1[i]
    return cost

def generate_cost_matrix(num_cores, numasize, groupsize):
    # Generate inter-core migration cost matrix based on frequency group and NUMA layout
    # You can replace this function with real mapping from `numactl --hardware`
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

def generate_cost_matrix_from_numactl(num_cores, numasize, numa_distance_matrix=None, scale=1):
    """
    Generate a CPU-level migration cost matrix from a NUMA distance matrix.

    Parameters:
    - num_cores: total number of CPUs (e.g., 128)
    - numasize: number of cores per NUMA node (e.g., 16)
    - numa_distance_matrix: distance between NUMA nodes
    - scale: distance scale factor

    Returns:
    - cost_matrix: CPU x CPU migration cost
    """
    if numa_distance_matrix is None:
        numa_distance_matrix = [
            [10, 20, 40, 30, 20, 30, 50, 40, 100, 100, 100, 100, 100, 100, 100, 100],
            [20, 10, 30, 40, 50, 20, 40, 50, 100, 100, 100, 100, 100, 100, 100, 100],
            [40, 30, 10, 20, 40, 50, 20, 30, 100, 100, 100, 100, 100, 100, 100, 100],
            [30, 40, 20, 10, 30, 20, 40, 50, 100, 100, 100, 100, 100, 100, 100, 100],
            [20, 50, 40, 30, 10, 50, 30, 20, 100, 100, 100, 100, 100, 100, 100, 100],
            [30, 20, 50, 20, 50, 10, 50, 40, 100, 100, 100, 100, 100, 100, 100, 100],
            [50, 40, 20, 40, 30, 50, 10, 30, 100, 100, 100, 100, 100, 100, 100, 100],
            [40, 50, 30, 50, 20, 40, 30, 10, 100, 100, 100, 100, 100, 100, 100, 100],
            [100, 100, 100, 100, 100, 100, 100, 100, 10, 20, 40, 30, 20, 30, 50, 40],
            [100, 100, 100, 100, 100, 100, 100, 100, 20, 10, 30, 40, 50, 20, 40, 50],
            [100, 100, 100, 100, 100, 100, 100, 100, 40, 30, 10, 20, 40, 50, 20, 30],
            [100, 100, 100, 100, 100, 100, 100, 100, 30, 40, 20, 10, 30, 20, 40, 50],
            [100, 100, 100, 100, 100, 100, 100, 100, 20, 50, 40, 30, 10, 50, 30, 20],
            [100, 100, 100, 100, 100, 100, 100, 100, 30, 20, 50, 20, 50, 10, 50, 40],
            [100, 100, 100, 100, 100, 100, 100, 100, 50, 40, 20, 40, 30, 50, 10, 30],
            [100, 100, 100, 100, 100, 100, 100, 100, 40, 50, 30, 50, 20, 40, 30, 10],
        ]

    cost_matrix = [[0 for _ in range(num_cores)] for _ in range(num_cores)]

    for i in range(num_cores):
        for j in range(num_cores):
            node_i = i // numasize
            node_j = j // numasize
            dist = numa_distance_matrix[node_i][node_j]
            cost_matrix[i][j] = dist / scale if scale != 1 else dist

    return cost_matrix

def calculate_cost_numa(arr1, arr2, cost_matrix):
    # Calculate migration cost using cost matrix
    effective_cores = sum(arr2)
    cost = 0
    for i in range(len(arr2)):
        if arr2[i] == 0:
            for j in range(len(arr2)):
                if arr2[j] == 1:
                    cost += arr1[i] * cost_matrix[i][j] // effective_cores
    return cost

def genetic_algorithm(n, m, arr, groupsize, numasize):
    # n: total CPUs
    # m: target effective CPUs
    # arr: current CPU load list
    # groupsize: frequency domain group size
    # numasize: NUMA node size

    population_size = n // groupsize
    generations = 20
    costmatrix = generate_cost_matrix(n, numasize, groupsize)

    def generate_population(pop_size):
        n_group = n // groupsize
        n_sel_group = round(m / groupsize)
        temparr = [1]*n_sel_group + [0]*(n_group - n_sel_group)
        population = []
        for _ in range(pop_size):
            individual = temparr.copy()
            random.shuffle(individual)
            population.append(individual)
        return population

    def fitness(individual):
        n_group = n // groupsize
        individual_arr = []
        for i in range(n_group):
            individual_arr += [1]*groupsize if individual[i] == 1 else [0]*groupsize
        return calculate_cost_numa(arr, individual_arr, costmatrix)

    def convert_to_weights(fitness_values):
        max_fitness = max(fitness_values)
        return [max_fitness - fitness + 1 for fitness in fitness_values]

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
            return parent1, parent2
        return child1, child2

    def mutate(individual):
        one_indices = [i for i, gene in enumerate(individual) if gene == 1]
        zero_indices = [i for i, gene in enumerate(individual) if gene == 0]
        if one_indices and zero_indices:
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
        return min(population, key=fitness)

    new_bitarr = run_genetic_algorithm(population_size, generations)
    n_group = n // groupsize
    target_arr = []
    for i in range(n_group):
        target_arr += [1]*groupsize if new_bitarr[i] == 1 else [0]*groupsize
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
        target_arr += [1]*groupsize if temparr[i] == 1 else [0]*groupsize
    return target_arr

if __name__ == "__main__":
    n = 128  # total CPUs
    m = 32   # target CPUs

    test_case = generate_test_case(n, m - 1)
    print("Initial load list:", test_case)
    print(f"Total load: {sum(test_case)}")

    new_load = genetic_algorithm(n, m, test_case, 16, 8)
    print("Load bitmap after genetic algorithm:", new_load)

    total_load = sum(test_case)
    print("Expected average CPU utilization:", round(total_load/m, 2))

    greedyresult = greedy_algorithm(n, m, test_case, 16)
    print(f"Greedy algorithm result: {greedyresult}")

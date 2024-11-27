import random

def generate_test_case(n, k):
    # Randomly generate loads for n cores
    arr = [random.randint(0, k*100//n) for _ in range(n)]
    # Generate a total load of k*100
    total_load = sum(arr)
    # Adjust each core's load based on the ratio between individual load and total load, to make the total load equal to k*100
    arr = [load * (k*100) // total_load for load in arr]
    return arr

def calculate_cost(arr1, arr2):
    # Calculate the migration cost between two load distributions, arr2 can be all 0s or 1s, we use the load from arr1 to calculate the cost
    cost = 0
    for i in range(0, len(arr2)):
        if arr2[i] == 0:
            cost += arr1[i]
    return cost

def generate_cost_matrix(num_cores, numasize, groupsize):
    # Generate a cost matrix for migrations between frequency groups
    n_group = num_cores // groupsize
    cost = [[0 for _ in range(num_cores)] for _ in range(num_cores)]
    half_cores = num_cores // 2
    for i in range(num_cores):
        for j in range(num_cores):
            # Same cost within the same frequency group
            cost[i][j] = abs(i // groupsize - j // groupsize)

            # If within the same NUMA node, the cost is 0
            if i // numasize == j // numasize:
                cost[i][j] = 0

            # Additional cost for cross-CPU migrations
            if i < half_cores and j >= half_cores:
                cost[i][j] += 1
            elif i >= half_cores and j < half_cores:
                cost[i][j] += 1

    return cost

def calculate_cost_numa(arr1, arr2, cost_matrix):
    # Calculate the migration cost between two load distributions, arr2 can be all 0s or 1s, we use the load from arr1 to calculate the cost
    effective_cores = sum(arr2)
    cost = 0
    for i in range(len(arr2)):
        if arr2[i] == 0:
            for j in range(len(arr2)):
                if arr2[j] == 1:
                    cost += arr1[i] * cost_matrix[i][j] // effective_cores
    return cost

def genetic_algorithm(n, m, arr, groupsize, numasize, costmatrix):
    # n: total number of CPUs
    # m: number of CPUs after consolidation
    # arr: current CPU list
    # groupsize: size of frequency group, at least 2 on Intel
    # numa: NUMA node size, not used here, will be used in the second research point

    # Define genetic algorithm parameters
    population_size = n // groupsize
    generations = 100

    # Define problem parameters
    num_cores = n
    num_targetcpus = m

    # Generate initial population
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

    # Calculate the fitness (migration cost) of an individual
    def fitness(individual):
        n_group = num_cores // groupsize
        individual_arr = []
        for i in range(n_group):
            if individual[i] == 1:
                individual_arr = individual_arr + [1]*groupsize
            else:
                individual_arr = individual_arr + [0]*groupsize
        
        return calculate_cost_numa(arr, individual_arr, costmatrix)

    # Convert fitness to weights, the smaller the fitness, the higher the weight
    def convert_to_weights(fitness_values):
        max_fitness = max(fitness_values)
        weights = [max_fitness - fitness + 1 for fitness in fitness_values]
        return weights

    # Selection operation: roulette wheel selection
    def roulette_wheel_selection(population, fitness_values):
        total_fitness = sum(fitness_values)
        probabilities = [fitness / total_fitness for fitness in fitness_values]
        return random.choices(population, weights=probabilities, k=len(population))

    # Crossover operation: single-point crossover
    def crossover(parent1, parent2):
        sumparent = sum(parent1)
        crossover_point = random.randint(1, min(len(parent1), len(parent2)) - 1)
        child1 = parent1[:crossover_point] + parent2[crossover_point:]
        child2 = parent2[:crossover_point] + parent1[crossover_point:]
        if sum(child1) != sumparent or sum(child2) != sumparent:  # Invalid offspring
            child1 = parent1
            child2 = parent2
        return child1, child2

    # Mutation operation: randomly swap a core's load value
    def mutate(individual):
        one_indices = [i for i, gene in enumerate(individual) if gene == 1]
        zero_indices = [i for i, gene in enumerate(individual) if gene == 0]

        if len(one_indices) > 0 and len(zero_indices) > 0:
            one_index = random.choice(one_indices)
            zero_index = random.choice(zero_indices)
            individual[one_index] = 0
            individual[zero_index] = 1

        return individual

    # Main function of the genetic algorithm
    def run_genetic_algorithm(pop_size, generations):
        population = generate_population(pop_size)
        best_individual_ever = None
        best_fitness_ever = float('inf')

        for _ in range(generations):
            fitness_values = [fitness(individual) for individual in population]

            # Find the best individual in the current population
            best_fitness_current = min(fitness_values)
            best_individual_current = population[fitness_values.index(best_fitness_current)]
            # If the current best individual is better than the previous best, update the best individual
            if best_fitness_current < best_fitness_ever:
                best_individual_ever = best_individual_current
                best_fitness_ever = best_fitness_current
            # Selection
            weights = convert_to_weights(fitness_values)
            selected_population = roulette_wheel_selection(population, weights)

            # Crossover
            offspring = []
            for i in range(0, pop_size, 2):
                child1, child2 = crossover(selected_population[i], selected_population[i+1])
                offspring.extend([child1, child2])

            # Mutation
            for individual in offspring:
                if random.random() < 0.3:  # Set mutation probability to 0.2
                    mutate(individual)

            # Update population
            population = offspring

            # Elitism: If the best individual in the new population is worse than the best individual in the old population, replace the worst individual in the new population with the best individual from the old population
            if fitness(best_individual_current) > fitness(best_individual_ever):
                if random.random() < 0.5:  # Flip a coin to decide whether to replace, as bad parents can still produce good children
                    worst_individual_index = fitness_values.index(max(fitness_values))
                    population[worst_individual_index] = best_individual_ever
            
            best_cost = min(fitness_values)
            print(f"iterations: {_}, fitness: {best_cost}")

        # Find the best solution
        best_individual = min(population, key=fitness)
        return best_individual

    # Call the genetic algorithm to generate a new load distribution based on the input initial load list
    new_bitarr = run_genetic_algorithm(population_size, generations)

    # Restore the original format
    n_group = num_cores // groupsize
    target_arr = []
    for i in range(n_group):
        if new_bitarr[i] == 1:
            target_arr = target_arr + [1]*groupsize
        else:
            target_arr = target_arr + [0]*groupsize

    return target_arr

def greedy_algorithm(n, m, arr, groupsize):
    # n: total number of CPUs
    # m: number of CPUs after consolidation
    # arr: current CPU list
    # groupsize: size of frequency group

    # Define problem parameters
    num_cores = n
    num_targetcpus = m

    # Generate initial population
    n_group = num_cores // groupsize
    n_sel_group = round(num_targetcpus / groupsize)
    temparr = [0]*n_group

    # Sort frequency groups by their total load
    group_loads = [sum(arr[i*groupsize:(i+1)*groupsize]) for i in range(n_group)]
    sorted_groups = sorted(range(n_group), key=lambda k: group_loads[k], reverse=True)

    # Select the most loaded frequency groups for consolidation
    for i in range(n_sel_group):
        temparr[sorted_groups[i]] = 1

    # Restore the original format
    target_arr = []
    for i in range(n_group):
        if temparr[i] == 1:
            target_arr = target_arr + [1]*groupsize
        else:
            target_arr = target_arr + [0]*groupsize
    
    return target_arr

if __name__ == "__main__":
    n = 128  # Total number of CPUs
    m = 32   # Number of effective CPUs after consolidation
    numasize = 8
    frequencygroup = 16

    # Generate test case
    test_case = generate_test_case(n, m - 1)
    print("Initial load list:", test_case)
    print(f"Total load: {sum(test_case)}")
    # Calculate the migration cost matrix
    costmatrix = generate_cost_matrix(n, numasize, frequencygroup)

    # Calculate the expected load distribution after consolidation
    total_load = sum(test_case)
    print("Expected utilization per CPU:", round(total_load/m, 2))

    # Use the genetic algorithm for load consolidation
    new_load = genetic_algorithm(n, m, test_case, frequencygroup, numasize, costmatrix)
    print("Load bitmap after genetic algorithm:", new_load)

    # Compare with the greedy algorithm
    greedyresult = greedy_algorithm(n, m, test_case, frequencygroup)
    print(f"Greedy result: {greedyresult}")

    genetic_cost = calculate_cost_numa(test_case, new_load, costmatrix)
    greedy_cost = calculate_cost_numa(test_case, greedyresult, costmatrix)
    print(f"Genetic cost: {genetic_cost}, Greedy cost: {greedy_cost}")
    
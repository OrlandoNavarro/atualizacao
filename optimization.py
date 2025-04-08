import random
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, filename="optimization.log", filemode="a",
                    format="%(asctime)s - %(levelname)s - %(message)s")

def populacao_inicial(pedidos_df, caminhoes_df, tamanho=50):
    """
    Inicializa uma população aleatória de soluções viáveis para o problema.
    Cada solução é um mapeamento de IDs de pedidos para IDs de caminhões.
    """
    population = []
    pedidos_ids = pedidos_df.index.tolist()
    caminhoes_ids = caminhoes_df.index.tolist()
    for _ in range(tamanho):
        sol = {pedido: random.choice(caminhoes_ids) for pedido in pedidos_ids}
        population.append(sol)
    return population

def avaliacao_fitness(solucao, pedidos_df, caminhoes_df):
    """
    Calcula a fitness de uma solução.
    Exemplo: soma dos 'Peso dos Itens'. Ajuste conforme os requisitos.
    """
    fitness = 0
    for pedido, caminhao in solucao.items():
        fitness += pedidos_df.loc[pedido, "Peso dos Itens"]
    return 1.0 / (fitness + 1e-6)

def selecionar(population, fitnesses, num=10):
    """
    Seleciona as melhores soluções com base nas fitnesses.
    """
    sorted_population = [sol for _, sol in sorted(zip(fitnesses, population), key=lambda x: x[0], reverse=True)]
    return sorted_population[:num]

def cruzar(sol1, sol2):
    """
    Realiza crossover entre duas soluções.
    """
    filho = {}
    for key in sol1.keys():
        filho[key] = sol1[key] if random.random() < 0.5 else sol2[key]
    return filho

def mutacao(solucao, caminhoes_ids, taxa=0.1):
    """
    Aplica mutação em uma solução: troca aleatoriamente alguns mapeamentos.
    """
    for pedido in solucao.keys():
        if random.random() < taxa:
            solucao[pedido] = random.choice(caminhoes_ids)
    return solucao

def run_genetic_algorithm(pedidos_df, caminhoes_df, geracoes=100, tamanho_pop=50):
    """
    Executa um algoritmo genético para gerar uma solução ótima.
    """
    population = populacao_inicial(pedidos_df, caminhoes_df, tamanho=tamanho_pop)
    pedidos_ids = pedidos_df.index.tolist()
    caminhoes_ids = caminhoes_df.index.tolist()
    melhor_solucao = None
    melhor_fitness = -np.inf
    for _ in range(geracoes):
        fitnesses = [avaliacao_fitness(sol, pedidos_df, caminhoes_df) for sol in population]
        melhores = selecionar(population, fitnesses, num=10)
        nova_pop = []
        for _ in range(tamanho_pop):
            sol1, sol2 = random.sample(melhores, 2)
            filho = cruzar(sol1, sol2)
            filho = mutacao(filho, caminhoes_ids)
            nova_pop.append(filho)
        population = nova_pop
        melhor_iter = max(fitnesses)
        if melhor_iter > melhor_fitness:
            melhor_fitness = melhor_iter
            melhor_solucao = population[fitnesses.index(melhor_iter)]
    return {"solucao": melhor_solucao, "fitness": melhor_fitness}
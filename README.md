# Análise de Paralelização – Soma de Números com Threads

## 1. Descrição do Problema

**Qual é o objetivo do programa?**  
O objetivo do programa é ler um arquivo de texto contendo vários números inteiros e calcular a soma total desses valores. Para melhorar o desempenho, o programa utiliza múltiplas threads para processar partes do arquivo em paralelo.

**Qual problema foi implementado?**  
Foi implementado um problema de processamento de dados em que é necessário somar uma grande quantidade de números armazenados em um arquivo. O desafio é realizar essa soma de forma eficiente utilizando paralelização.

**Qual algoritmo foi utilizado?**  
O algoritmo utilizado consiste em dividir os dados do arquivo entre várias threads. Cada thread calcula uma soma parcial dos números que recebeu, e ao final todas as somas parciais são combinadas para gerar o resultado final.

**Qual o volume de dados processado?**  
Nos testes foram utilizados arquivos com aproximadamente 1 milhão de números e 10 milhões de números, onde cada linha do arquivo contém um número inteiro.

**Qual o tamanho da entrada utilizada nos testes?**  
O tamanho da entrada corresponde ao número de linhas do arquivo. Foram utilizados arquivos com 1.000.000 e 10.000.000 de linhas.

**Qual o objetivo da paralelização?**  
O objetivo da paralelização é dividir o trabalho entre várias threads para reduzir o tempo total de execução do programa.

**Qual a complexidade aproximada do algoritmo?**  
A complexidade do algoritmo é aproximadamente O(n), pois cada número do arquivo precisa ser lido e somado uma única vez.

## 2. Ambiente Experimental

| Item | Descrição |
|---|---|
| Processador | I5-12500 |
| Número de núcleos | 6 |
| Memória RAM | 16gb |
| Sistema Operacional | Win 11 |
| Linguagem utilizada | Python |
| Biblioteca de paralelização | Threading |
| Compilador / Versão | VS Code - Python 3.13.2 |

## 3. Metodologia de Testes

**Como o tempo de execução foi medido?**  
O tempo de execução foi medido utilizando funções de medição de tempo da linguagem Python, registrando o tempo no início e no final da execução do programa. A diferença entre esses valores representa o tempo total de processamento.

**Quantas execuções foram realizadas?**  
Foram realizadas duas execuções para cada configuração de threads, para reduzir possíveis variações de desempenho durante os testes.

**Foi utilizada média dos tempos?**  
Sim. Para cada configuração foi calculada a média dos tempos obtidos nas duas execuções, e esse valor médio foi utilizado na análise dos resultados.

**Qual tamanho da entrada foi usado?**  
Nos testes foram utilizados arquivos contendo 1.000.000 de números e 10.000.000 de números, onde cada linha do arquivo possui um número inteiro.

**Configurações testadas**

1 thread (versão serial)  
2 threads  
4 threads  
8 threads  
12 threads  

**Número de execuções para cada configuração**  
Para cada configuração de threads foram realizadas duas execuções do programa.

**Forma de cálculo da média**  
A média foi calculada somando os tempos das duas execuções e dividindo o resultado por dois.

**Condições de execução**  
Os experimentos foram executados em um computador pessoal, utilizando o VS Code para rodar o programa em Python. Durante os testes, foram fechados outros programas e aplicações para reduzir interferências e permitir que o programa utilizasse a maior parte dos recursos da máquina.

## 4. Resultados Experimentais

| Nº Threads/Processos | Tempo de Execução (s) |
|---|---|
| 1 | 1.0100565 |
| 2 | 1.027310 |
| 4 | 1.041841 |
| 8 | 1.1240425 |
| 12 | 1.090313 |

## 5. Cálculo de Speedup e Eficiência

Fórmulas Utilizadas

Speedup(p) = T(1) / T(p)

Onde:

T(1) = tempo da execução serial  
T(p) = tempo com p threads/processos  

Eficiência(p) = Speedup(p) / p

Onde:

p = número de threads ou processos

## 6. Tabela de Resultados

| Threads/Processos | Tempo (s) | Speedup | Eficiência |
|---|---|---|---|
| 1 | 1.009876 | 1,000 | 1.000 |
| 2 | 1.023370 | 0.987 | 0.494 |
| 4 | 1.030603 | 0.980 | 0.245 |
| 8 | 1.094857 | 0.922 | 0.115 |
| 12 | 1.131273 | 0.962 | 0.080 |

## 7. Gráfico de Tempo de Execução

Construa um gráfico mostrando o tempo de execução em função do número de threads/processos.

Orientações

Eixo X: número de threads/processos  
Eixo Y: tempo de execução (segundos)

Gráfico abaixo:

![Tempo de Execução](graficos/chart.png)

Construa um gráfico mostrando o speedup obtido.

Orientações

Eixo X: número de threads/processos  
Eixo Y: speedup  
Incluir também a linha de speedup ideal (linear) para comparação  

Gráfico abaixo:

## 9. Gráfico de Eficiência

Construa um gráfico mostrando a eficiência da paralelização.

Orientações

Eixo X: número de threads/processos  
Eixo Y: eficiência  
Valores entre 0 e 1  

Gráfico abaixo:

## 10. Análise dos Resultados

**O speedup obtido foi próximo do ideal?**  
Não. O speedup ficou abaixo do esperado e em alguns casos foi menor que 1, indicando que o programa não ficou mais rápido com mais threads.

**A aplicação apresentou escalabilidade?**  
Não. O aumento do número de threads não reduziu o tempo de execução de forma significativa.

**Em qual ponto a eficiência começou a cair?**  
A eficiência começou a cair a partir de 2 threads e continuou diminuindo conforme mais threads foram adicionadas.

**O número de threads ultrapassa o número de núcleos físicos da máquina?**  
Sim. O processador possui 6 núcleos físicos e alguns testes foram realizados com 8 e 12 threads.

**Houve overhead de paralelização?**  
Sim. O gerenciamento e sincronização das threads gerou um custo adicional que impactou o desempenho.

**Possíveis causas para perda de desempenho**

- Overhead das threads
- Leitura do arquivo como gargalo
- Disputa por recursos da CPU

**Gargalos no algoritmo**

- Leitura do arquivo
- Divisão do trabalho entre as threads

**Sincronização entre threads/processos**

A necessidade de sincronizar algumas operações entre threads pode ter aumentado o tempo de execução.

**Comunicação entre processos**

Como foi utilizado threading, não houve comunicação entre processos, apenas entre threads.

**Contenção de memória ou cache**

Com muitas threads acessando dados ao mesmo tempo, pode ter ocorrido contenção de memória ou cache.

## 11. Conclusão

Os resultados mostram que a paralelização não trouxe o ganho de desempenho esperado para essa aplicação. Em alguns casos, o tempo de execução até aumentou com mais threads. Isso ocorreu devido ao overhead da paralelização, à leitura do arquivo e à limitação de núcleos do processador. Mesmo assim, o experimento foi importante para entender na prática conceitos de speedup, eficiência e limitações do paralelismo.
```

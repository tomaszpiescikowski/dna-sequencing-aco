from termcolor import colored
from datetime import datetime
import numpy as np
import datetime
import random
import time
import math
import sys

class ACO(object):
    
    def __init__(self, file_path, file_name, n, l, number_of_mistakes, instance_type):
        # Próby otworzenia pliku
        try:
            with open(file_path, "r+") as f:
                spektrum = list(f.read().split('\n'))
                spektrum.pop()
                spektrum = list(map(str, spektrum))
        except:
            print(colored("Error while reading file. Check the name of file or it's content.", "red"))
            sys.exit()

        # Liczba mrówek
        self.number_of_ants = 20  
        # Współczynnik ważności feromonów
        self.alpha = 1
        # Ważny czynnik funkcji heurystycznej
        self.beta = 40
        # Lotny czynnik feromonów
        self.rho = 0.1  
        # Stały współczynnik
        self.q = 1  
        # Liczba iteracji
        self.liczba_iteracji = 100

        # Sciezka do wynikow
        self.result_files_path = 'app\\results'
        # Nazwa pliku
        self.file_name = file_name
        # Spektrum - cały zbiór podanych słów 
        self.spektrum = spektrum
        # Rodzaj instancji
        self.instance_type = instance_type
        # Długość sekwencji
        # length_of_sequence nie być hard-coded, ale z pliku np. albo nazwy - DONE 27.05.2022
        self.length_of_sequence = n
        # Długość pojedynczego słowa w spektrum
        self.length_of_word = l
        # Liczba wszystkich slów w spektrum
        self.number_of_words = len(spektrum)
        # Liczba bledow
        self.number_of_mistakes = number_of_mistakes
        # Liczba wierzchołków
        self.number_of_verticles = self.number_of_words  
        # Macierz feromonów wypełniona jedynkami
        self.pheromone = np.ones([self.number_of_verticles, self.number_of_verticles])  
        # Kolonia mrówek, czyli każda mrówka i jej skończona droga
        self.ant_colony = [[-1 for _ in range(self.number_of_verticles)] for _ in range(self.number_of_ants)]
        # Oblicz macierz sąsiedztwa (odległości między miastami)
        self.graph = self.calculate_weights_between_verticles()  
        # Funkcja heurystyczna (do wzoru na prawdopodobieństwo)   
        # Ilość śladu feromonowego                                           
        self.eta = 1. / self.graph     
        # Tablica budzetu dla każdej mrówki
        self.budget = [self.length_of_sequence - self.length_of_word for _ in range(self.number_of_ants)]

        # Tablica dystansów zrobionych przez mrówki.
        self.paths = None  
        self.iter_x = []
        self.iter_y = []



    # Cij -> Funkcja sprawdzajaca wagi pomiedzy podanymi wierzcholkami (slowami)
    def check_weight_between(self, Si, Sj):
        if Si == Sj: return -1  # Zakłada się, że Si != Sj
        """
        Powyższy warunek powoduje, że ZAWSZE:
            0 <= Oij <= length_of_word -1
            1 <= Cij <= length_of_word
        """   
        
        Oij = 0 # oznacza liczbę końcowych symboli (długość sufiksu) słowa Si
    
        for index in range(self.length_of_word-1, -1, -1):
            if Sj[:self.length_of_word-index] == Si[index:]:
                Oij = self.length_of_word - index
        
        Cij = self.length_of_word - Oij
        return Cij


    # Tworzenie macierzy sąsiedztwa
    def calculate_weights_between_verticles(self): 
        # graph = [[0 for j in range(self.number_of_words)] for i in range(self.number_of_words)]
        graph = np.zeros((self.number_of_words, self.number_of_words))
        for Si in range(self.number_of_words):
            for Sj in range(self.number_of_words):
                x = self.spektrum[Si]
                y = self.spektrum[Sj]
                # Dodajemy wagę krawędzi między wierzchołami do grafu
                graph[Si][Sj] = self.check_weight_between(x, y)
        
        return graph


    # Ostateczny krok wybrania wierzchołka
    def random(self, probability_of_next_verticle):
        x = np.random.rand()
        # Enumerate umożliwia  iterację po obiektach takich jak lista
        # przy jednoczesnej informacji, którą iterację wykonujemy index - nr iteracji, t - wartości po których iterujemy.
        #-----  PRAWDOPODOBIEŃSTWO WIERZCHOŁKA START --------------------------- 24.05.2022
        # W teorii lepiej, żeby była tablica probability_of_next_verticle była posortowana od największego jednak nie wpływa to na wynik
        # sorted_probability_of_next_verticle = sorted(probability_of_next_verticle, reverse=True)
        # for index, t in enumerate(sorted_probability_of_next_verticle): 
        #     x -= t              
        #     if x <= 0: break   
        # # zwraca indeks następnego miasta do odwiedzenia.
        # return probability_of_next_verticle.index(sorted_probability_of_next_verticle[index])
        #-----  PRAWDOPODOBIEŃSTWO WIERZCHOŁKA END --------------------------- 24.05.2022
        #---------------------DZIAŁAJĄCA STARA CZĘŚĆ START---------------------------
        for index, t in enumerate(probability_of_next_verticle): 
            x -= t              
            if x <= 0: break 
        return index

    # Stwórz kolonię mrówek - kolejne słowa ze spektrum przypisane są liczbom od <0 do len(spektrum)>
    def ant_run(self):
        # Przerwanie gdy skończy się budżet - DONE 18.05.2022
        for current_ant_index in range(self.number_of_ants):  
            #Liczymy długość sekwencji (ścieżki)
            ant_sequence_len = 0
            # Losuje liczbę w zakresie liczby miast
            start_verticle = random.randint(0, self.number_of_verticles - 1)  
            # Zaczynamy zapisywanie ścieżki dla mrówki inicjując pierwszy wierzchołek
            self.ant_colony[current_ant_index][0] = start_verticle  
            # Lista wierzchołków do odwiedzenia
            not_visited_verticles = list(verticle for verticle in range(self.number_of_verticles) if verticle != start_verticle) 
            # Ustawiamy aktualny wierzchołek 
            current_verticle = start_verticle
            # Zmienna pomocnicza
            helper_index = 1
            # Zmienna pomocnicza 2
            counter = 0

            while (len(not_visited_verticles) != 0) and (ant_sequence_len <= self.length_of_sequence):
                # Tablica zawierająca prawodopodobieństwa przejść do kolejno nieodwiedzonych wierzchołków
                probability_of_next_verticle = []
                # Oblicz prawdopodobieństwo przejścia między wierzchołkami przez feromon
                for possible_verticle in not_visited_verticles:
                    # nasz wzór na prawdopodobieństwo
                    probability_of_next_verticle.append(
                        self.pheromone[current_verticle][possible_verticle] ** 
                        self.alpha * 
                        self.eta[current_verticle][possible_verticle] ** 
                        self.beta
                    )  
                # Suma pradopodobieństw w powyższej listy
                probability_list_sum = sum(probability_of_next_verticle)
                # Bierzemy prawdopodobienstwo jednego wierzchołka  i dzielimy przez sumę prawdopodobieństw wszystkich wierzchołków
                probability_of_next_verticle = [v / probability_list_sum for v in probability_of_next_verticle]
                
                #---------------------BUDGET PART START--------------------------- 18.05.2022
                # Ruletka wybiera miasto
                possible_next_verticle = not_visited_verticles[self.random(probability_of_next_verticle)]
                # Nie chcemy przejść do samego siebie
                if self.graph[current_verticle][possible_next_verticle] == 0:
                    not_visited_verticles.remove(possible_next_verticle)
                    continue
                # Jeśli budżet do przejścia między tymi dwoma jest za mały
                elif self.budget[current_ant_index] < self.graph[current_verticle][possible_next_verticle]:
                    not_visited_verticles.remove(possible_next_verticle)
                    # print("Nie starczy budzetu", helper_index)
                    continue
                elif (ant_sequence_len + self.graph[current_verticle][possible_next_verticle]) > self.length_of_sequence:
                    not_visited_verticles.remove(possible_next_verticle)
                    # print("Nie starczy sekwencji")
                    
                    

                # Jeśli koszt przejscia jest za duzy dla nas
                elif self.graph[current_verticle][possible_next_verticle] > 4:
                    # not_visited_verticles.remove(possible_next_verticle)
                    # print("za duzy koszt przejscia, sprobuje jeszcze raz", self.graph[current_verticle][possible_next_verticle])
                    counter+=1
                    if (counter < 5):
                        continue

                counter = 0

                # Jeżeli wybieramy się do nowego wierzchołka i mamy na to budżet
                self.budget[current_ant_index] -= self.graph[current_verticle][possible_next_verticle]
                
                
                #Zwiększamy długośc sekwencji o koszt
                ant_sequence_len += self.graph[current_verticle][possible_next_verticle]
                # print(self.graph[current_verticle][possible_next_verticle])
                
                # Przechodzimy, więc to nasz nowy obecny wierzchołek
                current_verticle = possible_next_verticle
                # Tworzymy więc dla każdej mrówkę jej ścieżkę.
                self.ant_colony[current_ant_index][helper_index] = current_verticle
                # Usuwamy wierzchołek z listy nieodwiedzonych 
                not_visited_verticles.remove(current_verticle)
                helper_index += 1
                

                #---------------------BUDGET PART END---------------------------18.05.2022

                #---------------------DZIAŁAJĄCA STARA CZĘŚĆ START---------------------------
                # # Ruletka wybiera miasto
                # next_verticle_index = self.random(probability_of_next_verticle)
                # current_verticle = not_visited_verticles[next_verticle_index]
                # # Tworzymy więc dla każdej mrówkę jej ścieżkę.
                # self.ant_colony[current_ant_index][helper_index] = current_verticle
                # not_visited_verticles.remove(current_verticle)
                # helper_index += 1
                #---------------------DZIAŁAJĄCA STARA CZĘŚĆ END---------------------------

            # # print(f"Mrowka {current_ant_index} sekwencja {ant_sequence_len} numer iteracji {helper_index} \
            #         len(not_visited_verticles) != 0 {len(not_visited_verticles) != 0} \
            #             ant_sequence_len {ant_sequence_len} <= self.length_of_sequence {self.length_of_sequence}")
    
    # Oblicz długość ścieżki
    def calculate_one_path_cost(self, path):
        cost = 0
        for index in range(len(path) - 1):
            #-------------ZMIANY START----------------18.05.2022
            # Jeżeli mrówka nie przeszła całej trasy bo miała za mały budżet,
            # to reszta jej ścieżki wierzchołków wypełniona jest -1, trzeba to uwzględnić.
            # Powoduje to jednak kolejny ?problem?, bo krótsze ścieżki będą tańsze
            # Odp: Nie do końca jest to problem, ponieważ w przypadku selektywnego komiwojażera nie zależy nam
            # na przejściu wszystkich ścieżek, tylko na przejściu jak największej ilości krótkich ścieżek zanim skończy  nam się budżet.
            a = path[index]
            b = path[index + 1]
            # Jeżli natrafimy na koniec trasy 
            if b == -1:
                break
            cost += self.graph[a][b]
            #-------------ZMIANY END----------------18.05.2022

            #-------------DZIAŁAJĄCA STARA CZĘŚĆ START----------------
            # a = path[index]
            # b = path[index + 1]
            # cost += self.graph[a][b]
            #-------------DZIAŁAJĄCA STARA CZĘŚĆ END----------------

        # Zwraca dystans pokonany przez mrówkę.
        return cost  

    # Oblicz koszt ścieżek
    def calculate_cost_of_paths(self): 
        list_of_path_costs = []
        # Dla każdej ścieżki mrówki:
        for path in self.ant_colony:  
            cost = self.calculate_one_path_cost(path)
            list_of_path_costs.append(cost)
        # Tablica dystansów zrobionych przez mrówki.
        return list_of_path_costs  

    # Zaktualizuj feromon
    def update_pheromone(self):
        # Macierz feromonów
        delta_pheromone = np.zeros([self.number_of_verticles, self.number_of_verticles]) 
        # Tablica kosztów ścieżek przebytych przez mrówki.
        # --- Poniższa linia jest nadmiarowa, nie trzeba liczyć jeszcze raz. --- 24.05.2022
        # Co dziwne przy ponownym obliczeniu paths wyniki wydają się ciut lepsze.
        # paths = self.calculate_cost_of_paths()  
        for i in range(self.number_of_ants):  # m - liczba mrówek
            for j in range(self.number_of_verticles - 1):
                
                a = self.ant_colony[i][j]
                b = self.ant_colony[i][j + 1]

                # Zastanowić się, czy mrówki tutaj zostawiają ślad tylko po wierzchołkach, które przeszły - DONE 25.05.2022
                if b == -1: break
                # Zostawianie feromonów.
                delta_pheromone[a][b] = delta_pheromone[a][b] + self.q / self.paths[i]  
                
            # W naszym przypadku nie ma domknięcie ścieżki - mrówki zostawiają feromon tylko na wierz., które przeszły. 24.05.2022
            # a = self.ant_colony[i][0]
            # b = self.ant_colony[i][-1]
            # Domknięcie ścieżki z zostawianiem feromonu.
            # delta_pheromone[a][b] = delta_pheromone[a][b] + self.q / self.paths[i]  
                                              
        # Na początku paruje i dodaje te nowe zostawione pheromone.
        # Wszystkie ścieżki parują tzn wszystkie wartości w tablicy feromonów mnożymy razy (1 - self.rho), czyli 0,9. I dodajemy wartość feromonow.
        self.pheromone = (1 - self.rho) * self.pheromone + delta_pheromone
        
    def time_to_finish(self, iteracja, czas):
        sekundyDoKonca = czas * (iteracja - self.liczba_iteracji)
        return str(datetime.timedelta(seconds=sekundyDoKonca))

    def run(self):
        startRun = time.time()
        # Wartość najtańszej ścieżki ustawiamy na plus nieskończoność.
        cheapest_cost = math.inf  
        # Najtańsza ścieżka.
        cheapest_path = None  
        for iteracja in range(self.liczba_iteracji):

            self.ant_colony = [[-1 for _ in range(self.number_of_verticles)] for _ in range(self.number_of_ants)]
            self.budget = [self.length_of_sequence - self.length_of_word for _ in range(self.number_of_ants)]

            start_verticle = time.time()
            # Tworzymy nową grupę składającą się z self.number_of_ants mrówek
            self.ant_run()  
            # Tablica kosztów przebytych przez powyższe mrówki ścieżek
            self.paths = self.calculate_cost_of_paths()
            # for i, v in enumerate(self.paths):
            #     print(i, v)  

            # Najmniejszy koszt z aktualnej grupy mrówek
            # current_cheapest_cost = min(self.paths)
            length_difference = math.inf
            for path_cost in self.paths:
                if self.length_of_sequence - path_cost < length_difference:
                    length_difference = self.length_of_sequence - path_cost
                    current_cheapest_cost = path_cost 
            # Najtańsza ścieżka z aktualnej grupy mrówek - lista wierzchołków
            current_cheapest_path = self.ant_colony[self.paths.index(current_cheapest_cost)]  

            # Zaktualizuj optymalne rozwiązanie
            if self.length_of_sequence - current_cheapest_cost > self.length_of_sequence - cheapest_cost:
                cheapest_cost = current_cheapest_cost
                cheapest_path = current_cheapest_path
                
            # Zaktualizuj feromon
            self.update_pheromone()

            end = time.time()
            print("Iteracja: ", iteracja, "     " if len(str(iteracja))==1 else "    ", colored(str(int(iteracja / self.liczba_iteracji * 100)) + ("%     " if len(str(iteracja))==1 else "%    "), "green"),
                  "Czas do końca: ", colored(str(self.time_to_finish(iteracja, start_verticle - end)), "yellow"), end=' ')
            print(f'    Dokladnosc algorytmu: {len(cheapest_path)}/{len(self.spektrum)} = {round(len(cheapest_path)/len(self.spektrum)*100, 2)}%')
        
        endRun = time.time()

        #------USUWANIE PUSTYCH PRZEJŚĆ (-1) START--------18.05.2022
        to_expensive_verticles = []
        # Usuwamy minus jedynki (-1) z ścieżki, (-1) oznaczają że tam już się skończył budżet
        while cheapest_path[-1] == -1:
            deleted = cheapest_path.pop()
            to_expensive_verticles.append(deleted)
        #------USUWANIE PUSTYCH PRZEJŚĆ (-1) END--------18.05.2022

        print(f"\nNajmniejszy koszt ścieżki {self.file_name}: {colored(cheapest_cost, 'green')}")
        print("\nKolejność indeksów wierzchołków:", *cheapest_path)

        shift = ""
        sequence_list = []
        sequence_matrix = []

        # Przechodzimy po wybranej najtanszej sciezce
        for verticle in range(len(cheapest_path)-1):
            Si = cheapest_path[verticle]
            Sj = cheapest_path[verticle+1]
            word = shift + self.spektrum[Si]
            sequence_list.append(word)
            next_shift = self.graph[Si][Sj]
            # Nastepny wierzcholek bedzie przesuniety o dana wartosc przejscia
            shift += " " * int(next_shift)
            # To wyjatek dla ostatniego wierzcholka
            if (verticle == len(cheapest_path)-2):
                word = shift + self.spektrum[Sj]
                sequence_list.append(word)

        size = max([len(x) for x in sequence_list ])      
        for i in sequence_list:
            temp = i
            while len(temp) != size:
                temp += " "
            sequence_matrix.append(list(temp))
        
        with open(f"app\\results\\result_{self.file_name}.txt", "w+") as file:
            sequence = ""
            for j in range(size):
                for i in reversed(range(len(cheapest_path))):
                # for i in reversed(range(self.number_of_verticles)):
                    letter = sequence_matrix[i][j]
                    if letter != " ":
                        sequence += letter
                        break
            
            # datetime object containing current date and time
            file.write(f'Data badania: {datetime.datetime.now()}\n')
            file.write(f'Nazwa pliku: {self.file_name}\n')
            file.write(f'Rodzaj instancji: {self.instance_type}\n')
            file.write(f'Liczba bledow: {self.number_of_mistakes}\n')

            file.write(f'Czas: {round(endRun - startRun, 4)}\n')


            file.write(f'Liczba iteracji: {self.liczba_iteracji}\n')
            file.write(f'Liczba mrowek: {self.number_of_ants}\n')


            file.write(f'Liczba oligonukleotydow w pliku: {len(self.spektrum)}\n')
            file.write(f'Liczba oligonukleotydow po algorytmie: {len(cheapest_path)}\n')
            file.write(f'Dokladnosc algorytmu: {len(cheapest_path)}/{len(self.spektrum)} = {round(len(cheapest_path)/len(self.spektrum)*100, 2)}%\n')

            file.write(f'Docelowa dlugosc sekwencji: n = {self.length_of_sequence}\n')
            file.write(f'Uzyskana dlugosc sekwencji: n = {len(sequence)}\n')

            file.write(f'Dokladnosc dlugosci sekwencji: {len(sequence)}/{self.length_of_sequence} = {round(len(sequence)/self.length_of_sequence*100, 2)}%\n')
            file.write(f'Uzyskana sekwencja: {sequence}\n')
            file.write(f'Ponizej kolejne oligonukleotydy sekwencji wraz z przejsciami (przesuniecia): \n\n')
            
            for x in range(len(cheapest_path)):
                file.write(f'{"".join(sequence_matrix[x])}\n')

        print("\nSekwencja: " + colored(sequence, "green"))
        print("\nDługość sekwencji: " + colored(len(sequence), "yellow"))

        print("\nPrzejścia w sekwencji z wagami: ")
        for visited in range(len(cheapest_path)-1):
            Si = cheapest_path[visited]
            Sj = cheapest_path[visited+1]
            print(self.spektrum[Si], colored("--", "green"), colored(self.graph[Si][Sj], "yellow"), colored("->", "green"), self.spektrum[Sj])
                

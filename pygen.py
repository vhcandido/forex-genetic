#!/usr/bin/env python2

import socket
import pdb

from pandas import DataFrame
from random import choice, random, randint, randrange

class Rule(object):
    def __init__(self, d):
    #    self.rule = dict()
    #    self.rule = {
    #            'buy':
    #                {'rule1': list(),
    #                'rule2': list(),
    #                'operator': 0},
    #            'sell':
    #                {'rule1': list(),
    #                'rule2': list(),
    #                'operator': 0}
    #                }
        self.buy_r1 = d['buy']['rule1']
        self.buy_r2 = d['buy']['rule2']
        self.buy_op = d['buy']['operator']

        self.sell_r1 = d['sell']['rule1']
        self.sell_r2 = d['sell']['rule2']
        self.sell_op = d['sell']['operator']

    def __str__(self):
        br1 = ','.join(str(i) for i in self.buy_r1)
        br2 = ','.join(str(i) for i in self.buy_r2)
        sr1 = ','.join(str(i) for i in self.sell_r1)
        sr2 = ','.join(str(i) for i in self.sell_r2)

        return '%s,%s,%s,%s,%s,%s' % (br1, br2, self.buy_op,
                sr1, sr2, self.sell_op)

    @staticmethod
    def gen_random():
        d = dict()
        d['buy'] = dict()
        d['sell'] = dict()

        d['buy']['rule1'] = Rule.generic_rule('ema')
        d['buy']['rule2'] = Rule.generic_rule()
        d['buy']['operator'] = choice(['and', 'or'])

        d['sell']['rule1'] = Rule.generic_rule('ema')
        d['sell']['rule2'] = Rule.generic_rule()
        d['sell']['operator'] = choice(['and', 'or'])

        return d

    @staticmethod
    def generic_rule(ob=''):
        r = list()
        ta = ['rsi','roc', 'macd']

        if(ob == 'ema'):
            r.append('ema')
            r.append(randint(3, 80)) # slow EMA
            r.append(randint(3, 150)) # fast EMA
        else:
            ob = choice(ta)
            r.append(ob)
            r.append(randint(3, 100))
            r.append(randint(0,100))
        # For EMAs:
        #   '>' means cross up
        #   '<' meand cross down
        r.append(choice(['>','<']))

        return r

    def get_dict(self):
        d = dict()
        d['buy'] = dict()
        d['sell'] = dict()
        d['buy']['rule1'] = self.buy_r1
        d['buy']['rule2'] = self.buy_r2
        d['buy']['operator'] = self.buy_op

        d['sell']['rule1'] = self.sell_r1
        d['sell']['rule2'] = self.sell_r2
        d['sell']['operator'] = self.sell_op
        return d

class Chromosome(Rule):
    def __init__(self, d):
        super(Chromosome, self).__init__(d)

    def mutate(self):
        ch = self.get_dict()
        rule = choice(['buy', 'sell'])

        # Equal chances for all genes
        param = choice(['rule1', 'rule1', 'rule1',
                        'rule2', 'rule2', 'rule2',
                        'operator'])

        if param == 'operator':
            # Switch the logical operator
            old = ch[rule][param]
            ch[rule][param] = ('and' if old == 'or' else 'or')
        else:
            v = randint(1,3)
            old = ch[rule][param][v]
            if v == 3:
                # Switch the relational operator
                ch[rule][param][v] = ('<' if old == '>' else '>')
            else:
                # move 15% up or down
                new = 0.15*old * (1 if random()<0.5 else -1)
                ch[rule][param][v] += int(round(new))


        return Chromosome(ch)

    def crossover(self, mate):
        p1 = self.get_dict()
        p2 = mate.get_dict()
        cross = randint(1, 4)
        # b1 s1 b2 s2 (original)
        if cross == 1:
            # s2 s1 b2 b1
            p1['buy'], p2['sell'] = p2['sell'], p1['buy']
        elif cross == 2:
             # b1 b2 s1 s2
            p1['sell'], p2['buy'] = p2['buy'], p1['sell']
        elif cross == 3:
            p1['buy']['rule1'], p2['sell']['rule1'] = p2['sell']['rule1'], p1['buy']['rule1']
        elif cross == 4:
            p1['buy']['rule2'], p2['sell']['rule2'] = p2['sell']['rule2'], p1['buy']['rule2']
        return [ Chromosome(p1), Chromosome(p2) ]

class Population(object):
    def __init__(self, size=1500, crossover=0.6, elitism=0.01, mutation=0.01,
            imigration=0.3, tournament_size=50, debug=False):
        self._size = size
        self._crossover = crossover
        self._elitism = elitism
        self._mutation = mutation
        self._imigration = imigration
        self._tournament_size = tournament_size
        self._debug = debug
        self.improved = False

        self._fitness = [0.0] * size
        self._population = list()
        for i in range(size):
            self._population.append(Chromosome(Rule.gen_random()))

    def tournament_selection(self):
        # Returns the tournament winner
        best = randrange(self._size)
        for i in range(self._tournament_size-1):
            curr = randrange(self._size)
            if self._fitness[curr] > self._fitness[best]:
                best = curr
        return self._population(best)

    def select_parents(self):
        return self.tournament_selection(), self.tournament_selection()

    def evaluate(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("localhost", 6011))

        buf = list()
        prev_best = self._fitness[0]
        for ch in self._population:
            msg = ch.__str__() + '\n'
            s.send( msg.encode() )
            fitness = s.recv(5000)
            print fitness
            buf.append(fitness)
        s.close()
        self._fitness = buf

        # Sort itself
        self.sort()
        # Flag to check if there was improvement
        self.improved = buf[0] >  prev_best

    def sort(self):
        df = DataFrame({'chromo': self._population,
                        'fitness': self._fitness})
        df = df.sort_values('fitness', ascending=False)
        dic = df.to_dict(orient='list')

        self._population = dic['chromo']
        self._fitness = dic['fitness']

    def evolve(self):
        # Save the fittest individuals according to elitism rate
        idx = int(round(self._size * self._elitism))
        buf = self._population[:idx]
        buff = self._fitness[:idx]

        # Create random individuals according to imigration rate
        idx = int(round(self._size * self._imigration))
        for i in range(idx):
            buf.append(Chromosome(Rule.gen_random()))
        buff.extend([0.0] * idx)

        # Fill the remaining positions with possible new* chromosomes
        #   *new -> according to crossover and mutation rates
        idx = len(buf)
        while(idx < self._size):
            parent1, parent2 = self.select_parents()

            # Perform crossover according to crossover rate
            if random() < self._crossover:
                childs = parent1.crossover(parent2)
            else:
                childs = [parent1, parent2]

            # Mutate according to mutation rate
            for ch in childs:
                if random() < self._mutation:
                    ch = ch.mutate()
                buf.append(ch)
            idx +=2
            buff.extend([0.0, 0.0])

        # Save only the first 'self._size'
        # This is due to the possibility of having an extra chromosome in the
        # population
        self._population = buf[:self._size]
        self._fitness = buff[:self._size]

    def show_first(self):
        print self._population[0]
        print 'Fitness: %f' % (self._fitness[0])


def main():
    max_generations = 100
    max_not_improved = 10

    # Creating initial population
    pop = Population( size = 100,
            crossover = 0.6,
            mutation = 0.01,
            elitism = 0.01,
            imigration = 0.3,
            tournament_size = 50,
            debug = False)


    print pop._population[0]
    pop._population[0] = pop._population[0].mutate()
    print pop._population[0]
    pdb.set_trace()
    # Generations without improvements
    no_improvements = 0
    for i in range(max_generations):
        print 'Generation %d' % (i+1)

        print 'Calculating fitness'
        pop.evaluate()

        if pop.improved:
            no_improvements += 1
        else:
            no_improvements = 0

        if no_improvements == max_not_improved:
            break

        print 'Evolving'
        pop.evolve()
        print

    if no_improvements == max_not_improved:
        print '%d generations without improvement' % (max_not_improved)

    print 'Best solution:'
    pop.show_first()

if __name__ == '__main__':
    main()






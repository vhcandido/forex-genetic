#!/usr/bin/env python2

import socket
#import pdb

import matplotlib.pyplot as plt

from pandas import DataFrame
from random import choice, random, randint, randrange

class Rule(object):
    def __init__(self, d, is_list=False):
    #    self.rule = dict()
    #    self.rule = {
    #            'buy':
    #                {'rule1': list(),
    #                'rule2': list(),
    #                'log_op': 0},
    #            'sell':
    #                {'rule1': list(),
    #                'rule2': list(),
    #                'log_op': 0}
    #                }
        if not is_list:
            self.buy_r1 = d['buy']['rule1']
            self.buy_r2 = d['buy']['rule2']
            self.buy_op = d['buy']['log_op']

            self.sell_r1 = d['sell']['rule1']
            self.sell_r2 = d['sell']['rule2']
            self.sell_op = d['sell']['log_op']
        else:
            self.buy_r1 = d[:4]
            self.buy_r2 = d[4:8]
            self.buy_op = d[8]

            self.sell_r1 = d[9:13]
            self.sell_r2 = d[13:17]
            self.sell_op = d[17]



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
        d['buy']['log_op'] = choice(['and', 'or'])

        d['sell']['rule1'] = Rule.generic_rule('ema')
        d['sell']['rule2'] = Rule.generic_rule()
        d['sell']['log_op'] = choice(['and', 'or'])

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
            r.append(random())
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
        d['buy']['log_op'] = self.buy_op

        d['sell']['rule1'] = self.sell_r1
        d['sell']['rule2'] = self.sell_r2
        d['sell']['log_op'] = self.sell_op
        return d

    def get_list(self):
        l = list()
        l.extend(self.buy_r1)
        l.extend(self.buy_r2)
        l.append(self.buy_op)

        l.extend(self.sell_r1)
        l.extend(self.sell_r2)
        l.append(self.sell_op)
        return l

class Chromosome(Rule):
    def __init__(self, d, is_list=False):
        super(Chromosome, self).__init__(d=d, is_list=is_list)

    def mutate(self):
        ch = self.get_dict()

        rule = choice(['buy', 'sell'])

        # New parameters
        new = Rule.gen_random()

        # Choose mutation
        mut = randrange(2)
        # 0 - generate new rule
        # 1 - new parameters
        #   '-> logical operator - flip
        #   '-> relational operator - flip
        #   '-> technical indicator*
        #   '-> numerical parameters*
        # *: taken from new rule
        if mut == 0: # generate new rule
            ch[rule] = new[rule]
        elif mut == 1: # new parameters
            # Equal chances for all 9 genes
            param = choice(['rule1']*4 + ['rule2']*4 + ['log_op'])
            if param == 'log_op':
                # Switch the logical operator
                old = ch[rule][param]
                ch[rule][param] = ('and' if old == 'or' else 'or')
            else:
                # Choose 1 of 4 params
                v = randrange(4)
                old = ch[rule][param][v]
                if v == 3:
                    # Switch the relational operator
                    ch[rule][param][v] = ('<' if old == '>' else '>')
                else:
                    ch[rule][param][v] = new[rule][param][v]

        return Chromosome(ch), mut

    def crossover(self, mate):
        ch1 = self.get_list()
        ch2 = mate.get_list()

        cross = randrange(3)
        # 0 - one point
        # 1 - two point
        # 2 - linear combination (numerical) or choice (string)
        if cross == 0:
            p = randint(1, len(ch1)-1)
            ch1[p:], ch2[p:] = ch2[p:], ch1[p:]
        elif cross == 1:
            p1 = randrange(len(ch1))
            p2 = randrange(len(ch1))
            p1, p2 = min(p1,p2), max(p1,p2) # order to get list interval
            ch1[p1:p2], ch2[p1:p2] = ch2[p1:p2], ch1[p1:p2]
        elif cross == 2:
            for i in range(len(ch1)):
                if type(ch1[i]) is str: # apply to string
                    c = [ch1[i], ch2[i]]
                    ch1[i], ch2[i] = choice(c), choice(c)
                else: # apply to numerical
                    if type(ch1[i]) is int:
                        # Round to integer later
                        flag = True
                    a = random()
                    ch1[i], ch2[i] = a*ch1[i] + (1-a)*ch2[i],\
                                    a*ch2[i] + (1-a)*ch1[i]
                    if flag:
                        ch1[i] = int(round(ch1[i]))
                        ch2[i] = int(round(ch2[i]))

        return ([ Chromosome(ch1, True), Chromosome(ch2, True) ], cross)

class Population(object):
    def __init__(self, size=1500, crossover=0.6, elitism=0.01, mutation=0.01,
            imigration=0.3, tournament_size=50, port=6000, debug=False):
        self._size = size
        self._crossover = crossover
        self._elitism = elitism
        self._mutation = mutation
        self._imigration = imigration
        self._tournament_size = tournament_size
        self._port = port
        self._debug = debug
        self.improved = False

        self.best = list()
        self.iteration = 0
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
        return self._population[best]

    def select_parents(self):
        return self.tournament_selection(), self.tournament_selection()

    def evaluate(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("localhost", self._port))

        buf = list()
        prev_best = self._fitness[0]
        for ch in self._population:
            msg = ch.__str__() + '\n'
            s.send( msg.encode() )
            fitness = float(s.recv(5000))
            print fitness
            buf.append(fitness)
        s.close()
        self._fitness = buf

        # Sort itself
        self.sort()
        # Flag to check if there was improvement
        self.improved = self._fitness[0] >  prev_best
        if self._debug:
            print 'Best:', self._fitness[0]

        self.best.append(prev_best)
        self.iteration += 1

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
        if self._debug:
            print "\nElitism"
            print '\n'.join(i.__str__() for i in buf)
            print '==============================='

        # Create random individuals according to imigration rate
        ## If the convergence ratio is reached, then imigration rate is 50%
        ## '--> (best - worst)/worst
        ratio = (self._fitness[0] - self._fitness[-1]) / self._fitness[-1]
        if ratio <= 0.08:
            imig_rate = 0.5
        else:
            imig_rate = self._imigration
        idx = int(round(self._size * imig_rate))
        for i in range(idx):
            buf.append(Chromosome(Rule.gen_random()))
        buff.extend([0.0] * idx)
        if self._debug:
            print "\nImigration"
            print '\n'.join(i.__str__() for i in buf[-idx:])
            print '==============================='

        # Fill the remaining positions with possible new* chromosomes
        #   *new -> according to crossover and mutation rates
        idx = len(buf)
        while(idx < self._size):
            parent1, parent2 = self.select_parents()
            if self._debug:
                print '\nSelected ==============================='
                print parent1.__str__()
                print parent2.__str__()
                print '==============================='

            # Perform crossover according to crossover rate
            if random() < self._crossover:
                childs, x_type = parent1.crossover(parent2)
                if self._debug: print 'Crossover @ ', x_type
            else:
                childs = [parent1, parent2]

            # Mutate according to mutation rate
            for ch in childs:
                if random() < self._mutation:
                    ch, m_type = ch.mutate()
                    if self._debug: print 'Mutation @ ', str(m_type)
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

    def plot_evolution(self):
        x = range(self.iteration)
        plt.step(x, self.best)
        plt.savefig('fitness_evolution.png')



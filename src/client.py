#!/usr/bin/env python2

# +===========================================================================+
# | @author Victor Hugo Candido de Oliveira                                   |
# | 2016                                                                      |
# |                                                                           |
# | This is a simple Genetic Algorithm developed to optimize parameters of    |
# | trading rules based on Technical Analysis.                                |
# +===========================================================================+

from genetic import Population

def main():
    max_generations = 100
    max_not_improved = 10

    # Creating initial population
    pop = Population( size = 100,
            crossover = 0.4,
            mutation = 0.05,
            elitism = 0.05,
            imigration = 0.3,
            tournament_size = 10,
            debug = False)

    # Generations without improvements
    no_improvements = 0
    for i in range(max_generations):
        print 'Generation %d' % (i+1)

        print 'Calculating fitness'
        pop.evaluate()
        pop.plot_evolution()

        if not pop.improved:
            no_improvements += 1
            print "Didn't improve:", no_improvements
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






#!/usr/bin/env python

#TODO make
#Installing pygraphviz
#sudo apt-get install graphviz graphviz-dev pkg-config
#sudo pip install pygraphviz --install-option="--include-path=/usr/include/graphviz" --install-option="--library-path=/usr/lib/graphviz/"

import time
import argparse
import sys
import os
import pygraphviz as pgv


#TODO
#verbosity
#Date


def _setup_argparse():
    '''It prepares the command line argument parsing'''

    desc = ('This script creates a network graph given some items and their ' +
            'relationships')
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('-i','--input', dest='input_fpath',
                        help='input file path')
    parser.add_argument('-o','--output', dest='output_fpath',
                        help='output file path')
#    parser.add_argument('-t','--threshold', dest='threshold',
#                        help='threshold for relationship representation',
#                        default='0.0442')
    parser.add_argument('-v', '--verbose', dest='verbosity',
                        help='increase output verbosity', action='store_true')
    parser.add_argument('-r', '--ranges', dest='ranges',
                        help='', default='0:0.5:0.0442,0.0884,0.177,0.354')

    #TODO
    #Attributes file

    args = parser.parse_args()
    return args


def _get_options():
    '''It checks arguments values'''
    args = _setup_argparse()

    # Checking if input file exists
    if not args.input_fpath:
        raise IOError('Input file path must be provided.')
    if not os.path.isfile(args.input_fpath):
        raise IOError('Input file does not exist. Check path.')

    # Checking if output folder exists
    if not args.output_fpath:
        raise IOError('Output folder path must be provided.')
    if not os.path.isdir(args.output_fpath):
        raise IOError('Output folder does not exist. Check path.')

    # Checking if ranges are well formatted
    try:
        assert len(args.ranges.split(':')) == 3
    except:
        raise ValueError('Ranges should be introduced as "min:max:breakpoints"')

    return args


def file_parser(fpath):
    '''Parse input file

    #ItemA    ItemB    RelationValue
    A         B        0.5
    B         C        0.3
    A         C        0.2

    '''

    # Reading input file
    # EAFP - Easier to ask for forgiveness than permission.
    try:
        fhand = open(fpath, 'r')
    except:
        raise IOError('Unable to read input file. Check permissions.')

    relationships = {}
    for line_number, line in enumerate(fhand):
        # Skipping header
        if line.startswith('#'):
            continue

        line = line.strip()
        split_line = line.split()

        # Checking number of fields in input file
        try:
            assert len(split_line) > 2
        except:
            raise ValueError('At least two related entities are required. ' +
                             'Check file input at line number: "' +
                             str(line_number) + '".')
        if len(split_line) == 2:
            item_a, item_b = split_line
            weight = None
        elif len(split_line) == 3:
            item_a, item_b, weight = split_line

        # Skipping if it is the same item
        if item_a == item_b:
            continue

        # Populating relationships dictionary
        relationships.setdefault(item_a, {})
        relationships[item_a][item_b] = weight

    fhand.close()

    return relationships


def create_graph(relationships, ranges):
    '''Creates the network graph'''

    G = pgv.AGraph(relationships,
                   strict = False,
                   #directed = True,
                   overlap = False, # Avoid overlapping nodes
                   splines = True) # Curvy edges


    # Getting weight thresholds
#    if ranges:
#        minimum, maximum, breakpoints = ranges.split(':')
#        minimum = int(minimum)
#        maximum = int(maximum)
#        breakpoints_split = map(int, breakpoints.split(','))
#        if len(breakpoints_split) == 1:
#            limits = range(minimum, maximum + 1, breakpoints_split[0])
#        else:
#            limits = [minimum]
#            limits.extend(breakpoints_split)
#            limits.extend([maximum])
#        print limits
#    
#    
#        try:
#            assert minimum < maximum
#        except:
#            raise ValueError('Max limit must be higher than min limit')
#    
#        try:
#            for num in limits[1:-1]:
#                assert minimum < num < maximum
#        except:
#            raise ValueError('Breakpoints must be between max and min limits')
        



    for item_a, item_b in relationships.items():
        for item_b, weight in item_b.items():
            if not weight:
                break


            



            edge = G.get_edge(item_a, item_b)
            edge.attr['penwidth'] = float(weight)*10
            edge.attr['len'] = 1


#            edge.attr['color'] = 'green'



#    G.layout(prog = 'fdp')
#    G.layout(prog = 'dot')
    G.layout(prog = 'circo')

    return G


def get_time():
    return time.strftime("%Y-%m-%d")

def main():
    '''The main function'''

    # Parsing options
    options = _get_options()
    if options.verbosity:
        print '[START]: "' + get_time() + '"'
        print 'Options parsed: ' + str(options)

    # Parsing input file
    relationships = file_parser(options.input_fpath)
    if options.verbosity:
        print 'Relationships parsed: ' + str(relationships)
    
    # Creating graph
    G = create_graph(relationships, options.ranges)


    #TODO
    # Formatting graph
    #G = set_attributes(G, att)


    # Writing output
    # EAFP - Easier to ask for forgiveness than permission.
    try:
        G.draw('./file1.png')
    except:
        raise IOError('Unable to write output file. Check permissions.')

    if options.verbosity:
        print '[END]: "' + get_time() + '"'

if __name__ == '__main__':
    main()

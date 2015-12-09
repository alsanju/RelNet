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
import numpy as np
import logging as log
import colorsys

_EDGE_MIN_WIDTH = 1
_EDGE_MAX_WIDTH = 5


def _setup_argparse():
    '''It prepares the command line argument parsing'''

    desc = ('This script creates a network graph given some items and their ' +
            'relationships')
    parser = argparse.ArgumentParser(description=desc,
                        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-i','--input', dest='input_fpath', required=True,
                        help='input file path')
    parser.add_argument('-o','--output', dest='output_fpath',
                        default='./output.png', help='output file path')
    parser.add_argument('-t','--threshold', dest='threshold',
                        help='weight threshold for relationship representation',
                        default='0.0442')
    parser.add_argument('-v', '--verbose', dest='verbosity',
                        help='increase output verbosity', action='store_true')
    parser.add_argument('-c', '--color', dest='color',
                        help='colour edges depending on its weight',
                        action='store_true')
    parser.add_argument('-l', '--limits', dest='limits', type=str,
                        default='I:0:0.5:0.0442,0.0884,0.177,0.354',
                        help=('If weights of the relationships are provided,' +
                              ' those weights located between the same limits' + 
                              ' will be represented with the same format.' + 
                              ' Limits should be introduced as range' + 
                              ' ("R:min:max:step") or as breakpoints' + 
                              ' ("L:min:max:breakpoints"). e.g. "R:0:10:2"' +
                              ' returns "[0,2,4,6,8]" (maximum value is not' +
                              ' included) and "L:0:10:2,4,6,8" returns' +
                              ' "[0,2,4,6,8,10]"'))
    #TODO
    #Attributes file

    args = parser.parse_args()
    return args


def _get_options():
    '''It checks arguments values'''
    args = _setup_argparse()

    # Setting up logging system
    if args.verbosity:
        log.basicConfig(format="[%(levelname)s] %(message)s", level=log.DEBUG)
    else:
        log.basicConfig(format="[%(levelname)s] %(message)s", level=log.ERROR)

    # Checking if input file is provided
    if not os.path.isfile(args.input_fpath):
        raise IOError('Input file does not exist. Check path.')

    # Checking if output file is provided
    if os.path.isdir(args.output_fpath):
        raise IOError('Output file name must be provided.')
    if not os.path.isdir(os.path.dirname(args.output_fpath)):
        raise IOError('Output folder does not exist. Check path.')

    # Checking if ranges are well formatted
    try:
        split_ranges = args.limits.split(':')
        assert (len(split_ranges) == 4 and
                (split_ranges[0] == 'I' or split_ranges[0] == 'R'))
    except:
        raise ValueError('Limits should be introduced as "R:min:max:step" or ' +
                         '"L:min:max:breakpoints". e.g. "R:0:10:1" or ' + 
                         '"L:0:10:2,4,6,8". See help.')

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


def _filter_by_weight(relationships, threshold):
    '''Filter relationship dict by weight threshold'''
    for item_a, item_b in relationships.items():
        for item_b, weight in item_b.items():
            if weight:
                if weight < threshold:
                    relationships[item_a].pop(item_b)
    for key in relationships.keys():
        if not relationships[key]:
            relationships.pop(key)
    log.debug('Relationships filtered by threshold: "' +
              str(relationships) + '"')
    return relationships


def parse_limits(limits):
    '''XXX'''

    kind, minimum, maximum, breakpoints = limits.split(':')
    minimum = float(minimum)
    maximum = float(maximum)
    breakpoints_split = map(float, breakpoints.split(','))

    try:
        assert minimum < maximum
    except:
        raise ValueError('Max limit must be higher than min limit')

    if kind == 'R':
        try:
            assert breakpoints_split[0] < (maximum - minimum)
        except:
            raise ValueError('Step must be lower than (max_limit - min_limit)')

    if kind == 'I':
        try:
            for num in breakpoints_split:
                assert minimum < num < maximum
        except:
            raise ValueError('Breakpoints must be between max and min limits')

    # Getting ranges
    if kind == 'R':
        limits = list(np.unique(np.arange(minimum, maximum,
                                          breakpoints_split[0])))
    elif kind == 'I':
        limits = list(np.unique([minimum] + breakpoints_split + [maximum]))

    return limits


def pseudocolor(val, minval=_EDGE_MIN_WIDTH, maxval=_EDGE_MAX_WIDTH):
    '''Given a range and a value, a color between red..yellow..green is returned
[NOTE]: stackoverflow.com/questions/10901085/range-values-to-pseudocolor'''
    # convert val in range minval..maxval to the range 0..120 degrees which
    # correspond to the colors red..green in the HSV colorspace
    h = (float(val-minval) / (maxval-minval)) * 120
    # convert hsv color (h,1,1) to its rgb equivalent
    # [NOTE]: hsv_to_rgb() function expects h to be 0..1 not 0..360
    r, g, b = colorsys.hsv_to_rgb(h/360, 1., 1.)
    # returning RGB in range 0..255
    rgb_hex = '#%02x%02x%02x' % (r*255, g*255, b*255)
    return rgb_hex


def create_graph(relationships, limits, color):
    '''Creates the network graph'''

    # Setting up graph format
    G = pgv.AGraph(relationships,
                   strict = False,
                   #directed = True,
                   overlap = False, # Avoid overlapping nodes
                   splines = True) # Curvy edges

    # Getting weight thresholds to set up edges thickness
    if limits:
        limits = np.array(parse_limits(limits))
        log.debug('Limits provided: "' + str(list(limits)) + '"')

        # Getting midpoints of limits intervals
        midpoints = (np.array(limits[1:]) + np.array(limits[:-1])) / 2
        log.debug('Limits midpoints: "' + str(list(midpoints)) + '"')

    # Creating relationships
    for item_a, item_b in relationships.items():
        for item_b, weight in item_b.items():
            if weight:
                edge = G.get_edge(item_a, item_b)

                # Getting the nearest midpoint
                index = (np.abs(midpoints-float(weight))).argmin()

                edge_width = np.linspace(_EDGE_MIN_WIDTH, _EDGE_MAX_WIDTH,
                                         num=len(midpoints),
                                         endpoint=True)[index]

                log.debug('Edge info: [item_a: "' + item_a +
                          '", item_b: "' + item_b +
                          '", weight: "' + weight + 
                          '", interval: "' + str(index) +
                          '", edge_width: "' + str(edge_width) + '"]')

                # Formatting edge
                edge.attr['penwidth'] = edge_width
                edge.attr['label'] = weight
                edge.attr['len'] = 1

                if color:
                    edge.attr['color'] = pseudocolor(edge_width)


#    G.layout(prog = 'fdp')
    G.layout(prog = 'dot')
#    G.layout(prog = 'circo')

    return G


def get_time():
    return time.strftime("%Y-%m-%d")


def main():
    '''The main function'''

    # Parsing options
    options = _get_options()
    if options.verbosity:
        log.info('START "' + get_time() + '"')
#        print 'Options parsed: ' + str(options)
        log.debug('Options parsed: "' + str(options) + '"')

    # Parsing input file
    relationships = file_parser(options.input_fpath)
    if options.verbosity:
        log.debug('Relationships parsed: "' + str(relationships) + '"')
    

    # Applying threshold if necessary
    relationships = _filter_by_weight(relationships, options.threshold)

    # Creating graph
    G = create_graph(relationships, options.limits, options.color)


    #TODO
    # Formatting graph
    #G = set_attributes(G, att)


    # Writing output
    # EAFP - Easier to ask for forgiveness than permission.
    try:
        if options.output_fpath.endswith('.png'):
            G.draw(options.output_fpath)
        else:
            G.draw(options.output_fpath + '.png')
    except:
        raise IOError('Unable to write output file. Check permissions.')

    if options.verbosity:
        log.info('END "' + get_time() + '"')


if __name__ == '__main__':
    main()

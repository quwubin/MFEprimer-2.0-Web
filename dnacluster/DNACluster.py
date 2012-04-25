#!/usr/bin/env python
# -*- coding:utf-8 -*-
from __future__ import division
'''Cluster DNA sequences by k-mer based method


by Wubin Qu <quwubin@gmail.com>,
Copyright @ 2010, All Rights Reserved.
'''

Author  = 'Wubin Qu, Yang Zhou & Chenggang Zhang <zhangcg@bmi.ac.cn>'
Date    = 'Apr-03-2011 22:46:09'
Version = '1.0'

import sys
import os
import argparse
from lib import KMer
from lib import FastaFormatParser
import operator

parser = argparse.ArgumentParser(description='Descriptions about the script.')
parser.add_argument('-i', '--infile', nargs='?', type=argparse.FileType('r'),
		    default=sys.stdin, help='Input file to be processed')
parser.add_argument('-o', '--outfile', nargs='?', type=argparse.FileType('w'),
		    default=sys.stdout, help='Output file name for storing the results')
parser.add_argument('-c', '--identity', nargs='?', type=int,
		    default=80, help='Identity cutoff value for clustering the sequences')
parser.add_argument('-k', nargs='?', type=int,
		    default=6, help='Default = 6, k-mer')
parser.add_argument('-v', '--version', action='version', version='%(prog)s 1.0')
args = parser.parse_args()

def find_cluster(seq_records, group=[]):
    '''Find clusters'''
    seed = seq_records.pop(0)
    seed_plus, seed_minus = KMer.kmer_occur(seed['seq'], k=args.k, step=1)
    #print 'Seed size:', seed['id'], seed['size']
    # Seed only use plus strand as reference
    group.append([[seed['id'], '+']])
    ungrouped = []
    for i, seq_record in enumerate(seq_records):
        seq = seq_record['seq']
        if 'plus' in seq_record and 'minus' in seq_record: 
            plus = seq_record['plus']
            minus = seq_record['minus']
        else:
            plus, minus = KMer.kmer_occur(seq, k=args.k, step=args.k)

        plus_identity = seed_plus & plus
        minus_identity = seed_plus & minus
        if len(plus_identity) > len(minus_identity):
            identity = len(plus_identity) * 6 / seq_record['size'] * 100
            strand = '+'
        else:
            identity = len(minus_identity) * 6 / seq_record['size'] * 100
            strand = '-'

        #print '\t', seq_record['id'], seq_record['size'], identity, len(plus_identity)*args.k, len(minus_identity)*args.k, strand
        if identity > args.identity:
            #group[-1].append([seq_record['id'], strand, identity])
            group[-1].append([seq_record['id'], strand])
        else:
            seq_record['plus'] = plus
            seq_record['minus'] = minus
            ungrouped.append(seq_record)

    if len(ungrouped) > 0:
        group = find_cluster(ungrouped, group=group)
        return group
    else:
        return group

def print_group(groups):
    '''Print out the group'''
    args.outfile.write('# %s V%s [%s]%s' % (os.path.splitext(os.path.basename(sys.argv[0]))[0], Version, Date, os.linesep))
    args.outfile.write('# Authors: %s%s' % (Author, os.linesep))
    args.outfile.write('# %s clusters%s' % (len(groups), os.linesep*2))

    for i, group in enumerate(groups):
	args.outfile.write('Cluster %s (%s): %s%s' % (i+1, len(group), ', '.join(['%s (%s)' % (id, strand) for id, strand in group]), os.linesep))

    args.outfile.write(os.linesep)

def cluster(fh):
    '''Cluster as a function'''
    unsorted_seq_records = FastaFormatParser.parse(fh)
    seq_records = sorted(unsorted_seq_records, key=operator.itemgetter('size'), reverse=True)
    groups = find_cluster(seq_records)
    return groups

def main ():
    '''Main'''
    groups = cluster(args.infile)
    print_group(groups)

if __name__ == '__main__':
    main()


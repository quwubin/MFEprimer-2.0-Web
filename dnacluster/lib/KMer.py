#!/usr/bin/env python
'''K-mer occurance calculation'''

Author = 'Wubin Qu <quwubin@gmail.com>'

import sys

D2n_dic = dict(A=0, T=3, C=2, G=1, a=0, t=3, c=2, g=1)
n2D_dic = {0:'A', 3:'T', 2:'C', 1:'G', 0:'a', 3:'t', 2:'c', 1:'g'}

def baseN(num, b):
    '''convert non-negative decimal integer n to equivalent in another base b (2-36)'''
    return ((num == 0) and  '0' ) or ( baseN(num // b, b).lstrip('0') + "0123456789abcdefghijklmnopqrstuvwxyz"[num % b])

def int2DNA(num, k):
    seq = baseN(num, 4)
    return 'A' * (k-len(seq)) + (''.join([n2D_dic[int(base)] for base in seq]))

def DNA2int_2(seq):
    '''convert a sub-sequence/seq to a non-negative integer'''
    plus_mer = 0
    minus_mer = 0
    length = len(seq) - 1 
    for i, letter in enumerate(seq):
        plus_mer += D2n_dic[letter] * 4 ** (length - i)
        minus_mer += (3 - D2n_dic[letter]) * 4 ** i

    return plus_mer, minus_mer

def DNA2int(seq):
    '''convert a sub-sequence/seq to a non-negative integer'''
    plus_mer = 0
    length = len(seq) - 1 
    for i, letter in enumerate(seq):
        plus_mer += D2n_dic[letter] * 4 ** (length - i)

    return plus_mer

def kmer_occur(seq, k=6, step=1):
    ''''''
    if step > k:
        print >> sys.stderr, 'step can not be greater than k'
        exit()

    plus_mer_list = []
    minus_mer_list = []

    fasta_seq = seq
    fasta_seq_length = len(fasta_seq)
    for i in xrange(0, fasta_seq_length - k + 1, step):
        if i < 1:
            temp_seq = fasta_seq[:k] # The first k bases
        else:
            temp_seq = fasta_seq[i:i+k]

        try:
            plus_mer_id, minus_mer_id = DNA2int_2(temp_seq)
        except:
            #print 'Unrecognized base: %s' % fasta_seq[i+k]
            # Skip the unrecognized base, such as 'N'
            continue

        plus_mer_list.append(plus_mer_id)
        minus_mer_list.append(minus_mer_id)

    #plus = list(set(plus_mer_list))
    #minus = list(set(minus_mer_list))
    plus = set(plus_mer_list)
    minus = set(minus_mer_list)
    return plus, minus 

def main ():
    '''main'''
    seq = 'AAAAATTTTTCCCCGGGGAA'
    print len(seq)
    print seq
    plus, minus = kmer_occur(seq, k=6, step=6)

if __name__ == '__main__':
    main()

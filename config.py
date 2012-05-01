#!/usr/bin/env python

# Python path
#  Mainly for batch mode
python_path = "/home/zhangcg/local/python/bin/python"

# For program test
DEBUG = True

# Session parrent directory for storing temp files
session_parent = 'session'

# Histogram settings
# When amplicons number > 10, output the histogram
hist_cutoff = 10
size_hist = {
	0 : 0,
	100 : 0,
	250 : 0,
	500 : 0,
	750 : 0,
	1000 : 0,
	2000 : 0,
	}

tm_hist = {
	0 : 0,
	10 : 0,
	20 : 0,
	30 : 0,
	40 : 0,
	50 : 0,
	60 : 0,
	70 : 0,
	80 : 0,
	}

dg_hist = {
	0 : 0,
	-5 : 0,
	-10 : 0,
	-15 : 0,
	-20 : 0,
	-25 : 0,
	-30 : 0,
	-35 : 0,
	}

# MFEprimerDB path
MFEprimerDB = 'MFEprimerDB'
MFEprimerDB_k_value = 9 # Should be identical to the k value when indexing the database

# The Citation (You may cite this paper if MFEprimer helps you)
Citation = 'Wubin Qu, Zhiyong Shen, Dongsheng Zhao, Yi Yang and Chenggang Zhang. (2009) MFEprimer: multiple factor evaluation of the specificity of PCR primers. Bioinformatics, 25(2), 276-278.'

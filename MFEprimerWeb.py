#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    MFEprimer-2.0

    :copyright: (c) 2011-2012 by Wubin Qu.
    :license: Please contact Wubin Qu <quwubin@gmail.com>.
"""
import time
import os
import sys
import re
import subprocess
from operator import itemgetter
import hashlib
import platform
from datetime import datetime
from flask import Flask, request, session, url_for, redirect, \
	render_template, abort, g, flash, send_from_directory

from chilli import FastaFormatParser
from chilli import Seq, TmDeltaG
from chilli import SeqCheck
from chilli import ve
from chilli import chilli
from mfeprimer import MFEprimer
from dnacluster import DNACluster
import uuid
import config
from config import DEBUG, MFEprimerDB, \
	size_hist, tm_hist, dg_hist, hist_cutoff, \
	session_parent, Citation

src_path = os.path.split(os.path.realpath(sys.argv[0]))[0]
bin_path = os.path.join(src_path, 'bin', platform.architecture()[0])

# configuration
SECRET_KEY = '4d98f55b-8adb-4b54-83c8-a41cdeca00c1'

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)
app.debug = config.DEBUG

def format_species_name(species):
    fields = species.split('_')
    if len(fields) > 1:
	return '<em>%s. %s</em>' % (fields[0][0].upper(), '_'.join(fields[1:]))
    else:
	return species.capitalize()

def capitalize_species_name(species):
    fields = species.split('_')
    if len(fields) > 1:
	return '%s. %s' % (fields[0][0].upper(), '_'.join(fields[1:]))
    else:
	return species.capitalize()

app.jinja_env.filters['format_species_name'] = format_species_name
app.jinja_env.filters['capitalize_species_name'] = capitalize_species_name

def format_datetime(timestamp):
    """Format a timestamp for display."""
    return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d @ %H:%M')

def get_current_date():
    """Format the current date for display."""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

@app.before_request
def before_request():
    """
    """
    session.permanent = True
    mtime = os.path.getmtime(sys.argv[0])
    g.date = time.strftime('%b %d, %Y', time.localtime(mtime))
    g.db_dict = {}
    g.db_name_dict = {}
    type_dict = {}
    for root, dirs, files in os.walk(MFEprimerDB):
	for file in files:
	    if file.endswith('db'):
		fields = file.split('.')
		type = fields[-3]
		if type == 'genomic':
		    type = type.capitalize()
		else:
		    type = type.upper()

		type_dict[type] = True

		species = '.'.join(fields[:-3]).capitalize()
		name = '.'.join(fields[:-2])
                g.db_name_dict[name.lower()] = name
		if species not in g.db_dict:
		    g.db_dict[species] = []

		g.db_dict[species].append({
		    'type': type,
		    'species': species,
		    'name' : name,
		    })

    g.db_list = g.db_dict.items()
    g.db_list.sort(key=itemgetter(0))
    g.db_type_list = type_dict.keys()
    g.db_type_list.sort()


@app.teardown_request
def teardown_request(exception):
    """At the end of the request."""
    pass

@app.route('/')
def root():
    """
    The root homepage.
    """
    error = None
    return render_template('index.html', error=error)

@app.route('/batch')
def batch():
    """Batch mode index"""
    error = None
    return render_template('batch.html', error = error)

@app.route('/batch_mode', methods=['GET', 'POST'])
def batch_mode():
    """batch mode"""
    error = None
    session_dir = chilli.session(session_parent)
    if request.method == 'POST':
        species_list = request.form.getlist('db_selected')
	if len(species_list) == 0:
	    error = 'Need select database first'
	    return render_template('batch.html', error = error)

        db_type_list = [db_type.lower() for db_type in request.form['db_type'].split(':')]

	session['db_type'] = request.form['db_type']
	session['species_list'] = species_list

        db_list = []
        for species in species_list:
            for db_type in db_type_list:
                db = '%s.%s' % (species, db_type)
		db = db.lower()
                if db in g.db_name_dict:
                    full_db = os.path.join(MFEprimerDB, g.db_name_dict[db])
		    db_list.append(full_db)

        db_list.sort()

	infile = os.path.join(session_dir, 'query.fa')
	upload_seq = ''
        if request.files.has_key('upload_seq'):
            upload_seq = request.files['upload_seq'].read()

	fasta_seq = ''
        if request.form.has_key('fasta_seq'):
            fasta_seq = request.form['fasta_seq']
	
	if upload_seq:
	    seq = upload_seq
	elif fasta_seq:
	    seq = fasta_seq
	else:
	    error = 'Need two or more primer sequences in fasta-format'
	    return render_template('batch.html', error = error)

        fh = open(infile, 'w')
	for line in seq.splitlines():
	    line = line.strip()
	    if line.startswith('>'):
		fh.write("%s\n" % line)
		continue

	    line = re.sub('^[^a-zA-Z]+|[^a-zA-Z]+$', '', line)
	    line = re.sub('\s', '', line)

	    fh.write("%s\n" % line)

        fh.close()
	    

	if len(open(infile).read()) == 0:
	    error = 'Need two or more primer sequences in fasta-format'
	    return render_template('batch.html', error = error)

	error_or_degenerate = SeqCheck.fasta_format_check(open(infile), err_path='here')
	if error_or_degenerate in ['yes', 'no']:
	    degenerate = error_or_degenerate
	else:
	    return render_template('batch.html', error=error_or_degenerate)


	Tm_upper_limit = float(request.form['Tm_upper_limit'])
	Tm_lower_limit = float(request.form['Tm_lower_limit'])

	size_upper_limit = int(request.form['size_upper_limit'])
	size_lower_limit = int(request.form['size_lower_limit'])

	if size_lower_limit < 0 or size_upper_limit > 100000:
	    error = 'Size range should be in [0, 100000]'
	    return render_template('batch.html', error = error)

	ppc_lower_limit = float(request.form['ppc_lower_limit'])
	if ppc_lower_limit < 0 or ppc_lower_limit > 100:
	    error = 'PPC lower cutoff should in (0, 100)'
	    return render_template('batch.html', error = error)

	mv = float(request.form['mono_conc'])
	dv = float(request.form['diva_conc'])
	dntp = float(request.form['dntp_conc'])
	oligo = float(request.form['oligo_conc'])


	options = OptionCreator(db_list, 
		infile,
		Tm_upper_limit,
		Tm_lower_limit,
		size_upper_limit,
		size_lower_limit,
		ppc_lower_limit,
		mv,
		dv,
		dntp,
		oligo,
		degenerate,
		)

	start_time = time.time()
        session_key = os.path.basename(session_dir)
        args = ['database', 'infile', 'dg_stop', 'dg_start', 'tm_stop', 'tm_start', 'size_stop', 'size_start', 'ppc', 'mono_conc', 'diva_conc', 'dntp_conc', 'oligo_conc', 'degenerate', 'k_value']
        job_file = create_jobs(options, args, session_key)
	return render_template('results_notice.html', session_key=session_key, job_file=job_file + '.zip', status='Submitted')

    return redirect(url_for('batch'))

@app.route('/download/<session_key>/<filename>', methods=['GET', 'POST'])
def download(filename=None, session_key=None):
    return send_from_directory(os.path.join(session_parent, session_key), filename, as_attachment=True, attachment_filename=filename.encode('utf-8'))

@app.route('/show_img/<filename>', methods=['GET', 'POST'])
def show_img(filename=None):
    return send_from_directory('show_img', filename, as_attachment=True, attachment_filename=filename.encode('utf-8'))

@app.route('/refresh', methods=['GET', 'POST'])
def refresh():
    """Refresh for batch mode"""
    error = None
    if request.method == 'POST':
	session_key = request.form['session_key']
	job_file = request.form['job_file']
        status = check_status(session_key, job_file)
	return render_template('results_notice.html', session_key=session_key, job_file=job_file, status=status)

    return redirect(url_for('batch'))


@app.route('/single_mode', methods=['GET', 'POST'])
def single_mode():
    """Single mode"""
    error = None
    session_dir = chilli.session(session_parent)

    if request.method == 'POST':
	database = request.form['db_selected']
	db_list = [os.path.join(MFEprimerDB, db) for db in database.split(':')]

	infile = os.path.join(session_dir, 'query.fa')
	fh = open(infile, 'w')
	seq_sn = 1
        seq_list = []
	while request.form.has_key("seq%d" % seq_sn):
	    seq = request.form["seq%d" % seq_sn]
	    seq = re.sub('^[^a-zA-Z]+|[^a-zA-Z]+$', '', seq) # Remove additional chars, such as 5'- 3'- 
	    seq = re.sub('\s', '', seq) # Remove spaces in sequence. Thanks anonymous reviewers.
	    if seq:
		seq_list.append(seq)
		fh.write(">Seq%s\n%s\n" % (seq_sn, seq))

	    seq_sn += 1

        fh.close()

	if len(seq_list) < 2:
	    error = 'Need two or more primer sequences'
	    return render_template('index.html', error=error)

	error_or_degenerate = SeqCheck.fasta_format_check(open(infile), err_path='here')
	if error_or_degenerate in ['yes', 'no']:
	    degenerate = error_or_degenerate
	else:
	    return render_template('index.html', error=error_or_degenerate)


	Tm_upper_limit = float(request.form['Tm_upper_limit'])
	Tm_lower_limit = float(request.form['Tm_lower_limit'])

	size_upper_limit = int(request.form['size_upper_limit'])
	size_lower_limit = int(request.form['size_lower_limit'])

	if size_lower_limit < 0 or size_upper_limit > 100000:
	    error = 'Size range should be in [0, 100000]'
	    return render_template('index.html', error=error)

	ppc_lower_limit = float(request.form['ppc_lower_limit'])
	if ppc_lower_limit < 0 or ppc_lower_limit > 100:
	    error = 'PPC lower cutoff should be in (0, 100)'
	    return render_template('index.html', error=error)

	mv = float(request.form['mono_conc'])
	dv = float(request.form['diva_conc'])
	dntp = float(request.form['dntp_conc'])
	oligo = float(request.form['oligo_conc'])

	session['db_selected'] = ':'.join([os.path.basename(str(db)) for db in db_list])

	options = OptionCreator(db_list, 
		infile,
		Tm_upper_limit,
		Tm_lower_limit,
		size_upper_limit,
		size_lower_limit,
		ppc_lower_limit,
		mv,
		dv,
		dntp,
		oligo,
		degenerate,
		)

	start_time = time.time()
        amp_list, oligos = MFEprimer.process_primer(options, session_dir)
        detail, size_dict, tm_dict, dg_dict = format_output_primer(amp_list, oligos, options, start_time, session_dir)
	if len(detail) > hist_cutoff:
	    size_hist_keys = size_hist.keys()
	    size_hist_keys.sort(reverse=True)
	    for size, num in size_dict.items():
		for hist_key in size_hist_keys:
		    if int(size) > hist_key:
			break

		size_hist[hist_key] += num

	    tm_hist_keys = tm_hist.keys()
	    tm_hist_keys.sort(reverse=True)
	    for tm, num in tm_dict.items():
		for hist_key in tm_hist_keys:
		    if float(tm) > hist_key:
			break

		tm_hist[hist_key] += num

	    dg_hist_keys = dg_hist.keys()
	    dg_hist_keys.sort(reverse=False)
	    for dg, num in dg_dict.items():
		for hist_key in dg_hist_keys:
		    if float(dg) < float(hist_key):
			break

		dg_hist[hist_key] += num

	new_dg_hist = {}
	for key, value in dg_hist.items():
	    new_dg_hist[str(key)] = value

        database = ', '.join([os.path.basename(db).capitalize() for db in options.database])
        oligos = format_oligos(oligos, options)
        elapsed_time = time.time() - start_time
	if elapsed_time < 1:
	    print_elapsed_time = '%.2f s' % elapsed_time
	else:
	    print_elapsed_time = '%s m %s s' % chilli.seconds2min_sec(int(elapsed_time))

	return render_template('primer_output.html', options=options, database=database, 
		oligos=oligos, amp_num=len(amp_list), time_used=print_elapsed_time, 
		date=chilli.format_show_time(), citation=Citation, detail=detail, 
		session_dir=session_dir, size_hist=size_hist, tm_hist=tm_hist, dg_hist=new_dg_hist, 
		max_size_num = max([num for num in size_hist.values()]),
		max_tm_num = max([num for num in tm_hist.values()]),
		max_dg_num = max([num for num in dg_hist.values()]),
		)

    return redirect(url_for('root'))


class OptionCreator:
    '''Option'''
    def __init__(self,
	    db_list,
	    infile,
	    Tm_upper_limit,
	    Tm_lower_limit,
	    size_upper_limit,
	    size_lower_limit,
	    ppc_lower_limit,
	    mv,
	    dv,
	    dntp,
	    oligo,
	    degenerate,
	    ):
	self.database = [str(db) for db in db_list]
        self.infile = infile
	self.dg_stop = 0
	self.dg_start = -9.0
	self.tm_stop = Tm_upper_limit
	self.tm_start = Tm_lower_limit
	self.size_stop = size_upper_limit
	self.size_start = size_lower_limit
	self.ppc = ppc_lower_limit
	self.mono_conc = mv
	self.diva_conc = dv
	self.dntp_conc = dntp
	self.oligo_conc = oligo
	self.degenerate = degenerate
	self.amplicon = False
	self.mv = mv
	self.dv = dv
	self.dntp = dntp
	self.oligo = oligo
	self.k_value = config.MFEprimerDB_k_value

	session['tm_start'] = self.tm_start
	session['tm_stop'] = self.tm_stop
	session['size_start'] = self.size_start
	session['size_stop'] = self.size_stop
	session['ppc'] = self.ppc
	session['mv'] = self.mono_conc
	session['dv'] = self.diva_conc
	session['dntp'] = self.dntp_conc
	session['oligo'] = self.oligo_conc

def format_output_primer(amp_list, oligos, options, start_time, session_dir):
    '''Format output in primer task'''
    linesep = os.linesep
    detail = []
    #fa_file = []

    ID_list = []
    for i in xrange(len(oligos)):
        ID_list.append(oligos[i]['id'])

    size_dict = {}
    dg_dict = {}
    tm_dict = {}
    sn = 0
    amp_list.sort(key=itemgetter(1, 2), reverse=True)
    for ave_Tm, ppc, amp_len, amp in amp_list:
        sn = sn + 1
        hid = amp['real_hid']
        try:
            acc = hid.split('|')[3]
        except:
            acc = hid
        desc = '%s: %s' % (sn, hid)

        amp_len = amp['size']

        p_qid = amp['pid']
        f_len = amp['plen']
        pseq = amp['pseq']
        f_3_pos = amp['f3_pos'] 
        #p_3_DeltaG = amp['p_3_DeltaG']
        p_3_DeltaG = '%.1f' % amp['p_3_DeltaG']
        p_qseq = amp['p_qseq']
        p_aseq = amp['p_aseq']
        p_sseq = amp['p_sseq']
        p_tail = amp['p_tail']
        #p_Tm = amp['p_Tm']
        p_Tm = '%.1f' % amp['p_Tm']
        #p_DeltaG = amp['p_DeltaG']
        p_DeltaG = '%.1f' % amp['p_DeltaG']
        p_sb = f_3_pos - len(pseq) + 1

        m_qid = amp['mid']
        r_len = amp['mlen']
        mseq = amp['mseq']
        r_3_pos = amp['r3_pos']
        #m_3_DeltaG = amp['m_3_DeltaG']
        m_3_DeltaG = '%.1f' % amp['m_3_DeltaG']
        m_qseq = amp['m_qseq']
        m_aseq = amp['m_aseq']
        m_sseq = amp['m_sseq']
        m_tail = amp['m_tail']
        #m_Tm = amp['m_Tm']
        m_Tm = '%.1f' % amp['m_Tm']
        #m_DeltaG = amp['m_DeltaG']
        m_DeltaG = '%.1f' % amp['m_DeltaG']
        m_se = r_3_pos + len(mseq)

        amp_graphic = amp['amp_graphic']
        mid_seq = amp['mid_seq']
        real_hid = amp['real_hid']
        hdesc = amp['hdesc']

        amp_seq = p_tail + p_qseq + mid_seq + m_qseq + m_tail
        amp_GC = '%.1f' % chilli.cal_GC_content(amp_seq, + amp_len)

        if len(desc) > 42:
            desc = desc[:42] + '...' 

        if p_qid == m_qid:
            ppc = '-%.1f' % ppc
        else:
            ppc = '%.1f' % ppc


        if not hdesc:
            amp_title = '%s: %s + %s ==> %s' % (sn, p_qid, m_qid, hid)
            fa_desc = '>Amp_%s %s + %s ==> %s' % (sn, p_qid, m_qid, hid)
        else:
            amp_title = '%s: %s + %s ==> %s %s' % (sn, p_qid, m_qid, hid, hdesc)
            fa_desc = '>Amp_%s %s + %s ==> %s %s' % (sn, p_qid, m_qid, hid, hdesc)

        fa_seq = chilli.print_seq(amp_seq, 80)
        fa_seq = fa_desc + linesep + fa_seq + linesep
        #fa_file.append(fa_desc)
        #fa_file.append(fa_seq)
	size_dict[amp_len] = size_dict.setdefault(amp_len, 0) + 1
	tm_dict[p_Tm] = tm_dict.setdefault(p_Tm, 0) + 1
	tm_dict[m_Tm] = tm_dict.setdefault(m_Tm, 0) + 1

	dg_dict[p_DeltaG] = dg_dict.setdefault(p_DeltaG, 0) + 1
	dg_dict[m_DeltaG] = dg_dict.setdefault(m_DeltaG, 0) + 1
	
	detail.append((sn, acc, p_qid, m_qid, amp_len, ppc, p_Tm, m_Tm, p_DeltaG, m_DeltaG, p_3_DeltaG, m_3_DeltaG, amp_GC, p_sb, len(p_aseq), f_len, m_se, len(m_aseq), r_len, amp_graphic, fa_seq, hid, hdesc))

    return detail, size_dict, tm_dict, dg_dict

def format_oligos(oligos, options):
    '''for output'''
    oligo_list = []
    for oligo in oligos:
	id = oligo['id']
	seq = oligo['seq'].upper()
	size = oligo['size']
        GC = chilli.cal_GC_content(seq, size)
	Tm = TmDeltaG.calTm(seq, Seq.complement(seq), mono_conc=options.mono_conc, diva_conc=options.diva_conc, dntp_conc=options.dntp_conc, oligo_conc=options.oligo_conc)
        GC = '%.1f' % GC
        Tm = '%.1f' % Tm
        oligo_list.append((id, seq, size, GC, Tm))

    return oligo_list

def create_jobs(options, args, session_key):
    '''Create jobs for batch running'''
    args = ['database', 'infile', 'dg_stop', 'dg_start', 'tm_stop', 'tm_start', 'size_stop', 'size_start', 'ppc', 'mono_conc', 'diva_conc', 'dntp_conc', 'oligo_conc', 'k_value']
    current_date = datetime.now().strftime('%Y-%m-%d_%H_%M_%S')
    job_file = 'MFEprimer-2.0-Result-%s.txt' % (current_date)
    fh = open(os.path.join('batch_jobs', job_file), 'w')
    fh.write('%s: %s%s' % ('session_key', session_key, os.linesep))
    for arg in args:
	tmp_str = 'options.%s' % arg
	if arg == 'database':
	    fh.write('%s: %s%s' % (arg, ' '.join(eval(tmp_str)), os.linesep))
	else:
	    fh.write('%s: %s%s' % (arg, eval(tmp_str), os.linesep))

    fh.close()
    return job_file

def check_status(session_key, job_file):
    '''Check the status'''
    job_lock = 'batch_jobs/job.lock'
    if os.path.isfile(job_lock):
	running_job = open(job_lock, 'r').read().strip()
    else:
	running_job = False

    if os.path.isfile(os.path.join(session_parent, session_key, job_file)):
	if running_job and running_job == session_key:
	    status = 'Running'
	else:
	    status = 'Finished'
    else:
	if running_job and running_job == session_key:
	    status = 'Running'
	else:
	    status = 'In Queue'
    
    return status

@app.route('/virtual_electrophoresis', methods=['GET', 'POST'])
def virtual_electrophoresis():
    error = None
    session_dir = chilli.session(session_parent)
    if request.method == 'POST':
	size_list_str = request.form['size_list']
	size_list = []
	try:
	    for size in [size for size in re.split('[^\d]', size_list_str)]:
		if size:
		    size_list.append(size)
	except:
	    error = 'Error: Wrong size list format'
	    return render_template('elec_index.html', error=error)

	gel_conc = float(request.form['gel_conc'])
	filename = chilli.random_string(12) + '.png'
	pic_path = os.path.join('show_img', filename)

        if len(size_list) == 0:
            error = 'Please input size list for Virtual Electrophresis'
	    return render_template('elec_index.html', error=error)
        else:
	    error = ve.paint(size_list, gel_conc, pic_path)
	    if error:
		return render_template('elec_index.html', error=error)

	    return render_template('ve.html', filename=filename)

    return render_template('elec_index.html', error=error)


@app.route('/virtual_e', methods=['GET', 'POST'])
def virtual_e():
    """Virtual Electrophoresis"""
    error = None
    if request.method == 'POST':
        amp_num, session_dir = request.form['amp_num'].split(':')
	filename = chilli.random_string(12) + '.png'
	pic_path = os.path.join('show_img', filename)
	#pic_path = os.path.join(session_dir, filename)
        size_list = []
        for i in range(int(amp_num)):
            amp_key = 'Amplicon_detail_name_%s' % (i+1)
            if request.form.has_key(amp_key):
                amp_seq = request.form[amp_key]
		size = len(''.join(amp_seq.splitlines()[1:]))
                size_list.append(size)

        if len(size_list) == 0:
            error = 'Please select the amplicons for Virtual Electrophresis'
	    return render_template('index.html', error=error)
        else:
	    error = ve.paint(size_list, 1, pic_path)
	    if error:
		return render_template('index.html', error=error)

	    return render_template('ve.html', filename=filename)

    return redirect(url_for('root'))

@app.route('/export_to_fasta', methods=['GET', 'POST'])
def export_to_fasta():
    """Refresh for batch mode"""
    error = None
    if request.method == 'POST':
        amp_num, session_dir = request.form['amp_num'].split(':')
        session_key = os.path.basename(session_dir)
        seq_list = []
        for i in range(int(amp_num)):
            amp_key = 'Amplicon_detail_name_%s' % (i+1)
            if request.form.has_key(amp_key):
                amp_seq = request.form[amp_key]
                seq_list.append(amp_seq)

        if len(seq_list) == 0:
            error = 'Please select the amplicons for export'
	    return render_template('index.html', error=error)
        else:
            filename = write_amplicons(session_dir, seq_list)

	return render_template('export_amplicon.html', session_key=session_key, filename=filename)

    return redirect(url_for('root'))

@app.route('/multi_align', methods=['GET', 'POST'])
def multi_liagn():
    """Refresh for batch mode"""
    error = None
    if request.method == 'POST':
        amp_num, session_dir = request.form['amp_num'].split(':')
        session_key = os.path.basename(session_dir)
        seq_list = []
        for i in range(int(amp_num)):
            amp_key = 'Amplicon_detail_name_%s' % (i+1)
            if request.form.has_key(amp_key):
                amp_seq = request.form[amp_key]
                seq_list.append(amp_seq)

        if len(seq_list) == 0:
            error = 'Please select the amplicons for multi-align'
	    return render_template('index.html', error=error)
        else:
            filename = write_amplicons(session_dir, seq_list)

        out = run_t_coffee(os.path.join(session_dir, filename))
        html = read_from_file(out)
	return render_template('multi_align.html', html=html)

    return redirect(url_for('root'))

#@app.route('/multi_align_view/<link>', methods=['GET', 'POST'])
@app.route('/multi_align_view/<session_key>/<link>')
def multi_align_view(session_key=None, link=None):
    """Refresh for batch mode"""
    error = None
    if not link:
	return redirect(url_for('root'))
    else:
        html = read_from_file(os.path.join(session_parent, session_key, link))
	return render_template('multi_align.html', html=html)

@app.route('/clust_align', methods=['GET', 'POST'])
def clust_liagn():
    """Refresh for batch mode"""
    error = None
    if request.method == 'POST':
        amp_num, session_dir = request.form['amp_num'].split(':')
        session_key = os.path.basename(session_dir)
        seq_list = []
        for i in range(int(amp_num)):
            amp_key = 'Amplicon_detail_name_%s' % (i+1)
            if request.form.has_key(amp_key):
                amp_seq = request.form[amp_key]
                seq_list.append(amp_seq)

        if len(seq_list) == 0:
            error = 'Please select the amplicons for clust-align'
	    return render_template('index.html', error=error)
        else:
            filename = write_amplicons(session_dir, seq_list)

        groups = DNACluster.cluster(open(os.path.join(session_dir, filename)))
        group_list = format_out(groups, amp_num, filename, session_dir)

	return render_template('clust_align.html', amp_num=amp_num, group_list=group_list, group_num=len(group_list), session_key=session_key)

    return redirect(url_for('root'))

def format_out(groups, amp_num, fa_amp_file_name, session_dir):
    '''Format output'''
    records = FastaFormatParser.parse(open(os.path.join(session_dir, fa_amp_file_name)))
    seq_dict = {}
    for record in records:
	id = record['id'].split()[0]
	desc = record['desc']
	seq = record['seq']
        seq = chilli.print_seq(seq, 80)
	fa_seq = '>%s %s%s%s%s' % (id, desc, os.linesep, seq, os.linesep)
	seq_dict[id] = fa_seq

    group_list = []
    for group_sn, group in enumerate(groups):
	seq_list = [seq_dict[amp_id] for amp_id, strand in group]

	file_name = write_amplicons(session_dir, seq_list)
        file_name = os.path.join(session_dir, file_name)
	if len(group) < 2:
	    t_coffee_result = file_name
	else:
	    t_coffee_result = run_t_coffee(file_name)

	t_coffee_result = os.path.basename(t_coffee_result)

        group_list.append((group_sn+1, ', '.join(['%s (%s)' % (amp_id, strand) for amp_id, strand in group]), t_coffee_result))

    return group_list


def write_amplicons(session_dir, seq_list):
    '''Write the sequence into file'''
    sn_list = []

    for seq in seq_list:
        desc_line = seq.split(os.linesep)[0]
        sn_list.append(desc_line.split()[0].rpartition('_')[2])

    sn_string = '_'.join(sn_list) 
    md5code = hashlib.new("md5", sn_string).hexdigest()
    md5file = os.path.join(session_dir, 'amplicons_sn_string.md5')
    file_name = os.path.join(session_dir, md5code + '.txt')

    is_exists = False
    if os.path.isfile(md5file):
	is_exists = check_md5(md5file, md5code)

    if not is_exists:
        fh = open(file_name, 'w')
        fh.write(os.linesep.join(seq_list))
        fh.close()
	write_to_file(md5file, md5code + os.linesep, model='a')

    return md5code + '.txt'

def write_to_file(file_name, file_content, model='w'):
    '''Write content into a file'''
    try:
        fh = open(file_name, model)
    except:
	error = 'Error: can not open %s for writing' % file_name
	return render_template('index.html', error=error)
        
    fh.write(file_content)
    fh.close()

def run_t_coffee(file_name):
    # Check if the file is alread exists 
    output = file_name + '.html'
    if os.path.isfile(output):
        return output

    output = file_name + '.html'
    cmd = '%s%smuscle -in %s -html -out %s'% (bin_path, os.sep, file_name, output)
    try:
        subprocess.Popen(cmd, shell=True).wait()
    except:
        error = 'Error in multiple alighment, please contact Wubin Qu [quwubin@gmail.com]'
	return render_template('index.html', error=error)

    if os.path.isfile(output):
        return output
    else:
	return ''

def read_from_file(file_name):
    fh = open(file_name)
    file_content = fh.read()
    fh.close()
    return file_content

def check_md5(md5file, md5code):
    '''Check the existance of md5code in the md5file'''
    code_list = open(md5file).read().splitlines()
    if md5code in code_list:
	return True
    else:
	return False

def run_ntthal(seq1, seq2, mv=50, dv=1.5, d=50, n=0.25, align_mode='ANY'):
    '''Run oligotm'''
    if align_mode == 'HAIRPIN':
        cmd = '%s%sntthal -mv %s -dv %s -d %s -n %s -s1 %s -a %s -path primer3_config/' \
                % (bin_path, os.sep, mv, dv, d, n, seq1, align_mode)
    else:
        cmd = '%s%sntthal -mv %s -dv %s -d %s -n %s -s1 %s -s2 %s -a %s -path primer3_config/' \
                % (bin_path, os.sep, mv, dv, d, n, seq1, seq2, align_mode)

    out, align = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    try:
        fields = out.splitlines()[0].split()
        delta_g = float(fields[-4]) / 1000
        tm = float(fields[-1])
        align = '<br/>'.join(out.splitlines()[1:])
	align = re.sub('\t', '    ', align)
	align = re.sub(' ', '&nbsp;', align)
    except:
        return -1, -1, -1

    return delta_g, tm, align


@app.route('/check_dimer', methods=['GET', 'POST'])
def check_dimer():
    error = None
    session_dir = chilli.session(session_parent)
    if request.method == 'POST':
	infile = os.path.join(session_dir, 'query.fa')
	upload_seq = ''
        if request.files.has_key('upload_seq'):
            upload_seq = request.files['upload_seq'].read()

	fasta_seq = ''
        if request.form.has_key('fasta_seq'):
            fasta_seq = request.form['fasta_seq']
	
	if upload_seq:
	    seq = upload_seq
	elif fasta_seq:
	    seq = fasta_seq
	else:
	    error = 'Need two or more primer sequences in fasta-format'
	    return render_template('dimer_index.html', error=error)

        fh = open(infile, 'w')
	for line in seq.splitlines():
	    line = line.strip()
	    if line.startswith('>'):
		fh.write("%s\n" % line)
		continue

	    line = re.sub('^[^a-zA-Z]+|[^a-zA-Z]+$', '', line)
	    line = re.sub('\s', '', line)

	    fh.write("%s\n" % line)

        fh.close()
	    

	if len(open(infile).read()) == 0:
	    error = 'Need two or more primer sequences in fasta-format'
	    return render_template('batch.html', error = error)

	error_or_degenerate = SeqCheck.fasta_format_check(open(infile), err_path='here')
	if error_or_degenerate not in ['yes', 'no']:
	    return render_template('batch.html', error=error_or_degenerate)

	mv = float(request.form['mono_conc'])
	dv = float(request.form['diva_conc'])
	dntp = float(request.form['dntp_conc'])
	oligo = float(request.form['oligo_conc'])
	align_mode = request.form['mode']
	if align_mode == 'HAIRPIN':
	    hairpin_list = analysis_hairpin(infile, mv, dv, oligo, dntp, align_mode)
	    return render_template('show_hairpin.html', error=error, hairpin_list=hairpin_list)
	else:
	    dimer_list = analysis_dimer(infile, mv, dv, oligo, dntp, align_mode)
	    return render_template('show_dimer.html', error=error, dimer_list=dimer_list)

    return render_template('dimer_index.html', error=error)

@app.route('/view_dimer', methods=['GET', 'POST'])
def view_dimer():
    error = None
    if request.method == 'POST':
	infile = request.form['infile']
	mv = request.form['mv']
	dv = request.form['dv']
	dntp = request.form['dntp']
	oligo = request.form['oligo']
	hairpin_list = analysis_hairpin(infile, mv, dv, oligo, dntp, 'HAIRPIN')
	dimer_list = analysis_dimer(infile, mv, dv, oligo, dntp, 'ANY')
	return render_template('view_hairpin_dimer.html', error=error, hairpin_list=hairpin_list, dimer_list=dimer_list)

    return render_template('dimer_index.html', error=error)

def analysis_hairpin(infile, mv, dv, oligo, dntp, align_mode):
    '''Analysis dimer'''
    records = FastaFormatParser.parse(open(infile))
    dimer_list = []
    for i in range(len(records)):
	record_i = records[i]
	id_i = record_i['id']
	seq_i = record_i['seq']
	delta_g, tm, align = run_ntthal(seq_i, seq_i, mv=mv, dv=dv, d=oligo, n=dntp, align_mode=align_mode)
	if tm >= 0:
	    dimer_list.append([id_i, seq_i, tm, delta_g, align])

    dimer_list.sort(key=itemgetter(2), reverse=True)
    return dimer_list

def analysis_dimer(infile, mv, dv, oligo, dntp, align_mode):
    '''Analysis dimer'''
    records = FastaFormatParser.parse(open(infile))
    dimer_list = []
    for i in range(len(records)):
	record_i = records[i]
	id_i = record_i['id']
	seq_i = record_i['seq']
	for j in range(i, len(records)):
	    record_j = records[j]
	    id_j = record_j['id']
	    seq_j = record_j['seq']

	    delta_g, tm, align = run_ntthal(seq_i, seq_j, mv=mv, dv=dv, d=oligo, n=dntp, align_mode=align_mode)
	    if tm >= 0:
		dimer_list.append([id_i, id_j, seq_i, seq_j, tm, delta_g, align])

    dimer_list.sort(key=itemgetter(4), reverse=True)
    return dimer_list

if __name__ == '__main__':
    app.run()


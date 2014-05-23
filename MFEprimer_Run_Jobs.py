#!/usr/bin/env python
# -*- coding:utf-8 -*-
'''Run Jobs


by Wubin Qu <quwubin@gmail.com>,
Copyright @ 2010, All Rights Reserved.
'''

Author = 'Wubin Qu  <quwubin@gmail.com> CZlab, BIRM, China'
Date = 'Jun-20-2011 16:05:49'
Version = '1.0'

import sys
import shutil
import os
from operator import itemgetter
import subprocess
import config
import zipfile


def create_lock(indir):
    '''Create the lock file'''
    fh = open(os.path.join(indir, 'job.lock'), 'w')
    fh.close()


def delete_lock(indir):
    '''Delete the lock file'''
    os.remove(os.path.join(indir, 'job.lock'))


def main():
    '''Main'''
    if len(sys.argv) != 2:
        print '''
	Usage: 

	%s batch_jobs_dir

	''' % os.path.basename(sys.argv[0])
        exit()
    else:
        indir = sys.argv[1]

    files = os.listdir(indir)
    if len(files) < 1:
        exit()

    job_locker = 'job.lock'
    if job_locker in files:
        delete_lock(indir)
        # exit()
    else:
        fh = open(os.path.join(indir, 'job.lock'), 'w')
        job_list = [(job_file, os.stat(os.path.join(indir, job_file)).st_mtime)
                    for job_file in files]
        job_list.sort(key=itemgetter(0))
        job = job_list[0][0]
        arg_dict = {}
        for line in open(os.path.join(indir, job)):
            fields = line.split(':')
            arg_dict[fields[0].strip()] = fields[1].strip()

        MFEprimer_web_root = os.path.dirname(sys.argv[0])

        fh.write(arg_dict['session_key'])
        fh.close()
        os.chdir(MFEprimer_web_root)
        session_dir = os.path.join('session', arg_dict['session_key'])

        out = os.path.join(session_dir, job)
        cmd = '%s ./mfeprimer/MFEprimer.py -i %s -o %s -d %s -k %s --mono_conc=%s --diva_conc=%s --oligo_conc=%s --dntp_conc=%s --ppc=%s --size_start=%s --size_stop=%s --tm_start=%s --tm_stop=%s --dg_start=%s --dg_stop=%s'% (config.python_path, arg_dict['infile'], out, arg_dict['database'], arg_dict['k_value'], arg_dict['mono_conc'], arg_dict['diva_conc'], arg_dict['oligo_conc'], arg_dict['dntp_conc'], arg_dict['ppc'], arg_dict['size_start'], arg_dict['size_stop'], arg_dict['tm_start'], arg_dict['tm_stop'], arg_dict['dg_start'], arg_dict['dg_stop'])

        subprocess.Popen(cmd, shell=True).wait()
        os.chdir(session_dir)
        try:
            f = zipfile.ZipFile(job + '.zip', 'w', zipfile.ZIP_DEFLATED)
            f.write(job)
            f.close()
            os.remove(job)
        except:
            print 'Zip Error'
            exit()

        os.chdir('../../')
        delete_lock(indir)
        shutil.move(os.path.join(indir, job), os.path.join('batch_jobs_done'))

if __name__ == '__main__':
    main()

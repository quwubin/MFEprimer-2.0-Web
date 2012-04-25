#!/bin/bash
dirs=('session' 'batch_jobs' 'batch_jobs_done' 'MFEprimerDB' 'show_img')
for dir in ${dirs[@]};do
    if [ -d $dir ]; then
	chmod 777 $dir 
	echo $dir 'created already.';
    else
	mkdir $dir
	chmod 777 $dir
	echo $dir 'created.';
    fi
done
ln -s mfeprimer/chilli .

#!/bin/bash
git clone https://github.com/quwubin/MFEprimer.git mfeprimer
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
cd mfeprimer/test/
../IndexDb.sh test.rna 9
cd ../../MFEprimerDB/
ln -s ../mfeprimer/test/test.rna* .

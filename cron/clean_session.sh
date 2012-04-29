#!/bin/bash
# From the following article:
# http://www.ahowto.net/linux/bash-script-delete-files-older-than-specified-time

real_path=$(dirname $(which ${0}))
cd $real_path

DIR='../session'                        # target directory where we should do some cleanup
FILES="*"           # file extensions that will be cleaned
let "EXPIRETIME=24*60*60"                         # expire time in seconds

shopt -s nullglob                               # suppress "not found" message

cd $DIR                                         # change current working directory to target directory

for f in $FILES
do
    NOW=`date +%s`                              # get current time
    FCTIME=`stat -c %Y ${f}`                    # get file last modification time
    let "AGE=$NOW-$FCTIME"
    if [[ $AGE -gt $EXPIRETIME ]] ; then
	rm -fr $f                                # this file age is more than the EXPIRETIME above, we can delete it
    fi
done

#!/usr/bin/env sh

# run nva process with directory structure creation
# args:
#	1. nva svn trunk directory
#	2. top level directory to create run directory in
#	3. location for oracle client 
#		should be /usr/lib/oracle/11.2/client64/lib
#	4. top level directory to copy excel files to

# check for args
if ["$4" == ""]; then
	echo "nva_run.sh svn_trunk_directory top_level_run_dir oracle_client_location top_level_copy_dir"
	exit
fi

echo VA:initiating nva process

export LD_LIBRARY_PATH=$3:$LD_LIBRARY_PATH
export PYTHONPATH=$1/modules:$PYTHONPATH

DIR=`date '+%F_%Hh-%Mm-%Ss_directory'`
DIRPATH=$2/$DIR

echo VA:creating run directory
mkdir $DIRPATH

echo VA:running tool...
$1/va_exec.py $1/nva_conf.yml $DIRPATH $DIRPATH/nva_summary.yml

echo VA:copying files
$1/va_dirtree.py $DIRPATH/nva_summary.yml $4

echo VA:process complete

exit

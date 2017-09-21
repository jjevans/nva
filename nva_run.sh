#!/usr/bin/env sh

# run nva process
# args:
#	1. nva svn trunk directory
#	2. top level directory to create run directory in
#	3. location for oracle client 
#		should be /usr/lib/oracle/11.2/client64/lib

# check for args
if ["$3" == ""]; then
	echo "nva_run.sh svn_trunk_directory top_level_run_dir oracle_client_location"
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

echo VA:process complete

exit

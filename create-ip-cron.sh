#!/bin/bash
ENV=$1
cd /export/witham3/create-ip-replica
bash ./conda.sh
. ~/.bashrc
conda activate $ENV
running=`ps -fe | grep pub-workflow | wc -l`
lastlog=`ls /esg/log/publisher/create-ip/*.log | tail -n 1`
errlines=`grep -c "checking errors" $lastlog`
if [ $errlines -gt 100 ] 
then
  echo "Potential logging issue, check replica publishing." | mail -s "Disk Space Warning" ames4@llnl.gov
  exit 1
fi
if [ $running -gt 1 ]
then
  exit 0
else
  # add --cmor-tables, --flag-file, and --config-file as arguments
  thedate=`date +%y%m%d_%H%M` ; time nohup python3 pub-workflow.py > /esg/log/publisher/main/replica-pub.$thedate.log
fi

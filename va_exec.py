#!/usr/bin/env python
import va_process
import sys
import yaml

####
# Jason Evans
####
# Executable for running annotation of variants for 
# the Novel Variant Assessment (NVA) project.
####

# argument is configuration file and the 
# directory to process in.
try:
	config = sys.argv[1]
	run_dir = sys.argv[2]
	summary_file = sys.argv[3]
except:
	print "usage: va_exec.py configuration_file directory_to_process_in summary_filename"
	exit()


process_obj = va_process.AssessRecentVariants(config,run_dir)

## annotate variants
results = process_obj.run_assessment()

## print results summary to summary file defined in config
#summary_file = run_dir+"/"+results["Time"]+"."+results["Settings"]["Project"]["files"]["extensions"]["summary"]

with open(summary_file,'w') as handle:
	handle.write("Time: "+results["Time"]+"\n")
	handle.write(yaml.dump(results))

exit()

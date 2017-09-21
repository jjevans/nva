#!/usr/bin/env python
import datetime
import va_process
import sys
import yaml

# build the NVA directory structure 
# of Gene directories, a "Variant" directory 
# within that and variant directories in that
# Input is the main yaml results in a file
print_summary = True

try:
	resyaml = sys.argv[1]
	datadir = sys.argv[2]
except:
	print "usage: va_dirtree.py nva_summary_yml root_directory_for_genes_and_variants"
	exit()

with open(resyaml) as handle:
	yamlstr = handle.read()
	
results = yaml.load(yamlstr)

rundir = results["Run_directory"]

vadirt = va_process.DirTree(rundir,datadir)

summary = "Processed variants\n\n"
summary += "Processed: "+results["Time"]+"\n"
summary += "Transfered: "+datetime.datetime.now().strftime("%b-%d-%Y_%Hh%Mm%Ss")+"\n\n"
summary += "From: "+rundir+"\n"
summary += "To: "+datadir+"\n\n"

variants = vadirt.variant_files(results["Processed"]["Variants"])

# print genes, their variants and excel files copied if exist
for variant in variants:
	summary += "Gene: "+variant["gene"]+" "
	summary += "Variant: "+variant["variant"]+" "
	summary += "Excel Produced: "+str(variant["excel"])+"\n"

if print_summary:
	print summary

exit()

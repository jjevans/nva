import alamut_util
import datetime
import gi_util

####
# Jason Evans
####
# Annotate variants
# library for the Variant Assessment project (Novel Variant Assessment, NVA)
# Uses variants found in CMS to process through Alamut-ht, HGMD, VEP
# Based on python script by Netsanet Gebremedhin (nvaLog2RawVcf.py)
####

class VA_Alamut():
	# run alamut-ht 
	# creates input, copy file to remote machine, execute alamut-ht, 
    # transfer alamut output back, evaluate output
	
	def __init__(self,settings=dict()):
		## process the alamut portion of the annotation
		## input is a settings dict as found in the "Alamut" section of 
		# the NVA configuration file
		
		self.settings = settings

		# output parser
		self.eval_obj = alamut_util.Evaluate()

	def machine_connect(self):
		# create connection to alamut machine
		# Must use this method before any processing!
		self.alamut_obj = alamut_util.RemoteAlamut(**self.settings)
		return

	def run_alamut(self,vcf,out,log,cleanup=True):
		# run alamut remotely
		## Input are filenames (with paths) to 
		# the input vcf, results output and log 
		# file.
		## puts input, runs alamut on remote machine, 
		# gets output and log, ...
		## cleanup if True removes the vcf and alamut output files 
		# on remote machine
		
		self.machine_connect()
		
		return self.alamut_obj.run_alamut(vcf=vcf,out=out,log=log)

	def eval_err(self,stderr):
		## evaluate returned stderr from alamut
		## Input is the stderr string
		if stderr is not None and len(stderr) > 0:
			err_str = "Alamut error string encountered: "+stderr
			raise VaAnnotateError(err_str)

		return

	def vcf_header(self):
		# returns a vcf header string
		# fields CHROM, POS, ID, REF, ALT, QUAL, FILTER, INFO
		return "##fileformat=VCFv4.1\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO"

	def process_output(self,output,build="GRCh37"):
		# separate alamut output into a dict of variants 
		# with values of their individual alamut lines
		# input is a list of lines from alamut output file
		# build only uses results having that genome build
		# returns a dict of variants and a list of column 
		# names from the header
		
		# get header and results lists
		(colnames,results) = self.eval_obj.split_output(output)
		
		# later pop off id and empty last column so need 
		# to make consistent column numbers in header
		colnames.pop(0) # id column name
		colnames.pop() # empty column ("" colname)
		
		variants = dict()
		for result in results:
			if result[12] == build:
				identifier = result.pop(0) # variant (gene_dnachange)
				result.pop() # empty column

				if not identifier in variants:
					variants[identifier] = list()
					
				variants[identifier].append(result)

		return colnames,variants

# Exception
class VaAnnotateError(Exception):
	def __init__(self,probstr):
		Exception.__init__(self,probstr)

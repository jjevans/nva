import datetime
import os
import re
import shutil
import sys
import va_finder as vfi
import yaml


####
# Jason Evans
####
# Perform whole process of annotating variants for 
# the Novel Variant Assessment (NVA) project.
###
# This library has class (Settings) to parse the NVA configuration file
# The structure of how the information is retrieved and all sql queries 
# were defined by Christine Folts, GeneInsight team
####
# The following criteria are used to find the variants to assess (reassess):
#   1. Novel: variant not found in the GeneInsight database at all
#	2. Novel: variant has never been reported in GI (timesReported = 0)
#	3. Reassess: variant category is "Likely Pathogenic" last being reported 
#		more than 6 months ago (180 days ago)
#	4. Reassess: variant category is "Unknown Significance" last 
#		being reported more than 3 months ago (90 days ago)
####


class Configure():
	# load the yaml configuration file for the NVA project
	
	def __init__(self,config):
		self.settings = self.load_config(config)
		
	def load_config(self,config):
		# load configuration file with yaml and return the structure
		
		with open(config) as handle:

			try:
				settings = yaml.load(handle.read())
			except:
				raise VariantAssessmentError("YAML configuration file was not able to load.")

		return settings


class AssessRecentVariants():
	# Runs the NVA process
	# Three primary functions: read in and set configuration options, 
	# build objects, use objects to find and annotate assessment 
	# variants.
	
	def __init__(self,config,run_directory):
		# config_file is the nva configuration file (nva_conf.yaml)
		# main directory in which the config resides is the directory 
		# that is referenced to get the path to supplemental files.
		# run_directory is the directory in which to process in
		import va_annotate as van
		import va_excel as vex

		self.config = config # path to configuration file
		
		# verify configuration file exists
		if not os.path.exists(self.config):
			err_str = "Configuration file does not exist: "+self.config
			raise VariantAssessmentError(err_str)
			

		self.run_directory = os.path.abspath(run_directory)


		####
		# all variants found and their information
		####
		self.variants = dict()

		####
		## process yaml config
		####
		self.settings = Configure(self.config).settings


		####
		## general values
		####
		self.build = self.settings["Project"]["genome_build"]


		###******
		#*** FILENAMES ***
		#*** for all intermediate, supplemental and final output files
		###******

		
		# verify directory for which to process exists
		if not os.path.exists(self.run_directory):
			err_str = "Directory specified for processing does not exist: "+self.run_directory
			raise VariantAssessmentError(err_str)


		# date and time as file basenames
		self.now = datetime.datetime.now().strftime("%b-%d-%Y_%Hh%Mm%Ss")

		# vcf filename produced from CMS query in basename of today's date 		
		cms_vcf = self.run_directory+"/"+self.now+"."+self.settings["Project"]["files"]["extensions"]["cms_vcf"]
		alamut_output = self.run_directory+"/"+self.now+"."+self.settings["Project"]["files"]["extensions"]["alamut_output"]
		alamut_log = self.run_directory+"/"+self.now+"."+self.settings["Project"]["files"]["extensions"]["alamut_log"]


		# template and fields filepaths to use when populating excel workbooks
		# if path relative in config, paths for template and fields 
		# specified are relative to the same directory as the config file 
		# otherwise they are absolute paths to these files
		template = str()
		fields = str()

		if self.settings["Project"]["files"]["relative_to_config"]:
			template += os.path.dirname(os.path.abspath(self.config))+"/"
			fields += os.path.dirname(os.path.abspath(self.config))+"/"
			
		template += self.settings["Project"]["files"]["excel_template"]
		fields += self.settings["Project"]["files"]["field_lookup"]

		# verify files are there
		if not os.path.exists(template):
			err_str = "Template file to use in populating Excel workbook does not exist: "+template
			raise VariantAssessmentError(err_str)
		if not os.path.exists(fields):
			err_str = "Fields file to use in populating Excel workbook does not exist: "+fields
			raise VariantAssessmentError(err_str)

		self.files = {"cms_vcf":cms_vcf,\
					"alamut_output":alamut_output,\
					"alamut_log":alamut_log,\
					"template":template,\
					"fields":fields}

		###*** END FILENAMES ***


		####
		## init obj that finds variants to assess
		####

		## criteria for choosing variants
		# number of days to go back in CMS
		self.num_days = self.settings["Project"]["criteria"]["time_period"]
		
		#variant categories to include ("Unknown Significance","Likely Pathogenic")
		self.categories = self.settings["Project"]["criteria"]["categories"]

		## db info
		dbuser = self.settings["GeneInsight"]["database"]["user"]
		dbpass = self.settings["GeneInsight"]["database"]["password"]
		host = self.settings["GeneInsight"]["database"]["host"]
		port = self.settings["GeneInsight"]["database"]["port"]
		sid = self.settings["GeneInsight"]["database"]["service"]
		dbname = host+":"+str(port)+"/"+sid

		## Web Service
		wsuser = self.settings["GeneInsight"]["web_service"]["user"]
		wspass = self.settings["GeneInsight"]["web_service"]["password"]
		variant_url = self.settings["GeneInsight"]["web_service"]["url"]["Variant"]
		gbm_url = self.settings["GeneInsight"]["web_service"]["url"]["GenomeBuildMapping"]
		
		find_kw = {"dbname":dbname,\
			"dbuser":dbuser,\
			"dbpass":dbpass,\
			"wsuser":wsuser,\
			"wspass":wspass,\
			"variant_url":variant_url,\
			"gbm_url":gbm_url}

		self.find_obj = vfi.Finder(**find_kw)


		####
		## annotation objs
		####

		## Alamut
		# alamut obj
		self.vaa_obj = van.VA_Alamut(self.settings["Alamut"])
		
		
		####		
		## excel obj
		####
		self.tbl_obj = vex.Table(self.files["template"])


	def run_assessment(self):
		## do entire process from CMS query to populating excel workbook
		## Process:
		#	1. query to find variants to assess
		#	2. create vcf from found variants and 
		#      find transcript id
		#	3. produce and evaluate annotations
		#		a alamut-ht
		#		b hgmd (not yet implemented)
		#		c vep (not yet implemented)
		#	4. merge annotations
		#	5. populate excel workbook
		## Process only certain parts: (unimplemented)
		#	process var is a list of integers 
		# 	and characters 
		##

		
		### find variants
		# get variant ids in cms
		recent = self.find_obj.recent_variants(num_days=self.num_days,categories=self.categories)
		self.cms_ids = recent

		#!!!ADD ABILITY TO SKIP REST OF THIS IF NO VARIANTS FOUND!!!

		# get details of those variants
		variants = self.find_obj.detail_variants(recent)


		### record variants
		# make vcf and get transcript ids
		# skips variants without genomic coordinates
		vcf_lines = [self.vaa_obj.vcf_header()]
		tests = dict()
		
		for variant in variants:

			genename = variant[0] # for clarity
			dnachange = variant[2]


			## record variant to variant info
			if genename not in self.variants:
				self.variants[genename] = dict()
				
			if dnachange not in self.variants[genename]:
				self.variants[genename][dnachange] = {"tests":list(),"coordinates":None}

			self.variants[genename][dnachange]["tests"].append(variant[7])
			
			## process those with dna coordinates
			if variant[4] is not None:

				# variant id is "genename_dnachange"
				identifier = genename+"_"+dnachange

				# genome coords
				(chrom,coords) = variant[4].split(":")
				position = coords.split("-")[0]
				
				# record coordinates to variant info, overwrites, but duplicate anyways
				self.variants[genename][dnachange]["coordinates"] = variant[4]

				## add unseen variant to test list and vcf
				if identifier not in tests:
					# transcript id and test codes
					tests[identifier] = list()
				
					# add to vcf
					vcf_lines.append(chrom+"\t"+position+"\t"+identifier+"\t"+variant[5]+"\t"+variant[6]+"\t"*3)
					
				tid = self.find_obj.transcript_id(chrom=chrom,position=position,build=self.build)
				tests[identifier].append((variant[7],tid))

		# remove variants duplicate entries with same variants and test codes.
		for testid in tests:
			tests[testid] = list(set(tests[testid]))

		# write vcf
		with open(self.files["cms_vcf"],'w') as handle:
			for vcf_line in vcf_lines:
				handle.write(vcf_line+"\n")


		### annotate
		## alamut
		# connect to alamut vm
		alamut_files = {"vcf":self.files["cms_vcf"],"out":self.files["alamut_output"],"log":self.files["alamut_log"]}
		stdout,stderr = self.vaa_obj.run_alamut(**alamut_files)

		# evalutate stderr
		self.vaa_obj.eval_err(stderr=stderr)

		# read in alamut output
		with open(self.files["alamut_output"]) as handle:
			alamut_lines = handle.readlines()

		# dict of variants and their output lines
		alamut_colnames,alamut_variants = self.vaa_obj.process_output(alamut_lines)


		### produce workbooks
		# create workbook for each variant
		for av in alamut_variants:
							
			# excel workbook filename
			# variant identifier with ".xls" extension.
			# a carrot (">") in id is changed to "_to_"
			wbname = re.sub(">","_to_",av)+"."+self.now+".xls"
			wbpath = os.path.join(self.run_directory,wbname)

			# add excel file name to the variant dict, 
			# overwrites, but duplicate anyways
			idgene,iddnac = av.split("_",1) # identifier genename_dnachange
			self.variants[idgene][iddnac]["excel"] = wbname

			
			# excel files
			pop_args = { "filename":wbpath,\
						"template":self.files["template"],\
						"fields":self.files["fields"],\
						"colnames":alamut_colnames,\
						"format":self.settings["Excel"]}

			# build table, create workbook
			pop_obj = vex.Populate(**pop_args)
			
			pop_obj.variant_book(filename=wbpath,tests=tests[av],results=alamut_variants[av])

		
		# add processing information to summary dict
		summary = {"Time":self.now,\
				"Run_directory":self.run_directory,\
				"Configuration_file":self.config,\
				"Processed":{"CMS_ids":self.cms_ids,"Variants":self.variants},\
				"Settings":self.settings}

		return summary


class QueryCMS():
	# Runs the NVA process
	# Three primary functions: read in and set configuration options, 
	# build objects, use objects to find and annotate assessment 
	# variants.
	
	def __init__(self,config):
		# config_file is the equivalent of nva configuration file (nva_conf.yaml)
		#runs current working directory

		self.config = config # path to configuration file
		
		# verify configuration file exists
		if not os.path.exists(self.config):
			err_str = "Configuration file does not exist: "+self.config
			raise VariantAssessmentError(err_str)
			

		####
		# all variants found and their information
		####
		self.variants = dict()

		####
		## process yaml config
		####
		self.settings = Configure(self.config).settings


		####
		## init obj that finds variants to assess
		####
		self.build = self.settings["Project"]["genome_build"]

		## criteria for choosing variants
		# number of days to go back in CMS
		self.num_days = self.settings["Project"]["criteria"]["time_period"]
		
		#variant categories to include ("Unknown Significance","Likely Pathogenic")
		self.categories = self.settings["Project"]["criteria"]["categories"]

		## db info
		dbuser = self.settings["GeneInsight"]["database"]["user"]
		dbpass = self.settings["GeneInsight"]["database"]["password"]
		host = self.settings["GeneInsight"]["database"]["host"]
		port = self.settings["GeneInsight"]["database"]["port"]
		sid = self.settings["GeneInsight"]["database"]["service"]
		dbname = host+":"+str(port)+"/"+sid

		## Web Service
		wsuser = self.settings["GeneInsight"]["web_service"]["user"]
		wspass = self.settings["GeneInsight"]["web_service"]["password"]
		variant_url = self.settings["GeneInsight"]["web_service"]["url"]["Variant"]
		gbm_url = self.settings["GeneInsight"]["web_service"]["url"]["GenomeBuildMapping"]
		
		find_kw = {"dbname":dbname,\
			"dbuser":dbuser,\
			"dbpass":dbpass,\
			"wsuser":wsuser,\
			"wspass":wspass,\
			"variant_url":variant_url,\
			"gbm_url":gbm_url}

		#file for vcf (stdout)
		self.files = {"cms_vcf":sys.stdout.fileno()}

		self.find_obj = vfi.Finder(**find_kw)

	def vcf_header(self,info=None):
		#return simple vcf header with no sample columns
		#info is list of tuples of id and description
		head = '##fileformat=VCFv4.2\n#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO'
		
		return head
		
	def days_ago(self):
	
		### find variants
		# get variant ids in cms
		recent = self.find_obj.recent_variants(num_days=self.num_days,categories=self.categories)
		self.cms_ids = recent


		# get details of those variants
		variants = self.find_obj.detail_variants(recent)


		### record variants
		# make vcf and get transcript ids
		# skips variants without genomic coordinates
		vcf_lines = list()
		tests = dict()
		
		for variant in variants:

			genename = variant[0] # for clarity
			dnachange = variant[2]


			## record variant to variant info
			if genename not in self.variants:
				self.variants[genename] = dict()
				
			if dnachange not in self.variants[genename]:
				self.variants[genename][dnachange] = {"tests":list(),"coordinates":None}

			self.variants[genename][dnachange]["tests"].append(variant[7])
			
			## process those with dna coordinates
			if variant[4] is not None:

				# variant id is "genename_dnachange"
				identifier = genename+"_"+dnachange

				# genome coords
				(chrom,coords) = variant[4].split(":")
				position = coords.split("-")[0]
				
				# record coordinates to variant info, overwrites, but duplicate anyways
				self.variants[genename][dnachange]["coordinates"] = variant[4]

				## add unseen variant to test list and vcf
				if identifier not in tests:
					# transcript id and test codes
					tests[identifier] = list()
				
					# add to vcf
										
				tid = self.find_obj.transcript_id(chrom=chrom,position=position,build=self.build)
				tests[identifier].append((variant[7],tid))
				
				vcf_lines.append(chrom+"\t" + position + "\t" + identifier + "\t" + variant[5] + "\t" + variant[6] + "\t." * 3)

		vcf_uniq = list(set(vcf_lines))
		vcf_uniq.insert(0, self.vcf_header())
		
		return vcf_uniq
		

class DirTree():
	# check and create directory structure for genes and their variants
	# each gene has a directory. within the gene directory is 
	# a "Variants" directory and within that is a directory 
	# for every variant (variant directory name pending)

	def __init__(self,run_directory,data_directory):
		# input is a directory where processing 
		# occurred containing output excel files
		# and the data directory being the 
		# root directory for the gene and 
		# variant directories
		self.run_directory = run_directory
		self.data_directory = data_directory
		
	def dir_structure(self,gene,variant):
		# check for a gene's directory. if 
		# doesn't exist, make it. find 
		# or create the "Variants" directory 
		# and find or create a specific 
		# variant directory
		## Input is a gene and the variant 
		# directory names to create
		
		genedir = os.path.join(self.data_directory,gene)
		Variantdir = os.path.join(genedir,"Variant")
		
		# find or create gene directory
		if not os.path.isdir(genedir):
			os.mkdir(genedir)
		
		# find or create "Variant" directory
		if not os.path.isdir(Variantdir):
			os.mkdir(Variantdir)
			
		# find or create specific variant directories
		vdirpath = os.path.join(Variantdir,variant)
			
		if not os.path.isdir(vdirpath):
			os.mkdir(vdirpath)
				
		return vdirpath

		
	def variant_files(self,Variants):
		# use the Variants dict 
		# produced in the Processed 
		# key of the main dictionary 
		# from NVA processing. 
		# Input is a dictionary with 
		# keys of gene name, values as 
		# dictionaries with keys of 
		# variant name.  one key of  
		# each variant dictionary is 
		# "excel" which is a filename 
		# to be transferred.
		# example Variant dictionary:
		# {"TTN":{"20495-15C>T":"excel":abc.xls}}
		# returns gene, variant, and excel 
		# file copied if one existed
		# its a list of dictionaries having 
		# the keys "gene","variant","excel".
		# returns None for excel if 
		# none existed
		summary = list()

		for gene in Variants:
			
			for variant in Variants[gene]:
				info = {"gene":gene,"variant":variant}
				
				if "excel" in Variants[gene][variant]:
					excelfile = Variants[gene][variant]["excel"]
					info["excel"] = excelfile
					
					# file to copy
					frompath = os.path.join(self.run_directory,excelfile)
					
					# find and create directories
					topath = self.dir_structure(gene,variant)
					
					# copy file
					shutil.copy(frompath,topath)
					
				else:
					info["excel"] = None
			
				summary.append(info)
		
		return summary


# Exception
class VariantAssessmentError(Exception):
	def __init__(self,probstr):
		Exception.__init__(self,probstr)
		

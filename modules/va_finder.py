import gi_util

####
# Jason Evans
####
# Find variants to assess (novel, reassess)
# library for the Variant Assessment project (Novel Variant Assessment, NVA)
# Queries CMS database for recent variants to identify novel and those 
# variants to reassess being of certain categories and last assessed 
# greater than a specified time ago
####

class Finder():
	####
	# find the variants that should be assessed
	# function is to query CMS for recent variants to find novel variants 
	# and variants to reassess based on the criteria that follows below.
	# Uses GeneInsight class for web service to find if variants have 
	# been assessed before and when
	# See comments at top of this file for how variants are identified
	####

	def __init__(self,dbname,dbuser,dbpass,wsuser,wspass,variant_url,gbm_url):
		# input is the CMS database name, user, and password and the 
		# GeneInsight web service user, password, and urls to 
		# both the Variant and genomeBuildMapping wsdls

		# init database utility for geneinsight queries, connect to db
		self.db = gi_util.CMS_DB(dbname,dbuser,dbpass)

		# init GeneInsight class to query with web service for variant entries
		self.gi_variant = Variant(wsuser,wspass,variant_url)
		
		# init GeneInsight class to query with web service for transcript ids
		self.gbm_ws = gi_util.GI_GenomeBuildMapping(wsuser=wsuser,wspass=wspass,wsurl=gbm_url)
		
	def recent_variants(self,num_days=1,categories=None):
		# Input is  a list of variant categories to check along with the number 
		# of days back to query database for variants entered into CMS
		# categories is a list of dictionaries with keys "type" and "days_ago" 
		# indicating the variant class found in GeneInsight and the minimum number 
		# of days ago that the variant should last have been assessed to add
		# returns a list of variant ids of variants to assess based on criteria 
		# defined above in constructor

		# get the SQL statement for the query to CMS for the recent variants
		recent_variant_query = self.db.recent_variant_query(num_days)
		
		# get all variants entered to CMS recently
		variants = self.db.ask(recent_variant_query)

		# get the variants to assess
		return self.gi_variant.variants_to_assess(variants,categories)

	def detail_variants(self,variant_lst):
		# Get the details of variants to assess.
		# Input is a list of variant ids to get information for.
		# Query retrieves gene, exon, dna allele change, amino acid change, 
		# dna coordinates, reference base, variant base, and the test code
		# returns a list of 8-tuples, missing elements denoted as None

		variant_detail_query = self.db.variant_detail_query(variant_lst)
		
		return self.db.ask(variant_detail_query)
	
	def transcript_id(self,chrom,position,build="GRCh37"):
		# get transcript id from chromosome and position. 
		# genome build optional (default GRCh37).
		# returns a transcript id
		return self.gbm_ws.transcript_id(chrom=chrom,start=position,end=position,build=build)


class Variant():
	# connect and query PCPGM GeneInsight web service 
	# for novel variants and variants to reassess using 
	# their Variant wsdl
	
	def __init__(self,wsuser,wspass,variant_url):
		# input is the GeneInsight web service user, password, and wsdl url 

		# init web service client with authentication
		self.variant_ws = gi_util.GI_Variant(wsuser=wsuser,wspass=wspass,wsurl=variant_url)

	def variants_to_assess(self,cms_variants,categories=None):
		## get the variants to access
		## input is the recent variants from CMS, the variant categories and 
		# amount of time since they have been assessed to reassess
		# The CMS variants should be a list of lists of CMS variants 
		# with the following elements:
		# 1. variant id, 2. gene name, 3. variant name, 4. exon number (leading zeros ok)
		# categories is a list of dictionaries with keys "type" and "days_ago"
		# In order to find if a variant found in CMS is in GeneInsight it compares the 
		# CMS exon number to the GeneInsight exon number
		## returns a list variant ids of variants to assess
		toassess = list()
		
		# go through all variants recently added (num_days ago) to CMS		
		for identifier,gene,name,exon in cms_variants:

			# remove leading zeros from exon number 
			exon = exon.lstrip("0")
	
			# fetch all entries of variants found in GeneInsight database for 
			# this gene and variant name
			variant_entries = self.variant_ws.geneAndVariant(gene,name)

			# find variants that have been reported 0 times or variants in the 
			# inputted categories assessed more than the specified number of days ago
			for entry in variant_entries:

				# try to match exon numbers
				if self.match_exon(entry,name,exon): # found matching entry

					# !!! Skip but check: Christine's checks to see if timesReported is defined, 
					# but I can't find instance where it is not, include check or no??? !!!
					#if "timesReported" in entry:

					if entry["timesReported"] == 0: # novel variant that's in GI db
						toassess.append(str(identifier))
						
					elif categories is not None: # reassess categories of interest

						# go through each category class adding variants to reassess if there 
						# last assessment was greater than the indicated time months ago
						for category in categories:
								
							if category["type"] == entry["category"]:
						
								date = self.variant_ws.previous_date(category["time_period"])
							
								# finds variants that have not been assessed since the date
								if not self.variant_ws.assessed_since(gene,name,date):
									toassess.append(str(identifier))

					break # skip rest

				else: # assess because variant not found in GI db at all
					toassess.append(str(identifier))
					
		return toassess

	def match_exon(self,variant_entry,name,exon):
		# from a variant entry (one of the variants from web service variantSearch) 
		# match the location to the inputted exon.  The feature (exon,intron) 
		# is parsed out and then matched.  If it matches the exon, returns True, 
		# else False
		# variant name is required because the case where the feature is "Intron" 
		# and the variant name contains a "-", the exon number needs to be incremented by 1

		# get region feature (exon,intron) and number (ie. exon number)
		if "region" in variant_entry["geneRegion"]: # returns False if region not in geneRegion
			try:
				feature_type,feature_num = variant_entry["geneRegion"]["region"].split(" ")
			except ValueError: # cannot unpack because single word like "Promoter" (no space)
				return False

			# fix the exon number (feature_num) in the following cases:
			#	The feature_type is "Intron"
			#	The variantName from CMS query is a deletion (contains a "-" in it)
			#	The feature_num includes a letter (ex. 45A)
			# fix made as to increment the feature_num by one if the letter in 
			# the feature_num is not an "i", otherwise leaves the feature_num as is	
			if feature_type == "Intron" and name.count("-") > 0:

				try: # see if the exon number contains a letter
					feature_num = str(int(feature_num))
				except ValueError:

					chars = list(feature_num)
					exon_letter = chars.pop()
					exon_number = int("".join(chars))

					# increment exon_number if exon_letter is not an "i"
					if exon_letter != "i":
						exon_number += 1

					feature_num = str(exon_number)+exon_letter
					
			if feature_num == exon: # found matching entry
				return True
	
		return False


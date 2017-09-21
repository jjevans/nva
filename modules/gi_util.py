import cx_Oracle
from suds.client import Client
from suds.wsse import *
from suds.plugin import MessagePlugin
import datetime

####
# Jason Evans
####
# Library to access GeneInsight web service and CMS database
# The structure of how the information is retrieved and all sql queries 
# were defined by Christine Folts, GeneInsight team
####

class CMS_DB():
	# Queries to LMM GeneInsight CMS database
	
	def __init__(self,db,user,password):
		# db is in the form host:port/service_id
		
		conn = cx_Oracle.connect(user,password,db)
		self.cursor = conn.cursor()
		
		self.queries = dict()
	
	def ask(self,query):
		# query database
		# input is a sql query
		# returns a list of all lines of output (result of fetchall())
		
		self.cursor.execute(query)
		
		return self.cursor.fetchall()

	def recent_variant_query(self,num_days=1):
		# get the sql query for the recent variants put into CMS
		# input optionally is the number of days to go back 
		# into GeneInsight (defaults to one day)
		
		return """
			select distinct sq.variant_id,
				lv.gene,
				lv.dna_change,
				lv.exon 
			from lmm_variant lv
				join (
					select 
						distinct lv.variant_id 
					from lmm_variant lv 
						left join lmm_seq_review_variant lsrv on lv.variant_id = lsrv.variant_id 
						left join lmm_seq_file_review lsfr on lsrv.file_review_id = lsfr.file_review_id 
							and lv.gene is not null and lsfr.is_final = 1 
							having count(distinct to_char(lsfr.last_review_edit_date, \'MM/DD/YY\')) = 1 
							group by lv.variant_id) sq on lv.variant_id = sq.variant_id 
						join lmm_seq_review_variant lsrv on lv.variant_id = lsrv.variant_id 
						join lmm_seq_file_review lsfr on lsrv.file_review_id = lsfr.file_review_id 
					where trunc(lsfr.last_review_edit_date) >= trunc(sysdate - """+str(num_days)+""") 
						and not (lv.gene = \'MTRNR1\' and lv.dna_change = \'1438A>G\') 
						and not (lv.gene = \'SDHB\' and lv.dna_change = \'843+159_843+184delins25\') 
					order by variant_id"""


	def variant_detail_query(self,variant_lst):
		# get the sql query to find the information for each variant
		# retrieves gene, exon, allele change, dna coordinates, 
		# ref and variant base, and the powerpath code whats the powerpath code???
		# input is a list of variant ids (from CMS)
		# based on Christine Folts nvaReport.pl::gcReport()
		
		return """
			select lv.gene,
				lv.exon,
				lv.dna_change,
				lv.aa_change,
				lntc.coordinates,
				lntc.ref_base,
				lntc.variant_base,
				ltd.powerpath_code
			from lmm_variant lv
				left join lmm_accession la on lv.accession_id = la.accession_id
				left join lmm_specimen ls on la.accession_id = ls.accession_id
				left join lmm_test lt on ls.specimen_id = lt.specimen_id
				left join lmm_test_definition ltd on lt.test_definition_id = ltd.test_definition_id
				left join lmm_ngs_testcall_variant lntv on lv.variant_id = lntv.variant_id
				left join lmm_ngs_test_call lntc on lntv.test_call_id = lntc.test_call_id
				left join lmm_ngs_test_run lntr on lntc.test_run_id = lntr.test_run_id
			where lv.variant_id in ("""+",".join(variant_lst)+""")
	  		order by lv.gene,lv.exon"""

class GI_WS():
	# Queries through LMM GeneInsight soap-based web service
	
	def __init__(self,user,password):
		# input is a web service username, password 
		# an explicit client connection must be made later with client_connect()
		# if client not connected, it will complain about None type 
		# having no variable "factory"
		
		# timeout
		self.timeout = 3600
	
		# create security token with username and password
		self.security = Security()
		
		user_token = UsernameToken(user,password)
		self.security.tokens.append(user_token)

	def client_connect(self,url):
		# create a new soap client
		
		client = Client(url=url,plugins=[PasswordTypePlugin()])
		
		client.set_options(wsse=self.security,timeout=self.timeout)
		
		return client

class GI_Variant():
	# get variant information from GeneInsight web service using their variant wsdl
	
	def __init__(self,wsurl=None,wsuser=None,wspass=None,client=None):
		# input is either an already established client using the variant wsdl or 
		# the GeneInsight web service url to variant wsdl, user, password to 
		# create a new client.  Existing client most likely will be produced 
		# using GI_WS class above.
		# Either a url/user/pass or a client must be defined or a GeneInsightWSError 
		# exception will be raised.
		# If both a client and web service credentials provided, the existing 
		# client will be used instead of creating a new one.

		if client is not None: # existing client
			self.client = client
			
		else: # init web service client with authentication
			if wsurl is None:
				err_str = "Niether an existing GeneInsight Variant client or the proper credentials to make one supplied in class GI_Variant."
				raise GeneInsightWSError(err_str)
				
			ws = GI_WS(wsuser,wspass)
			
			self.client = ws.client_connect(wsurl)

	def geneAndVariant(self,gene,name):
		# get the variant information for a variant in the inputted gene with inputted variant name
		
		gav = self.client.factory.create("queryParameter")
		gav.name = "geneAndVariant"
		gav.operator = "EQ"
		gav.values = gene+" "+name
		
		response = self.client.service.variantSearch(arg0=gav)
		
		return response

	def assessed_before(self,gene,name):
		# determines if a variant has ever been assessed before.
		# checks GI web service to see if any variant entry exists
		# needs two web service calls: 1st to see if the date of 
		# assessment is less than today's date and 2nd to find if 
		# assessment is equal to today's date (assessment done today)
		# returns a boolean, True if it has been assessed previously
		found = False # assessment found
		
		date_str = datetime.date.today().strftime("%d-%b-%Y")
		
		gav = self.client.factory.create("queryParameter")
		gav.name = "geneAndVariant"
		gav.operator = "EQ"
		gav.values = gene+" "+name
		
		vlacLT = self.client.factory.create("queryParameter")
		vlacLT.name = "variantLastAssessmentCompletedDate"
		vlacLT.operator = "LT" # GT checks to see if assessed previous to
		vlacLT.values = date_str

		vlacEQ = self.client.factory.create("queryParameter")
		vlacEQ.name = "variantLastAssessmentCompletedDate"
		vlacEQ.operator = "EQ" # GT checks to see if assessed previous to
		vlacEQ.values = date_str
		
		# two calls to find if previous assessment and assessment today	
		if len(self.client.service.variantSearch(arg0=(gav,vlacLT))) > 0 or \
				len(self.client.service.variantSearch(arg0=(gav,vlacEQ))) > 0:
			return True

		return False

 	def assessed_since(self,gene,name,date):
 		# determines if a variant was assessed since a certain date.  
 		# Input is the gene, variant name along with the 
 		# datetime.date() from which to test.
 		# Returns a boolean whether assessed or not
 		
		# make string of date in form GI uses
 		date_str = date.strftime("%d-%b-%Y")
 		
		gav = self.client.factory.create("queryParameter")
		gav.name = "geneAndVariant"
		gav.operator = "EQ"
		gav.values = gene+" "+name
		
		vlacd = self.client.factory.create("queryParameter")
		vlacd.name = "variantLastAssessmentCompletedDate"
		vlacd.operator = "GT" # GT checks to see if assessed more recent than
		vlacd.values = date_str
		
		if len(self.client.service.variantSearch(arg0=(gav,vlacd))) > 0:
			return True
			
		return False

	def previous_date(self,days_ago):
		# finds the date a specified number of days prior from today.
		# input is the number of days previous to go back
		# returns a datetime.date() object

		date = datetime.date.today()
		
		return date - datetime.timedelta(days=days_ago)

class GI_GenomeBuildMapping():
	# use GeneInsight web service to get the gene information 
	# for specified variants using their GenomeBuildMapping wsdl
	
	def __init__(self,wsurl=None,wsuser=None,wspass=None,client=None):
		# input is either an already established client using the GenomeBuildMapping 
		# wsdl or the GeneInsight web service url to that wsdl, user, password to 
		# create a new client.  Existing client most likely will be produced 
		# using GI_WS class above.
		# Either a url/user/pass or a client must be defined or a GeneInsightWSError 
		# exception will be raised.
		# If both a client and web service credentials provided, the existing 
		# client will be used instead of creating a new one.
		
		
		if client is not None: # existing client
			self.client = client
		
		else: # init web service client with authentication
			if wsurl is None:
				err_str = "Niether an existing GeneInsight web service client or the proper credentials to make one supplied in class GI_GenomeBuildMapping."
				raise GeneInsightWSError(err_str)
				
			ws = GI_WS(wsuser,wspass)
			
			self.client = ws.client_connect(wsurl)

	def region_info(self,chrom,start,end,build="GRCh37"):
		# retrieve all information for a region
		# input is the chromosome, start position, end position
		# optional is the genome build (defaults to GRCh37)
		# for a variant, start and end will be the same
		
		gbr = self.client.factory.create("genomeBuildRegion")
		gbr.chromosome = chrom
		gbr.genomeStartPosition = start
		gbr.genomeEndPosition = end
		
		return self.client.service.mapRegions(genomeBuild=build,regions=gbr)
		
	def transcript_id(self,chrom,start,end,build="GRCh37"):
		# get the transcript id from genomic coordinates
		# input is the chromosome, start position, end position
		# optional is the genome build (defaults to GRCh37)
		# for a variant, start and end will be the same

		gbr = self.client.factory.create("genomeBuildRegion")
		gbr.chromosome = chrom
		gbr.genomeStartPosition = start
		gbr.genomeEndPosition = end
		
		# not sure if bad practice to not have a return statement outside of try/except
		try:
			return self.client.service.mapRegions(genomeBuild=build,regions=gbr)[0]["transcriptId"]
		except:
			return None

	def hgvs_cdna(self,chrom,start,end,ref,alt,test_code,build="GRCh37"):
		# retrieve the HGVS cDNA nomenclature
		# input is the chromosome, start position, end position,
		# ref is the variant reference base, alt the alt base,
		# test code for GeneInsight
		# along with generic hgvs nomen for the variant,
		# genome build optional, defaults to GRCh37
		# generic nomenclature in the form of 
		
		gbv = self.client.factory.create("genomeBuildVariant")
		gbv.chromosome = chrom
		gbv.genomeStartPosition = start
		gbv.genomeEndPosition = end
		gbv.referenceSeq = ref
		gbv.variantSeq = alt
		gbv.otherData = generic_nomen
		
		try:
			return client.service.mapVariants(genomeBuild=build,testCodes=test_code,variants=gbv)
		except:
			return None

	def hgvs_cdna_batch(self,variants,test_code,build="GRCh37"):
		# retrieve the HGVS cDNA nomenclature for a batch of variants
		# input is a list having the chromosome, start position, 
		# end position, ref is the variant reference base, alt the alt base.
		# also needs a test code for GeneInsight,
		# along with generic hgvs nomen for the variant.
		# arg genome build optional, defaults to GRCh37
		# generic nomenclature in the form of 
		# input list of chrom,start,end,ref,alt,test_code for each variant
		
		desired = list()
		for variant in variants:
			gbv = self.client.factory.create("genomeBuildVariant")
			gbv.chromosome = chrom
			gbv.genomeStartPosition = start
			gbv.genomeEndPosition = end
			gbv.referenceSeq = ref
			gbv.variantSeq = alt
			gbv.otherData = generic_nomen
			
			desired.append(gbv)
	
		try:
			return client.service.mapVariants(genomeBuild=build,testCodes=test_code,variants=desired)
		except:
			return None	
			
class GeneInsightWSError():
	def __init__(self,probstr):
		Exception.__init__(self,probstr)
		
####
## Web service security.
## The following class is taken from 
## http://svn.dipr.partners.org/ngs/variant-reporting/annotation/trunk/lmm_variant_detection_report.py
####

class PasswordTypePlugin(MessagePlugin):
    def marshalled(self, context):
        # Grab the WSSE Password
        password = context.envelope.childAtPath('Header/Security/UsernameToken/Password')

        # Set a valid Type parameter on the WSSE Password
        password.set('Type', 'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText')
		

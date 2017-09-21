import copy
import xlwt

####
# Jason Evans
####
# Create excel workbook of variant annotations
# Based on python script by Netsanet Gebremedhin (nvaLog2RawVcf.py)
####
# Nutshell: 
#  1. each variant gets a workbook
#  2. each workbook has an worksheet of test codes with transcripts
#  3. each transcript gets a worksheet
####

class Populate():
	# run whole process of populating excel workbook 
	# with template and annotations
	
	def __init__(self,filename,template,fields,colnames,format):
		# Input is a workbook filename,
		# an excel sheet template filename (tab delimited)
		# colnames is a list of column names (header) 
		# with 1st and last fields removed (id and 
		# empty string).
		# settings is a dictionary having style and 
		# format definitions (optional).  derives 
		# from the nva configuration file.

		# tests sheet name is "LMM-Transcripts"
		self.tests_sheetname = "LMM-Transcripts"
		
		# excel workbook object
		self.wb = xlwt.Workbook()

		# save to this file
		self.filename = filename

		self.tbl_obj = Table(template)
		self.tbl_obj.fields_lookup(fields)

		self.colnames = colnames
		self.tablecol = 2 # what column to put values

		self.styles = self.build_styles(format["format"]["definitions"])
		self.locations = format["format"]["locations"]
		self.colwidth = format["column_widths"]

	def build_styles(self,definitions):
		# from a list of style definitions, 
		# create xlwt.easyxf objects
		# each list element is a dict with 
		# style name as key, style definition 
		# as value
		# returns a dict of style name as key,
		# easyxf object as values
		
		styles = dict()
		for definition in definitions:
			styles[definition] = xlwt.easyxf(definitions[definition])
			
		return styles

	def variant_book(self,filename,tests,results):
		## create a workbook having a tests 
		# sheet and sheets for each transcript 
		## Input is the the workbook name, 
		# tests list with tuples of lmm test 
		# codes and associated transcript ids, 
		# and a list of alamut result lines 
		# split by column in lists.

		# LMM-Transcripts sheet
		self.lmm_tests(tests,self.tests_sheetname)

		# transcript id in lmm test.
		# !!! fix to handle tests being None (no tid page) !!!
		# one test always present, same id for all tests
		tests_tid = tests[0][1]
		
		# store all tables so can write table 
		# to worksheet for test transcript id 
		# first and then write the rest thereafter.
		tbls = dict() # key worksheet name, value table
		for result in results:
			result_tbl = self.tbl_obj.transcript_table(result=result,colnames=self.colnames,colnum=self.tablecol)			

			# result transcript id, worksheet name
			result_tid = result[3]
			
			if result_tid == tests_tid: # add first ws
				self.table_to_sheet(result_tid,result_tbl)
			else:
				tbls[result_tid] = result_tbl

		# add all subsequent worksheets
		for wsname in tbls:
			self.table_to_sheet(wsname,tbls[wsname])

		# save workbook
		self.wb.save(self.filename)
		
		return

	def lmm_tests(self,tests,sheetname="LMM-Transcripts"):
		## create a sheet of an overview of the variant 
		# with its CMS test codes and associated transcript ids.
		## Input is the worksheet name and a list 
		# of 2-tuples having test code and their 
		# transcript id
		## returns reference to the worksheet
		header_col1 = "LMM Test Code"
		header_col2 = "Transcript Id"
		wstype = "tests" # type of worksheet format in config
		
		sheet = self.wb.add_sheet(sheetname)

		sheet.write(0,0,header_col1,self.styles["header"])
		sheet.write(0,1,header_col2,self.styles["header"])
		
		for i,test in enumerate(tests):
			# add 1 to i to add after header
			sheet.write(i+1,0,test[0])
			sheet.write(i+1,1,test[1])
		
		self.set_colwidth(sheet,wstype)

		return

	def table_to_sheet(self,sheetname,table):
		# produce a worksheet from a list 
		# of lists (2-d array).
		# Input is a worksheet and table. 
		# The table elements are 2-tuples 
		# having the cell value and the 
		# cell XFStyle object.
		# returns reference to the worksheet
		wstype = "transcripts"

		sheet = self.wb.add_sheet(sheetname)
		
		for i in xrange(0,len(table)): # rows
			for j,value in enumerate(table[i]): # columns

				locstr = str(i)+","+str(j)
				if locstr in self.locations[wstype]:

					style = self.styles[self.locations[wstype][locstr]]
					sheet.write(i,j,value,style)

				else: # no style for this cell
					sheet.write(i,j,value)
					
		self.set_colwidth(sheet,wstype)

		return

	def set_colwidth(self,sheet,wstype):
		# set column widths in the 
		# inputted sheet referencing 
		# widths defined for this worksheet
		# type. each column is a tuple 
		# of column number and column width
		
		for col in self.colwidth[wstype]:
			sheet.col(col[0]).width = col[1]
			
		return


class Table():
	# insert list into tab-delimited template file

	def __init__(self,template):
		self.table = self.load_template(template)
	
	def load_template(self,template):
		## load table to list of lists
		# from a tab-delimited table file
		## Input is the table filename
		table = list()
		
		with open(template) as handle:
			lines = handle.readlines()
			
		for line in lines:
			table.append(line.rstrip("\n").split("\t"))
			
		return table

	def fields_lookup(self,fieldfile):
		# create lookup of table row 
		# positions for a specific row 
		# id.
		# from a tab-delimited file of 
		# field name and field position, 
		# set up a dict with name as key, 
		# pos as value.
		self.fields = dict()
		
		with open(fieldfile) as handle:
			lines = handle.readlines()
			
			for line in lines:
				(name,pos) = line.rstrip("\n").split("\t")
				self.fields[name] = pos
				
		return

	def transcript_table(self,result,colnames,colnum):
		## produces a table of an alamut 
		# result set in copy of template 
		# table to write to excel file.
		# It looks up the position of 
		# each column of output using 
		# the fields dict and sets the 
		# value in the template table.
		## input is from an alamut result 
		# split by column into a list. 
		# the colnames is a list of column 
		# names to associate to each column 
		# of the result. colnum is the 
		# column of the table to insert 
		# row values into.
		## returns the table.
		#tbl = list(self.table)
		tbl = copy.deepcopy(self.table)		

		for i,res in enumerate(result):
			colname = colnames[i]
			rowpos = self.fields[colname]
			tbl[int(rowpos)][colnum] = res
	
		return tbl


# Exception
class VaExcelError(Exception):
	def __init__(self,probstr):
		Exception.__init__(self,probstr)
			

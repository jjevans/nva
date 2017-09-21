import os
import re
import remote_machine
# imports subprocess below

####
# Jason Evans
####

# utilities to help run alamut-ht

class Alamut():
	####
	# run alamut-ht
	# this class builds the command-line string and evaluates output and error
	####
	## Call this class to build the alamut command string to run, 
	# execute string, evaluate error, deal with output
	## Note! In running our alamut-ht, an error is thrown.  This error is 
	# harmless as it completes fine and gives proper output.  For this 
	# reason, we decided to ignore it.  When evaluating the run stderr, 
	# when we find this string, we remove it from the error string without 
	# Exception.  The error line found is:
	# "QSqlDatabasePrivate::removeDatabase: connection 'qt_sql_default_connection' 
	# is still in use, all queries will cease to work."
	####

	def __init__(self,options=None,executable="alamut-ht"):
		## Input is the alamut options, and ssh credentials 
		# if to be run remotely, and the program name (optional) 
		# if different than "alamut-ht" or if not in path and 
		# requires full path. may be redefined later when building command.
		## options is described in method opt_arg_str. nutshell, a list 
		# of alamut command-line arguments with exception to input vcf, 
		# results output and log filenames.
		
		self.options = options
		self.executable = executable
		
	def run_alamut(self,vcf,out,log):
		## builds and executes alamut command using subprocess 
		## Input is the input vcf and resulting output and 
		# log filenames (with paths).
		## returns two-tuple of the stdout and stderr strings
		import subprocess
		
		# build command
		command = self.build_command(vcf=vcf,out=out,log=log)
		
		# evaluate it			
		process = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
		
		return process.communicate()

	def build_command(self,vcf,out,log):
		## builds the string for command-line call to alamut-ht.
		## uses the variables defined in constructor "executable" 
		# and "options" both described there or in method "cmd_with_opts".
		return self.cmd_with_opts(vcf=vcf,out=out,log=log,options=self.options,executable=self.executable)

	def cmd_with_opts(self,vcf,out,log,options=None,executable="alamut-ht"):
		## builds a string of command-line arguments to feed into alamut.
		## Required input is the input vcf, output (alamut ann argument), 
		# and log (alamut unann arg) filenames (with paths).
		## options (optional) is a list of command-line arguments to 
		# add to the command-line string and is described in method opt_arg_str.
		## Provide the program name if different than "alamut-ht" or requires 
		# the full path to the executable.
		## Returns a string to evaluate
		
		cmd = executable+" --in "+vcf+" --ann "+out+" --unann "+log
		
		if options is not None:
			cmd += " "+self.opt_arg_str(options)
			
		return cmd
	
	def opt_arg_str(self,options):
		# creates a string of alamut command-line arguments.
		## options (optional) is a list of values.  A value may either be a string 
		# (a command-line option with no value like "nonnsplice") or a dictionary 
		# for command-line arguments with values.  These dictionaries may only 
		# have one key (the command-line option) and a value (the value for that
		## Example alamut-ht command-line:
		# alamut-ht --in file1 --ann file2 -unann file3 --nonnsplice --assbly GRCh37
 		## command line argument example options list:
		#	options[
		#		"nonnsplice",
		#		{"assbly":"GRCh37"},
		#       {"strand":1}.
		#		"alltrans"
		#	]
		# translates to string "--nonnsplice --assbly GRCh37 --strand 1 --alltrans"
		# This data structure is done for ease of defining yaml a 
		# configuration file for alamut options,
		
		args = str()	
		for opt in options:
			
			if isinstance(opt,dict):
				key = opt.keys()[0]
				args += " --"+key+" "+opt[key]
			else:
				args += " --"+opt
		
		return args

	def filter_stderr(self,err_txt,skip_patterns):
		##!!!NO LONGER USED!!! harmless error encountered in past remedied
		## removes specific error strings from alamut run stderr 
		## input is the stderr string and a list 
		# of strings to use as patterns.  Any pattern 
		# match results in removal of that line from the 
		# stderr string.
		## This a fix to ignore the harmless error explained in 
		# the class comment above.
		# removes all lines having the words: 
		# "QSqlDatabasePrivate::removeDatabase: connection 'qt_sql_default_connection' 
		# is still in use, all queries will cease to work."
		## returns string of stderr without lines having patterns

		lines = err_txt.split("\n")
		
		for line in lines:
		
			# patterns
			for pattern in skip_patterns:
				compiled_pattern = re.compile(pattern)
				if compiled_pattern.search(line):
					lines.remove(line)
				
		return "\n".join(lines)

		
class RemoteAlamut(Alamut):
	## functions to run alamut-ht on a remote machine
	# Process transfers an input vcf file to the remote machine, runs alamut-ht, 
	# and transfers its output back to the current machine.

	def __init__(self,ssh,options=None,executable="alamut-ht",cleanup=True):
		## Input is a dictionary of ssh credentials including the hostname 
		# of the remote machine and optionally a ssh username and password. 
		# The directory for alamut output defined in ssh dict is optional and 
		# defaults to the ssh landing point (presumably the user's home dir).
		# for future implementations either to chdir or just prepend to filenames !!!
		## The SSH connection to the remote machine may authenticate using 
		# established keys or optionally a username and password, if defined here.  
		## If established ssh keys exist for current user, username 
		# and password do not work and are ignored.
		# See class Alamut() for description of options and executable
		## Also required is a dictionary of ssh credentials
		# The dictionary needs the keys 
		# "machine" (required), "username" (optional), "password" (optional).
		# If ssh keys for user are established, remote connection established 
		# by them and username and password are ignored.  see class RemoteAlamut 
		# below.
		## cleanup being True removes the remote files when done
		
		self.options = options
		self.executable = executable
		self.cleanup = cleanup

		# run directory
		self.directory = ssh["directory"]
		
		# init objs for remote communication
		self.link_obj = remote_machine.Link(machine=ssh["machine"],user=ssh["user"],password=ssh["password"])
		self.ssh_obj = remote_machine.SSH(link_obj=self.link_obj)
		self.sftp_obj = remote_machine.SFTP(link_obj=self.link_obj)

	def run_remote(self,command):
		# runs alamut through ssh connection
		# executes inputted alamut command string 
		# containing executable name and all options
		# returns two-tuple of alamut stdout and stderr strings
		return self.ssh_obj.execute_no_exception(command)

	def run_alamut(self,vcf,out,log,remote_directory=None):
		## transfers vcf to remote machine, builds command and 
		# executes it using ssh, transfers output and log back 
		# to local machine, returns 2-tuple of stdout and stderr strings.
		## ssh credentials must have been provided in class instantiation
		# otherwise exception thrown. 
		## vcf, out and log files points to local filenames with 
		# paths. The basenames are used on remote machine in 
		# the run directory provided in constructor ssh dict. 
		# If no run directory in ssh dict, uses the ssh landing 
		# point (presumably user's home dir; defaults to empty string).
		## cleanup if True removes both the input vcf transferred to 
		# the remote host and the alamut output files created
		
		# set up the remote filenames and paths.
		remote_vcf = self.remote_file(vcf)
		remote_out = self.remote_file(out)
		remote_log = self.remote_file(log)
				
		# transfer input vcf to remote machine
		self.put(local=vcf,remote=remote_vcf,clobber=True,mkdir=True)
		
		# build command
		command = self.build_command(vcf=remote_vcf,out=remote_out,log=remote_log)
		
		# run alamut-ht
		response = self.run_remote(command)

		# transfer output and log back to local machine
		self.get(remote=remote_out,local=out,clobber=True)
		self.get(remote=remote_log,local=log,clobber=True)
		
		# remove remote files if cleanup specified 
		if self.cleanup:
			self.rm_file(remote_vcf)
			self.rm_file(remote_out)
			self.rm_file(remote_log)

		return response

	def put(self,local,remote=None,clobber=False,mkdir=False):
		# copy input to remote machine
		# Input is the full path to the file.
		# if clobber is True, clobbers existing file if already exists
		# if mkdir is True, creates remote directory if doesn't exist
		# returns the filepath to the remote vcf file

		# make sure local file exists
		if not os.path.exists(local):
			err_str = "No such file: "+local
			raise AlamutError(err_str)

		# remote vcf filename
		if remote is None:
			remote = str()
			
			if self.directory is not None:
				remote = self.directory+"/"
			
			remote += os.path.basename(local)

		# throw exception if file already exists (no clobber)
		if not clobber:

			try:
				self.sftp_obj.stat(remote)

				err_str = "VCF file already exists on remote machine (clobber=False): "+remote
				raise AlamutError(err_str)
			except remote_machine.RemoteMachineError:
				pass

		# create directory if it isn't already there
		if mkdir:
			self.sftp_obj.mkdir_recursively(os.path.dirname(remote))
		else: # make sure directory exists
			try:
				self.sftp_obj.stat(os.path.dirname(remote))	
			except remote_machine.RemoteMachineError:
				err_str = "No such directory: "+os.path.dirname(remote)
				raise AlamutError(err_str)

		self.sftp_obj.put(localpath=local,remotepath=remote)

		return remote

	def get(self,remote,local=None,clobber=False):
		# copy file back
		# if no local filepath, transfers the file to current directory 
		# with filename of the remote file's basename
		# if clobber is False, throws exception if local file 
		# already exists
		# returns True on success
		
		if local is None:
			local = os.path.basename(remote)
		
		if not clobber:
			try:
				os.stat(local)
				
				err_str = "File already exists on local machine: "+local
				raise AlamutError(err_str)
			except OSError:
				pass	
		
		return self.sftp_obj.get(remote,local)

	def remote_file(self,file):
		## return the filename (with path) of remote file
		## Input is a file (with path ok) to take basename 
		# and concatenate to the run directory in constructor
		## if no directory in constructor, returns just 
		# the basename of the inputted file.
		
		remote = str()
		if self.directory is not None:
			remote += self.directory+"/"
			
		remote += os.path.basename(file)
		
		return remote

	def rm_file(self,file):
		## remove file on remote machine
		# input is the remote file path
		return self.sftp_obj.remove(file)


class Evaluate():
	# parse and retrieve results
	# !!!assumed small amount of text inputted, but need to implement 
	# to accomodate a stream if large data expected.!!!
	''' Input is a string of alamut output. 
	Creates a lookup of column names to their column 
	number from header names along with a list of 
	lists of alamut result table '''
		
	def split_output(self,output):
		# splits output into the header and 
		# a list of rows.  Each row is a list 
		# of column elements. returned 
		# header is a list of column names.
		header = output.pop(0)
		
		# column names
		colnames = header.rstrip("\n").split("\t")
		
		# create a 2-D list
		results = list()
		for line in output:
			results.append(line.rstrip("\n").split("\t"))

		return colnames,results
	
	def colname_by_colnum(self,colnum):
		# retrieve column name from header by the column number
		# column number is zero-based
		return self.colname[colnum]
	
		
class AlamutError(Exception):
	def __init__(self,probstr):
		Exception.__init__(self,probstr)

# nva
Application to annotate variants for interpretation of it being causal to condition.

This application is a tool to assist in queueing which uncharacterized variants need assessment as to pathogenicity.  Checking LIMS, any variants encountered in the lab are candidates for assessment.  The candidate variants that lack conclusive data to be confident in its role need be assessed on a regular and systematic iterative curation.


va_exec.py is the top level application.  va_process.py is the top level library responsible for all the following processes along with logging progress to file.


The pipeline for this application does the core tasks of determining which variants to assess, annotating using Alamut Batch, parsing to spreadsheet and placement of file assessible to those making the interpretation.

Identify which variants need assessment
    #Query LIMS for all variants sequenced
    #Filter all variants classified as benign/pathogenic.  The remaining variants don't have conclusive evidence and need assessment
    #Keep only those variants that haven't been recently assessed
    #The remaining variants need revisiting to consider any new finding supporting conclusive pathogenicity
    
Run Alamut Batch on remote server
    #SFTP input vcf to remote host
    #Connect to remote host using SSH
    #Run Alamut Batch
    #Transfer output file back to local server

Parse, populate sheet, transfer to assessible file system
    #Transform Alamut Batch output to fit desired Excel format
    #Created Excel workbook with Python to convert a table and apply styles to this sheet
    #Mount to filesystem and transfer file 
    
![nva_workflow](https://user-images.githubusercontent.com/803012/30942794-02e45a12-a3bb-11e7-9395-f1510cf369fe.png)


NOTE: The code in this repository is most of the code used for this project.  Some content is ommitted in concern for breach of patient confidentiality.

##notes on installation and configuration of the variant assessment process

#virtual machines
novel-assess.dipr.partners.org
pcpgm.dipr.partners.org
alamut-ht1.dipr.partners.org


#production code put by direct copy of directory SVN/ngs/NVA to 
	/pcpgm/Tools/code on VMs
	
	
#cronjob set up to run va_exec.py (whole process) 
	and va_dirtree.py (directory creation and file transfer)
	

##setting up virtual machine from fresh build

#ssh keys
ssh: need to ssh to alamut vm once to create entry of host into known_hosts ssh file

#python-devel (python development headers and libs)
	sudo rpm -Uvf python-devel-2.6.6-51.el6.x86_64.rpm

#python libs (sudo easy_install)
pyyaml
paramiko: easy_install http://ftp.dlitz.net/pub/dlitz/crypto/pycrypto/pycrypto-2.1.0.tar.gz
suds
xlwt

	
#Oracle
install instant client and python lib cx_Oracle
	all necessary files and a little instruction 
	in SVN/ngs/bioinfo/People/Jason/build/cx_oracle_install.tar.gz

LD_LIBRARY_PATH has to be set in .bashrc if running from va_exec.py directly 
	(alternative is running sh script nva_run.sh which sets up environment)
	export LD_LIBRARY_PATH=/usr/lib/oracle/11.2/client64/lib



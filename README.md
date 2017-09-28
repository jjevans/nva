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
    
Run Alamut Batch on remote server </br>
    #SFTP input vcf to remote host</br>
    #Connect to remote host using SSH</br>
    #Run Alamut Batch</br>
    #Transfer output file back to local server</br>
</br>
Parse, populate sheet, transfer to assessible file system</br>
    #Transform Alamut Batch output to fit desired Excel format</br>
    #Created Excel workbook with Python to convert a table and apply styles to this sheet</br>
    #Mount to filesystem and transfer file </br>
  </br></br></br>  

 usage: va_exec.py config directory logfilename</br>
 
 arguments: yaml configuration_file, processing directory, filename for log
 </br></br></br>
 
![nva_workflow](https://user-images.githubusercontent.com/803012/30942794-02e45a12-a3bb-11e7-9395-f1510cf369fe.png)

</br></br></br>
 
 #Key Files</br>
 Configuration file: nva_conf.yml</br></br>
 Executable: va_exec.py</br></br></br>
 Libraries (modules directory):</br>
    alamut_util.py</br>
     - ssh to server using </br>
       paramiko, run annotation </br>
       with Alamut Batch</br></br>
    remote_machine.py</br>
     - implementation to run</br> 
       command-line tools on </br>
       another server</br></br>
    lsf_util.py</br>
      - library wraps drmaa-python </br>
        allowing job runner control </br>
        from your own script</br></br>
    aln_util.py</br>
     - wrap bwa (system), pysam</br></br>
    gi_util.py</br>
     - GeneInsight Oracle or web </br>
       service queries.</br></br>  
 Supplementary is directory of helper files for making Excel workbook</br>
 </br></br>

NOTE: The code in this repository is most of the code used for this project.  Some content is ommitted in concern for breach of patient confidentiality.
</br></br></br>
##notes on installation and configuration of the variant assessment process

#virtual machines</br>
novel-assess.dipr.partners.org</br>
pcpgm.dipr.partners.org</br>
alamut-ht1.dipr.partners.org</br>


#production code put by direct copy of directory SVN/ngs/NVA to </br>
	/pcpgm/Tools/code on VMs</br>
	
	
#cronjob set up to run va_exec.py (whole process) </br>
	and va_dirtree.py (directory creation and file transfer)</br>
	

##setting up virtual machine from fresh build

#ssh keys
ssh: need to ssh to alamut vm once to create entry of host into known_hosts ssh file

#python-devel (python development headers and libs)
	sudo rpm -Uvf python-devel-2.6.6-51.el6.x86_64.rpm

#python libs (sudo easy_install)
pyyaml</br>
paramiko: easy_install http://ftp.dlitz.net/pub/dlitz/crypto/pycrypto/pycrypto-2.1.0.tar.gz</br>
suds</br>
xlwt</br>

	
#Oracle
install instant client and python lib cx_Oracle
	all necessary files and a little instruction </br>
	in SVN/ngs/bioinfo/People/Jason/build/cx_oracle_install.tar.gz</br>

LD_LIBRARY_PATH has to be set in .bashrc if running from va_exec.py directly 
	(alternative is running sh script nva_run.sh which sets up environment)
	export LD_LIBRARY_PATH=/usr/lib/oracle/11.2/client64/lib



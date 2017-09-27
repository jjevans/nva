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
    
![Image of nva](https://github.com/jjevans/nva/blob/master/nva_workflow.pdf)


NOTE: The code in this repository is most of the code used for this project.  Some content is ommitted in concern for breach of patient confidentiality.


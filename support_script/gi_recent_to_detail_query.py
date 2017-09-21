#!/usr/bin/env python
import gi_util
import sys

user = "gigpad_clinical"
password = "g2J$3KHU"
host = "racclusr2.dipr.partners.org"
port = 1521
service = "gpadprod.pcpgm.partners.org"
db = host+":"+str(port)+"/"+service

try:
	num_days = sys.argv[1]
except:
	print "usage: gi_recent_to_detail_query.py num_days_to_go_back"
	exit();

gi_obj = gi_util.CMS_DB(db=db,user=user,password=password)

variants = gi_obj.ask(gi_obj.recent_variant_query(num_days))

variant_ids = [str(variant[0]) for variant in variants]
	
for detail in gi_obj.ask(gi_obj.variant_detail_query(variant_ids)):
	detail = map(str,detail)
	print "\t".join(detail)

exit();
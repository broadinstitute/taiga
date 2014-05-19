# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

import json
import urllib2
import shelve

# <codecell>

import sys

taiga_url = sys.argv[1]
fd = urllib2.urlopen(taiga_url+"/rest/v0/datasets")
datasets = json.loads(fd.read())
fd.close()

# <codecell>

checked_ids = shelve.open("checked_ids.shelve")

for d in datasets['datasets']:
    dsid = str(d["id"])
    if dsid in checked_ids:
        print "Skipping %s" % (dsid,)
        continue
    
    if d["columnar_path"] != None:
        formats = ["csv", "rdata"]
    else:
        formats = ["tabular_csv", "rdata"]
        
    for format in formats:
        print "fetching %s (%s)" % (dsid, format)
        fd = urllib2.urlopen(taiga_url+"/rest/v0/datasets/"+dsid+"?format="+format)
        assert fd.getcode() == 200
        
        bytes_read = 0
        while True:
            buf = fd.read(200000)
            if buf == "":
                break;
            bytes_read += len(buf)
        fd.close()
        
        assert bytes_read > 1
    checked_ids[dsid] = True


# <codecell>


# <codecell>



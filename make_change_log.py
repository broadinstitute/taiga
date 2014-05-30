# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

import yaml
import os
import urllib2
import json

# <codecell>

project_id = 1072300
config = yaml.safe_load(open(os.path.expanduser("~/.pivotal")).read())
token = config['token']

def get_done_stories():
    stories = []
    for state in ["accepted", "delivered", "finished"]:
        url = "https://www.pivotaltracker.com/services/v5/projects/%s/stories?date_format=millis&with_state=%s" % (project_id, state)
        request = urllib2.Request(url, headers={"X-TrackerToken" : token})
        contents = urllib2.urlopen(request).read()

        stories.extend(json.loads(contents))
    
    stories.sort(lambda a, b: -cmp(a["updated_at"], b["updated_at"]))
    
    return stories

import time

fd = open("taiga/static/changelog.md", "w")
stories = get_done_stories()
stories = stories[:10]
for story in stories:
    date = time.strftime("%Y-%m-%d", time.localtime(story["updated_at"]/1000))
    title = story["name"]
    if story["story_type"] == "bug":
        title = "Bug fix: "+title
    fd.write("%s [%s](%s)\n\n" % (date, title, story["url"]))
fd.close()

# <codecell>


# <codecell>



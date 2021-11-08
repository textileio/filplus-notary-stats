#!/usr/bin/env python
# coding: utf-8

# In[1]:


import copy, csv, datetime, json, os, statistics
from github import Github
from tabulate import tabulate


# In[ ]:


# Two notary handles that have since been replaced by a single one.
ignored_notries = ["Broz221", "Rin-huang", "1am5UP3RasM4R10", "dkkapur", "jsonsivar"]


# In[2]:


GH_TOKEN = os.environ.get("GITHUB_TOKEN")

g = Github(GH_TOKEN)

repo = g.get_repo("filecoin-project/filecoin-plus-client-onboarding")


# In[3]:


open_issues = repo.get_issues(state="all")


# In[4]:


notaries = {}
regions = {}
everyone = {}
all_time_open_hours = []
all_time_granted_hours = []
labels = set([])
base = {"granted": 0, "open": 0, "closed": 0, "regions": [], "hours_to_grant": [], "hours_still_open": [], "median_to_grant": [], "median_still_open": []}
rbase = {"granted": 0, "open": 0, "closed": 0, "notaries": [], "hours_to_grant": [], "hours_still_open": [], "median_to_grant": [], "median_still_open": []}
for issue in open_issues:
    if issue.assignee == None:
        continue
    if issue.assignee in ignored_notries:
        continue
    granted = False
    region = ""
    for label in issue.labels:
        if label.name == 'state:Granted':
            granted = True
        if label.name == 'region:Asia excl. Greater China':
            region = 'Asia excl. Greater China'
        if label.name == 'region:Europe':
            region = 'Europe'
        if label.name == 'region:Greater China':
            region = 'Greater China'
        if label.name == 'region:North America':
            region = 'North America'
        if label.name == 'region:Asia excl.  Japan':
            region = 'Asia excl.  Japan'
        labels.add(label.name)
        
    assignee = issue.assignee.login
    
    if assignee not in notaries:
        notaries[assignee] = copy.deepcopy(base)
    if issue.state == "open": 
        notaries[assignee]["open"] += 1
        opent = issue.created_at
        nowt = datetime.datetime.now()
        notaries[assignee]["hours_still_open"].append(((nowt - opent).total_seconds() / 3600))
        all_time_open_hours.append(((nowt - opent).total_seconds() / 3600))
    else:
        notaries[assignee]["closed"] += 1
        if granted == True:
            notaries[assignee]["granted"] += 1
            opent = issue.created_at
            clost = issue.closed_at
            notaries[assignee]["hours_to_grant"].append(((clost - opent).total_seconds() / 3600))
            all_time_granted_hours.append(((clost - opent).total_seconds() / 3600))
        
    if region != "":
        pr = set(notaries[assignee]["regions"])
        pr.add(region)
        notaries[assignee]["regions"] = list(pr)

        if region not in regions:
            regions[region] = copy.deepcopy(rbase)
        if issue.state == "open": 
            regions[region]["open"] += 1
            opent = issue.created_at
            nowt = datetime.datetime.now()
            notaries[assignee]["hours_still_open"].append(((nowt - opent).total_seconds() / 3600))
        else:
            regions[region]["closed"] += 1
            if granted == True:
                regions[region]["granted"] += 1
                opent = issue.created_at
                clost = issue.closed_at
                regions[region]["hours_to_grant"].append(((clost - opent).total_seconds() / 3600))
        pn = set(regions[region]["notaries"])
        pn.add(assignee)
        regions[region]["notaries"] = list(pn)
        
for n in notaries.keys():
    if len(notaries[n]["hours_to_grant"]) > 0: 
        notaries[n]["avg_hours_to_grant"] = sum(notaries[n]["hours_to_grant"]) / len(notaries[n]["hours_to_grant"]) 
        notaries[n]["median_to_grant"] = statistics.median(notaries[n]["hours_to_grant"])

    if len(notaries[n]["hours_still_open"]) > 0: 
        notaries[n]["avg_hours_still_open"] = sum(notaries[n]["hours_still_open"]) / len(notaries[n]["hours_still_open"]) 
        notaries[n]["median_still_open"] = statistics.median(notaries[n]["hours_still_open"])


# In[5]:




f = open("history.csv", "a")
history = csv.writer(f)

headers = ["Handle", "Granted", "Days to Grant \nAvg (Median)", "Open", "Days Left Open \nAvg (Median)", "Closed (no grant)"]
summary = []
nnn = sorted(notaries.keys(), key=str.lower)

for n in nnn:
    ahg = "...."
    row=[str(datetime.date.today()), n, notaries[n]["granted"]]
    if "avg_hours_to_grant" in notaries[n]:
        ahg = str(round(notaries[n]["avg_hours_to_grant"] / 24, 1))
        row.append(ahg)
        if "median_to_grant" in notaries[n] and type(notaries[n]["median_to_grant"]) == float:
            mhg = str(round(notaries[n]["median_to_grant"] / 24, 1))
            ahg += "  (" + mhg + ")"
            row.append(mhg)
        else:
            row.append("")
    else:
        row.extend(["",""])
        
            
    row.append(notaries[n]["open"])
    aho = "...."
    if "avg_hours_still_open" in notaries[n]:
        aho = str(round(notaries[n]["avg_hours_still_open"] / 24, 1))
        row.append(aho)
        if "median_still_open" in notaries[n] and type(notaries[n]["median_still_open"]) == float:
            mo = str(round(notaries[n]["median_still_open"] / 24, 1))
            aho += "  (" + mo + ")"
            row.append(mo)
        else:
            row.append("")
    else:
        row.extend(["",""])
            
    row.append(notaries[n]["closed"])
    history.writerow(row)
    
    summary.append(
        [
            n,
            notaries[n]["granted"],
            ahg,
            notaries[n]["open"],
            aho,
            notaries[n]["closed"]
        ]
    )


# In[6]:


r = open("README.md", "w+")
r.write(str(datetime.date.today())+"\n")
r.write("==========\n\n")
all_time_open_hours_avg = sum(all_time_open_hours) / len(all_time_open_hours) 

r.write("# Open applications\n\n")
r.write("- All issues left open: " + str(len(all_time_open_hours)))
r.write("\n")
r.write("- Average days open: " + str(round(all_time_open_hours_avg / 24, 1)))
r.write("\n")
r.write("- Median days open: " + str(round(statistics.median(all_time_open_hours) / 24, 1)))
r.write("\n\n")

all_time_granted_hours_avg = sum(all_time_granted_hours) / len(all_time_granted_hours) 
r.write("# Granted applications\n\n")
r.write("- All granted: " + str(len(all_time_granted_hours)))
r.write("\n")
r.write("- Average days to grant: " + str(round(all_time_granted_hours_avg / 24, 1)))
r.write("\n")
r.write("- Median days to grant: " + str(round(statistics.median(all_time_granted_hours) / 24, 1)))
r.write("\n\n")

r.write("# Notary Details\n\n")

md_headers = ["Handle", "Granted", "Days to Grant Avg (Median)", "Open", "Days Left Open Avg (Median)", "Closed (no grant)"]

r.write(tabulate(summary, headers=md_headers, tablefmt="github"))


# In[7]:


print(datetime.date.today())
print("==========")
print("")
all_time_open_hours_avg = sum(all_time_open_hours) / len(all_time_open_hours) 
print("All issues left open (" + str(len(all_time_open_hours)) + ")")
print(round(all_time_open_hours_avg / 24, 1), "(avg days)")
print(round(statistics.median(all_time_open_hours) / 24, 1), "(median days)")

all_time_granted_hours_avg = sum(all_time_granted_hours) / len(all_time_granted_hours) 
print("")
print("All granted (" + str(len(all_time_granted_hours)) + ")")
print(round(all_time_granted_hours_avg / 24, 1), "(avg days)")
print(round(statistics.median(all_time_granted_hours) / 24, 1), "(median days)")

print("")
print("Per notary")
print("==========")
print("")
print(tabulate(summary, headers=headers))


# In[ ]:





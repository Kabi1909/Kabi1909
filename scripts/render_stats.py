"""Refresh repository-hosted profile cards using GitHub's API (stdlib only)."""
import collections
import datetime as dt
import html
import json
import os
import sys
from pathlib import Path
import urllib.request

OUT = Path(__file__).resolve().parents[1] / "assets"
USER = os.environ.get("PROFILE_USERNAME", "Kabi1909")
TOKEN = os.environ["GITHUB_TOKEN"]
def query(q, variables):
    request = urllib.request.Request("https://api.github.com/graphql",
        data=json.dumps({"query":q,"variables":variables}).encode(),
        headers={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json","User-Agent":"profile-cards"})
    with urllib.request.urlopen(request, timeout=60) as response:
        data=json.load(response)
    if data.get("errors"):
        raise RuntimeError(json.dumps(data["errors"]))
    return data["data"]

user = query("""query($login:String!) { user(login:$login) {
 followers { totalCount }
 contributionsCollection { contributionCalendar {
 totalContributions weeks { contributionDays { date contributionCount } }
 } }
} }""",{"login":USER})["user"]
repos=[]
cursor=None
while True:
    page=query("""query($login:String!,$cursor:String) { user(login:$login) {
 repositories(first:100,after:$cursor,privacy:PUBLIC,ownerAffiliations:OWNER,isFork:false) {
 pageInfo { hasNextPage endCursor }
 nodes { stargazerCount languages(first:100) { edges { size node { name color } } } }
 } } }""",{"login":USER,"cursor":cursor})["user"]["repositories"]
    repos.extend(page["nodes"])
    if not page["pageInfo"]["hasNextPage"]: break
    cursor=page["pageInfo"]["endCursor"]
lang=collections.Counter()
colors={}
for repo in repos:
    for edge in repo["languages"]["edges"]:
        name=edge["node"]["name"]
        lang[name]+=edge["size"]
        colors[name]=edge["node"]["color"] or "#78dce8"
calendar=user["contributionsCollection"]["contributionCalendar"]
today=dt.datetime.now(dt.timezone.utc).date()
days=sorted((dt.date.fromisoformat(day["date"]),day["contributionCount"]) for week in calendar["weeks"] for day in week["contributionDays"] if dt.date.fromisoformat(day["date"])<=today)
run=best=0
previous=None
for date,count in days:
    if previous is not None and (date-previous).days != 1: run=0
    run=run+1 if count else 0
    best=max(best,run)
    previous=date
# A streak remains current while today is still in progress.
current=run
if days and days[-1][0]==today and days[-1][1]==0:
    current=0
    for date,count in reversed(days[:-1]):
        if not count: break
        current+=1
active=sum(count>0 for _,count in days)
stamp=today.isoformat()
def text(x,y,s,size=16,color="#9fafc6",weight=400):
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" font-weight="{weight}">{html.escape(str(s))}</text>'
def card(width,height,title,body,footer):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">
<title>{html.escape(title)}</title>
<rect x="1" y="1" width="{width-2}" height="{height-2}" rx="16" fill="#0d1628" stroke="#293a54"/>
<g font-family="Segoe UI,Arial,sans-serif">{text(26,36,title,18,"#edf5ff",600)}
{body}
{text(26,height-19,footer,11)}
</g></svg>'''
body=""
for x,value,label in [(28,len(repos),"PUBLIC REPOSITORIES"),(275,sum(r["stargazerCount"] for r in repos),"STARS EARNED"),(525,user["followers"]["totalCount"],"FOLLOWERS"),(760,calendar["totalContributions"],"CONTRIBUTIONS / YEAR")]:
    body+=text(x,102,f"{value:,}",40,"#85e4f0",700)+text(x,132,label,12)
stats=card(1000,180,"GitHub at a glance",body,f"Updated {stamp} UTC · Public, owned repositories; forks excluded")
# The frequent refresh must not rewrite the language or streak cards.
if "--activity-only" in sys.argv:
    OUT.mkdir(exist_ok=True)
    (OUT/"github-stats.svg").write_text(stats,encoding="utf-8")
    print("Updated GitHub activity card only.")
    sys.exit(0)
body=""
total=sum(lang.values())
if total:
    for i,(name,size) in enumerate(lang.most_common(4)):
        y=70+i*34
        color=html.escape(colors[name],quote=True)
        body+=f'<circle cx="30" cy="{y-5}" r="4" fill="{color}"/>'
        body+=text(43,y,name,14,"#dce9fa")+text(370,y,f"{size/total:.1%}",14,"#9fafc6")
        body+=f'<rect x="43" y="{y+7}" width="{350*size/total:.2f}" height="3" rx="1.5" fill="{color}"/>'
else: body+=text(26,90,"No public language data yet.")
languages=card(480,240,"Most-used languages",body,"Share of public repository bytes · Not proficiency")
body=""
for x,value,label in [(26,current,"CURRENT"),(180,best,"LONGEST"),(339,active,"ACTIVE DAYS")]:
    body+=text(x,113,value,38,"#a8a0f4",700)+text(x,142,label,11)
body+=text(26,181,"Contribution streaks in the past year",13)
streak=card(480,240,"Consistency over time",body,f"Updated {stamp} UTC · Days with contributions")
OUT.mkdir(exist_ok=True)
for name,content in [("github-stats.svg",stats),("top-languages.svg",languages),("streak-stats.svg",streak)]:
    (OUT/name).write_text(content,encoding="utf-8")
print("Updated three profile cards from GitHub API data.")

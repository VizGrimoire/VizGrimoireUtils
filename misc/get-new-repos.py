import github3
from github3 import login
import os

user = raw_input("Enter your Github Username: ")
passwd = raw_input("Enter the password: ")
gh = login(user, password=passwd)
org = gh.organization('bitergia')
repos = org.repositories(type='sources')
url = 'https://github.com'
for repo in repos:
    org, repo = str(repo).split("/")
    if os.path.exists(str(repo)) == True:
        print("The repository %s already exists" % repo)
    else:
        print("Cloning repo %s" % str(repo))
        os.system("git clone --quiet " + url + "/" + org + "/" + repo)

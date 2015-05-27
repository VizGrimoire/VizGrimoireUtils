import yaml #(it's necessary having installed python-yaml before)
import urllib
import ConfigParser

# variables
url = "https://git.openstack.org/cgit/openstack/governance/plain/reference/projects.yaml"
path = "/home/git/Automator/"
file_name = path+"projects.yaml"

# file with list of repos is downloaded
urllib.urlretrieve(url, filename=file_name)

# list of repositories (repositories[]) and file where list of repositories is saved
with open(file_name, "r") as f:
    file = yaml.load(f)
    file2 = open(path+"repos", "w")
    repositories = []
    for projects in file:
        projects_info = file[projects]['projects']
        for repo in projects_info:
            repositories.append("git://git.openstack.org/"+repo['repo'])
            file2.write("git://git.openstack.org/"+repo['repo']+"\n")

# string = list of repositories (format: repo,repo,repo...)
repos = ""
for i in range(len(repositories)):
    repos = repos+repositories[i]
    if i < len(repositories) -1:
        repos = repos+","

# files are closed
f.close()
file2.close()

# file openstack.conf
with open(path+"openstack.conf", "w") as f:   
    config = ConfigParser.RawConfigParser()
    config.add_section('Openstack')
    config.set('Openstack', 'source', repos)
    config.set('Openstack', 'trackers', '')
    config .write(f)

# file is closed
f.close()

import os

path = "/home/git/Automator/"
cadena = "config_r(tools_dir)"

with open(path+"create_projects.py", "r") as f:
    file = open(path+"aux", "w")
    for linea in f:
        if cadena in linea:
            file.write("#"+linea)
        else:
            file.write(linea)

f.close()
file.close()


os.remove(path+"create_projects.py")
os.rename(path+"aux",path+"create_projects.py")

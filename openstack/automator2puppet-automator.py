import os

path = "/home/git/Automator/"
contador = 0

with open(path+"create_projects.py", "r") as f:
    file = open(path+"aux", "w")
    for linea in f:
        contador = contador + 1
        #if (contador == 184) or (contador == 224) or (contador == 501) or (contador == 671) or (contador == 825):
        if contador == 224:
            file.write("#"+linea)
	elif contador == 271:
	    file.write("            [\"db_password\",\"root\"],\n")
        else:
            file.write(linea)

f.close()
file.close()

contador = 0

with open(path+"launch.py", "r") as f:
    file = open(path+"aux2", "w")
    for linea in f:
        contador = contador + 1
        if (contador == 1704) or (contador == 1705):
            file.write("#"+linea)
        else:
            file.write(linea)

f.close()
file.close()

os.remove(path+"create_projects.py")
os.remove(path+"launch.py")
os.rename(path+"aux",path+"create_projects.py")
os.rename(path+"aux2",path+"launch.py")

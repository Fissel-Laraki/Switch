 # -*-coding:utf-8 -*


from sys import argv
from pexpect import pxssh
from Slave import Slave
from Master import Master
from getpass import getuser
from Common import *


class Robot:

    def __init__(self,hostname='localhost',user=None,port=22,password=None):
        try :
            TIMEOUT = 1
            self.hostname = hostname
	        #,'IdentityAgent':'/tmp/ssh-wKLNj4eMnc/agent.553'}
            self.s = pxssh.pxssh(options={'StrictHostKeyChecking': 'no'})
            if password is None:
                self.s.login(self.hostname,user,port=port,ssh_key="/home/fissel/.ssh/id_rsa",login_timeout=TIMEOUT)
            else:
                self.s.login(self.hostname,user,password=password,port=port,login_timeout=TIMEOUT)
            self.getUsername()
            printc("Connexion à l'hote "+self.hostname+" en tant que " + self.user + " reussie!",'Success')
            if self.user != "root":
                self.sudo()
            self.type = None
        except pxssh.ExceptionPxssh:
            printc("Connexion échouée!",'Fail')
            exit(-1)

    def getUsername(self):
        self.s.sendline("whoami")
        self.s.prompt()
        data = self.s.before.decode().replace('\r','').split('\n')
        data.pop(0)
        self.user = data[0]

    # Se connecter en tant que root
    def sudo(self,password=None):
        self.s.sendline('sudo su -')
        self.s.set_unique_prompt()
        
        self.getUsername()
        if self.user == 'root':
            printc("Passage en tant que "+ self.user,"Success")
        else:
            printc("Le passage en tant que root a échoué",'Fail')
        
        
        
       
    # Trouve le type (Slave,Master) d'un serveur
    def recognition(self):
        data = self.getSlaveData()
        try:
            if len(data) == 0 or (data[0] == 'No' and data[1] == 'No'): # master
                self.type = "Master"
            elif data[0] == 'Yes' and data[1] == 'Yes':
                self.type = "Slave"
            else :
                raise Exception()
        except:
            printc("Slave/Master non détécté",'Fail')


    # Renvoie les infos des variables Slave_IO_Running et Slave_SQL_Running
    def getSlaveData(self):
        self.s.sendline("mysql -e 'show slave status\G;' | grep -E '(Slave_IO_Running|Slave_SQL_Running)' | awk '{print $2}'")
        self.s.prompt()
        data = self.s.before.decode().replace('\r','').split('\n')
        data.pop(0)
        data.pop(len(data)-1)
        return data

    def __del__(self):
        
        self.s.close()
        printc("Deconnexion de "+ self.hostname,"Primary")

# Fonction principale permettant de permuter le slave et le master
def switch(master,slave):
    master.flushLogs()
    slave.slaveIsReady()
    master.resetMaster()
    user,password = slave.getUserPassFromMasterInfoFile()
    slave.stopResetSlave()
    slave.resetMaster()
    logbin, position = slave.getSlaveLogBinInfo()
    master.changeMaster(slave.ip,logbin,position,slave.replicationUser,slave.replicationPassword)
    master.startSlave()
    master.setReadOnly()
    slave.unsetReadOnly()

"""
 Reçoit en paramètres 2 robots et retourne un duo slave,master
"""
def assignMasterSlave(robot1, robot2):
    
    if robot1.type == robot2.type:
        printc("On ne peut pas permuter 2 " + robot2.type,'Fail')
     
    if robot1.type == "Slave":
        slave = Slave(robot1.s,robot1.hostname)
        master = Master(robot2.s,robot2.hostname)
    else :
        slave = Slave(robot2.s,robot2.hostname)
        master = Master(robot1.s,robot1.hostname)
    return master, slave


# Verifie que le slave donné est bien slave du master donné
def checkMasterIp(master,slave):
    if master.ip == slave.getMasterIp():
        printc(slave.hostname + " est bien le slave de " + master.hostname,"Success")
    else:
        printc(slave.hostname + " n'est pas le slave de " + master.hostname,"Fail")

# Fonction d'affichage 
def display(master,slave):
    printc(master,'Primary')
    printc(slave,'Primary')

# Permet de récuperer les 2 serveurs donnés en serveur et de les parser
def getUsersHostnames():
    users = list()
    hostnames = list()

    for i in range(1,len(argv)):
        if '@' in argv[i] : 
            liste = argv[i].split('@')
            users.append(liste[0])
            hostnames.append(liste[1])
        else :
            users.append(getuser())
            hostnames.append(argv[i])
    return users,hostnames

# Fonction main
def main():
    if len(argv) != 3 :
        printc("Utilisation : python switchMS.py hostname1 hostname2\npython switchMS.py user1@hostname1 user2@hostname2",'Fail')
    try :
        users, hostnames = getUsersHostnames()

        robot1, robot2 = None,None
        robot1 = Robot(hostname=hostnames[0],user=users[0])
        robot2 = Robot(hostname=hostnames[1],user=users[1])

        robot1.recognition()
        robot2.recognition()

        master, slave = assignMasterSlave(robot1,robot2)
        
        setMasterAndSlaveIp(master,slave)

        display(master,slave)
        checkMasterIp(master,slave)

        slave.dropAndCreateReplicationUser(master)
        
        
        permuter = input("Voulez vous permuter ?[o/n] : ") 
        if permuter == 'o':
            switch(master,slave)
        


    except KeyboardInterrupt:
        printc("Arret en cours...",'Fail')

    if robot1 is not None:
        del robot1
    if robot2 is not None:
        del robot2

if __name__=="__main__": 
    main()

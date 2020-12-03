 # -*-coding:utf-8 -*

from sys import argv
from pexpect import pxssh
from Slave import Slave
from Master import Master
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
        self.user = "root"
        printc("Passage en tant que root ","Success")
        
        
        
       
    # Trouve le type (Slave,Master) d'un serveur
    def recognition(self):
        data = self.getSlaveData()
        if len(data) == 0: # master
            self.type = "Master"
        elif data[0] == 'Yes' and data[1] == 'Yes':
            self.type = "Slave"
        else :
            self.type = "Master"


    # Renvoie les infos des variables Slave_IO_Running et Slave_SQL_Running
    def getSlaveData(self):
        self.s.sendline("mysql -e 'show slave status\G;' | grep -E '(Slave_IO_Running|Slave_SQL_Running)' | awk '{print $2}'")
        self.s.prompt()
        data = self.s.before.decode().replace('\r','').split('\n')
        data.pop(0)
        data.pop(len(data)-1)
        return data

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

def assignMasterSlave(robot1, robot2):
    
    if robot1.type == robot2.type:
        printc("On ne peut pas permuter 2 " + robot2.type,'Fail')
        exit(-1)
     
    if robot1.type == "Slave":
        slave = Slave(robot1.s,robot1.hostname)
        master = Master(robot2.s,robot2.hostname)
    else :
        slave = Slave(robot2.s,robot2.hostname)
        master = Master(robot1.s,robot1.hostname)
    return master, slave

def checkMasterIp(master,slave):
    if master.ip == slave.getMasterIp():
        printc(slave.hostname + " est bien le slave de " + master.hostname,"Success")
    else:
        printc(slave.hostname + " n'est pas le slave de " + master.hostname,"Fail")
        exit(-1)

def display(master,slave):
    printc(master,'Primary')
    printc(slave,'Primary')

if __name__=="__main__": 
    if len(argv) != 3 :
        printc("Utilisation : python switch.py hostname1 hostname2",'Fail')
        exit(-1)

    robot1 = Robot(hostname=argv[1],user='fissel')
    robot2 = Robot(hostname=argv[2],user='fissel')

    robot1.recognition()
    robot2.recognition()

    master, slave = assignMasterSlave(robot1,robot2)
    
    setMasterAndSlaveIp(master,slave)

    display(master,slave)
    checkMasterIp(master,slave)

    slave.checkUserExistence(master)
    
    
    permuter = input("Voulez vous permuter ?[o/n] : ") 
    if permuter == 'o':
        switch(master,slave)
    else :
        print("Au revoir")

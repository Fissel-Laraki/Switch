from Common import *
class Slave:
    def __init__(self,s,hostname):
        self.s = s
        self.hostname = hostname
        self.ip = None
        self.replicationUser, self.replicationPassword = self.getUserPassFromMasterInfoFile()
        self.getSlaveLogBinInfo()
    
    def __str__(self):
        return self.hostname + " est un Slave."

    # Detecte si un Slave a fini d'ecrire
    def slaveIsReady(self):
        currentData = self.getSlaveCurrentData()
        continuer = True
        INTERVALLE = 0.5 # En secondes
        TOTAL_WAIT = 5 # En secondes
        i = 0
        while continuer and i < int(TOTAL_WAIT/INTERVALLE):
            sleep(INTERVALLE) 
            data = self.getSlaveCurrentData()
            if data == currentData:
                continuer = False
            else :
                currentData = data
            i += 1
        if i == int(TOTAL_WAIT/INTERVALLE):
            printc("Slave est encore en train d'écrire.",'Fail')
            exit(-1)
        printc(self.hostname + " : a arrêté d'écrire",'Success')
    
    # permet de reset un Slave
    def stopResetSlave(self):

        self.s.sendline("mysql -e 'stop slave;'")
        self.s.prompt()
        printc(self.hostname + " : le slave a été arrêté",'Success')
        self.s.sendline("mysql -e 'reset slave;'")
        self.s.prompt()
        printc(self.hostname + " : le slave a été reset",'Success')

    # Renvoie le fichier logbin et la position
    def getSlaveLogBinInfo(self):
        self.s.sendline("mysql -e 'show master status' | grep --color=never -v File")
        self.s.prompt()
        data = self.s.before.decode().replace('\r','').replace('\t',' ').split('\n')
        data.pop(0)
        if len(data) == 0 :
            printc(self.hostname + " : Le logbin n'est pas activé sur le slave",'Fail')
            exit(-1)
        
        try :
            data = data[0].split(' ')
            return data[0],data[1]
        except:
            printc(self.hostname + " : Le logbin n'est pas activé sur le slave",'Fail')
            exit(-1)

    # Renvoie les infos sur les variable Master_Log_Pos et Relay_Log_Pos 
    def getSlaveCurrentData(self):
        self.s.sendline("mysql -e 'show slave status\G' | grep -E '(Master_Log_Pos|Relay_Log_Pos)' | awk '{print $2}' ")
        self.s.prompt()
        data = self.s.before.decode().replace('\r','').split('\n')
        data.pop(0)
        return data
    
    # permet de reset le master BOTH
    def resetMaster(self):
        self.s.sendline("mysql -e 'reset master;'")
        self.s.prompt()
        printc(self.hostname + " : a reset son master",'Success')

    # Autorise l'ecriture dans le slave ( nouveau master )
    def unsetReadOnly(self):
        self.s.sendline("mysql -e 'SET GLOBAL READ_ONLY=OFF;'")
        self.s.prompt()
    
    def getMysqlDataDir(self):
        cmd = "show variables like '%datadir%'"
        self.s.sendline("mysql -e \"" + cmd + "\" | grep datadir | awk '{print $2}'")
        self.s.prompt()
        data = self.s.before.decode().replace('\r','').split('\n')
        data.pop(0)
        return data[0]
    
    def getUserPassFromMasterInfoFile(self):
        
        path = self.getMysqlDataDir()
        path += "master.info"
        self.s.sendline("cat "+path)
        self.s.prompt()
        data = self.s.before.decode().replace('\r','').split('\n')
        data.pop(0)
        ip_pattern = "^\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}$"
        try:
            if re.match(ip_pattern,data[3]):
                    return data[4],data[5]
            else:
                printc("Le fichier master.info ne correspond pas aux attentes","Fail")
                exit(-1)
        except:
            printc("Le fichier master.info est introuvable","Fail")
    
    def getMasterIp(self):
        self.s.sendline("mysql -e 'show slave status\G' | grep Master_Host | awk '{print $2}'")
        self.s.prompt()
        data = self.s.before.decode().replace('\r','').split('\n')
        data.pop(0)
        return data[0]

    def checkUserExistence(self,master):
        cmd = "select user from mysql.user where user = '"+self.replicationUser+"' and host='"+master.ip+"'"
        self.s.sendline("mysql -e \""+cmd+"\" | grep -v -i user")
        self.s.prompt()
        data = self.s.before.decode().replace('\r','').replace('\t',' ').split('\n')
        data.pop(0)
        username = data[0]
        if username == self.replicationUser:
            cmd = "alter user '"+username+"'@'"+master.ip+"' identified by '"+self.replicationPassword+"'"
            self.s.sendline("mysql -e \""+cmd+"\"")
            self.s.prompt()
            self.s.sendline("mysql -e 'flush privileges'")
            self.s.prompt()
        else:
            printc("Le compte de replication n'existe pas dans le Slave","Fail")
            exit(-1)

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

    # Detecte si un Slave a fini d'ecrire depuis les log Relay
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
        printc(self.hostname + " : Arrêt d'écriture depuis les RelayLOG",'Success')
    
    # permet de reset un Slave
    def stopResetSlave(self):

        self.s.sendline("mysql -e 'stop slave;'")
        self.s.prompt()
        printc(self.hostname + " : Arrêt du slave",'Success')
        self.s.sendline("mysql -e 'reset slave;'")
        self.s.prompt()
        printc(self.hostname + " : RESET du slave",'Success')

    # Renvoie le fichier logbin et la position
    def getSlaveLogBinInfo(self):
        self.s.sendline("mysql -e 'show master status' | grep --color=never -v File")
        self.s.prompt()
        data = self.s.before.decode().replace('\r','').replace('\t',' ').split('\n')
        data.pop(0)
        if len(data) == 0 :
            printc(self.hostname + " : Le logbin n'est pas activé sur le slave",'Fail')
        
        try :
            data = data[0].split(' ')
            return data[0],data[1]
        except:
            printc(self.hostname + " : Le logbin n'est pas activé sur le slave",'Fail')

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
        printc(self.hostname + " : RESET du master",'Success')

    # Autorise l'ecriture dans le slave ( nouveau master )
    def unsetReadOnly(self):
        self.s.sendline("mysql -e 'SET GLOBAL READ_ONLY=OFF;'")
        self.s.prompt()
    
    # Permet d'obtenir le datadir de mysql
    def getMysqlDataDir(self):
        cmd = "show variables like '%datadir%'"
        self.s.sendline("mysql -e \"" + cmd + "\" | grep datadir | awk '{print $2}'")
        self.s.prompt()
        data = self.s.before.decode().replace('\r','').split('\n')
        data.pop(0)
        return data[0]
    
    # Lit le fichier $datadir/master.info et récupère le username et password du compte de réplication
    def getUserPassFromMasterInfoFile(self):
        
        path = self.getMysqlDataDir()
        path += "master.info"
        self.s.sendline("cat "+path)
        self.s.prompt()
        data = self.s.before.decode().replace('\r','').split('\n')
        data.pop(0)
        
        try:
            if re.match(ip_pattern,data[3]):
                    return data[4],data[5]
            else:
                printc("Le fichier master.info ne correspond pas aux attentes","Fail")
                exit(-1)
        except:
            printc("Le fichier master.info est introuvable","Fail")
    
    # Retourne l'adresse ip du master à partir du slave
    # Même si la classe Master contient un attribut ip, on doit s'assurer que l'ip du master de ce slave
    # correspond à l'ip du Master
    def getMasterIp(self):
        self.s.sendline("mysql -e 'show slave status\G' | grep Master_Host | awk '{print $2}'")
        self.s.prompt()
        data = self.s.before.decode().replace('\r','').split('\n')
        data.pop(0)
        return data[0]

    # On vérifie qu'il existe un compte de réplication dans le slave qui est exactement le même que celui
    # présent dans le master
    def checkUserExistence(self,master):
        cmd = "select user from mysql.user where user = '"+self.replicationUser+"' and host='"+master.ip+"'"
        self.s.sendline("mysql -e \""+cmd+"\" | grep -v -i user")
        self.s.prompt()
        data = self.s.before.decode().replace('\r','').replace('\t',' ').split('\n')
        data.pop(0)
        username = data[0]
        return True if username == self.replicationUser else False
        

    # permet de supprimer un utilisateur et le recréer
    def dropAndCreateReplicationUser(self,master):
         
        if self.checkUserExistence(master) :
            self.dropUser(master)
            if  not self.checkUserExistence(master) :
                self.createUser(master)
                if self.checkUserExistence(master) :
                    printc("Création du compte de replication",'Success')
                else:
                    printc("Échec lors de la création du compte de réplication",'Fail')
            else :
                printc("Échec lors de la suppression du compte de réplication",'Fail')
        else:
            printc("Le compte de réplication n'existe pas ",'Fail')
    # Supprime un utilisateur
    def dropUser(self,master):
        cmd = "DROP USER "+self.replicationUser+"@"+master.ip
        self.s.sendline("mysql -e \""+cmd+"\"")
        self.s.prompt()
    # Crée un utilisateur
    def createUser(self,master):
        cmd = " GRANT REPLICATION SLAVE,REPLICATION CLIENT ON *.* TO '"+self.replicationUser+"'@'"+master.ip+"' identified by '"+self.replicationPassword+"'" 
        self.s.sendline("mysql -e \""+cmd+"\"")
        self.s.prompt()
        data = self.s.before.decode().replace('\r','').split('\n')
        self.s.sendline("mysql -e 'flush privileges'")
        self.s.prompt()


    # Permet de connaître la version de mysql utilisée
    def getVersion(self):
        self.s.sendline("mysql -e \"show variables like \'version\' \" | grep -v Value | awk '{print $2}'") #5.5.68-MariaDB
        self.s.prompt()
        data = self.s.before.decode().replace('\r','').replace('\t',' ').split('\n')
        data.pop(0)
        res = data[0]
       
        try :
            version = res.split('-')[0]
            if re.match(version_pattern,version):
                self.version = version
            else:
                raise Exception("")
        except:
            printc("Version de mysql non détéctée",'Fail')
            exit(-1)

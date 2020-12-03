from Common import *

class Master:
    def __init__(self,s,hostname):
        self.s = s
        self.hostname = hostname
        self.ip = None
    
    def __str__(self):
        return self.hostname + " est un Master."
    
    # Permet de flush les logs du master
    def flushLogs(self):
        self.s.sendline("mysql -e 'flush logs;'")
        self.s.prompt()
        printc(self.hostname + " : flushing logs",'Success')

    def startSlave(self):
        self.s.sendline("mysql -e 'start slave;'")
        self.s.prompt()
        printc(self.hostname + " : Démarrage du slave",'Success')
    
    # Permet de transformer un master en slave en lui precisant son nouveau master(qui est l'ex slave ici)
    def changeMaster(self,exslave_ip,exslave_logbin,exslave_pos,exslave_user,exslave_pass):
        
        cmd = "change master to MASTER_HOST='"+exslave_ip+"', MASTER_USER='"+exslave_user+"',MASTER_PASSWORD='"+exslave_pass+"',MASTER_LOG_FILE='"+exslave_logbin+"',MASTER_LOG_POS="+exslave_pos+";"
        self.s.sendline("mysql -e \"" + cmd + "\"") 
        self.s.prompt()
        printc(self.hostname + " : Est devenu slave",'Success')
    
    # permet de reset le master BOTH
    def resetMaster(self):
        self.s.sendline("mysql -e 'reset master;'")
        self.s.prompt()
        printc(self.hostname + " : RESET du master",'Success')
    
    # Interdit l'ecriture dans le master ( nouveau slave )
    def setReadOnly(self):
        self.s.sendline("mysql -e 'SET GLOBAL READ_ONLY=ON;'")

    
        

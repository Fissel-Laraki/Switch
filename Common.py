from time import sleep
import re


Colors = {}
Colors['Success'] = '\033[92m'
Colors['Warning'] = '\033[93m'
Colors['Fail'] = '\033[91m'
Colors['End'] = '\033[0m'
Colors['Primary'] = '\033[94m'

ip_pattern = "^\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}$"
version_pattern = "^(\d+\.)?(\d+\.)?(\*|\d+)$"

def printc(strg,color):
    if color == 'Success':
        print(Colors[color]+"[+] "+str(strg)+Colors['End'])
    elif color == 'Fail':
        print(Colors[color]+"[-] "+str(strg)+Colors['End'])
        exit(-1)
    else:
        print(Colors[color]+"[*] "+str(strg)+Colors['End'])

def findIp(robot):
    robot.s.sendline("hostname -i")
    robot.s.prompt()
    data = robot.s.before.decode().replace('\r','').split('\n')
    data.pop(0)
    try:
        ip = data[0]
        if re.match(ip_pattern,ip):
            return ip
        else:
            print(ip)
            raise Exception()
    except:
        printc("L'adresse ip de "+ robot.hostname + " n'a pas pu être trouvée",'Fail') 
    return data[0]

def setMasterAndSlaveIp(master,slave):
    slave.ip = findIp(slave)
    master.ip = findIp(master)
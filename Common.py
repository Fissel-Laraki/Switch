from time import sleep
import re


Colors = {}
Colors['Success'] = '\033[92m'
Colors['Warning'] = '\033[93m'
Colors['Fail'] = '\033[91m'
Colors['End'] = '\033[0m'
Colors['Primary'] = '\033[94m'

def printc(strg,color):
    if color == 'Success':
        print(Colors[color]+"[+] "+str(strg)+Colors['End'])
    elif color == 'Fail':
        print(Colors[color]+"[-] "+str(strg)+Colors['End'])
    else:
        print(Colors[color]+"[*] "+str(strg)+Colors['End'])

def findIp(s,hostname):
    s.sendline("hostname -i")
    s.prompt()
    data = s.before.decode().replace('\r','').split('\n')
    data.pop(0)
    return data[0]

def setMasterAndSlaveIp(master,slave):
    slave.ip = findIp(slave.s,slave.hostname)
    master.ip = findIp(master.s,master.hostname)
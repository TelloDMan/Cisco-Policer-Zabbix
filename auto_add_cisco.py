#!/usr/bin/python3
import requests
import json
from auto_snmp_cisco import start_snmp
import re
from pyzabbix import ZabbixAPI#, ZabbixAPIException

# Zabbix IP
ip = "" #example 192.168.1.1

# Zabbix API URL
url = 'http://" + ip +"/zabbix/api_jsonrpc.php'

# Zabbix API authentication details
user = ''
password = ''

# Headers for the HTTP request
headers = {'Content-Type': 'application/json-rpc'}

zapi = ZabbixAPI("http://"+ ip +"/zabbix")
zapi.login(user,password)

list_of_hosts = [[]] # [["hostname", ip_host , community_string],["hostname2", ip_host2 , community_string]]



for instance in list_of_hosts:

    host_name = instance[0]
    hosts = zapi.host.get(filter={"host": host_name},selectInterfaces=["interfaceid"])
    host_id = hosts[0]["hostid"]
    interfaceid=hosts[0]["interfaces"][0]["interfaceid"]


    priority = 1  # 0 - (default) not classified, 1 - information, 2 - warning, 3 - average, 4 - high, 5 - disaster

    content = start_snmp(instance[1],instance[2]) #[speed,ifDesc,Direction]


        
    trigger_data = zapi.trigger.get(hostids = host_id)

    Inbound = [data for data in trigger_data if data['description'].split(' ')[1][0] == "I"] # xe-0/0/0.108 Inbound 10M
    Outbound = [data for data in trigger_data if data['description'].split(' ')[1][0] == "O"] # xe-0/0/0.108 Onbound 10M

    if len(Inbound) > 0:
        for entry in Inbound:
            interface = entry['description'].split(' ')[0]
            for policy in content: #policy = [speed,ifDesc,Direction]
                notpresent = True
                #match entries from the policing rules per subinterface
                if interface == policy[1]:
                    notpresent = False
                    limiting = policy[0]
                    description = policy[1] + " " + "Inbound " + str(int(int(policy[0])/1000000)) +"m"
                        
                    #specifies the item key inside the expression which is created by a discovery rule
                    expression = 'avg(/{host_name}/1.3.6.1.2.1.31.1.1.1.6.[{interface}],600s)>{limit}'.format(host_name=host_name, interface=policy[1], limit=limiting)
                    #remove already present triggers
                    content.remove(policy)
                    triggered = entry["triggerid"]
                    #update entries for already available trigegrs
                    trigger_update = zapi.trigger.update({
                            'triggerid': triggered,
                            'description': description,
                            'expression': expression,
                            'status': 0,  # 0 - enabled, 1 - disabled
                        })
                    break
            if notpresent:
                #delete any trigger that does'nt have a subinterface 
                try:
                    trigger_delete = zapi.trigger_delete(entry["triggerid"])
                except:
                    print("Delete Failed",entry)

    if len(Outbound) > 0:
        for entry in Outbound:
            interface = entry['description'].split(' ')[0]
            for policy in content:#policy = [speed,ifDesc,Direction]
                notpresent = True

                if interface == policy[1]:
                    notpresent = False
                    limiting = policy[0]
                    description = policy[1] + " " + "Outbound " + str(int(int(policy[0])/1000000)) +"m"

                    expression = 'avg(/{host_name}/1.3.6.1.2.1.31.1.1.1.10.[{interface}],600s)>{limit}'.format(host_name=host_name, interface=policy[1], limit=limiting)
                    content.remove(policy)
                    triggered = entry["triggerid"]
                    trigger_update = zapi.trigger.update({
                            'triggerid': triggered,
                            'description': description,
                            'expression': expression,
                            'status': 0,  # 0 - enabled, 1 - disabled
                        })
                    break
            if notpresent:
                try:
                    trigger_delete = zapi.trigger_delete(entry["triggerid"])
                except:
                    print("Delete Failed",entry)




    for policy in content:
        #policy = [speed,ifDesc,Direction]
        interfaces = policy[1]
        if policy[2] == "i":
            description = interfaces + " " + "Inbound " + str(int(int(policy[0])/1000000)) +"m"
            expression = 'avg(/{host_name}/1.3.6.1.2.1.31.1.1.1.6.[{interface}],600s)>{limit}'.format(host_name=host_name, interface=policy[1], limit=policy[0])

        elif policy[2] == 'o':
            description = interfaces + " " + "Outbound " + str(int(int(policy[0])/1000000)) +"m"
            expression = 'avg(/{host_name}/1.3.6.1.2.1.31.1.1.1.10.[{interface}],600s)>{limit}'.format(host_name=host_name, interface=policy[1], limit=policy[0])

        trigger_create = zapi.trigger.create({
            'description': description,
            'expression': expression,
            'priority': priority,
            'status': 0,  # 0 - enabled, 1 - disabled
            'type': 0,  # 0 - trigger, 1 - discovery
            'dependencies': [],
            })


 
zapi.user.logout()

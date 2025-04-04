#!/usr/bin/python3
import subprocess
import re



def start_snmp(IP,community):
        #snmpwalk into the Router Policers
        content = subprocess.run(["snmpwalk" ,"-v2c", "-c", community ,IP + ":161", "1.3.6.1.4.1.9.9.166.1.5.1.1.2"],capture_output=True)

        #split content
        content = content.stdout.decode("utf-8")
        
        #split the content
        content = content.split("\n")[3::4]
        new_content = []
        for line in content:
            if line != "":
                OID = line.split(" = ")
                map_oid = OID[0].replace("iso.3.6.1.4.1.9.9.166.1.5.1.1.2.","").split(".")[0] # 482.65538
                policy = OID[1].split(" ")[1] #Gauge32: 1711869248

                Direction = "1.3.6.1.4.1.9.9.166.1.1.1.1.3." + map_oid
                Direction = subprocess.run(["snmpwalk" ,"-v2c", "-c", community ,IP + ":161", Direction],capture_output=True)
                Direction = Direction.stdout.decode("utf-8").strip("\n")
                Direction = Direction.split(" = ")[1].split(" ")[1]

                if Direction == '1':## Inbound
                    Direction = 'i'
                elif Direction == '2':##Outbound
                    Direction = 'o'

                ifindex = "1.3.6.1.4.1.9.9.166.1.1.1.1.4." + map_oid
                ifindex = subprocess.run(["snmpwalk" ,"-v2c", "-c", community ,IP + ":161", ifindex],capture_output=True)
                ifindex = ifindex.stdout.decode("utf-8").strip("\n")
                ifindex = ifindex.split(" = ")[1].split(" ")[1]

                ifDesc = "1.3.6.1.2.1.31.1.1.1.1." + ifindex
                ifDesc = subprocess.run(["snmpwalk" ,"-v2c", "-c", community ,IP + ":161", ifDesc],capture_output=True)
                ifDesc = ifDesc.stdout.decode("utf-8")
                ifDesc = re.findall("\".*\"$",ifDesc)[0][1:-1]
                

                policy_OID =  "1.3.6.1.4.1.9.9.166.1.12.1.1.1."+ policy
                speed_OID = subprocess.run(["snmpwalk" ,"-v2c", "-c", community ,IP + ":161", policy_OID],capture_output=True)
                speed_OID = speed_OID.stdout.decode("utf-8")
                speed = speed_OID.split(' = ')[1].split(' ')[1].strip("\n")
                
                new_content.append([speed,ifDesc,Direction])
        return new_content





# 1.3.6.1.4.1.9.9.166.1.1.1.1.4 [ifindex]
# 1.3.6.1.2.1.31.1.1.1.1. + ifindex  [ifname]
# 1.3.6.1.4.1.9.9.166.1.1.1.1.3 [direction]
# 1.3.6.1.4.1.9.9.166.1.5.1.1.2 + OID + 65538  last number is class default gets all configs of interface policies [map]
# 1.3.6.1.4.1.9.9.166.1.12.1.1.1 + [map] gets the speed

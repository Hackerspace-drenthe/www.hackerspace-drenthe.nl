---
title: "Netwerk"
menu: "Netwerk"
visible: false
status: draft
reviewed_by: ""
reviewed_at: ""
source_title: "Netwerk"
source_url: "https://wiki.hackerspace-drenthe.nl/wiki/Netwerk"
---

# Coevorden
## IP gegevens
* subnet: 10.0.0.0/24
* gateway: 10.0.0.1
* dhcp range: 100-254

## WIFI
* SSID: HSD
* Password: hsd31337

## Static IPs intern:
* 10.0.0.1: gateway/router (op proxmox) -> ip aan de kant van het schoolnetwerk: 10.1.24.6/23
* 10.0.0.2: Proxmox server [https://10.0.0.2:8006/](https://10.0.0.2:8006/) (ledder dingen)
* 10.0.0.3: Proxmox server DELL   [https://10.0.0.3:8006/](https://10.0.0.3:8006/#v1:0:18:4:::::::) (router/dhcp server opnnsense)
* 10.0.0.5: Ledder vm
* 10.0.0.6: IPMI proxmox server
* 10.0.0.7: fileserver
* 10.0.0.8: iDRAC DELL
* 10.0.0.25: hsd grote cnc machine
* 10.0.0.42: Muziek Server http://10.0.0.42/ (en kassa laptop)
* http://10.0.0.2:8080/#/ : Zigbee2mqtt
* http://10.0.0.2:3000/   lichtkrant kast (72 x 18 pixels)
* [http://10.0.0.2:3001/](http://10.0.0.2:3000/)   lichtkrant raam (75 x 8 pixels)
* [http://10.0.0.2:3002/](http://10.0.0.2:3000/)   lichtkrant frame (32 x 32 pixels)

## Dhcp intern:
* http://10.0.0.143/    led banner ding raam
* http://10.0.0.123:3000/   cirkel lichtkrant boven lounge (ledder)
*https://10.0.0.204:4343/ Aruba accesspoints
*http://10.0.0.205/ netgear POE switch
*http://10.0.0.216  NODE1 lounge kast (space state knop etc)
*http://10.0.0.209/ Ronde bloempot ledding in kast (WLED)
*http://10.0.0.210  Kristal MCH led-ding (WLED)
*http://10.0.0.200:8123/lovelace/default_view  homeassist (volgensmij is deze er niet meer?)

## Services
* mqtt: mqtt.hackerspace-drenthe.nl
**user: HSD
**password: hsd31337
**example: **mosquitto_sub -h mqtt.hackerspace-drenthe.nl -t '#' -u HSD -P hsd31337 -v**
*node-red: https://mqtt.hackerspace-drenthe.nl/

* Fileserver:
** luie regel op command line:  **mount -tcifs -oguest //10.0.0.7/storage /mnt**
** nette regel in /etc/fstab: **//10.0.0.7/storage /mnt/hsd cifs noauto,guest 0 0**  <br />

# Emmen
Switch op houten rek doet de uplink.

vlan 1= greenwise

vlan 2=HSD

poort 1 is uplink greenwise coreswitch poort 7  (1U 2T)

poort. 2 is uplink unifi AP in HSD ruimte via POE injector  (1U 2T)

poort 3 is greenwise/switch management (1U)

poort 4 is uplink HSD, (2U)

## IP Gegevens
* subnet: **<u>192.168.2</u>.0**/24
* gateway: **192.168.2.1**
* dhcp range: **50-254**

## Static IPs intern:
* Docker server in werkplaats: 192.168.2.3. (ledder/asterisk/spaceapi2leds)
* HP switch in de houten serverkast: 192.168.2.**10 (alleen via mangement poort 3 / vlan 1)**
* Grote CNC machine: 192.168.2.**11**
* Elger01: 192.168.2.**12**
* Elger02: 192.168.2.**13**
* idrac-HZ5S813 PowerEdge R340: 192.168.2.**14**
* pve01: 192.168.2.**15:8006** - draait op idrac-HZ5S813
* pve02: 192.168.2.**16:8006** - draait op Elger01
* pve03: 192.168.2.**17:8006** - draait op Elger02
* ILOCZJ3180JL8 (ProLiant DL360p Gen8): 192.168.2.**18**
* Proxmox Backup Server: 192.168.2.**19:8007** - draait op ILOCZJ3180JL8
* NPM 192.168.2.**20:81**
* Vaultwarden 192.168.2.**21:8000**
* Tickets (test-server) (Pretix) 192.168.2.**22**
* Tickets (productie-server) (Pretix) 192.168.2.**23**
* Owncast 192.168.2.**24:8080**
* Listmonk 192.168.2.**25:9000**
* Node-red 192.168.2.**26:1880**
* Excalidraw 192.168.2.**28:3000**
* Redis (productie-server) 192.168.2.**46:6379**
* PostgreSQL (productie-server) 192.168.2.**47:5432** (incl. adminer)
* Redis (test-server) 192.168.2.**48:6379**
* PostgreSQL (test-server) 192.168.2.**49:5432** (incl. adminer)

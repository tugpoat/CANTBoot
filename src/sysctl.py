#system control helpers.
#requires provisions to be made in sudo/wheel config.

import os
from subprocess import run, PIPE
from string import Template

import ipaddress

def remount_rw(mountpoint : str):
	os.system("sudo mount -o remount,rw "+mountpoint)

def remount_ro(mountpoint : str):
	os.system("sudo mount -o remount,ro "+mountpoint)

def reboot_system():
	os.system("sudo reboot")

def shutdown_system():
	os.system("sudo shutdown -h now")

def set_ifconfig(iface : str, ip : str, mask : str):
	os.system("sudo ifconfig ? ? netmask ?", [iface, ip, mask])

def disable_sshd():
	os.system("sudo systemctl disable ssh")
	os.system("sudo service ssh disable")

def enable_sshd():
	os.system("sudo systemctl enable ssh")
	os.system("sudo service ssh start")

def enable_ftpd(newpass):
	remount_rw('/mnt/roms')
	remount_rw('/mnt/cfg')

	#set new password for ftp user
	p = run(['passwd', 'naomiftp'], stdout=PIPE,
        input=newpass+"\n"+newpass+"\n", encoding='ascii')

	os.system("sudo service vsftpd start")

def disable_ftpd():
	remount_ro('/mnt/roms')
	remount_ro('/mnt/cfg')
	os.system("sudo service vsftpd stop")

def disable_dnsmasq():
	os.system("sudo service dnsmasq stop")
	os.system("sudo systemctl disable dnsmasq")

def enable_dnsmasq():
	os.system("sudo systemctl enable dnsmasq")
	os.system("sudo service dnsmasq start")

def disable_hostapd():
	os.system("sudo service hostapd stop")
	os.system("sudo systemctl disable hostapd")

def enable_hostapd():
	os.system("sudo systemctl enable hostapd")
	os.system("sudo service hostapd start")

def disable_wpasupplicant():
	os.system("sudo systemctl disable wpa_supplicant")
	os.system("sudo service wpa_supplicant stop")


def enable_wpasupplicant():
	os.system("sudo systemctl enable wpa_supplicant")
	os.system("sudo service wpa_supplicant start")


def iptables_ap():
	eth0n = ipaddress.IPv4Interface(prefs.get('Network', 'eth0_ip')+"/"+prefs.get('Network', 'eth0_netmask'))
	wlan0n = ipaddress.IPv4Interface(prefs.get('Network', 'wlan0_ip')+"/"+prefs.get('Network', 'wlan0_netmask'))
	td = {
		'ip': prefs.get('Network', 'wlan0_ip'),
	}
	with open('/etc/iptables/rules.v4.pytpl') as tin:
		data = Template(tin.read())
		data = data.substitute(td)
		with open('/etc/iptables/rules.v4', 'w') as outfile:
				outfile.write(data)
				outfile.close()
		tin.close()

	os.system('iptables-restore < /etc/iptables/rules.v4')

def iptables_client():
	os.system('iptables -F')
	os.system('iptables -t nat -F')

#FIXME: actually read from stdout
def get_ifstate(iface : str):
	#get output from ifconfig to check up on live configuration data/state
	os.system("ifconfig "+iface)

#FIXME: actually read from stdout
def get_wlanstate(iface : str):
	#get output from iwconfig to check up on live state
	os.system("sudo iwconfig "+iface)



#FIXME: remove the logic from this part later and clean it up. just get it working for now.
def write_ifconfig(prefs):
	#We should be templating this but I don't really want to deal with that extra dependency
	with open("/etc/network/interfaces.default") as defaultconf:
		data=defaultconf.readlines()
		defaultconf.close()

	eth0n = ipaddress.IPv4Interface(prefs.get('Network', 'eth0_ip')+"/"+prefs.get('Network', 'eth0_netmask'))
	wlan0n = ipaddress.IPv4Interface(prefs.get('Network', 'wlan0_ip')+"/"+prefs.get('Network', 'wlan0_netmask'))

	td = {
		'eth0_ip': str(eth0n.ip),
		'eth0_mask': prefs.get('Network', 'eth0_netmask'),
		'eth0_netw': str(eth0n.network.network_address),
		'eth0_bcast': str(eth0n.network.broadcast_address),

	}

	data.append("#-----Managed by CANTBoot, don't touch\n")
	data.append("auto lo\n")
	data.append("iface lo inet loopback\n")

	with open ("/etc/network/interfaces", "w") as outfile:
		data.append("\nauto eth0\n")
		if prefs.get('Network', 'eth0_mode') == 'static':
			data.append("iface eth0 inet static\n")
			data.append("address "+str(eth0n.ip)+"\n")
			data.append("netmask "+prefs.get('Network', 'eth0_netmask')+"\n")

			data.append("network "+str(eth0n.network.network_address)+"\n")
			data.append("broadcast "+str(eth0n.network.broadcast_address)+"\n")
		else:
			data.append("iface eth0 inet auto\n")
			
		if prefs.get('Network', 'wlan0_mode').lower() != 'disabled':
			data.append("\nallow-hotplug wlan0\n")
			# Don't allow DHCP if we're running as an AP.
			if prefs.get('Network', 'wlan0_mode') == 'client' and prefs.get('Network', 'wlan0_dhcp_client') == 'True':
				data.append("iface wlan0 inet auto\n")
				#DHCP setting
			else:
				data.append("iface wlan0 inet static\n")
				data.append("address "+str(wlan0n.ip)+"\n")
				data.append("netmask "+prefs.get('Network', 'wlan0_netmask')+"\n")
				data.append("network "+str(wlan0n.network.network_address)+"\n")
				data.append("broadcast "+str(wlan0n.network.broadcast_address)+"\n")

		outfile.writelines(data)


#FIXME: remove the logic from this part later and clean it up. just get it working for now.
def write_iwconfig(prefs):

	#eth0n = ipaddress.IPv4Interface(prefs.get('Network', 'eth0_ip')+"/"+prefs.get('Network', 'eth0_netmask'))
	#wlan0n = ipaddress.IPv4Interface(prefs.get('Network', 'wlan0_ip')+"/"+prefs.get('Network', 'wlan0_netmask'))
	td = {
		'ip': prefs.get('Network', 'wlan0_ip'),
		'dhcp_low': prefs.get('Network', 'wlan0_dhcp_low'),
		'dhcp_high': prefs.get('Network', 'wlan0_dhcp_high'),
		'ssid': prefs.get('Network', 'wlan0_ssid'),
		'psk': prefs.get('Network', 'wlan0_psk')
	}

	files = ['/etc/dnsmasq.conf', '/etc/iptables/rules.v4']

	#client?
	if prefs.get('Network', 'wlan0_mode') == 'client':
		files.append('/etc/wpa_supplicant/wpa_supplicant.conf')
	elif prefs.get('Network', 'wlan0_mode') == 'ap':
		files.append('/etc/hostapd/hostapd.conf')

	for f in files:
		with open(f + '.pytpl') as tin:
			data = Template(tin.read())
			data = data.substitute(td)
			with open(f, "w") as outfile:
				outfile.write(data)
				outfile.close()

			tin.close()

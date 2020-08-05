#system control helpers.
#requires provisions to be made in sudo/wheel config.

import os

def remount_rw(mountpoint : str):
	os.system("sudo mount -o remount,rw %s", mountpoint)

def remount_ro(mountpoint : str):
	os.system("sudo mount -o remount,ro %s", mountpoint)

def reboot_system():
	os.system("sudo reboot")

def shutdown_system():
	os.system("sudo shutdown -h now")

def set_ifconfig(iface : str, ip : str, mask : str):
	os.system("sudo ifconfig ? ? netmask ?", [iface, ip, mask])

def disable_sshd():
	os.system("sudo service ssh stop")
	os.system("sudo service ssh disable")

def enable_sshd():
	os.system("sudo service ssh enable")
	os.system("sudo service ssh start")

def disable_dnsmasq():
	os.system("sudo service dnsmasq stop")
	os.system("sudo service dnsmasq disable")

def enable_dnsmasq():
	os.system("sudo service dnsmasq enable")
	os.system("sudo service dnsmasq start")

def disable_hostapd():
	os.system("sudo service hostapd stop")
	os.system("sudo service hostapd disable")

def enable_hostapd():
	os.system("sudo service hostapd enable")
	os.system("sudo service hostapd start")

def get_ifstate(iface : str):
	#get output from ifconfig to check up on live configuration data/state
	os.system("ifconfig "+iface)

def get_wlanstate(iface : str):
	#get output from iwconfig to check up on live state
	os.system("sudo iwconfig "+iface)


#FIXME: remove the logic from this part later and clean it up. just get it working for now.
def write_ifconfig(prefs):
	#We should be templating this but I don't really want to deal with that extra dependency
	with open("/etc/network/interfaces.default") as defaultconf:
		data=defaultconf.readlines()
		defaultconf.close()

	data.append("#-----Managed by ACNTBoot, don't touch")
	data.append("auto lo")
	data.append("iface lo inet loopback")


	with open ("/etc/network/interfaces", "rw") as outfile:

		data.append("auto eth0")
		if prefs.get('Network', 'eth0_mode') == 'static':
			data.append("iface eth0 inet static")
			data.append("address ?", [prefs.get('Network', 'eth0_ip')])
			data.append("netmask ?", [prefs.get('Network', 'eth0_netmask')])

			#TODO: do bitwise operations to figure out the network and bcast from ip and mask.
			#data.append("network ?", [])
			data.append("network ?", [prefs.get('Network', 'eth0_network')])
			data.append("broadcast ?", [prefs.get('Network', 'eth0_bcast')])

		data.append("allow-hotplug wlan0")
		# Don't allow DHCP if we're running as an AP.
		if (prefs.get('Network', 'wlan0_ip') == 'dhcp' or prefs.get('Network', 'wlan0_subnet') == 'dhcp') and prefs.get('Network', 'wlan0_mode') == 'client':
			setdhcp()
			#DHCP setting
		else:
			data.append("iface wlan0 inet static")
			data.append("address ?", [prefs.get('Network', 'wlan0_ip')])
			data.append("netmask ?", [prefs.get('Network', 'wlan0_netmask')])
			data.append("network ?", [prefs.get('Network', 'wlan0_network')])
			data.append("broadcast ?", [prefs.get('Network', 'wlan0_bcast')])

	outfile.writelines(data)
	outfile.close()

#FIXME: remove the logic from this part later and clean it up. just get it working for now.
def write_iwconfig(prefs):

	#client?
	if (prefs.get('Network', 'wlan0_ip') == 'dhcp' or prefs.get('Network', 'wlan0_subnet') == 'dhcp') and prefs.get('Network', 'wlan0_mode') == 'client':
		with open("/etc/wpa_supplicant/wpa_supplicant.conf",  "rw") as outfile:

			data = "country=US\nctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\nupdate_config=1\n\nnetwork={\nssid=\"%s\"\nscan_ssid=1\npsk=\"%s\"\nkey_mgmt=WPA-PSK\n}\n"  % (prefs.get('Network', 'wlan0_ssid'), prefs.get('Network', 'wlan0_psk')))

			outfile.writelines(data)
			outfile.close()
	else:

		#not client. ap.

		#hostapd
		with open("/etc/hostapd/hostapd.conf",  "rw") as outfile:
			data ="interface=wlan0\ndriver=nl80211\nsid=%s\n\nhw_mode=g\nchannel=6\nieee80211n=1\nwmm_enabled=1\nht_capab=[HT40][SHORT-GI-20][DSSS_CCK-40]\nmacaddr_acl=0\nauth_algs=1\nignore_broadcast_ssid=0\nwpa=2\nwpa_key_mgmt=WPA-PSK\nwpa_passphrase=%s\nrsn_pairwise=CCMP"  % (prefs.get('Network', 'wlan0_ssid'), prefs.get('Network', 'wlan0_psk'))
			outfile.writelines(data)
			outfile.close()

		#dnsmasq
		with open("/etc/dnsmasq.conf", "rw") as outfile:
			data="interface=wlan0\nlisten-address=%s\nbind-interfaces\n#server=8.8.8.8\n#domain-needed\nbogus-priv\ndhcp-range=%s,%s,24h" % (prefs.get('Network', 'wlan0_ip'), prefs.get('Network', 'wlan0_dhcp_low'), prefs.get('Network', 'wlan0_dhcp_high'))
			outfile.writelines(data)
			outfile.close()

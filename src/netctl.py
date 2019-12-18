'''
containers for abstracting network configuration/state.
we an just use two instances for application config and system config/live state
'''
class NetIfConfigState:
	_name = None

	_ipv4_address = None
	_ipv4_netmask = None

	_ipv6_address = None # NetDIMM doesn't support IPv6 so maybe only use it for external network comms

	_link_state = None

	_wifi = None

#this one gets attached to a NetIfConfigState if the interface is using wifi
class WifiConfigState:
	_mode = None
	_ssid = None
	_psk = None #it's technically bad practice to store the psk in memory like this but whatever, it's stored plaintext in /etc anyway and this isn't exactly a high-risk application.

	_state = None

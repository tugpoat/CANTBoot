ACNTBoot
========
********WARNING: THIS MAY OR MAY NOT WORK.

It should work and load games and stuff, and I try my best to make sure that it does with each commit.

ACNTBoot is loosely based on NAOMIWeb, and started life as a fork of it.
### Github links:
		- https://github.com/root670/NaomiWeb
		- https://github.com/tugpoat/NaomiWeb
		- https://github.com/tugpoat/ACNTBoot

I wanted a cleanly-written, easy-to-use, efficient, and easily extensible loader, which was also functional and pleasant to look at.
I couldn't find one, so I wrote it.
This will be what I think a NetDIMM loader should be.

It's written in Python 3, using Bottle and Bootstrap.

Note: This is still a major work in progress.

Requirements
------------
### Hardware:
 * Any of the following:
 	- Sega NAOMI mainboard (Must use one of the following BIOS revisions: E, F, G, H. Region shouldn't matter)
 	- Sega NAOMI 2 mainboard (Any BIOS revision will work)
 	- Sega Chihiro
 	- Triforce

 * NetDIMM cartridge w/ security PIC (NULL PIC recommended, but other PICs may work)
 * Raspberry Pi 3,4 (2 may work but will not be supported)
 * CAT5 Crossover Cable

### Software:
 * Raspbian -- Other Linux distros should work, but haven't been rubberstamped (Works fine on my gentoo-based laptop minus GPIO functionality).
 * Python 3.6+ with:
 	-bottle
  -hashlib
 	-json
  -pymessagebus
 	-sqlite3
  -threads
 * NetDIMM-compatible game images (these are usually .bin files; you're on your own to find these!)

Software Setup (TODO)
---------------------

Hardware Setup Examples
-----------------------
### Single DIMM:

    +---------+                         +--------------+
    | NetDIMM | <==[Crossover Cable]==> | Raspberry Pi |
    +---------+                         +--------------+
                                              /\
                                              ||
                                        [WiFi Connection]
                                              ||
                                              \/
                                      +------------------+
                                      | Internet Browser |
                                      +------------------+

### Multiple DIMMs (IN PROGRESS):

    +---------+
    | NetDIMM | <==[Straight-thru Cable]==|
    +---------+                          ||
                                         ||    +--------+
                                         |===> |        |
    +---------+                                |        |                              +--------------+                      +-------------+
    | NetDIMM | <==[Straight-thru Cable]=====> | Switch | <==[Straight-thru Cable]==>  | Raspberry Pi | <~~[ WiFi/Wired ]~~> | Web Browser |
    +---------+                                |        |                              +--------------+                      +-------------+
                                         |===> |        |
                                         ||    +--------+
    +---------+                          ||
    | NetDIMM | <==[Straight-thru Cable]==|
    +---------+

### API Master/Slave mode (STRETCH GOAL):
This would allow for very large deployments with great manageability, and enable one to just toss a RasPi into a cabinet, hook up another one elsewhere and never have to go into the cabinet to mess with it. Could live patch and then transfer games over wifi to the slave node and boot from there.

    +---------+                            +-----------------+                    +------------+
    | NetDIMM | <==[Straight-thru Cable]==>| API Slave RasPi | <~~[WiFi/Wired]~~~>|            |
    +---------+                            +-----------------+                    | API Master |                  +-------------+
                                                                             //~~>| RasPi      |<~~[WiFi/Wired]~~>| Web Browser |
    +---------+                            +-----------------+                    | Web UI     |                  +-------------+
    | NetDIMM | <==[Straight-thru Cable]==>| API Slave RasPi | <~~[WiFi/Wired]~~~>|            |
    +---------+                            +-----------------+                    +------------+

DONE
----
 * Ditch the whole "install games to database" thing and just dump the gamelist out to YAML on the games partition
 * Messagebus
 * Plug everything into the messagebus
 * Redo Web UI for event-based operation
 * Redo Web UI for multinode
 * GPIO Reset
 * Redo Web UI for multinode (add/delete functionality)

In Progress
----
  * Adafruit UI
  * Interface for Network Configuration (WiFi SSID, PSK, IP, DNS options, etc.)
  * Interface for System Settings/Commands (Power off, Reboot, Manual GPIO Reset, etc.)
  * Live/in-place binary patching of ROMs
  * API Master/Slave modes for large networks and GPIO reset support for every node

On Hold
----
  * Catch exit signals and close everything properly
  * Unit tests and E2E tests
  * Set up build pipeline and automatic SD image generation

Todo
----
 * DHCP configuration of NetDIMM(s)
 * Card emulation
 * Some kind of user authentication so some dingus on the network can't just reconfigure everything
 * Some kind of API authentication so some dingus on the network can't just reconfigure everything
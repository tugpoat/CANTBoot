ACNTBoot
========
********WARNING: THIS DOES NOT WORK YET.********

It might work. It might load games and stuff, and I try my best to make sure that it does with each commit.
No guarantees though. Use at your own risk.

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
 * Raspberry Pi 3 (2 may work but will not be supported)
 * CAT5 Crossover Cable

### Software:
 * Raspbian (other Linux distros should work, but haven't been tested)
 * Python 3.3+ with:
 	-asyncio
 	-bottle
  	-hashlib
 	-json
 	-multiprocessing
 	-sqlite3
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

Todo
----
 * MESSAGEBUS. JEBUS. WHY AM I PUTTING THIS OFF? IT WILL MAKE EVERYTHING SUPER COOL AND SMOOTH AND EVENT DRIVEN, AND ENABLE FUTURE GROWTH.
 * Redo Web UI for event-based operation
 * Redo Web UI for multinode mode
 * Adafruit UI
 * GPIO Reset (Supported, but needs to get plugged in properly)
 * DHCP configuration of NetDIMM(s)
 * Interface for Network Configuration (WiFi SSID, PSK, IP, DNS options, etc.)
 * Interface for System Settings/Commands (Power off, Reboot, Manual GPIO Reset, etc.)
 * Card emulation
 * Live binary patching of ROMs, in RAM. (Useful for preservation of original game data and updatability).
 * API Master/Slave modes for large networks
 * Catch exit signals and close everything properly
 * Unit tests and E2E tests
 * Set up build pipeline and automatic SD image generation

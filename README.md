ACNTBoot
========
********WARNING: THIS DOES NOT WORK YET.********

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

### Multiple DIMMs:

    +---------+
    | NetDIMM | <==[Straight-thru Cable]==|
    +---------+                          ||
                                         ||    +--------+
                                         |===> |        |
    +---------+                                |        |                              +--------------+                         +-------------+
    | NetDIMM | <==[Straight-thru Cable]=====> | Switch | <==[Straight-thru Cable]==>  | Raspberry Pi | <==[WiFi Connection]==> | Web Browser |
    +---------+                                |        |                              +--------------+                         +-------------+
                                         |===> |        |
                                         ||    +--------+
    +---------+                          ||
    | NetDIMM | <==[Straight-thru Cable]==|
    +---------+

Todo
----
 * Make the dang thing work
 * Web UI
 * Adafruit UI
 * GPIO Reset
 * DHCP configuration of NetDIMM(s)
 * Interface for Network Configuration (WiFi SSID, PSK, IP, DNS options, etc.)
 * Interface for System Settings/Commands (Power off, Reboot, Manual GPIO Reset, etc.)
 * Card emulation
 * Multiboot
 * Style the edit buttons to actually look and flow nice
 * Catch exit signals and close everything properly
 * Incorporate actual messaging between load jobs and interface
 * Unit tests and E2E tests
 * Set up build pipeline and automatic SD image generation

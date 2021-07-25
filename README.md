CANTBoot
========
********WARNING: THIS MAY OR MAY NOT WORK.

It should work and load games and stuff, and I try my best to make sure that it does with each commit.

CANTBoot is loosely based on NAOMIWeb, and started life as a fork of it.
### Github links:
    - https://github.com/root670/NaomiWeb
    - https://github.com/tugpoat/NaomiWeb
    - https://github.com/tugpoat/CANTBoot

I wanted a cleanly-written, easy-to-use, efficient, and easily extensible loader, which was also functional and pleasant to look at.
I couldn't find one, so I wrote it. It's currently a bit more gross than I'd like, however.
This will be what I think a NetDIMM loader should be.

It's written in Python 3, using Bottle and Bootstrap.

Note: This is still a major work in progress.

Requirements
------------
### Hardware:
 * Any of the following:
  - Sega NAOMI mainboard (Must use one of the following BIOS revisions: E, F, G, H. Region shouldn't matter)
  - Sega NAOMI 2 mainboard (BIOS revision A or later)
  - Sega Chihiro (TODO)
  - Triforce (TODO)

 * NetDIMM cartridge w/ security PIC (NULL PIC recommended, but other PICs may work)
 * Raspberry Pi 3,4 (2 may work but will not be supported)
 * RJ45-terminated Cat5/6 cable(s) as needed

### Software:
 * Raspbian -- Other Linux distros should work, but haven't been rubberstamped (Works fine on my gentoo-based laptop minus GPIO functionality).
 * Python 3.6+ with:
  -bottle
  -beaker
  -hashlib
  -pymessagebus
  -smbus
  -sqlite3
  -threads
  -pyyaml
 * NetDIMM-compatible game images (these are usually .bin files; you're on your own to find these!)

Software Setup (TODO)
---------------------

Hardware Setup Examples
-----------------------
NOTE: You can use a straight through or crossover cable on a RasPi 3 or 4. The ports are autosensing, it doesn't care.
      On a 2 you might have to use a crossover cable between the NetDIMM and the Pi. I don't know, I haven't tested it and I don't care to.

### Single DIMM:

                         [ GPIO Reset ] -------
                                              |
    +---------+                         +--------------+
    | NetDIMM | <====[cat5/6+rj45]====> | Raspberry Pi |
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
    | NetDIMM | <==[cat5/6+rj45]===|
    +---------+                   ||
                                  ||    +--------+
                                  |===> |        |
    +---------+                         |        |                      +--------------+
    | NetDIMM | <===[cat5/6+rj45]=====> | Switch | <==[cat5/6+rj45]===> | Raspberry Pi |
    +---------+                         |        |                      +--------------+
                                  |===> |        |                             /\
                                  ||    +--------+                             ||
    +---------+                   ||                                      [ WiFi/Wired ]
    | NetDIMM | <==[cat5/6+rj45]===|                                           ||
    +---------+                                                                \/
                                                                        +--------------+
                                                                        |  Web Browser |
                                                                        +--------------+

### API Master/Slave mode (IN PROGRESS):
This would allow for very large deployments with great manageability, and enable one to just toss a RasPi into a cabinet, hook up another one elsewhere and never have to go into the cabinet to mess with it. Could live patch and then transfer games over wifi to the slave node and boot from there. Also, this would enable every node to be able to GPIO reset.

                      [ GPIO Reset ] -------
                                           |
    +---------+                    +-----------------+              +-------------+
    | NetDIMM | <==[cat5/6+rj45]==>| API Slave RasPi | <~~[WiFi]~~~>|             |
    +---------+                    +-----------------+              | API Master  |
                                                               //~~>| RasPi       |
    +---------+                    +-----------------+              | Web UI      |
    | NetDIMM | <==[cat5/6+rj45]==>| API Slave RasPi | <~~[WiFi]~~~>|             |
    +---------+                    +-----------------+              +-------------+
                                           |                              /\
                      [ GPIO Reset ] -------                              ||
                                                                    [ WiFi/Wired ]
                                                                          ||
                                                                          \/
                                                                    +-------------+
                                                                    | Web Browser |
                                                                    +-------------+

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
  * Catch exit signals and close everything properly 

On Hold
----
  * Unit tests and E2E tests
  * Set up build pipeline and automatic SD image generation

TODO
----
 * DHCP configuration of NetDIMM(s)
 * Card emulation
 * Implement DragonMinded's universal freeplay/monitor force patches
 * Some kind of user authentication so some dingus on the network can't just reconfigure everything
 * Some kind of API authentication so some dingus on the network can't just reconfigure everything

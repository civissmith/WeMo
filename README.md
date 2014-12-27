WeMo
====

Belkin WeMo Control System

The project contains the source code for a Python-based sytem to control the Belkin WeMo family of home automation devices. The following assumptions/design decisions have been made.

1 General Design

The system is split into two major components, a client application and a daemon. The client application is intended to be the user-facing portion of the system. It should use the commands exposed by the daemon's API instead of trying to access the Wemo class directly. Typically the client will issue a command in the format 'send( "cmd_name", "arg1 arg2 argn")'. The 'cmd_name' field should be one of the registered commands in the daemon and the string of arguments should be separated by whitespace.

The daemon is in charge of listening for user commands and processing them. The commands from the user will translate to actions on the WeMo devices. For instance, the "on_cmd" in the daemon will turn on the WeMo switch that is passed as an argument. The daemon uses instances of the WemoSocket class and WemoSensor class to communicate with the physical devices.

2 The daemon does not make any assumptions about the state (# of devices, device status, etc.)

Belkin has apps that can change the system externally and the daemon can run on multiple computers, so the daemon will not assume anything about the current state.

3 The daemon will refresh it's device list periodically 

Since the daemon doesn't know ahead of time how many devices are on the network, it will periodically query to see what devices are there. This technique was also chosen because the WeMo devices will periodically change the IP address and port that they'll respond to (the port changes far more frequently than the IP address).

4 The daemon is a single event loop (no threading)

The event loop manages the entire process of listening for client communication, processing commands and updating device lists. While threading may be a nice addition later, the initial design simply didn't need it.

5 IPC

The system uses local BSD sockets for communication. The intent was to have a user layer and a control layer that didn't rely on each other to run. Since Python doesn't play nicely with Sys-V IPC, local BSD sockets were chosen as the message passing mechanism. The daemon will create on endpoint to recieve commands from the client and will expect to send data on another. The client should ensure that it uses the same endpoints (make sure to connect client.tx -> daemon.rx, client.rx -> daemon.tx).


File Layout:

wemod - The daemon. This module contains the daemon code that creates a server and listens for commands.

client.py - A rough demo of a client app. It uses just a handful of supported commands and is really just to show the concept.

Wemo.py - Contains the Wemo classes. This module is creates the object representation of the different WeMo devices.

icons - directory containing different icons that can be used if desired.

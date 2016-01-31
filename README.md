# hdc1000evm
Python Wrapper to access HDC1000 measurements on the HDC1000EVM

# ReadMe for the Python class HDC1000EVM to interface to the HDC1000EVM stick to read temperature and humidity.

The software is inspired by work of [Doug Wyman](http://www.element14.com/community/people/wymand/blog/2015/04/16/hdc1000evm-python-code-for-raspberry-pi). With own re-engineering of the communication between the stick and its demo-tool, the messages have been decoded so that temperature and humidity can be read.

# Table of Contents
1. HDC1000EVM
2. Intention 
3. Usage

# 1. HDC1000EVM
The stick is an evaluation kit for the HDC1000. The sensor is attached to a microcontroller, that works as bridge between the I2C-interface of the sensor and the USB-interface. From the software side, the stick is visible as serial interface tunneled via USB.

# 2. Intention
A HDC1000EVM-object should hide away the communication with the sensor an provides a simple interface to read out temperature and humidity as a pair. The class can be extended to read out the other registers of the sensor. 

The class can even so be an example to communicate with other peripherals one can attach to the I2C-bus of the stick.

# 3. Usage
The serial interface of the stick is visible in the OS. The class HDC1000EVM needs to know the path to the serial interface on creation. All following connection attemps are via that path. On the Linux-System, the path looks for example like:  
/dev/serial/by-path/platform-20980000.usb-usb-0:1.2:1.0

Before reading temperature and humidtiy, the object needs to connect to the stick. This may take a short while, as the stick may not respond to the first connection attemp. The object automatically makes addtitional attemps, before giving up with an error.

After connection is established, temperature and humidity are read as pair in combination with a time stamp. The result of the last read can be read again via getter.



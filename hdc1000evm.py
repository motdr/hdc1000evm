import serial
import binascii
import time
import argparse
"""
Wrapper for HDC1000EVM from TI.

Code bases on work from XXX and own reverse engineering.

On the evaluation board the HDC1000 is connected to a MSP processor.
That processor bridges the I2C communication to the USB. The USB
connection appears on the host side as serial interface.

To read out registers, a command is send to the MSP processor via
serial interface. The response contains the requested data. Request
and response messages have fixed length. For reading humidity and
temperature a special request responses both values in one go.

The first command is not responded. It looks like, that this message
is used to adjust the baud rate. The Software provided with the
evaluation kit uses 9600 baud, baud rates of 115k are possible as
well.
"""


class HDC1000:
    def __init__(self, path):
        """
        The assigned HDC1000EVM must be reachable via the given path.
        Argument:
        path -- path to the USB device.
        """
        self.ser = serial.Serial()
        if path is None:
            self.ser.port = "/dev/serial/by-path/platform-3f980000.usb-usb-0:1.4:1.0"
        else:
            self.ser.port = path
        self.ser.baudrate = 115200
        self.ser.bytesize = serial.EIGHTBITS      # number of bits per bytes
        self.ser.parity = serial.PARITY_NONE      # set parity check: no parity
        self.ser.stopbits = serial.STOPBITS_ONE   # number of stop bits
        self.ser.timeout = 2         # timeout block read
        self.ser.xonxoff = False     # disable software flow control
        self.ser.rtscts = False      # disable hardware (RTS/CTS) flow control
        self.ser.dsrdtr = False      # disable hardware (DSR/DTR) flow control
        self.ser.writeTimeout = 2    # timeout for write
        self.lastAnswer = (time.time(), [])
        self.connected = False       # not connected
        self.MESSAGE_LENGTH = 22     # number of bytes expected as answer

    def connect(self):
        """
        Connect to the HDC1000 via USB. The configuration register is read
        out in multiple attemps as the first requests might not responded
        (auto adjustment of baud rate). Returns whether the connection
        could be established or not.
        """
        try:
            self.ser.open()
            # print("serial open")
            for request in range(1, 3):
                self.ser.flushInput()   # flush input buffer, discarding all its contents
                self.ser.flushOutput()  # flush output buffer, aborting current output
                # request configuration register as first connection attemp
                if self.request_configuration():
                    self.connected = True
                    break
        except Exception as e:
            self.ser.close()
            self.connected = False
        return self.connected

    def is_connected(self):
        """ Returns whether HDC1000 is connected or not. """
        return self.connected

    def __send_request(self, data):
        if self.ser.isOpen():
            # print("Request:")
            # print(data)
            try:
                self.ser.flushInput()
                self.ser.write(serial.to_bytes(data))
            except:
                # print("serial write exception")
                self.ser.close()
                self.connected = False
                raise Exception('serial write exception')
        else:
            print("try to send but connection close")

    def __fetch_answer(self, expected):
        result = False
        timeout = 4          # try x seconds to get an answer
        if self.ser.isOpen():
            now = time.time()
            answer = []
            # print("expect answer")
            try:
                while ((time.time()-now) < timeout) and not result:
                    if self.ser.inWaiting() != 0:
                        b = self.ser.read(1)
                        answer.append(b)
                        if len(answer) == expected:
                            result = True
            except:
                # print("fetch answer exception")
                self.ser.close()
                self.connected = False
            if len(answer) > 0:
                # print("Answer:")
                # print(answer)
                # for a in answer:
                #    print(ord(a))
                self.lastAnswer = (time.time(), answer)
        return result

    def request_configuration(self):
        result = False
        if self.ser.isOpen():
            self.__send_request([0x4C, 0x12, 0x01, 0x00, 0x03, 0x40, 0x02, 0x02, 0xD3])
            if self.__fetch_answer(self.MESSAGE_LENGTH):
                if len(self.lastAnswer[1]) == self.MESSAGE_LENGTH and ord(self.lastAnswer[1][6]) == 2:    # crosscheck returned register value
                    # print(self.lastAnswer)
                    self.configuration = ord(self.lastAnswer[1][7])*256+ord(self.lastAnswer[1][8])
                    result = True
                else:
                    print("Result register error")
                    print(self.lastAnswer[1])
            else:
                print("Length error")
                print(len(self.lastAnswer[1]))
        return result

    def read_measurements(self):
        """
        Read humidity and temperature.
        Returns:
        Tuple (timestamp, temperature[C], humidity[%])
        """
        if self.is_connected():
            self.time = 0
            self.temperature = -273
            self.humidity = 0
            try:
                # read both values in one go
                self.__send_request([0x4C, 0x30, 0x01, 0x00, 0x01, 0x40, 0x0F])
                if self.__fetch_answer(self.MESSAGE_LENGTH):
                    # print( self.lastAnswer )
                    if len(self.lastAnswer[1]) > 9:   # crosscheck length to avoid array index error
                        x = ord(self.lastAnswer[1][6]) * 256 + ord(self.lastAnswer[1][7])
                        self.temperature = x / (65536.0)*165 - 40
                        x = ord(self.lastAnswer[1][8]) * 256 + ord(self.lastAnswer[1][9])
                        self.humidity = x / (65536.0) * 100
                        self.time = time.time()
                else:
                    print("no answer")
                    raise Exception('no response')
            except Exception as e:
                print("read Measurement Exception")
                raise Exception('connection lost')
        return (self.time, self.temperature, self.humidity)

if __name__ == '__main__':
    hdc = HDC1000(None)
    if hdc.connect():
        print(hdc.read_measurements())
    else:
        print("connection failed")

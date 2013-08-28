"""

An implement of ping program using Python

"""
import os, time, struct, select, sys
from socket import *
from optparse import OptionParser

ICMP_ECHO_REQUEST = 8

def checksum(str):
    sum = 0
    countTo = (len(str) / 2) * 2
    count = 0
    while count < countTo:
        thisVal = ord(str[count + 1]) * 256 + ord(str[count])
        sum = sum + thisVal
        sum = sum & 0xffffffff
        count = count + 2

    if countTo < len(str):
        sum = sum + ord(str[len(str) - 1])
        sum = sum & 0xffffffff

    sum = (sum >> 16) + (sum & 0xffff)
    sum = sum + (sum >> 16)
    answer =~ sum
    answer = answer & 0xffff

    answer = answer >> 8 | (answer << 8 & 0xff00)

    return answer

class Ping(object):
    sequence = 0
    packets = []
    def __init__(self, dest_addr='127.0.0.1', timeout=1):
        self.dest_addr = dest_addr
        self.timeout = timeout
        self.pid = os.getpid()
        try:
            self.sock = socket(AF_INET, SOCK_RAW, getprotobyname("icmp"))
        except:
            print "This program can only be run by root"
            sys.exit(1)

    def _generatePacket(self):
        # packet structure:
        # type (8), code (8), checksum (16), id (16), sequence (16)
        my_checksum = 0
        header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, my_checksum, self.pid, self.sequence)
        bytesInDouble = struct.calcsize("d")
        data = (192 - bytesInDouble) * "X"
        data = struct.pack("d", time.time()) + data
        # Calculate the checksum on the data and the dummy header.
        my_checksum = checksum(header + data)
        # Now that we have the right checksum, we put that in. It's just easier
        # to make up a new header than to stuff it into the dummy.
        header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, htons(my_checksum), self.pid, self.sequence)
        self.sequence = self.sequence + 1
        return header + data

    def sendPacket(self):
        packet = self._generatePacket()
        self.sock.sendto(packet, (self.dest_addr, 1))

    def receive(self):
        timeLeft = self.timeout
        while True:
            startedSelect = time.time()
            whatReady = select.select([self.sock], [], [], timeLeft)
            howLongInSelect = (time.time() - startedSelect)
            if not whatReady[0]:
                return None
            timeReceived = time.time()
            recPacket, addr = self.sock.recvfrom(1024)
            icmpHeader = recPacket[20:28]
            type, code, checksum, packetID, sequence = struct.unpack("bbHHh", icmpHeader)
            if packetID == self.pid:
                bytesInDouble = struct.calcsize("d")
                timeSent = struct.unpack("d", recPacket[28:28 + bytesInDouble])[0]
                return timeReceived - timeSent

            timeLeft = timeLeft - howLongInSelect
            if timeLeft <= 0:
                return None

class PingCMD(object):
    def __init__(self):
        self.parser = OptionParser()
        self.parser.add_option("-c", "--count", type="int",
                                dest="count", default=5,
                                action="store", help="times to ping")
        self.parser.add_option("-t", "--timeout", type="int",
                                dest="timeout", default=1,
                                action="store", help="timeout for each ping action")
        self.parser.add_option("-s", "--sleeptime", type="int",
                                dest="sleeptime", default=1,
                                action="store", help="sleep time after each ping action")

    def run(self):
        options, args = self.parser.parse_args()

        dest_addr = args[0]

        ping = Ping(dest_addr=dest_addr, timeout=options.timeout)
        for i in range(options.count):
            ping.sendPacket()
            delay = ping.receive()
            if delay:
                print "Ping %s successed, icmp_seq = %s, delay is %.3f ms" % (dest_addr, i, delay * 1000)
            else:
                print "Ping %s failed, timeout" % dest_addr
            time.sleep(options.sleeptime)

if __name__ == '__main__':
    cmd = PingCMD()
    cmd.run()

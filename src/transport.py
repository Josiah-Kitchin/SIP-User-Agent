
import socket 
from abc import abstractmethod


class TransportClient:
    def __init__(self, host: str): 
        self.port = 3000
        if ':' in host: 
            host, self.port = host.split(":", 1)
            self.port = int(self.port)

        self.ip_addr = socket.gethostbyname(host)
        self._addr_type = socket.AF_INET6 if ':' in self.ip_addr else socket.AF_INET


    @abstractmethod
    def send(self, msg: bytes):  
        ... 

    @abstractmethod
    def recv(self, num_bytes: int) -> bytes: 
        ... 

    @abstractmethod 
    def close(self): 
        ... 


class UDPClient(TransportClient): 
    def __init__(self, host: str): 
        super().__init__(host)
        self._socket = socket.socket(self._addr_type, socket.SOCK_DGRAM)

    def send(self, msg: bytes): 
        self._socket.sendto(msg, (self.ip_addr, self.port))

    def recv(self, num_bytes: int) -> bytes: 
        return self._socket.recv(num_bytes)

    def close(self): 
        self._socket.close()

class TCPClient(TransportClient): 
    def __init__(self, host: str): 
        super().__init__(host)
        self._socket = socket.socket(self._addr_type, socket.SOCK_STREAM)
        self._socket.connect((self.ip_addr, self.port))

    def send(self, msg: bytes): 
        sent = 0
        while sent < len(msg): 
            sent += self._socket.send(msg[sent:])

    def recv(self, num_bytes: int) -> bytes: 
        received = bytearray()
        while len(received) < num_bytes: 
            bytes_needed = num_bytes - len(received)
            recv_num = 4096 if bytes_needed > 4096 else bytes_needed
            received += self._socket.recv(recv_num)

        return bytes(received)

    def close(self): 
        self._socket.close()


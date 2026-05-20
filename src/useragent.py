

import sipmsg 
import socket 



class SIPCall: 
    def __init__(self, 
                 uri: str, 
                 sip_server: str, 
                 transport_type: sipmsg.TransportType=sipmsg.TransportType.UDP): 
        self.uri = uri
        self.cseq = 0
        self.hostname = socket.gethostname()










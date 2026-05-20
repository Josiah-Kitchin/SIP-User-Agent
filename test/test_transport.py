
from transport import UDPClient, TCPClient
import threading 
import socket 
import pytest


@pytest.fixture(scope="session")
def udp_server(): 
    """
    UDP socket to be used in tests 
    """
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    addr = "127.0.0.1"
    addr_port = 3000
    server_sock.bind((addr, addr_port))
    return f"{addr}:{addr_port}", server_sock

@pytest.fixture(scope="session") 
def tcp_echo_server_host() -> str: 
    """
    TCP server that echos back response 
    """
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    addr = "127.0.0.1"
    addr_port = 3000
    server_sock.bind((addr, addr_port))
    server_sock.listen()
    def run_tcp_server(): 
        while True: 
            client_socket, _ = server_sock.accept()
            msg = client_socket.recv(4096)
            client_socket.send(msg)

    threading.Thread(target=run_tcp_server, daemon=True).start()
    return f"{addr}:{addr_port}"


def test_tcp_client_send_recv(tcp_echo_server_host: str): 
    cli = TCPClient(tcp_echo_server_host)
    send_msg = "Hello there".encode()
    cli.send(send_msg)
    assert cli.recv(len(send_msg)) == send_msg


def test_udp_client_send(udp_server): 
    host, server_socket = udp_server
    client = UDPClient(host)
    msg = "Hello world!".encode()
    client.send(msg)
    recv_msg = server_socket.recv(len(msg))
    assert msg == recv_msg

def test_udp_client_bad_hostname(): 
    with pytest.raises(Exception): 
        _ = UDPClient("www.fjdkallfjfkdljfklada.fakl")


def test_udp_client_hostname(): 
    _ = UDPClient("www.google.com")









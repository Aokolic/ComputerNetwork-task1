import socket
import threading
from logger import setup_logger

from self_defined_protocol import (
    recv_packet, 
    send_packet, 
    pack_agree, 
    pack_answer,
    TYPE_INIT,
    TYPE_REQUEST,
    TYPE_NAMES
    )

logger = setup_logger('run_log_server.txt')

def handler_client(sock):
    try:
        pkt = recv_packet(sock)
        if pkt['type'] != TYPE_INIT:
            raise RuntimeError(f'Excepted Initialization, got type={TYPE_NAMES.get(pkt["type"])}')
        send_packet(sock, pack_agree())

        for i in range(pkt['n']):
            pkt = recv_packet(sock)
            if pkt['type'] == TYPE_REQUEST:
                data = pkt['data']
                if isinstance(data, bytes):
                    reversed_data = data[::-1]
                    send_packet(sock, pack_answer(reversed_data))
    finally:
        sock.close()
    

if __name__ == '__main__':
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', 8080))
    server_socket.listen()
    while True:
        conn, addr = server_socket.accept()
        print(f'客户端 {addr} 已连接')
        threading.Thread(target=handler_client, args=(conn, )).start()

    
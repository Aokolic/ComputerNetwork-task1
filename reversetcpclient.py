import socket
import argparse
import random
import os
import threading
import sys
from logger import setup_logger
from self_defined_protocol import (
    pack_init,
    pack_request,
    send_packet,
    recv_packet,
    TYPE_AGREE,
    TYPE_ANSWER
)

# 配置logger
logger = setup_logger()

def split_file(total_size: int, Lmin: int, Lmax: int, seed):
    random.seed(seed)
    chunks = []
    remaining = total_size

    while remaining > 0:
        if remaining <= Lmax:
            chunks.append(remaining)
            break
        else:
            chunk_len = random.randint(Lmin, Lmax)
            chunks.append(chunk_len)
            remaining -= chunk_len
    return chunks

parse = argparse.ArgumentParser()
parse.add_argument('serverIP', help='服务器IP地址')
parse.add_argument('serverPort', type=int, help='服务器端口号')
parse.add_argument('--seed', type=int, default=26, help='自定义随机种子，默认为为26')


args = parse.parse_args()

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    client_socket.connect((args.serverIP, args.serverPort))
except Exception as e:
    print(f"连接失败: {e}")
    client_socket.close()
    sys.exit(1)
    
while True:
    file_path = input('输入发送的文件地址：').strip()
    if not file_path:
        print('路径不能为空')
        continue
    try:
        with open(file_path, 'rb') as f:
            file_data = f.read()
        break
    except FileNotFoundError:
        print(f'文件不存在: {file_path}')
    except OSError as e:
        print(f'打开文件失败: {e}')

if len(file_data) == 0:
    print('文件内容为空')
    client_socket.close()
    sys.exit(1)

while True:
    try:
        Lmin = int(input('输入最小发送长度：'))
        Lmax = int(input('输入最大发送长度：'))
        if Lmin <= Lmax:
            break
    except ValueError:
        print('输入错误')

chunks_len = split_file(len(file_data), Lmin, Lmax, args.seed)

offset = 0
file_chunks = []

for chunk_len in chunks_len:
    file_chunks.append(file_data[offset:offset + chunk_len])
    offset += chunk_len

N = len(file_chunks)

send_packet(client_socket, pack_init(N))
pkt = recv_packet(client_socket)
if pkt['type'] != TYPE_AGREE:
    raise RuntimeError(f'Excpeted Agreement, got type={pkt["type"]}')

recv_data = []
for i, file_chunk in enumerate(file_chunks):
    send_packet(client_socket, pack_request(file_chunk))
    pkt = recv_packet(client_socket)
    if pkt['type'] != TYPE_ANSWER:
        raise RuntimeError(f'Excepted answer, got type={pkt["type"]}')
    recv_data.append(pkt['data'])
    print(f'第 {i+ 1} 块: {pkt["data"]}')
    
# wait for receive thread to finish if it was started
file_dir = os.path.dirname(file_path)
file_name = os.path.basename(file_path)
pos = file_name.find('.')
prev_name, suffix = os.path.splitext(file_name)
output_path = os.path.join(file_dir, prev_name + '_reverse' + suffix)
with open(output_path, 'wb') as f:
    for reverse_chunk in recv_data:
        f.write(reverse_chunk)
        
client_socket.close()
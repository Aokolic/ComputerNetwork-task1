import struct
import logging

logger = logging.getLogger('reverse_tcp')

# 安全常量
MAX_PAYLOAD_SIZE = 4096  # 单个分块最大 4KB，符合题目 Lmin/Lmax 的需求
MIN_CHUNKS = 1
MAX_CHUNKS = 1_000_000   # N 的合理上限

# 报文类型
TYPE_INIT = 1
TYPE_AGREE = 2
TYPE_REQUEST = 3
TYPE_ANSWER = 4

# 类型名映射（方便调用方/日志使用）
TYPE_NAMES = {
    TYPE_INIT: 'Initialization',
    TYPE_AGREE: 'Agreement',
    TYPE_REQUEST: 'reverseRequest',
    TYPE_ANSWER: 'reverseAnswer',
}

def _peer_str(sock) -> str:
    try:
        peer = sock.getpeername()
        return f'{peer[0]}:{peer[1]}'
    except OSError:
        return 'unknow'

def pack_init(n: int) -> bytes:
    """打包 Initialization 报文: Type=1, N"""
    if not isinstance(n, int):
        raise TypeError(f"n must be int, got {type(n).__name__}")
    if not (MIN_CHUNKS <= n <= MAX_CHUNKS):
        raise ValueError(f"n must be between {MIN_CHUNKS} and {MAX_CHUNKS}, got {n}")
    return struct.pack('!HI', TYPE_INIT, n)


def pack_agree() -> bytes:
    """打包 Agreement 报文: Type=2"""
    return struct.pack('!H', TYPE_AGREE)


def pack_request(data: bytes) -> bytes:
    """打包 reverseRequest 报文: Type=3, Length, Data"""
    if not isinstance(data, bytes):
        raise TypeError(f"data must be bytes, got {type(data).__name__}")
    if len(data) > MAX_PAYLOAD_SIZE:
        raise ValueError(f"data size {len(data)} exceeds max payload {MAX_PAYLOAD_SIZE}")
    return struct.pack('!HI', TYPE_REQUEST, len(data)) + data


def pack_answer(reverse_data: bytes) -> bytes:
    """打包 reverseAnswer 报文: Type=4, Length, reverseData"""
    if not isinstance(reverse_data, bytes):
        raise TypeError(f"reverse_data must be bytes, got {type(reverse_data).__name__}")
    if len(reverse_data) > MAX_PAYLOAD_SIZE:
        raise ValueError(f"reverse_data size {len(reverse_data)} exceeds max payload {MAX_PAYLOAD_SIZE}")
    return struct.pack('!HI', TYPE_ANSWER, len(reverse_data)) + reverse_data

def send_packet(sock, packet_bytes: bytes):
    sock.sendall(packet_bytes)

    pkt_type = struct.unpack('!H', packet_bytes[:2])[0]
    type_name = TYPE_NAMES.get(pkt_type)

    extra = ''
    if pkt_type == TYPE_INIT and len(packet_bytes) >= 6:
        n = struct.unpack('!I', packet_bytes[2:6])[0]
        extra = f' | N={n}'
    elif pkt_type in (TYPE_ANSWER, TYPE_REQUEST) and len(packet_bytes) >= 6:
        length = struct.unpack('!I', packet_bytes[2:6])[0]
        extra = f' | length={length}'
    
    logger.info(
        f'SEED -> {_peer_str(sock)} | Type={pkt_type}({type_name}){extra}'
    )

# ========== 接收函数 ==========

def recv_n(sock, n: int) -> bytes:
    """
    精确接收 n 字节，处理 TCP 粘包问题
    使用 bytearray 避免 O(n^2) 的字符串拼接
    """
    if n < 0:
        raise ValueError(f"n must be non-negative, got {n}")
    if n == 0:
        return b''

    buf = bytearray(n)
    view = memoryview(buf)
    bytes_received = 0

    while bytes_received < n:
        chunk = sock.recv(n - bytes_received)
        if not chunk:
            raise ConnectionError("Connection closed while receiving data")
        chunk_len = len(chunk)
        view[bytes_received:bytes_received + chunk_len] = chunk
        bytes_received += chunk_len

    return bytes(buf)


def recv_packet(sock):
    """
    接收一个完整报文
    返回字典:
      - {'type': TYPE_INIT, 'n': 总块数}
      - {'type': TYPE_AGREE}
      - {'type': TYPE_REQUEST, 'length': 长度, 'data': 数据}
      - {'type': TYPE_ANSWER, 'length': 长度, 'data': 反转后的数据}
    """
    # 1. 读取 Type (2 bytes)
    type_bytes = recv_n(sock, 2)
    pkt_type = struct.unpack('!H', type_bytes)[0]
    type_name = TYPE_NAMES.get(pkt_type)
    pkt_type = struct.unpack('!H', type_bytes)[0]
    peer = _peer_str(sock)

    # 2. 根据 Type 读取后续内容
    if pkt_type == TYPE_INIT:
        n_bytes = recv_n(sock, 4)
        n = struct.unpack('!I', n_bytes)[0]
        if not (MIN_CHUNKS <= n <= MAX_CHUNKS):
            raise ValueError(f"Received invalid n={n}, must be between {MIN_CHUNKS} and {MAX_CHUNKS}")
        logger.info(
            f'RECV <- {peer} | Type={pkt_type}({type_name}) | N={n}'
        )
        return {'type': pkt_type, 'n': n}

    elif pkt_type == TYPE_AGREE:
        logger.info(
            f'RECV <- {peer} | Type={pkt_type}({type_name})'
        )
        return {'type': pkt_type}

    elif pkt_type in (TYPE_REQUEST, TYPE_ANSWER):
        length_bytes = recv_n(sock, 4)
        length = struct.unpack('!I', length_bytes)[0]

        # 检查 Length 上限，防止内存耗尽
        if length > MAX_PAYLOAD_SIZE:
            raise ValueError(f"Received length={length} exceeds max payload {MAX_PAYLOAD_SIZE}")

        data = recv_n(sock, length)

        logger.info(
            f'RECV <- {peer} | Type={pkt_type}({type_name}) | length={length}'
        )
        return {'type': pkt_type, 'length': length, 'data': data}

    else:
        raise ValueError(f"Unknown packet type: {pkt_type}")

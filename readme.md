# 程序运行说明文件

**运行环境**：Python 3.14

**代码编写工具**：VSCode，PyCharm

**代码启动选项**：

- `reversetcpclient.py` 启动时必须附加启动参数：`serverIP` 和 `serverPort`，可选参数为 `--seed`，默认值为 26
  - 代码执行中需要输入发送文件的地址，以及最小发送长度 `Lmin` 和最大发送长度 `Lmax`
- `reversetcpserver.py` 无启动参数，默认监听本机 8080 端口

**文件目录结构**：

| 文件名 | 作用 |
|--------|------|
| `logger.py` | 日志文件处理模块 |
| `self_defined_protocol.py` | 自定义应用层协议模块 |
| `reversetcpclient.py` | TCP 客户端程序 |
| `reversetcpserver.py` | TCP 服务器程序 |

**各文件具体作用**：

- **logger.py**：定义了日志文件的处理，提供 `setup_logger()` 方法，参数为 `log_file: str='run_log.txt'`，`name: str='reverse_tcp'`。日志输出格式为 `年-月-日 时:分:秒.毫秒 [记录等级] 具体内容`。客户端日志默认写入 `run_log.txt`，服务器端日志默认写入 `run_log_server.txt`。

- **self_defined_protocol.py**：自定义应用层协议模块，基于 TCP 实现，处理 TCP 粘包问题。定义了 4 种报文类型：
  - `Initialization`（Type=1）：初始化报文，携带总分块数 N
  - `Agreement`（Type=2）：同意报文，服务器响应初始化请求
  - `reverseRequest`（Type=3）：数据请求报文，携带文件分块数据
  - `reverseAnswer`（Type=4）：数据响应报文，携带反转后的文件分块数据
  提供报文打包（`pack_init`、`pack_agree`、`pack_request`、`pack_answer`）、发送（`send_packet`）和接收（`recv_packet`）功能。

- **reversetcpclient.py**：TCP 客户端程序。功能包括：
  1. 通过命令行参数连接指定服务器
  2. 读取用户输入的文件路径
  3. 根据用户输入的 `Lmin` 和 `Lmax` 以及 `--seed` 参数，使用随机数将文件拆分为若干块
  4. 向服务器发送初始化报文，协商分块数量
  5. 逐块发送文件数据，接收服务器返回的反转后的数据块
  6. 将所有反转后的数据块拼接，输出为 `原文件名_reverse.原后缀` 的文件

- **reversetcpserver.py**：TCP 服务器程序。功能包括：
  1. 监听 0.0.0.0:8080，支持多客户端并发连接（多线程处理）
  2. 接收客户端的初始化报文，回复同意报文
  3. 逐块接收客户端发送的数据，将每块数据进行字节级反转后返回
  4. 处理完毕后自动关闭客户端连接，继续等待新连接

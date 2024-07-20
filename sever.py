import socket
import threading
import time
import sqlite3

# 服务器配置
HOST = 'localhost'
PORT = 12345

# 连接到 SQLite 数据库
conn = sqlite3.connect('chat_server.db', check_same_thread=False)
cursor = conn.cursor()

# 创建昵称表（如果不存在）
cursor.execute("CREATE TABLE IF NOT EXISTS nicknames (id INTEGER PRIMARY KEY, nickname TEXT)")
conn.commit()

# 客户端处理函数
def handle_client(client_socket, client_address):
    print(f"[新连接] {client_address} connected.")

    try:
        # 接收客户端发送的昵称
        nickname = client_socket.recv(1024).decode('utf-8')
        
        # 检查昵称是否重复
        cursor.execute("SELECT * FROM nicknames WHERE nickname=?", (nickname,))
        existing_nickname = cursor.fetchone()
        if existing_nickname:
            client_socket.send("[ERROR] 昵称重复.".encode('utf-8'))
            client_socket.close()
            print(f"[已断开] {client_address} disconnected due to duplicate nickname.")
            return
        else:
            cursor.execute("INSERT INTO nicknames (nickname) VALUES (?)", (nickname,))
            conn.commit()
            print(f"[NICKNAME] {client_address} chose nickname: {nickname}")

        while True:
            try:
                # 接收消息
                message = client_socket.recv(1024).decode('utf-8')
                if not message:
                    break

                # 添加时间戳
                current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                full_message = f"{current_time} {nickname}: {message}"

                # 广播消息给所有客户端
                broadcast(full_message)
                
                # 如果希望消息也显示在发送者自己的客户端上，取消下面的注释
                #client_socket.send(f"You: {message}".encode('utf-8'))
            except ConnectionResetError:
                break

    finally:
        # 客户端断开连接后清除昵称
        cursor.execute("DELETE FROM nicknames WHERE nickname=?", (nickname,))
        conn.commit()
        print(f"[已断开] {client_address} disconnected.")
        client_socket.close()

# 广播消息给所有客户端
def broadcast(message):
    for client_socket in clients[:]:  # 使用[:]复制列表，避免迭代过程中列表改变
        try:
            client_socket.send(message.encode('utf-8'))
        except Exception as e:
            print(f"Error broadcasting message to client: {e}")
            clients.remove(client_socket)  # 移除无效的客户端套接字

# 主程序
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen()

print(f"[监听] 服务器在 {HOST}:{PORT} 上运行")

clients = []

while True:
    client_socket, client_address = server_socket.accept()
    clients.append(client_socket)

    # 启动线程处理客户端
    client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
    client_thread.start()

    print(f"[活动连接] {threading.activeCount() - 1}")

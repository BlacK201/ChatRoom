import asynchat
import asyncore
from time import sleep
# 定义端口
PORT = 6666


class EndSession(Exception):
    # 定义结束异常类
    pass


class ChatServer(asyncore.dispatcher):
    """
    聊天服务器
    """

    def __init__(self, port):
        asyncore.dispatcher.__init__(self)
        # 创建socket
        self.create_socket()
        # 设置 socket 为可重用
        self.set_reuse_addr()
        # 监听端口
        self.bind(('', port))
        self.listen(5)
        self.users = {}
        self.main_room = ChatRoom(self)

    def handle_accept(self):
        conn, addr = self.accept()
        ChatSession(self, conn)


class ChatSession(asynchat.async_chat):
    """
    负责和客户端通信
    """

    def __init__(self, server, sock):
        asynchat.async_chat.__init__(self, sock)
        self.server = server
        self.set_terminator(b'\n')
        self.data = []
        self.name = None
        self.enter(LoginRoom(server))

    def enter(self, room):
        # 从当前房间移除自身，然后添加到指定房间
        try:
            cur = self.room
        except AttributeError:
            pass
        else:
            cur.remove(self)
        self.room = room
        room.add(self)

    def collect_incoming_data(self, data):
        # 接收客户端的数据
        self.data.append(data.decode("utf-8"))

    def found_terminator(self):
        # 当客户端的一条数据结束时的处理
        line = ''.join(self.data)
        self.data = []
        try:
            self.room.handle(self, line.encode("utf-8"))
        # 退出聊天室的处理
        except EndSession:
            self.handle_close()

    def handle_close(self):
        # 当 session 关闭时，将进入 LogoutRoom
        asynchat.async_chat.handle_close(self)
        self.enter(LogoutRoom(self.server))


class CommandHandler:
    """
    命令处理类
    """

    def unknown(self, session, cmd):
        # 响应未知命令
        # 通过 aynchat.async_chat.push 方法发送消息
        session.push(('Unknown command {} \n'.format(cmd)).encode("utf-8"))

    def handle(self, session, line):
        line = line.decode()
        # 命令处理
        if not line.strip():
            return
        parts = line.split(' ', 1)
        cmd = parts[0]
        try:
            line = parts[1].strip()
        except IndexError:
            line = ''
        # 通过协议代码执行相应的方法
        method = getattr(self, 'do_' + cmd, None)
        try:
            method(session, line)
        except TypeError:
            self.unknown(session, cmd)


class Room(CommandHandler):
    """
    包含多个用户的环境，负责基本的命令处理和广播
    """

    def __init__(self, server):
        self.server = server
        self.sessions = []

    def add(self, session):
        # 一个用户进入房间
        self.sessions.append(session)

    def remove(self, session):
        # 一个用户离开房间
        self.sessions.remove(session)

    def broadcast(self, line):
        # 向所有的用户发送指定消息
        # 使用 asynchat.asyn_chat.push 方法发送数据
        for session in self.sessions:
            session.send(line.encode('utf-8') + b'\xFE')
    def do_logout(self, session, line):
        # 退出房间
        raise EndSession


class LoginRoom(Room):
    """
    处理登录用户
    """
    sleep(1)
    def add(self, session):
        # 用户连接成功的回应
        Room.add(self, session)
        # 使用 asynchat.asyn_chat.push 方法发送数据
        session.push(b'Connect Success')

    def do_login(self, session, line):
        # 用户登录逻辑

        name = line.strip()

        # 获取用户名称
        # 检查是否有同名用户
        if not name:
            session.push(b'UserName Empty')
        # 检查用户名是否有特殊字符
        elif ' ' in name or ':' in name:
            session.push(b'UserName is not standard')
        elif name in self.server.users:
            session.push(b'UserName Exist')
        # 用户名检查成功后，进入主聊天室
        else:
            session.name = name
            session.enter(self.server.main_room)


class LogoutRoom(Room):
    """
    处理退出用户
    """

    def add(self, session):
        # 从服务器中移除
        try:
            del self.server.users[session.name]
        except KeyError:
            pass

class ChatRoom(Room):
    """
    聊天用的房间
    """
    def add(self, session):
        # 广播新用户进入
        session.push(b'Login Success')
        Room.add(self, session)
        userData = 'Online Users:\n'
        for other in self.sessions:
            userData = userData + other.name + '\n'
        self.broadcast(userData)
        self.broadcast('系统消息：' + session.name + ' 加入了聊天室.\n')
        self.server.users[session.name] = session

    def remove(self, session):
        # 广播用户离开
        Room.remove(self, session)
        self.broadcast('系统消息：' + session.name + ' 离开了聊天室.\n')

    def do_say(self, session, line):
        # 客户端发送消息
        self.broadcast(session.name + ': ' + line + '\n')


    def do_look(self, session, line):
        # 查看在线用户
        userData = 'Online Users:\n'
        for other in self.sessions:
            userData = userData + other.name + '\n'
        self.broadcast(userData)

    def do_Psay(self, session, line):
        tuser, msg, _ = line.split('\xFD')
        for sess in self.sessions:
            if sess.name == tuser:
                try:
                    sess.send('Private Chat:'.encode('utf-8') + b'\xFD' + session.name.encode('utf-8') + b'\xFD' + msg.encode('utf-8') + b'\xFE')
                except Exception as e:
                    print(e)


if __name__ == '__main__':
    s = ChatServer(PORT)
    try:
        print("闪讯服务器正在'0.0.0.0:{0}'上运行！".format(PORT))
        asyncore.loop()
    except KeyboardInterrupt:
        print("chat server exit")

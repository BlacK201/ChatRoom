import wx
import telnetlib
from time import sleep
import _thread as thread
import re

class LoginFrame(wx.Frame):
    """
    登录窗口
    """
    def __init__(self, parent, id, title, size):
        # 初始化，添加控件并绑定事件
        wx.Frame.__init__(self, parent, id, title)
        self.SetSize(size)
        self.Center()
        self.serverAddressLabel = wx.StaticText(self, label="Server Address", pos=(10, 50), size=(120, 25))
        self.userNameLabel = wx.StaticText(self, label="UserName", pos=(40, 100), size=(120, 25))
        self.serverAddress = wx.TextCtrl(self, pos=(120, 47), size=(150, 25),value=('127.0.0.1:6666'))
        self.userName = wx.TextCtrl(self, pos=(120, 97), size=(150, 25))
        self.loginButton = wx.Button(self, label='登陆', pos=(95, 145), size=(130, 30))
        # 绑定登录方法
        self.loginButton.Bind(wx.EVT_BUTTON, self.login)
        self.Show()

    def login(self, event):
        # 登录处理
        try:
            serverAddress = self.serverAddress.GetLineText(0).split(':')
            con.open(serverAddress[0], port=int(serverAddress[1]), timeout=10)
            response = con.read_some()
            if response != b'Connect Success':
                self.showDialog('Error', 'Connect Fail!', (200, 100))
                return
            con.write(('login ' + str(self.userName.GetLineText(0)) + '\n').encode("utf-8"))
            response = con.read_some()
            if response == b'UserName Empty':
                self.showDialog('Error', 'UserName Empty!', (200, 100))
            elif response == b'UserName Exist':
                self.showDialog('Error', 'UserName Exist!', (200, 100))
            else:
                self.Close()
#                ChatFrame(None, 2, title='Chat Room',size=(652,370))
                #大框框
                ChatFrame(None, 2, title='Chat Room    '+ "用户名: " + self.userName.GetLineText(0), size=(588, 370))
        except Exception as e:
            self.showDialog('Error', 'Connect Fail!', (95, 60))

    def showDialog(self, title, content, size):
        # 显示错误信息对话框
        dialog = wx.Dialog(self, title=title, size=size)
        dialog.Center()
        wx.StaticText(dialog, label=content)
        dialog.ShowModal()


class ChatFrame(wx.Frame):
    """
    聊天窗口
    """
    
    def __init__(self, parent, id, title, size):
        # 初始化，添加控件并绑定事件
        wx.Frame.__init__(self, parent, id, title)
        self.SetSize(size)
        self.Center()
        #消息框
        self.chatFrame = wx.TextCtrl(self, pos=(5, 5), size=(426, 310), style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.message = wx.TextCtrl(self, pos=(5, 320), size=(275, 25))

        # bitmap = wx.Image("emoji.jpeg",wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        # self.emojiButton= wx.BitmapButton(panel,-1,bitmap,pos=(380,320), size=(25, 25))
        self.sendButton = wx.Button(self, label="发送 ", pos=(310, 320), size=(58, 25))
        #self.usersButton = wx.Button(self, label="Users", pos=(373, 320), size=(58, 25))
        self.closeButton = wx.Button(self, label="关闭", pos=(373, 320), size=(58, 25))
        self.languageButton = wx.Button(self, label='😁', pos=(279, 320), size=(30, 25))
        '''
        此处添加 用户列表
        '''
        self.userListWindow = wx.Panel(self, pos=(436, 8), size=(150, 340))
        self.userListTitle = wx.StaticText(self.userListWindow, label = "在线用户:")
        self.userList = wx.ListBox(self.userListWindow, -1, pos=(0, 20), size=(146, 287.5),
                                   style=wx.LB_HSCROLL | wx.LB_SINGLE | wx.LB_ALWAYS_SB)

        self.userList.Bind(wx.EVT_LISTBOX_DCLICK, self.privateChat)
        # 发送按钮绑定发送消息方法
        self.sendButton.Bind(wx.EVT_BUTTON, self.send)
        # Users按钮绑定获取在线用户数量方法
        #self.usersButton.Bind(wx.EVT_BUTTON, self.lookUsers)
        # 关闭按钮绑定关闭方法
        self.closeButton.Bind(wx.EVT_BUTTON, self.close)
        #切换语言绑定切换方法
        #self.languageButton.Bind(wx.EVT_BUTTON, self.changeLanguage)
        thread.start_new_thread(self.receive, ())
        self.Show()

    def showDialog(self, title, content, size):
        # 显示错误信息对话框
        dialog = wx.Dialog(self, title=title, size=size)
        dialog.Center()
        wx.StaticText(dialog, label=content)
        dialog.ShowModal()


    def privateChat(self, event):
        self.showDialog('Attention', 'Chatting with ' + self.userList.GetStringSelection(), (195, 160))

    def send(self, event):
        # 发送消息
        message = str(self.message.GetLineText(0)).strip()
        if message != '':
            con.write(('say ' + message + '\n').encode("utf-8"))
            self.message.Clear()

    def lookUsers(self, event):
        # 查看当前在线用户
        con.write(b'look\n')

    def close(self, event):
        # 关闭窗口
        con.write(b'logout\n')
        con.close()
        self.Close()
    '''
    ClickNum = 0
    def changeLanguage(self, event):
        self.ClickNum+=1
        if self.ClickNum % 2 == 1:  #根据按下次数判断
            self.sendButton.SetLabel("发送")#修改按键的标签
            print(self.sendButton.GetLabel())#打印信息（返回按键的标签信息）
        else:
            self.sendButton.SetLabel("send")
            self.ClickNum = 0
            print(self.sendButton.GetLabel())
    '''
    def receive(self):
        # 接受服务器的消息
        while True:
            sleep(0.6)
            result = con.read_very_eager()
            if result != '':
                # 用户列表处理
                if result.startswith(b'Online Users:'):
                    result = result[14:]
                    users = result.split(b'\n')
                    users.pop()
                    self.userList.Clear()
                    self.userList.AppendItems(users)
                # 私聊处理
                elif result.startswith(b'Private Chat:'):
                    pass
                # 普通消息处理
                else:
                    self.chatFrame.AppendText(result)

class personal_ChatFrame(ChatFrame):
    def __init__(self, parent, id, title, size):
        # 初始化，添加控件并绑定事件
        wx.Frame.__init__(self, parent, id, title)
        self.SetSize(size)
        self.Center()
        self.chatFrame = wx.TextCtrl(self, pos=(5, 5), size=(436, 310), style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.message = wx.TextCtrl(self, pos=(5, 320), size=(275, 25))
        self.sendButton = wx.Button(self, label="发送 ", pos=(310, 320), size=(58, 25))
        #self.usersButton = wx.Button(self, label="Users", pos=(373, 320), size=(58, 25))
        self.closeButton = wx.Button(self, label="关闭", pos=(373, 320), size=(58, 25))
        #self.languageButton = wx.Button(self, label='中/En', pos=(436, 320), size=(58, 25))
        self.userList.Bind(wx.EVT_LISTBOX_DCLICK, self.privateChat)
        # 发送按钮绑定发送消息方法
        self.sendButton.Bind(wx.EVT_BUTTON, self.send)
        # Users按钮绑定获取在线用户数量方法
        #self.usersButton.Bind(wx.EVT_BUTTON, self.lookUsers)
        # 关闭按钮绑定关闭方法
        self.closeButton.Bind(wx.EVT_BUTTON, self.close)
        #切换语言绑定切换方法
        #self.languageButton.Bind(wx.EVT_BUTTON, self.changeLanguage)
        thread.start_new_thread(self.receive, ())
        #self.Show()
    

        

if __name__ == '__main__':
    app = wx.App()
    con = telnetlib.Telnet()
    LoginFrame(None, -1, title="Login", size=(320, 250))
    app.MainLoop()

import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox, Menu
import socket
import threading
import tkinter.ttk as ttk

class ClientApp:
    def __init__(self, master):
        self.master = master
        self.master.title("yuLu_Chat")
        
        self.chat_history = scrolledtext.ScrolledText(master, wrap=tk.WORD)
        self.chat_history.pack(expand=True, fill=tk.BOTH)
        
        self.entry_message = tk.Entry(master)
        self.entry_message.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=10, pady=10)
        self.entry_message.bind("<Return>", self.send_on_enter)
        
        self.send_button = tk.Button(master, text="发送", command=self.send_message)
        self.send_button.pack(side=tk.RIGHT, padx=10, pady=10)
        
        self.menu_bar = Menu(master)
        self.master.config(menu=self.menu_bar)
        
        self.edit_menu = Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="编辑", menu=self.edit_menu)
        self.edit_menu.add_command(label="复制", command=self.copy_text, accelerator="Ctrl+C")
        self.edit_menu.add_command(label="粘贴", command=self.paste_text, accelerator="Ctrl+V")
        
        self.master.bind_all("<Control-c>", lambda event: self.copy_text())
        self.master.bind_all("<Control-v>", lambda event: self.paste_text())
        
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = 'cn-sz-yd-plustmp2.natfrp.cloud'
        self.port = 42494
        self.nickname = None

        self.connect_to_server()

    def connect_to_server(self):
        try:
            self.client_socket.connect((self.host, self.port))
            self.nickname = simpledialog.askstring("昵称", "输入您的昵称", parent=self.master)
            if self.nickname:
                self.client_socket.send(self.nickname.encode())
                receive_thread = threading.Thread(target=self.receive_message)
                receive_thread.start()
            else:
                messagebox.showwarning("需要昵称", "您必须输入昵称才能加入聊天")
                self.master.quit()
        except ConnectionRefusedError:
            messagebox.showerror("连接错误", "无法连接到服务器")
            self.master.quit()

    def receive_message(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode()
                if message == 'NICK':
                    self.client_socket.send(self.nickname.encode())
                else:
                    self.display_message(message)
            except Exception as e:
                print(f"发生错误：{str(e)}")
                self.client_socket.close()
                break

    def send_message(self):
        message = self.entry_message.get()
        if message:
            try:
                self.client_socket.send(message.encode())
                if message.lower() == "!quit":
                    self.client_socket.close()
                    self.master.quit()
            except Exception as e:
                print(f"发送消息错误：{str(e)}")
                messagebox.showerror("发送错误", "无法发送消息。请检查您的连接")
        else:
            messagebox.showwarning("空消息", "不能发送空消息")

        self.entry_message.delete(0, tk.END)

    def display_message(self, message):
        self.chat_history.insert(tk.END, message + '\n')
        self.chat_history.yview(tk.END)

    def send_on_enter(self, event):
        self.send_message()

    def copy_text(self):
        selected_text = self.chat_history.get(tk.SEL_FIRST, tk.SEL_LAST)
        if selected_text:
            self.master.clipboard_clear()
            self.master.clipboard_append(selected_text)

    def paste_text(self):
        clipboard_text = self.master.clipboard_get()
        self.entry_message.insert(tk.END, clipboard_text)

def main():
    root = tk.Tk()
    app = ClientApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()

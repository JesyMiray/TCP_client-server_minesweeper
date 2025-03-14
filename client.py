import socket
import tkinter as tk
from tkinter import messagebox
import threading

FIELD_SIZE = 5
server_host = "127.0.0.1"
server_port = 5555

class MinesweeperClient:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((server_host, server_port))

        self.root = tk.Tk()
        self.root.title("Сапёр — Клиент")

        self.frame = tk.Frame(self.root)
        self.frame.pack()

        self.buttons = [[None] * FIELD_SIZE for _ in range(FIELD_SIZE)]
        self.mines = set()
        self.is_placing_mines = True
        self.is_my_turn = False
        self.game_over = False

        self.info_label = tk.Label(self.root, text="Ожидание второго игрока...")
        self.info_label.pack()

        self.create_grid()
        self.wait_for_message()

        self.root.mainloop()

    def create_grid(self):
        for x in range(FIELD_SIZE):
            for y in range(FIELD_SIZE):
                btn = tk.Button(self.frame, width=4, height=2, command=lambda i=x, j=y: self.on_cell_click(i, j))
                btn.grid(row=x, column=y)
                self.buttons[x][y] = btn

    def on_cell_click(self, x, y):
        if self.game_over:
            return

        if self.is_placing_mines:
            if len(self.mines) < 5:
                self.mines.add((x, y))
                self.buttons[x][y].config(text="M", state=tk.DISABLED)
                if len(self.mines) == 5:
                    self.send_mines()
        elif self.is_my_turn:
            self.send_move(x, y)

    def send_mines(self):
        mine_str = ";".join(f"{x},{y}" for x, y in self.mines)
        self.client.sendall(mine_str.encode())
        self.is_placing_mines = False
        self.info_label.config(text="Ожидаем начала игры...")

    def send_move(self, x, y):
        self.client.sendall(f"{x},{y}".encode())
        self.is_my_turn = False
        self.disable_buttons()

    def wait_for_message(self):
        def receive():
            while True:
                try:
                    message = self.client.recv(1024).decode()
                    if "Ваш ход!" in message:
                        self.is_my_turn = True
                        self.info_label.config(text="Ваш ход! Выберите клетку")
                        self.enable_buttons()
                    elif "Вы попали на мину" in message:
                        x, y = map(int, message.split(":")[-1].split(","))
                        self.buttons[x][y].config(text="X", bg="red", state=tk.DISABLED)
                    elif "Выход чист" in message:
                        x, y = map(int, message.split(":")[-1].split(","))
                        self.buttons[x][y].config(text="✔", bg="green", state=tk.DISABLED)
                    elif "Вы проиграли" in message or "Вы победили" in message:
                        self.game_over = True
                        messagebox.showinfo("Игра окончена", message)
                        self.disable_buttons()
                    else:
                        self.info_label.config(text=message)
                except:
                    break

        threading.Thread(target=receive, daemon=True).start()

    def enable_buttons(self):
        for x in range(FIELD_SIZE):
            for y in range(FIELD_SIZE):
                self.buttons[x][y].config(state=tk.NORMAL)

    def disable_buttons(self):
        for x in range(FIELD_SIZE):
            for y in range(FIELD_SIZE):
                self.buttons[x][y].config(state=tk.DISABLED)


if __name__ == "__main__":
    MinesweeperClient()

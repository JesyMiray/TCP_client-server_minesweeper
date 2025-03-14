import socket
import threading
import time

FIELD_SIZE = 5
MINES_COUNT = 5

players = {}
turn_order = []
connections = []
lock = threading.Lock()

game_active = True

def handle_client(conn, addr, player_id):
    global players, turn_order, game_active

    print(f"Игрок {player_id} подключился: {addr}")

    conn.sendall("Ожидаем второго игрока...\n".encode())

    while len(players) < 2:
        time.sleep(0.1)

    conn.sendall("Введите 5 координат мин (формат: x,y; x,y; ...): ".encode())
    mines = conn.recv(1024).decode().strip().split(";")
    mines = {tuple(map(int, mine.strip().split(","))) for mine in mines}

    with lock:
        players[player_id] = {"mines": mines, "hits": set()}

    conn.sendall("Ожидаем расстановку мин вторым игроком...\n".encode())

    while len(players[1]["mines"]) < MINES_COUNT or len(players[2]["mines"]) < MINES_COUNT:
        time.sleep(0.1)

    conn.sendall("Мины расставлены. Начинаем игру!\n".encode())

    if player_id == turn_order[0]:
        conn.sendall("Ваш ход! Введите координаты для атаки (x,y): ".encode())

    while game_active:
        if turn_order[0] != player_id:
            time.sleep(0.1)
            continue

        conn.sendall("Ваш ход! Введите координаты для атаки (x,y): ".encode())
        move = conn.recv(1024).decode().strip()
        x, y = map(int, move.split(","))

        #проверяем на попадание
        opponent = 2 if player_id == 1 else 1
        hit = (x, y) in players[opponent]["mines"]

        if hit:
            players[player_id]["hits"].add((x, y))
            conn.sendall(f"Вы попали на мину: {x},{y}\n".encode())
        else:
            conn.sendall(f"Выход чист: {x},{y}\n".encode())

        #проверяем на поражение
        if players[player_id]["hits"] == players[opponent]["mines"]:
            conn.sendall("Вы проиграли!\n".encode())
            connections[opponent - 1].sendall("Вы победили!\n".encode())
            game_active = False
            break

        #передаём ход другому игроку
        with lock:
            turn_order.reverse()

    conn.close()


def main():
    global players

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", 5555))
    server.listen(2)

    print("Сервер запущен. Ожидание подключений...")

    while len(players) < 2:
        conn, addr = server.accept()
        player_id = len(players) + 1  
        with lock:
            players[player_id] = {"mines": set(), "hits": set()}  
        connections.append(conn)
        threading.Thread(target=handle_client, args=(conn, addr, player_id)).start()

    turn_order.append(1)
    turn_order.append(2)


if __name__ == "__main__":
    main()

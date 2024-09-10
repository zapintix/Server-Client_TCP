import asyncio
import random
import logging
from datetime import datetime

logging.basicConfig(
    filename='server.log',
    level=logging.INFO,
    format='%(asctime)s; %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

clients = {}
global_response_number = 0


async def handle_client(reader, writer):
    global global_response_number
    client_address = writer.get_extra_info('peername')
    client_id = len(clients) + 1  # Присваиваем клиенту порядковый номер
    clients[writer] = client_id

    print(f'Клиент {client_address} подключился с ID {client_id}')

    request_number = 0
    while True:
        data = await reader.read(100)
        if not data:
            print(f"Клиент {client_address} отключился")
            break

        message = data.decode().strip()
        print(f"Получено сообщение от {client_address}: {message}")

        # Логирование времени получения запроса
        receive_time = datetime.now().strftime('%H:%M:%S.%f')[:-3]

        if random.random() < 0.1:
            logging.info(f"{datetime.now().strftime('%Y-%m-%d')}; "
                         f"{receive_time}; {message}; (проигнорировано)")
            print(f"Запрос {message} проигнорирован")
            continue

        delay = random.uniform(0.1, 1.0)
        await asyncio.sleep(delay)

        response = f"[{global_response_number}]/{request_number} PONG ({client_id})"
        writer.write((response + '\n').encode())
        await writer.drain()

        # Логирование времени отправки ответа
        send_time = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        logging.info(f"{datetime.now().strftime('%Y-%m-%d')}; {receive_time}; {message}; {send_time}; {response}")

        request_number += 1
        global_response_number += 1

    del clients[writer]
    writer.close()
    await writer.wait_closed()


async def send_keepalive():
    global global_response_number
    while True:
        await asyncio.sleep(5)
        message = f"[{global_response_number}] keepalive"
        print(f"Отправка keepalive-сообщения: {message}")

        for client in clients:
            client.write((message + '\n').encode())
            await client.drain()

        # Логирование отправленного keepalive
        logging.info(f"{datetime.now().strftime('%Y-%m-%d')}; ; ; {datetime.now().strftime('%H:%M:%S.%f')[:-3]}; {message}")

        global_response_number += 1


async def stop_server(server, delay):
    await asyncio.sleep(delay)
    tasks = []
    for client in clients:
        client.close()
        tasks.append(client.wait_closed())
    await asyncio.gather(*tasks)
    server.close()
    await server.wait_closed()
    print("Завершение работы сервера...")


async def run_server():
    server = await asyncio.start_server(handle_client, '127.0.0.1', 8888)
    print("Сервер запущен и слушает порт 8888")

    try:
        await asyncio.gather(
            server.serve_forever(),
            send_keepalive(),
            stop_server(server, 305)
        )
    except asyncio.CancelledError:
        print("Сервер завершил работу")

asyncio.run(run_server())

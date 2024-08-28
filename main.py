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

clients = set()


async def handle_client(reader, writer):
    client_address = writer.get_extra_info('peername')
    print(f'Клиент {client_address} подключился')

    request_number = 0
    clients.add(writer)
    while True:
        data = await reader.read(100)
        if not data:
            print(f"Клиент {client_address} отключился")
            break

        message = data.decode().strip()
        print(f"Получено сообщение от {client_address}: {message}")

        if random.random() < 0.1:
            logging.info(f"{datetime.now().strftime('%Y-%m-%d')}; "
                         f"{datetime.now().strftime('%H:%M:%S.%f')}; "
                         f"{message}; (проигнорировано)")
            print(f"Запрос {message} проигнорирован")
            continue

        delay = random.uniform(0.1, 1.0)
        await asyncio.sleep(delay)

        response = f"[{request_number}]/{message} PONG"
        writer.write(response.encode())
        await writer.drain()

        logging.info(f"{datetime.now().strftime('%Y-%m-%d')}; "
                     f"{datetime.now().strftime('%H:%M:%S.%f')}; "
                     f"{message}; "
                     f"{datetime.now().strftime('%H:%M:%S.%f')}; "
                     f"{response}")

        request_number += 1
    clients.remove(writer)
    writer.close()
    await writer.wait_closed()


async def send_keepalive():
    response_number = 0
    while True:
        await asyncio.sleep(5)
        message = f"[{response_number}] keepalive"
        print(f"Отправка keepalive-сообщения: {message}")
        for client in clients:
            client.write(message.encode() + b'\n')
            await client.drain()
        response_number += 1


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

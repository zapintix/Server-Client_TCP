import asyncio
import logging
import random
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    filename='client.log',
    level=logging.INFO,
    format='%(asctime)s; %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


# Корутина для подключения к серверу и отправки сообщений
async def connect_to_server(client_id):
    reader, writer = await asyncio.open_connection('127.0.0.1', 8888)

    request_number = 0

    try:
        while True:
            # Отправляем PING сообщение
            message = f"[{request_number}] PING"
            print(f"Клиент {client_id} отправляет: {message}")
            writer.write((message + '\n').encode())
            await writer.drain()

            # Логирование отправленного сообщения
            send_time = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            logging.info(f"{datetime.now().strftime('%Y-%m-%d')}; {send_time}; {message}; ")

            # Ожидаем ответ или таймаут
            try:
                data = await asyncio.wait_for(reader.read(100), timeout=3.0)
                response = data.decode().strip()

                # Проверяем, является ли ответ keepalive сообщением
                if "keepalive" in response:
                    print(f"Клиент {client_id} получил keepalive: {response}")

                    # Логирование keepalive сообщения
                    logging.info(f"; ; ; {datetime.now().strftime('%H:%M:%S.%f')[:-3]}; {response}")
                else:
                    print(f"Клиент {client_id} получил: {response}")

                    # Логирование обычного ответа
                    logging.info(f"; {datetime.now().strftime('%H:%M:%S.%f')[:-3]}; {response}")

            except asyncio.TimeoutError:
                print(f"Клиент {client_id}: таймаут")

                # Логирование таймаута
                logging.info(f"; {datetime.now().strftime('%H:%M:%S.%f')[:-3]}; (таймаут)")

            request_number += 1

            # Добавляем случайную задержку между отправкой сообщений
            await asyncio.sleep(random.uniform(0.3, 3.0))

    finally:
        writer.close()
        await writer.wait_closed()


async def stop_client(delay):
    await asyncio.sleep(delay)
    for task in asyncio.all_tasks():
        task.cancel()
    print("Завершение работы клиентов...")


# Корутина для запуска клиентов
async def run_clients():
    try:
        await asyncio.gather(
            connect_to_server(1),
            connect_to_server(2),
            stop_client(300)
        )
    except asyncio.CancelledError:
        print("Клиенты завершили работу")

# Запуск клиентов
asyncio.run(run_clients())

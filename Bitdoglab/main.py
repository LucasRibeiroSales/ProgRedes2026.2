"""Cliente MicroPython para Raspberry Pi Pico W / BitDogLab."""

import socket
import time
import network
from machine import I2C, Pin
from vl53l0x import VL53L0X

# Preencha as credenciais e o IPv4 do computador na mesma rede Wi-Fi.
WIFI_NOME = "wIFRN-IoT"
WIFI_SENHA = "deviceiotifrn"
IP_SERVIDOR = "192.168.1.100"
PORTA_SERVIDOR = 6666

DISPOSITIVO = "BITDOG01"
PINO_SDA = 0
PINO_SCL = 1
ENDERECO_SENSOR = 0x29
INTERVALO_LEITURA_MS = 1000


def conectar_wifi(wlan):
    if wlan.isconnected():
        return True

    print("Conectando ao Wi-Fi...")
    if not wlan.active():
        wlan.active(True)
    try:
        wlan.connect(WIFI_NOME, WIFI_SENHA)
    except OSError as erro:
        print("Falha ao iniciar conexão Wi-Fi:", erro)
        return False

    # Aguarda até 15 segundos e depois tenta novamente no laço principal.
    for _ in range(15):
        if wlan.isconnected():
            print("Wi-Fi conectado:", wlan.ifconfig()[0])
            return True
        time.sleep(1)

    print("Não foi possível conectar ao Wi-Fi. Nova tentativa em breve.")
    return False


def enviar_linha(sock, linha):
    dados = linha.encode("utf-8")
    enviados = 0
    while enviados < len(dados):
        quantidade = sock.send(dados[enviados:])
        if quantidade == 0:
            raise OSError("Conexão TCP fechada durante o envio")
        enviados += quantidade


def main():
    i2c = I2C(0, sda=Pin(PINO_SDA), scl=Pin(PINO_SCL), freq=100000)
    dispositivos = i2c.scan()
    print("Dispositivos I2C encontrados:", dispositivos)

    wlan = network.WLAN(network.STA_IF)
    sensor = None
    sock = None

    while True:
        if sensor is None:
            if ENDERECO_SENSOR not in i2c.scan():
                print("VL53L0X não encontrado no endereço 0x29; verifique as conexões.")
                time.sleep(3)
                continue
            try:
                sensor = VL53L0X(i2c, address=ENDERECO_SENSOR)
                print("VL53L0X inicializado no endereço 0x29.")
            except (OSError, RuntimeError) as erro:
                print("Falha ao inicializar o VL53L0X:", erro)
                time.sleep(3)
                continue

        if not conectar_wifi(wlan):
            time.sleep(2)
            continue

        if sock is None:
            try:
                sock = socket.socket()
                sock.connect((IP_SERVIDOR, PORTA_SERVIDOR))
                print("Conectado ao servidor TCP.")
            except OSError as erro:
                print("Falha na conexão TCP:", erro)
                if sock is not None:
                    sock.close()
                    sock = None
                time.sleep(2)
                continue

        try:
            distancia_mm = sensor.range
            mensagem = "{};{}\n".format(DISPOSITIVO, distancia_mm)
            enviar_linha(sock, mensagem)
            print("Distância enviada:", distancia_mm, "mm")
        except (OSError, RuntimeError) as erro:
            print("Falha na leitura ou no envio:", erro)
            sock.close()
            sock = None
            # Recria o sensor na próxima passagem, caso a falha tenha sido I2C.
            sensor = None

        time.sleep_ms(INTERVALO_LEITURA_MS)


main()

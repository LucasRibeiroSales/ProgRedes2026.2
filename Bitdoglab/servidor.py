"""Servidor TCP que recebe leituras e calcula médias usando SQLite."""

import socket
import sqlite3

HOST = "0.0.0.0"
PORTA = 6666
BANCO = "telemetria.db"


def criar_tabela(conexao):
    conexao.execute(
        """CREATE TABLE IF NOT EXISTS leituras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dispositivo TEXT NOT NULL,
            distancia_mm INTEGER NOT NULL,
            instante DATETIME DEFAULT CURRENT_TIMESTAMP
        )"""
    )
    conexao.commit()


def gravar_leitura(conexao, dispositivo, distancia_mm):
    conexao.execute(
        "INSERT INTO leituras (dispositivo, distancia_mm) VALUES (?, ?)",
        (dispositivo, distancia_mm),
    )
    conexao.commit()


def consultar_media(conexao, periodo):
    # As duas consultas são explícitas para facilitar a leitura por iniciantes.
    if periodo == "-5 minutes":
        consulta = "SELECT AVG(distancia_mm) FROM leituras WHERE instante >= datetime('now', '-5 minutes')"
    elif periodo == "-1 hour":
        consulta = "SELECT AVG(distancia_mm) FROM leituras WHERE instante >= datetime('now', '-1 hour')"
    else:
        raise ValueError("Período de média não reconhecido")
    return conexao.execute(consulta).fetchone()[0]


def processar_linha(conexao, linha):
    """Valida e grava uma mensagem; retorna True quando foi aceita."""
    try:
        dispositivo, texto_distancia = linha.split(";")
        distancia = int(texto_distancia)
        if not dispositivo or len(dispositivo) > 32 or not dispositivo.replace("_", "").isalnum():
            raise ValueError("identificação inválida")
        if distancia < 0:
            raise ValueError("distância negativa")
    except (ValueError, TypeError):
        print("Mensagem inválida ignorada:", repr(linha))
        return False

    gravar_leitura(conexao, dispositivo, distancia)
    media_5 = consultar_media(conexao, "-5 minutes")
    media_1h = consultar_media(conexao, "-1 hour")
    print("Dispositivo:", dispositivo, "| Distância:", distancia, "mm")
    print("Média últimos 5 minutos:", formatar_media(media_5), "mm")
    print("Média última 1 hora:", formatar_media(media_1h), "mm")
    return True


def formatar_media(valor):
    return "sem leituras no período" if valor is None else "{:.2f}".format(valor)


def atender_cliente(cliente, endereco, conexao):
    print("Cliente conectado:", endereco)
    buffer = ""
    try:
        while True:
            dados = cliente.recv(1024)
            if not dados:
                break
            buffer += dados.decode("utf-8", errors="replace")
            while "\n" in buffer:
                linha, buffer = buffer.split("\n", 1)
                processar_linha(conexao, linha.strip())
            if len(buffer) > 256:
                print("Mensagem muito longa ignorada.")
                buffer = ""
    except (ConnectionError, OSError) as erro:
        print("Conexão encerrada com erro:", erro)
    finally:
        cliente.close()
        print("Cliente desconectado:", endereco)


def main():
    conexao = sqlite3.connect(BANCO)
    criar_tabela(conexao)
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((HOST, PORTA))
    servidor.listen()
    print("Servidor aguardando conexões em {}:{}".format(HOST, PORTA))
    try:
        while True:
            cliente, endereco = servidor.accept()
            atender_cliente(cliente, endereco, conexao)
    except KeyboardInterrupt:
        print("\nServidor finalizado pelo usuário.")
    finally:
        servidor.close()
        conexao.close()


if __name__ == "__main__":
    main()

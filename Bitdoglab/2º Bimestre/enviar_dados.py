"""Coleta os dados da máquina com psutil e envia um resumo ao Telegram."""
import html
import os
import platform
import socket
from datetime import datetime

import psutil
import requests


def enderecos_ipv4():
    """Retorna a lista 'interface: endereço' dos IPv4 da máquina, sem o loopback."""
    enderecos = []
    for interface, lista in psutil.net_if_addrs().items():
        for endereco in lista:
            if endereco.family == socket.AF_INET and not endereco.address.startswith("127."):
                enderecos.append(f"{interface}: {endereco.address}")
    return enderecos


def coletar_dados():
    """Retorna um dicionário com os principais dados da máquina."""
    memoria = psutil.virtual_memory()
    disco = psutil.disk_usage(os.path.abspath(os.sep))   # "/" no Linux, "C:\" no Windows
    rede = psutil.net_io_counters()
    return {
        "host": socket.gethostname(),
        "sistema": f"{platform.system()} {platform.release()}",
        "ligada_desde": datetime.fromtimestamp(psutil.boot_time()).strftime("%d/%m/%Y %H:%M"),
        "cpu_pct": psutil.cpu_percent(interval=1),        # mede o uso durante 1 segundo
        "nucleos": psutil.cpu_count(),
        "mem_pct": memoria.percent,
        "mem_total_gb": memoria.total / 1024**3,
        "disco_pct": disco.percent,
        "disco_livre_gb": disco.free / 1024**3,
        "enviados_mb": rede.bytes_sent / 1024**2,
        "recebidos_mb": rede.bytes_recv / 1024**2,
        "ipv4": enderecos_ipv4(),
    }


def montar_mensagem(d):
    """Monta o texto da mensagem em HTML (parse_mode="HTML")."""
    ips = "\n".join(f"  <code>{html.escape(ip)}</code>" for ip in d["ipv4"]) or "  (nenhum)"
    return (
        f"<b>Dados da máquina {html.escape(d['host'])}</b>\n"
        f"Sistema: {html.escape(d['sistema'])}\n"
        f"Ligada desde: {d['ligada_desde']}\n\n"
        f"CPU: {d['cpu_pct']:.1f}% ({d['nucleos']} núcleos)\n"
        f"Memória: {d['mem_pct']:.1f}% de {d['mem_total_gb']:.1f} GB\n"
        f"Disco: {d['disco_pct']:.1f}% usado, {d['disco_livre_gb']:.1f} GB livres\n"
        f"Rede: {d['enviados_mb']:.1f} MB enviados, {d['recebidos_mb']:.1f} MB recebidos\n\n"
        f"Endereços IPv4:\n{ips}"
    )


def enviar_mensagem(token, chat_id, texto):
    """Envia o texto com o método sendMessage. Retorna True se o Telegram confirmar."""
    resposta = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": texto, "parse_mode": "HTML"},
        timeout=10,
    )
    dados = resposta.json()
    if not dados["ok"]:
        print("Erro do Telegram:", dados.get("error_code"), dados.get("description"))
    return dados["ok"]


def main():
    token = os.environ.get("TELEGRAM_TOKEN")        # nunca escreva o token no código
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise SystemExit("Defina as variáveis de ambiente TELEGRAM_TOKEN e TELEGRAM_CHAT_ID.")

    texto = montar_mensagem(coletar_dados())
    print(texto)
    try:
        if enviar_mensagem(token, chat_id, texto):
            print("\nMensagem enviada.")
    except requests.exceptions.RequestException as erro:
        print("Falha na comunicação com o Telegram:", type(erro).__name__)   # não exibe a URL com o token


if __name__ == "__main__":
    main()
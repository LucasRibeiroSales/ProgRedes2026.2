# app.py – Sistema de cadastro de computadores para monitoramento
# Uma única aplicação Flask com duas "portas de entrada":
#   - páginas HTML (templates) para usar no navegador;
#   - uma API REST (JSON) para outros programas.
import re
from ipaddress import ip_address

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for

app = Flask(__name__)
app.json.ensure_ascii = False      # mantém os acentos nas respostas JSON
app.secret_key = "troque-esta-chave"   # necessária para usar session e flash

# ------------------------------------------------------------------
# Credenciais (apenas para fins didáticos!)
# ------------------------------------------------------------------
USUARIO = "admin"
SENHA = "ifrn"
TOKEN_API = "token-da-turma"

# ------------------------------------------------------------------
# "Banco de dados": uma lista de dicionários na memória
# ------------------------------------------------------------------
computadores = [
    {"id": 1, "nome": "Servidor-Web", "ip": "192.168.0.10", "mac": "AA:BB:CC:00:00:01"},
    {"id": 2, "nome": "Lab-PC-01", "ip": "192.168.0.101", "mac": "AA:BB:CC:00:00:02"},
    {"id": 3, "nome": "Impressora-Sala", "ip": "192.168.0.50", "mac": "AA:BB:CC:00:00:03"},
]
proximo_id = 4

# ------------------------------------------------------------------
# Funções auxiliares (usadas pelas páginas E pela API)
# ------------------------------------------------------------------
def buscar_por_id(id):
    for computador in computadores:
        if computador["id"] == id:
            return computador
    return None


def filtrar(texto):
    """Devolve os computadores cujo nome, IP ou MAC contém o texto."""
    if not texto:
        return computadores
    texto = texto.lower()
    resultado = []
    for c in computadores:
        if texto in c["nome"].lower() or texto in c["ip"] or texto in c["mac"].lower():
            resultado.append(c)
    return resultado


def validar(dados):
    """Confere os dados recebidos. Devolve uma mensagem de erro ou None."""
    if not isinstance(dados, dict):
        return "Os dados devem ser enviados em JSON."

    nome = str(dados.get("nome", "")).strip()
    ip = str(dados.get("ip", "")).strip()
    mac = str(dados.get("mac", "")).strip()

    if nome == "":
        return "O nome é obrigatório."
    try:
        ip_address(ip)
    except ValueError:
        return "Endereço IP inválido."
    if not re.fullmatch(r"([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}", mac):
        return "Endereço MAC inválido. Use o formato AA:BB:CC:DD:EE:FF."
    return None


def limpar(dados):
    """Padroniza os dados: tira espaços e escreve o MAC em maiúsculas com ':'."""
    return {
        "nome": dados["nome"].strip(),
        "ip": dados["ip"].strip(),
        "mac": dados["mac"].strip().upper().replace("-", ":"),
    }


def usuario_logado():
    return session.get("logado") is True


def token_valido():
    return request.headers.get("Authorization") == f"Bearer {TOKEN_API}"

# ==================================================================
# PARTE 1 – PÁGINAS HTML (templates)
# ==================================================================
@app.route("/")
def pagina_inicial():
    busca = request.args.get("busca", "")
    lista = filtrar(busca)
    return render_template("lista.html", computadores=lista, busca=busca)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["usuario"] == USUARIO and request.form["senha"] == SENHA:
            session["logado"] = True
            flash("Login realizado com sucesso.")
            return redirect(url_for("pagina_inicial"))
        flash("Usuário ou senha incorretos.")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Você saiu do sistema.")
    return redirect(url_for("pagina_inicial"))

@app.route("/computadores/novo", methods=["GET", "POST"])
def novo_computador():
    global proximo_id
    if not usuario_logado():
        return redirect(url_for("login"))

    if request.method == "POST":
        erro = validar(request.form)
        if erro:
            flash(erro)
            return render_template("formulario.html", titulo="Novo computador", dados=request.form)
        novo = limpar(request.form)
        novo["id"] = proximo_id
        proximo_id += 1
        computadores.append(novo)
        flash(f"Computador {novo['nome']} cadastrado.")
        return redirect(url_for("pagina_inicial"))

    return render_template("formulario.html", titulo="Novo computador", dados={})


@app.route("/computadores/<int:id>/editar", methods=["GET", "POST"])
def editar_computador(id):
    if not usuario_logado():
        return redirect(url_for("login"))
    computador = buscar_por_id(id)
    if computador is None:
        flash("Computador não encontrado.")
        return redirect(url_for("pagina_inicial"))

    if request.method == "POST":
        erro = validar(request.form)
        if erro:
            flash(erro)
            return render_template("formulario.html", titulo="Editar computador", dados=request.form)
        computador.update(limpar(request.form))
        flash(f"Computador {computador['nome']} atualizado.")
        return redirect(url_for("pagina_inicial"))

    return render_template("formulario.html", titulo="Editar computador", dados=computador)

@app.route("/computadores/<int:id>/apagar", methods=["POST"])
def apagar_computador(id):
    if not usuario_logado():
        return redirect(url_for("login"))
    computador = buscar_por_id(id)
    if computador:
        computadores.remove(computador)
        flash(f"Computador {computador['nome']} apagado.")
    return redirect(url_for("pagina_inicial"))

# ==================================================================
# PARTE 2 – API REST (JSON)
# ==================================================================
@app.route("/api/computadores", methods=["GET"])
def api_listar():
    busca = request.args.get("busca", "")
    return jsonify(filtrar(busca))


@app.route("/api/computadores/<int:id>", methods=["GET"])
def api_consultar(id):
    computador = buscar_por_id(id)
    if computador is None:
        return jsonify({"erro": "Computador não encontrado."}), 404
    return jsonify(computador)

@app.route("/api/computadores", methods=["POST"])
def api_cadastrar():
    global proximo_id
    if not token_valido():
        return jsonify({"erro": "Token ausente ou inválido."}), 401

    dados = request.get_json(silent=True)
    erro = validar(dados)
    if erro:
        return jsonify({"erro": erro}), 400

    novo = limpar(dados)
    novo["id"] = proximo_id
    proximo_id += 1
    computadores.append(novo)
    return jsonify(novo), 201


@app.route("/api/computadores/<int:id>", methods=["PUT"])
def api_atualizar(id):
    if not token_valido():
        return jsonify({"erro": "Token ausente ou inválido."}), 401
    computador = buscar_por_id(id)
    if computador is None:
        return jsonify({"erro": "Computador não encontrado."}), 404

    dados = request.get_json(silent=True)
    erro = validar(dados)
    if erro:
        return jsonify({"erro": erro}), 400

    computador.update(limpar(dados))
    return jsonify(computador)


@app.route("/api/computadores/<int:id>", methods=["DELETE"])
def api_apagar(id):
    if not token_valido():
        return jsonify({"erro": "Token ausente ou inválido."}), 401
    computador = buscar_por_id(id)
    if computador is None:
        return jsonify({"erro": "Computador não encontrado."}), 404

    computadores.remove(computador)
    return "", 204

if __name__ == "__main__":
    app.run(debug=True)


"""
Comunidade Sinfônica — backend de autenticação e conteúdo (agenda/bandas).

Serve o site estático (HTML/CSS/JS da pasta comunidade-sinfonica/) e expõe uma
API de login/cadastro (sessão por cookie, SQLite) e de gerenciamento da agenda
de shows e das bandas da comunidade — essa parte só pode ser usada por quem
tiver a flag "admin" (veja promover_admin.py para promover alguém).

Como rodar:
    pip install -r requirements.txt
    python app.py

O site fica disponível em http://localhost:5000
"""

import json
import os
import re
import secrets
import sqlite3
import urllib.request
from datetime import datetime, timedelta, timezone
from functools import wraps
from pathlib import Path

from flask import Flask, abort, jsonify, request, send_from_directory, session
from werkzeug.security import check_password_hash, generate_password_hash

from db import get_db
import seed_bandas
import seed_agenda

BACKEND_DIR = Path(__file__).resolve().parent
BASE_DIR = BACKEND_DIR.parent  # pasta comunidade-sinfonica/ (onde ficam os .html)
SECRET_KEY_PATH = BACKEND_DIR / "secret.key"

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
DATA_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")  # AAAA-MM-DD
HORA_REGEX = re.compile(r"^\d{2}:\d{2}$")  # HH:MM

BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "").strip()
BREVO_SENDER_EMAIL = os.environ.get("BREVO_SENDER_EMAIL", "").strip()
BREVO_SENDER_NOME = "Comunidade Sinfônica"
VALIDADE_TOKEN_REDEFINICAO = timedelta(hours=1)


def carregar_secret_key() -> str:
    """Usa a variável de ambiente SECRET_KEY se existir (produção, ex: Render —
    assim a chave não se perde a cada novo deploy). Em desenvolvimento local,
    gera e reaproveita uma chave salva em backend/secret.key."""
    da_variavel_ambiente = os.environ.get("SECRET_KEY")
    if da_variavel_ambiente:
        return da_variavel_ambiente
    if SECRET_KEY_PATH.exists():
        return SECRET_KEY_PATH.read_text().strip()
    chave = secrets.token_hex(32)
    SECRET_KEY_PATH.write_text(chave)
    return chave


app = Flask(__name__)
app.secret_key = carregar_secret_key()
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)


def init_db() -> None:
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                senha_hash TEXT NOT NULL,
                admin INTEGER NOT NULL DEFAULT 0,
                criado_em TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        # Migração leve: se o banco já existia (de uma versão anterior sem a
        # coluna "admin"), adiciona ela agora. Ignora erro se já existir.
        try:
            conn.execute("ALTER TABLE usuarios ADD COLUMN admin INTEGER NOT NULL DEFAULT 0")
        except sqlite3.OperationalError:
            pass

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS shows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                banda TEXT NOT NULL,
                local TEXT NOT NULL,
                cidade TEXT NOT NULL,
                data TEXT NOT NULL,
                horario TEXT DEFAULT '',
                observacoes TEXT DEFAULT '',
                criado_por INTEGER,
                criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (criado_por) REFERENCES usuarios(id)
            )
            """
        )
        # Migração leve: bancos criados antes de "observacoes" existir
        # (e antes do horário virar opcional).
        try:
            conn.execute("ALTER TABLE shows ADD COLUMN observacoes TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS bandas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                genero TEXT NOT NULL,
                descricao TEXT DEFAULT '',
                emoji TEXT DEFAULT '🎵',
                instagram TEXT DEFAULT '',
                criado_por INTEGER,
                criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (criado_por) REFERENCES usuarios(id)
            )
            """
        )
        # Migração leve: bancos criados antes do campo "instagram" existir.
        try:
            conn.execute("ALTER TABLE bandas ADD COLUMN instagram TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS redefinicoes_senha (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                token TEXT NOT NULL UNIQUE,
                expira_em TEXT NOT NULL,
                usado INTEGER NOT NULL DEFAULT 0,
                criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
            """
        )


def emails_admin_configurados() -> set[str]:
    """Lê a variável de ambiente ADMIN_EMAIL (um ou mais e-mails separados por
    vírgula, ex: "a@x.com,b@y.com") e devolve um conjunto em minúsculo."""
    emails_admin = os.environ.get("ADMIN_EMAIL", "")
    return {email.strip().lower() for email in emails_admin.split(",") if email.strip()}


def bootstrap_admin() -> None:
    """Promove quem já estiver cadastrado com um e-mail de ADMIN_EMAIL.
    Serve de reforço pra contas que já existiam antes da variável ser
    definida — mas o caminho principal é o registrar() já criar a conta como
    admin na hora (veja abaixo), porque em serviços como o Render mudar uma
    variável de ambiente dispara um novo deploy, e o deploy reseta o banco
    ANTES desta função rodar — ou seja, uma conta cadastrada e só promovida
    depois corre o risco de ser apagada nesse meio-tempo."""
    emails = emails_admin_configurados()
    if not emails:
        return
    with get_db() as conn:
        for email in emails:
            conn.execute("UPDATE usuarios SET admin = 1 WHERE email = ?", (email,))


def seed_inicial() -> None:
    """Popula bandas e shows com os dados já cadastrados pela comunidade,
    mas só se as tabelas estiverem vazias — assim o site nunca fica "pelado"
    quando o disco reseta (ex: a cada novo deploy no plano grátis do Render),
    e não duplica nada se as tabelas já tiverem dados."""
    with get_db() as conn:
        if not conn.execute("SELECT 1 FROM bandas LIMIT 1").fetchone():
            for nome, genero, instagram in seed_bandas.BANDAS:
                conn.execute(
                    "INSERT INTO bandas (nome, genero, descricao, emoji, instagram) VALUES (?, ?, ?, ?, ?)",
                    (nome, genero, "", seed_bandas.EMOJI_PADRAO, instagram or ""),
                )

        if not conn.execute("SELECT 1 FROM shows LIMIT 1").fetchone():
            for banda, local, cidade, data, horario, observacoes in seed_agenda.SHOWS:
                conn.execute(
                    "INSERT INTO shows (banda, local, cidade, data, horario, observacoes) VALUES (?, ?, ?, ?, ?, ?)",
                    (banda, local, cidade, data, horario, observacoes),
                )


def enviar_email(destinatario: str, assunto: str, html: str) -> bool:
    """Envia um e-mail via API do Brevo (brevo.com). Se BREVO_API_KEY não
    estiver configurada (ex: desenvolvimento local), não envia de verdade —
    só imprime no console, pra dar pra testar sem precisar de conta lá.
    Retorna True se enviou (ou simulou) com sucesso, False se deu erro."""
    if not BREVO_API_KEY or not BREVO_SENDER_EMAIL:
        print(f"[email simulado] Para: {destinatario} | Assunto: {assunto}\n{html}")
        return True

    corpo = json.dumps(
        {
            "sender": {"email": BREVO_SENDER_EMAIL, "name": BREVO_SENDER_NOME},
            "to": [{"email": destinatario}],
            "subject": assunto,
            "htmlContent": html,
        }
    ).encode("utf-8")

    requisicao = urllib.request.Request(
        "https://api.brevo.com/v3/smtp/email",
        data=corpo,
        method="POST",
        headers={
            "api-key": BREVO_API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )

    try:
        # timeout curto pra nunca travar a requisição do usuário esperando o
        # Brevo responder (mesma lição aprendida com o Turso)
        with urllib.request.urlopen(requisicao, timeout=10):
            return True
    except Exception as erro:  # não deixa o cadastro/login quebrar por causa do e-mail
        print(f"[erro ao enviar e-mail via Brevo] {erro}")
        return False


# Roda sempre que o módulo é carregado — seja com "python app.py" (dev local)
# ou importado pelo gunicorn em produção (o bloco "if __name__" no fim do
# arquivo não executa nesse segundo caso).
init_db()
bootstrap_admin()
seed_inicial()


# =====================================================
# Autenticação / autorização
# =====================================================

def usuario_atual():
    """Retorna a linha do usuário logado (com base na sessão) ou None."""
    usuario_id = session.get("usuario_id")
    if not usuario_id:
        return None
    with get_db() as conn:
        usuario = conn.execute(
            "SELECT id, nome, email, admin FROM usuarios WHERE id = ?", (usuario_id,)
        ).fetchone()
    return usuario


def requer_login(f):
    @wraps(f)
    def decorado(*args, **kwargs):
        if not usuario_atual():
            return jsonify(ok=False, erro="É preciso estar logado."), 401
        return f(*args, **kwargs)

    return decorado


def requer_admin(f):
    @wraps(f)
    def decorado(*args, **kwargs):
        usuario = usuario_atual()
        if not usuario:
            return jsonify(ok=False, erro="É preciso estar logado."), 401
        if not usuario["admin"]:
            return jsonify(ok=False, erro="Apenas administradores podem fazer isso."), 403
        return f(*args, **kwargs)

    return decorado


# =====================================================
# API de autenticação
# =====================================================

@app.post("/api/registrar")
def registrar():
    dados = request.get_json(silent=True) or {}
    nome = (dados.get("nome") or "").strip()
    email = (dados.get("email") or "").strip().lower()
    senha = dados.get("senha") or ""

    if not nome or len(nome) < 2:
        return jsonify(ok=False, erro="Informe seu nome."), 400
    if not EMAIL_REGEX.match(email):
        return jsonify(ok=False, erro="E-mail inválido."), 400
    if len(senha) < 6:
        return jsonify(ok=False, erro="A senha precisa ter pelo menos 6 caracteres."), 400

    senha_hash = generate_password_hash(senha)
    # Se ADMIN_EMAIL já estiver configurado com esse e-mail, a conta nasce
    # admin na hora — não depende de nenhum restart/promoção posterior.
    é_admin = email in emails_admin_configurados()

    try:
        with get_db() as conn:
            cursor = conn.execute(
                "INSERT INTO usuarios (nome, email, senha_hash, admin) VALUES (?, ?, ?, ?)",
                (nome, email, senha_hash, int(é_admin)),
            )
            usuario_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        return jsonify(ok=False, erro="Já existe uma conta com esse e-mail."), 409

    session.clear()
    session["usuario_id"] = usuario_id
    session.permanent = False

    return jsonify(ok=True, usuario={"id": usuario_id, "nome": nome, "email": email, "admin": é_admin})


@app.post("/api/login")
def login():
    dados = request.get_json(silent=True) or {}
    email = (dados.get("email") or "").strip().lower()
    senha = dados.get("senha") or ""
    lembrar = bool(dados.get("lembrar"))

    with get_db() as conn:
        usuario = conn.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()

    if not usuario or not check_password_hash(usuario["senha_hash"], senha):
        return jsonify(ok=False, erro="E-mail ou senha incorretos."), 401

    session.clear()
    session["usuario_id"] = usuario["id"]
    session.permanent = lembrar
    if lembrar:
        app.permanent_session_lifetime = timedelta(days=30)

    return jsonify(
        ok=True,
        usuario={
            "id": usuario["id"],
            "nome": usuario["nome"],
            "email": usuario["email"],
            "admin": bool(usuario["admin"]),
        },
    )


@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify(ok=True)


@app.get("/api/eu")
def eu():
    usuario = usuario_atual()
    if not usuario:
        return jsonify(ok=False), 401

    return jsonify(
        ok=True,
        usuario={
            "id": usuario["id"],
            "nome": usuario["nome"],
            "email": usuario["email"],
            "admin": bool(usuario["admin"]),
        },
    )


def _token_ainda_valido(expira_em_iso: str) -> bool:
    try:
        expira_em = datetime.fromisoformat(expira_em_iso)
    except ValueError:
        return False
    return datetime.now(timezone.utc) < expira_em


@app.post("/api/esqueci-senha")
def esqueci_senha():
    dados = request.get_json(silent=True) or {}
    email = (dados.get("email") or "").strip().lower()

    # Sempre devolve a mesma mensagem, exista ou não a conta — evita que
    # alguém descubra quais e-mails estão cadastrados tentando um por um.
    mensagem_padrao = "Se esse e-mail estiver cadastrado, você vai receber um link de redefinição em instantes."

    if not EMAIL_REGEX.match(email):
        return jsonify(ok=True, mensagem=mensagem_padrao)

    with get_db() as conn:
        usuario = conn.execute("SELECT id, nome FROM usuarios WHERE email = ?", (email,)).fetchone()

        if usuario:
            token = secrets.token_urlsafe(32)
            expira_em = (datetime.now(timezone.utc) + VALIDADE_TOKEN_REDEFINICAO).isoformat()
            conn.execute(
                "INSERT INTO redefinicoes_senha (usuario_id, token, expira_em) VALUES (?, ?, ?)",
                (usuario["id"], token, expira_em),
            )

            link = f"{request.url_root.rstrip('/')}/redefinir-senha.html?token={token}"
            html = f"""
                <div style="font-family: Georgia, serif; background:#0a0505; color:#f4ede4; padding:32px;">
                  <h1 style="color:#d4af37; font-size:22px; margin:0 0 16px;">Comunidade Sinfônica</h1>
                  <p>Olá, {usuario['nome']}!</p>
                  <p>Recebemos um pedido pra redefinir sua senha. Clique no link abaixo (válido por 1 hora):</p>
                  <p><a href="{link}" style="color:#d4af37;">Redefinir minha senha</a></p>
                  <p style="color:#cbb4b4; font-size:13px;">Se você não pediu isso, pode ignorar esse e-mail com tranquilidade — sua senha continua a mesma.</p>
                </div>
            """
            enviar_email(email, "Redefinir sua senha — Comunidade Sinfônica", html)

    return jsonify(ok=True, mensagem=mensagem_padrao)


@app.get("/api/validar-token-redefinicao")
def validar_token_redefinicao():
    token = (request.args.get("token") or "").strip()
    if not token:
        return jsonify(ok=True, valido=False)

    with get_db() as conn:
        registro = conn.execute(
            "SELECT expira_em, usado FROM redefinicoes_senha WHERE token = ?", (token,)
        ).fetchone()

    valido = bool(registro) and not registro["usado"] and _token_ainda_valido(registro["expira_em"])
    return jsonify(ok=True, valido=valido)


@app.post("/api/redefinir-senha")
def redefinir_senha():
    dados = request.get_json(silent=True) or {}
    token = (dados.get("token") or "").strip()
    senha = dados.get("senha") or ""

    if len(senha) < 6:
        return jsonify(ok=False, erro="A senha precisa ter pelo menos 6 caracteres."), 400

    with get_db() as conn:
        registro = conn.execute(
            "SELECT id, usuario_id, expira_em, usado FROM redefinicoes_senha WHERE token = ?",
            (token,),
        ).fetchone()

        if not registro or registro["usado"] or not _token_ainda_valido(registro["expira_em"]):
            return jsonify(ok=False, erro="Link inválido ou expirado. Peça um novo."), 400

        senha_hash = generate_password_hash(senha)
        conn.execute(
            "UPDATE usuarios SET senha_hash = ? WHERE id = ?", (senha_hash, registro["usuario_id"])
        )
        conn.execute("UPDATE redefinicoes_senha SET usado = 1 WHERE id = ?", (registro["id"],))

    return jsonify(ok=True)


# =====================================================
# API da agenda de shows
# (leitura: qualquer usuário logado / escrita: só admin)
# =====================================================

@app.get("/api/shows")
@requer_login
def listar_shows():
    with get_db() as conn:
        linhas = conn.execute(
            "SELECT id, banda, local, cidade, data, horario, observacoes FROM shows ORDER BY data, horario"
        ).fetchall()
    return jsonify(ok=True, shows=[dict(linha) for linha in linhas])


@app.post("/api/shows")
@requer_admin
def criar_show():
    dados = request.get_json(silent=True) or {}
    banda = (dados.get("banda") or "").strip()
    local = (dados.get("local") or "").strip()
    cidade = (dados.get("cidade") or "").strip()
    data = (dados.get("data") or "").strip()
    horario = (dados.get("horario") or "").strip()  # opcional — "a confirmar" se vazio
    observacoes = (dados.get("observacoes") or "").strip()

    if not banda or not local or not cidade:
        return jsonify(ok=False, erro="Preencha banda, local e cidade."), 400
    if not DATA_REGEX.match(data):
        return jsonify(ok=False, erro="Data inválida."), 400
    if horario and not HORA_REGEX.match(horario):
        return jsonify(ok=False, erro="Horário inválido."), 400

    usuario = usuario_atual()
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO shows (banda, local, cidade, data, horario, observacoes, criado_por) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (banda, local, cidade, data, horario, observacoes, usuario["id"]),
        )
        show_id = cursor.lastrowid

    return jsonify(
        ok=True,
        show={
            "id": show_id,
            "banda": banda,
            "local": local,
            "cidade": cidade,
            "data": data,
            "horario": horario,
            "observacoes": observacoes,
        },
    )


@app.put("/api/shows/<int:show_id>")
@requer_admin
def editar_show(show_id):
    dados = request.get_json(silent=True) or {}
    banda = (dados.get("banda") or "").strip()
    local = (dados.get("local") or "").strip()
    cidade = (dados.get("cidade") or "").strip()
    data = (dados.get("data") or "").strip()
    horario = (dados.get("horario") or "").strip()
    observacoes = (dados.get("observacoes") or "").strip()

    if not banda or not local or not cidade:
        return jsonify(ok=False, erro="Preencha banda, local e cidade."), 400
    if not DATA_REGEX.match(data):
        return jsonify(ok=False, erro="Data inválida."), 400
    if horario and not HORA_REGEX.match(horario):
        return jsonify(ok=False, erro="Horário inválido."), 400

    with get_db() as conn:
        cursor = conn.execute(
            """UPDATE shows SET banda = ?, local = ?, cidade = ?, data = ?, horario = ?,
               observacoes = ? WHERE id = ?""",
            (banda, local, cidade, data, horario, observacoes, show_id),
        )
        if cursor.rowcount == 0:
            return jsonify(ok=False, erro="Show não encontrado."), 404

    return jsonify(
        ok=True,
        show={
            "id": show_id,
            "banda": banda,
            "local": local,
            "cidade": cidade,
            "data": data,
            "horario": horario,
            "observacoes": observacoes,
        },
    )


@app.delete("/api/shows/<int:show_id>")
@requer_admin
def excluir_show(show_id):
    with get_db() as conn:
        conn.execute("DELETE FROM shows WHERE id = ?", (show_id,))
    return jsonify(ok=True)


# =====================================================
# API das bandas da comunidade
# (leitura: qualquer usuário logado / escrita: só admin)
# =====================================================

@app.get("/api/bandas")
@requer_login
def listar_bandas():
    with get_db() as conn:
        linhas = conn.execute(
            "SELECT id, nome, genero, descricao, emoji, instagram FROM bandas ORDER BY nome"
        ).fetchall()
    return jsonify(ok=True, bandas=[dict(linha) for linha in linhas])


def normalizar_instagram(valor: str) -> str:
    """Aceita '@usuario', 'usuario' ou um link do Instagram e devolve sempre '@usuario'."""
    valor = (valor or "").strip()
    if not valor:
        return ""
    # se colaram um link completo (instagram.com/usuario), extrai só o usuário
    valor = re.sub(r"^https?://(www\.)?instagram\.com/", "", valor, flags=re.IGNORECASE)
    valor = valor.strip("/ ")
    if not valor:
        return ""
    return valor if valor.startswith("@") else f"@{valor}"


@app.post("/api/bandas")
@requer_admin
def criar_banda():
    dados = request.get_json(silent=True) or {}
    nome = (dados.get("nome") or "").strip()
    genero = (dados.get("genero") or "").strip()
    descricao = (dados.get("descricao") or "").strip()
    emoji = (dados.get("emoji") or "").strip() or "🎵"
    instagram = normalizar_instagram(dados.get("instagram"))

    if not nome or not genero:
        return jsonify(ok=False, erro="Preencha nome e gênero."), 400

    usuario = usuario_atual()
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO bandas (nome, genero, descricao, emoji, instagram, criado_por) VALUES (?, ?, ?, ?, ?, ?)",
            (nome, genero, descricao, emoji, instagram, usuario["id"]),
        )
        banda_id = cursor.lastrowid

    return jsonify(
        ok=True,
        banda={
            "id": banda_id,
            "nome": nome,
            "genero": genero,
            "descricao": descricao,
            "emoji": emoji,
            "instagram": instagram,
        },
    )


@app.put("/api/bandas/<int:banda_id>")
@requer_admin
def editar_banda(banda_id):
    dados = request.get_json(silent=True) or {}
    nome = (dados.get("nome") or "").strip()
    genero = (dados.get("genero") or "").strip()
    descricao = (dados.get("descricao") or "").strip()
    emoji = (dados.get("emoji") or "").strip() or "🎵"
    instagram = normalizar_instagram(dados.get("instagram"))

    if not nome or not genero:
        return jsonify(ok=False, erro="Preencha nome e gênero."), 400

    with get_db() as conn:
        cursor = conn.execute(
            "UPDATE bandas SET nome = ?, genero = ?, descricao = ?, emoji = ?, instagram = ? WHERE id = ?",
            (nome, genero, descricao, emoji, instagram, banda_id),
        )
        if cursor.rowcount == 0:
            return jsonify(ok=False, erro="Banda não encontrada."), 404

    return jsonify(
        ok=True,
        banda={
            "id": banda_id,
            "nome": nome,
            "genero": genero,
            "descricao": descricao,
            "emoji": emoji,
            "instagram": instagram,
        },
    )


@app.delete("/api/bandas/<int:banda_id>")
@requer_admin
def excluir_banda(banda_id):
    with get_db() as conn:
        conn.execute("DELETE FROM bandas WHERE id = ?", (banda_id,))
    return jsonify(ok=True)


# =====================================================
# Arquivos estáticos do site (html/css/js/assets)
# =====================================================

@app.get("/")
def home():
    return send_from_directory(BASE_DIR, "index.html")


@app.get("/<path:caminho>")
def arquivos_estaticos(caminho):
    alvo = (BASE_DIR / caminho).resolve()
    # impede sair da pasta do site (ex: ../) e impede servir o próprio backend/
    if not alvo.is_relative_to(BASE_DIR) or alvo.is_relative_to(BACKEND_DIR):
        abort(404)
    if not alvo.is_file():
        abort(404)
    return send_from_directory(BASE_DIR, caminho)


if __name__ == "__main__":
    # host="0.0.0.0" faz o servidor aceitar conexões de outros dispositivos na
    # mesma rede (ex: celular), não só da própria máquina.
    # debug=True só é usado aqui (dev local) — em produção o gunicorn nem
    # executa este bloco, então o modo debug nunca fica exposto publicamente.
    app.run(host="0.0.0.0", debug=True, port=5000)

"""
Camada de acesso ao banco de dados.

Usa a biblioteca "libsql", que fala com bancos locais (arquivo) e remotos
(Turso) exatamente da mesma forma. Em produção — quando as variáveis de
ambiente TURSO_DATABASE_URL e TURSO_AUTH_TOKEN estiverem definidas (ex: no
Render) — conecta no Turso, um banco hospedado à parte que não se apaga
quando o servidor reinicia. Sem essas variáveis, usa um arquivo SQLite local
(comunidade.db), que é mais simples pra desenvolvimento no seu PC.

O resto do app.py não precisa saber qual dos dois está em uso: chama
get_db() e usa como um cursor comum (execute, fetchone, fetchall,
lastrowid), com acesso às colunas por nome (linha["coluna"]) nos dois casos.

Conexões remotas do libSQL podem travar ou "expirar" depois de um tempo sem
uso (é um problema conhecido da biblioteca — veja
https://github.com/tursodatabase/libsql/issues/985). Como o servidor do
Render só roda um processo, uma trava assim derruba o site inteiro até o
Render perceber e reiniciar à força. Por isso: cada requisição abre a sua
própria conexão (não reaproveita uma antiga que pode estar travada), e toda
chamada ao Turso tem um limite de tempo (TEMPO_LIMITE_PADRAO) — se estourar,
a operação desiste e devolve um erro tratável em vez de travar o servidor.
"""

import os
import queue as fila_module
import threading
from pathlib import Path

import libsql

TURSO_URL = os.environ.get("TURSO_DATABASE_URL", "").strip()
TURSO_TOKEN = os.environ.get("TURSO_AUTH_TOKEN", "").strip()
USANDO_TURSO = bool(TURSO_URL and TURSO_TOKEN)

DB_PATH = Path(__file__).resolve().parent / "comunidade.db"

TEMPO_LIMITE_PADRAO = 10  # segundos


class IntegrityError(Exception):
    """Violação de restrição única (ex: e-mail duplicado) — mesma exceção
    seja o banco por trás o SQLite local ou o Turso."""


class TempoEsgotado(Exception):
    """O banco (Turso) demorou demais pra responder e a operação foi
    abandonada, pra não travar o site inteiro nesse meio-tempo."""


def _com_tempo_limite(funcao, tempo_limite: float = TEMPO_LIMITE_PADRAO):
    """Roda "funcao" (sem argumentos) numa thread separada e desiste depois
    de "tempo_limite" segundos, mesmo que a thread continue travada por
    dentro (a chamada nativa do libsql não tem como ser cancelada à força —
    só abandonamos ela e seguimos em frente)."""
    resultado_fila: fila_module.Queue = fila_module.Queue(maxsize=1)

    def alvo() -> None:
        try:
            resultado_fila.put(("ok", funcao()))
        except Exception as erro:  # repassa qualquer erro pro chamador original
            resultado_fila.put(("erro", erro))

    thread = threading.Thread(target=alvo, daemon=True)
    thread.start()
    thread.join(timeout=tempo_limite)

    if thread.is_alive():
        raise TempoEsgotado("O banco de dados demorou demais pra responder. Tente novamente.")

    tipo, valor = resultado_fila.get()
    if tipo == "erro":
        raise valor
    return valor


class Linha:
    """Deixa uma linha de resultado acessível por nome de coluna
    (linha["email"]) ou índice, e suporta dict(linha) — igual ao
    sqlite3.Row que o projeto já usava antes do Turso."""

    def __init__(self, colunas, valores):
        self._colunas = colunas
        self._valores = valores

    def __getitem__(self, chave):
        if isinstance(chave, str):
            return self._valores[self._colunas.index(chave)]
        return self._valores[chave]

    def keys(self):
        return self._colunas

    def __repr__(self):
        return repr(dict(zip(self._colunas, self._valores)))


class Cursor:
    """Deixa o cursor do libsql parecido com o do sqlite3 (fetchone/fetchall
    retornando linhas por nome de coluna, e lastrowid)."""

    def __init__(self, cursor_bruto):
        self._cursor = cursor_bruto
        self._colunas = [coluna[0] for coluna in (cursor_bruto.description or [])]

    @property
    def lastrowid(self):
        return self._cursor.lastrowid

    def fetchone(self):
        linha = self._cursor.fetchone()
        return Linha(self._colunas, linha) if linha is not None else None

    def fetchall(self):
        return [Linha(self._colunas, linha) for linha in self._cursor.fetchall()]


class Conexao:
    """Conexão com o banco (Turso ou arquivo local), com suporte a
    "with get_db() as conn:" — comita ao sair do bloco sem erro."""

    def __init__(self):
        if USANDO_TURSO:
            self._conn = _com_tempo_limite(
                lambda: libsql.connect(database=TURSO_URL, auth_token=TURSO_TOKEN)
            )
        else:
            self._conn = libsql.connect(str(DB_PATH))

    def execute(self, sql: str, params=()):
        try:
            if USANDO_TURSO:
                cursor_bruto = _com_tempo_limite(lambda: self._conn.execute(sql, params))
            else:
                cursor_bruto = self._conn.execute(sql, params)
        except ValueError as erro:
            if "UNIQUE constraint failed" in str(erro):
                raise IntegrityError(str(erro)) from erro
            raise
        return Cursor(cursor_bruto)

    def commit(self) -> None:
        self._conn.commit()

    def close(self) -> None:
        try:
            self._conn.close()
        except Exception:
            pass

    def __enter__(self) -> "Conexao":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is None:
            self.commit()
        self.close()


def get_db() -> Conexao:
    return Conexao()


def coluna_ja_existe(erro: Exception) -> bool:
    """Usado nas migrações leves (ALTER TABLE ADD COLUMN) pra saber se o
    erro foi só porque a coluna já existe — nesse caso é seguro ignorar."""
    return isinstance(erro, ValueError) and "duplicate column name" in str(erro)

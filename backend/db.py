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
"""

import os
from pathlib import Path

import libsql

TURSO_URL = os.environ.get("TURSO_DATABASE_URL", "").strip()
TURSO_TOKEN = os.environ.get("TURSO_AUTH_TOKEN", "").strip()
USANDO_TURSO = bool(TURSO_URL and TURSO_TOKEN)

DB_PATH = Path(__file__).resolve().parent / "comunidade.db"

# Conexão com o Turso é reaproveitada entre requisições (fica cara e lenta
# abrir uma conexão de rede nova a cada clique — foi isso que travou um
# worker do Render e derrubou ele por timeout). Cada processo do gunicorn
# mantém a sua própria.
_conexao_turso_compartilhada = None


class IntegrityError(Exception):
    """Violação de restrição única (ex: e-mail duplicado) — mesma exceção
    seja o banco por trás o SQLite local ou o Turso."""


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
    "with get_db() as conn:" — comita ao sair do bloco sem erro. No Turso,
    a conexão de rede é compartilhada entre requisições (ver
    _conexao_turso_compartilhada) e por isso não é fechada aqui; no arquivo
    local, abrir/fechar por requisição é barato e continua como antes."""

    def __init__(self):
        global _conexao_turso_compartilhada

        if USANDO_TURSO:
            if _conexao_turso_compartilhada is None:
                _conexao_turso_compartilhada = libsql.connect(
                    database=TURSO_URL, auth_token=TURSO_TOKEN
                )
            self._conn = _conexao_turso_compartilhada
        else:
            self._conn = libsql.connect(str(DB_PATH))

    def execute(self, sql: str, params=()):
        try:
            cursor_bruto = self._conn.execute(sql, params)
        except ValueError as erro:
            if "UNIQUE constraint failed" in str(erro):
                raise IntegrityError(str(erro)) from erro
            raise
        return Cursor(cursor_bruto)

    def commit(self) -> None:
        self._conn.commit()

    def close(self) -> None:
        if not USANDO_TURSO:
            self._conn.close()
        # a conexão do Turso fica aberta pra ser reaproveitada na próxima requisição

    def __enter__(self) -> "Conexao":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is None:
            self.commit()
        else:
            # desfaz qualquer coisa pendente pra não deixar a conexão
            # (principalmente a compartilhada do Turso) suja pro próximo uso
            try:
                self._conn.rollback()
            except Exception:
                pass
        self.close()


def get_db() -> Conexao:
    return Conexao()


def coluna_ja_existe(erro: Exception) -> bool:
    """Usado nas migrações leves (ALTER TABLE ADD COLUMN) pra saber se o
    erro foi só porque a coluna já existe — nesse caso é seguro ignorar."""
    return isinstance(erro, ValueError) and "duplicate column name" in str(erro)

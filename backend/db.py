"""
Camada de acesso ao banco de dados — SQLite puro (Python padrão).

O caminho do arquivo do banco vem da variável de ambiente DATA_DIR quando
ela existir (produção — no Render, aponta pro disco persistente montado no
serviço, ex: /var/data), e cai pra pasta backend/ quando não existir
(desenvolvimento local, sem precisar configurar nada).

Esse projeto já usou o Turso (banco remoto) antes disso, mas voltou pro
SQLite simples porque conexões remotas viviam travando/expirando em uso
esporádico (problema conhecido do libSQL) e derrubavam o site inteiro, já
que o Render só roda um processo. Com o disco persistente do plano pago do
Render, o arquivo local não se apaga mais entre deploys — resolve o mesmo
problema sem essa complexidade.
"""

import os
import sqlite3
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent

_data_dir = os.environ.get("DATA_DIR", "").strip()
DB_PATH = Path(_data_dir) / "comunidade.db" if _data_dir else BACKEND_DIR / "comunidade.db"


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

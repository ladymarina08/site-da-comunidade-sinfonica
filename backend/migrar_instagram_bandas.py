"""
Migração única: extrai o @ do Instagram que estava embutido no campo
"descricao" das bandas (formato antigo "Instagram: @handle", usado antes de
existir uma coluna própria) e move para a nova coluna "instagram".

Seguro rodar mais de uma vez — bandas que já têm instagram preenchido são
puladas.

Uso:
    python migrar_instagram_bandas.py
"""

import re
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "comunidade.db"
PADRAO = re.compile(r"Instagram:\s*(@[\w.\-]+)")


def main() -> None:
    if not DB_PATH.exists():
        print("Banco de dados não encontrado em backend/comunidade.db.")
        return

    conn = sqlite3.connect(DB_PATH)

    # garante que a coluna existe, mesmo rodando este script antes do app.py
    try:
        conn.execute("ALTER TABLE bandas ADD COLUMN instagram TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass

    linhas = conn.execute("SELECT id, descricao, instagram FROM bandas").fetchall()
    migradas = 0

    for banda_id, descricao, instagram_atual in linhas:
        if instagram_atual:
            continue  # já tem instagram próprio, não mexe
        if not descricao:
            continue

        match = PADRAO.search(descricao)
        if not match:
            continue

        handle = match.group(1)
        nova_descricao = PADRAO.sub("", descricao).strip(" .-—")

        conn.execute(
            "UPDATE bandas SET instagram = ?, descricao = ? WHERE id = ?",
            (handle, nova_descricao, banda_id),
        )
        migradas += 1

    conn.commit()
    conn.close()

    print(f"[OK] {migradas} banda(s) migrada(s) para o novo campo de Instagram.")


if __name__ == "__main__":
    main()

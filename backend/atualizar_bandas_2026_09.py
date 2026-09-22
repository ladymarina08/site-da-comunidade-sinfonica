"""
Script de atualizacao pontual das bandas — mudancas enviadas pela Admin em
22/09/2026 (1 banda removida, 2 instagrams atualizados, 5 bandas novas).

Seguro rodar mais de uma vez: a remocao so acontece se a banda ainda
existir, atualizacoes de instagram so mudam o valor se for diferente, e
adicoes pulam bandas que ja existem (mesma checagem usada em
seed_bandas.py).

Uso:
    python atualizar_bandas_2026_09.py
"""

import db

REMOVER = [
    "Darkdream (SP)",  # saiu da comunidade
]

ATUALIZAR_INSTAGRAM = [
    # (nome, instagram novo)
    ("SymphoniCore (SP)", "@symphonicoreofficial"),
    ("Lovelorn (SP)", "@love.lorn_band"),
]

EMOJI_PADRAO = "🦇"

ADICIONAR = [
    # (nome, genero, instagram)
    ("Dimmu Borgir Experience (SP)", "Dimmu Borgir Tributo", "@dimmuborgirexperience"),
    ("Southern Queens (SP)", "Pop/Flash Back: Versão Metal Sinfônico, Exit Éden Tributo & etc", None),
    ("Xandream (SP)", "Xandria Cover", "@xandriatributo"),
    ("Celtic Darling (SP)", "Eluveitie & Cellar Darling", None),
    ("Eduardo Lobbo (SP)", "Autoral | Folk Metal BR", "@eduardogaldur"),
]


def main() -> None:
    conn = db.get_db()

    removidas = 0
    for nome in REMOVER:
        linha = conn.execute("SELECT id FROM bandas WHERE nome = ?", (nome,)).fetchone()
        if not linha:
            continue
        conn.execute("DELETE FROM bandas WHERE id = ?", (linha["id"],))
        removidas += 1

    atualizadas = 0
    for nome, instagram in ATUALIZAR_INSTAGRAM:
        cursor = conn.execute(
            "UPDATE bandas SET instagram = ? WHERE nome = ? AND instagram != ?", (instagram, nome, instagram)
        )
        atualizadas += cursor.rowcount

    inseridas = 0
    puladas = 0
    for nome, genero, instagram in ADICIONAR:
        ja_existe = conn.execute("SELECT 1 FROM bandas WHERE nome = ?", (nome,)).fetchone()
        if ja_existe:
            puladas += 1
            continue
        conn.execute(
            "INSERT INTO bandas (nome, genero, descricao, emoji, instagram) VALUES (?, ?, ?, ?, ?)",
            (nome, genero, "", EMOJI_PADRAO, instagram or ""),
        )
        inseridas += 1

    conn.commit()
    conn.close()

    print(f"[OK] {removidas} banda(s) removida(s), {atualizadas} instagram(s) atualizado(s), {inseridas} banda(s) adicionada(s).")
    if puladas:
        print(f"[INFO] {puladas} banda(s) ja existiam e foram puladas.")


if __name__ == "__main__":
    main()

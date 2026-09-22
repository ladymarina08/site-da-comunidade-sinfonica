"""
Script de publicacao pontual do primeiro recado — enviado pela Admin em
22/09/2026 (bandas da comunidade procurando integrantes).

Seguro rodar mais de uma vez: pula a publicacao se ja existir um recado
com o mesmo titulo.

Uso:
    python atualizar_recados_2026_09.py
"""

import db

TITULO = "🎸 Bandas procurando integrantes"

CORPO = """🦇 Dimmu Borgir Exp (SP) — @dimmuborgirexperience
Procura: Baixista
Contato: 11 95780-2257

🦇 Arcanis (RJ) — @wearearcanis
Procura: Tecladista
Contato: 21 99141-4576

🦇 Amaranthe Cover (SP)
Procura: Baixista, Baterista
Contato: 11 98863-1233

🦇 Blacked Doom Metal (SP)
Procura: Baterista
Contato: 11 98863-1233

🦇 Lithium — Evanescence Tributo
Procura: Guitarrista
Contato: 11 96477-3616

🦇 Admirável — Pitty Tributo
Procura: Guitarrista
Contato: 11 96477-3616

🦇 Descomplicated — Avril Lavigne Tributo
Procura: Guitarrista
Contato: 11 96477-3616"""


def main() -> None:
    conn = db.get_db()

    ja_existe = conn.execute("SELECT 1 FROM recados WHERE titulo = ?", (TITULO,)).fetchone()
    if ja_existe:
        conn.close()
        print("[INFO] Recado ja existia e foi pulado.")
        return

    conn.execute("INSERT INTO recados (titulo, corpo) VALUES (?, ?)", (TITULO, CORPO))
    conn.commit()
    conn.close()

    print("[OK] 1 recado publicado.")


if __name__ == "__main__":
    main()

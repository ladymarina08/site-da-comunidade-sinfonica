"""
Script de importação única: cadastra a agenda de shows enviada pela Admin.

É seguro rodar mais de uma vez — shows com a mesma combinação de
banda + local + data já existente no banco são pulados (não duplica).

Uso:
    python seed_agenda.py
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "comunidade.db"

# (banda, local, cidade, data AAAA-MM-DD, horario "HH:MM" ou "", observacoes)
SHOWS = [
    ("Oceanborn", "Feira Medieval Hon Helden", "Imbé/RS", "2026-08-30", "", "Tributo a Nightwish"),

    ("Darkwish", "Bar'tô", "Osasco/SP", "2026-09-12", "", ""),

    (
        "Encontro da Comunidade",
        "Condomínio — R. Antônio Valência, 681 (próx. Metrô Artur Alvim)",
        "Artur Alvim/SP",
        "2026-09-19",
        "22:00",
        "Churras dos Amigos Trevosos. Leve carne para o churrasco — bebidas podem ser "
        "compradas no bar do local.",
    ),

    ("Anette Olzon", "Teatro Ney Soares", "Belo Horizonte/MG", "2026-09-24", "", "Com orquestra"),
    ("Anette Olzon", "Teatro APCD", "Santana/SP", "2026-09-26", "", "Com orquestra"),
    ("Anette Olzon", "Teatro Clara Nunes", "Rio de Janeiro/RJ", "2026-09-29", "", "Com orquestra"),

    ("Santo Graal", "St Patrick Tatuapé", "Tatuapé/SP", "2026-10-11", "", "Autoral"),
    ("Lumynox", "St Patrick Tatuapé", "Tatuapé/SP", "2026-10-11", "", "Tributo a Nightwish"),

    ("After Forever", "Tokio Marine Hall", "São Paulo/SP", "2026-10-16", "", ""),

    ("Roy Khan", "Carioca Club", "Pinheiros/SP", "2026-10-17", "", ""),
    ("Roy Khan", "Armazém 14", "Recife/PE", "2026-10-18", "", ""),
    ("Roy Khan", "Mirage Eventos", "Limeira/SP", "2026-10-23", "", ""),
    ("Roy Khan", "Tork 'N Roll", "Curitiba/PR", "2026-10-24", "", ""),
    ("Roy Khan", "Opinião", "Porto Alegre/RS", "2026-10-25", "", ""),

    ("Arena 89 Halloween Fest", "Arena Galeria", "República/SP", "2026-10-31", "", "Line-up surpresa"),

    ("Darkwish", "A confirmar", "Brasília/DF", "2026-11-20", "", "Nightwish Party"),
    ("Darkwish", "De Leon Music Pub", "Goiânia/GO", "2026-11-21", "", "Nightwish Party"),

    ("Tarja Turunen", "Terra SP", "Campo Grande/SP", "2026-12-05", "", "Spirit Christmas"),

    ("Darkwish", "Darkness Festival", "Agudos/SP", "2026-12-12", "", "Tarja Turunen Exp"),
    ("Principle Of Evil", "Darkness Festival", "Agudos/SP", "2026-12-12", "", "Tributo a Children Of Bodom"),
    ("Devil's Deal", "Darkness Festival", "Agudos/SP", "2026-12-12", "", ""),
    ("Midgard", "Darkness Festival", "Agudos/SP", "2026-12-12", "", ""),

    ("Liberation Festival", "A confirmar", "São Paulo/SP", "2026-12-12", "", ""),
    ("Liberation Festival", "A confirmar", "São Paulo/SP", "2026-12-13", "", ""),
]


def main() -> None:
    if not DB_PATH.exists():
        print(
            "Banco de dados não encontrado em backend/comunidade.db.\n"
            "Rode 'python app.py' pelo menos uma vez antes de usar este script."
        )
        return

    conn = sqlite3.connect(DB_PATH)
    inseridos = 0
    pulados = 0

    for banda, local, cidade, data, horario, observacoes in SHOWS:
        ja_existe = conn.execute(
            "SELECT 1 FROM shows WHERE banda = ? AND local = ? AND data = ?",
            (banda, local, data),
        ).fetchone()
        if ja_existe:
            pulados += 1
            continue

        conn.execute(
            "INSERT INTO shows (banda, local, cidade, data, horario, observacoes) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (banda, local, cidade, data, horario, observacoes),
        )
        inseridos += 1

    conn.commit()
    conn.close()

    print(f"[OK] {inseridos} show(s) cadastrado(s).")
    if pulados:
        print(f"[INFO] {pulados} show(s) já existiam e foram pulados.")


if __name__ == "__main__":
    main()

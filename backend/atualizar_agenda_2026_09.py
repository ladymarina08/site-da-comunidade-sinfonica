"""
Script de atualizacao pontual da agenda — mudancas enviadas pela Admin em
22/09/2026 (2 shows removidos, 19 shows novos entre set/2026 e jan/2027).

Seguro rodar mais de uma vez: remocoes so acontecem se o show ainda
existir, e adicoes pulam shows que ja existem (mesma checagem usada em
seed_agenda.py).

Uso:
    python atualizar_agenda_2026_09.py
"""

import db

REMOVER = [
    # (banda, local, data) — show cancelado
    ("After Forever", "Tokio Marine Hall", "2026-10-16"),
    # (banda, local, data) — substituida pela Loreley (Sirenia) no mesmo show
    ("Lumynox", "St Patrick Tatuapé", "2026-10-11"),
]

ADICIONAR = [
    # (banda, local, cidade, data, horario, observacoes)
    ("Lumynox", "Devil's Pub", "Sorocaba/SP", "2026-09-25", "21:00", "Tributo a Nightwish"),
    (
        "Pride", "Casarão do Benfica", "Fortaleza/CE", "2026-09-26", "",
        "Encontro dos Tributos — tributo a Andre Matos (Angra e Shaman). Ingressos pelo Instagram @pridetributee",
    ),
    (
        "Ghostlight", "Casarão do Benfica", "Fortaleza/CE", "2026-09-26", "",
        "Encontro dos Tributos — tributo a Avantasia. Ingressos pelo Instagram @pridetributee",
    ),
    (
        "Metalwar", "Casarão do Benfica", "Fortaleza/CE", "2026-09-26", "",
        "Encontro dos Tributos — tributo a Manowar. Ingressos pelo Instagram @pridetributee",
    ),
    (
        "Dio's Legacy", "Casarão do Benfica", "Fortaleza/CE", "2026-09-26", "",
        "Encontro dos Tributos — tributo a Dio. Ingressos pelo Instagram @pridetributee",
    ),
    (
        "Cinetose", "Casarão do Benfica", "Fortaleza/CE", "2026-09-26", "",
        "Encontro dos Tributos — Trash Metal. Ingressos pelo Instagram @pridetributee",
    ),
    ("Sitra Ahra", "Cineteatro São Luiz", "Fortaleza/CE", "2026-09-30", "", "V Sinistro Fest — com orquestra"),
    ("Far From Heaven", "Espetinho Perus", "Perus/SP", "2026-10-02", "", "Evanescence Tributo"),
    ("Loreley", "St Patrick Tatuapé", "Tatuapé/SP", "2026-10-11", "", "Sirenia"),
    ("The Gathering", "Áudio", "São Paulo/SP", "2026-10-15", "", ""),
    ("Far From Heaven", "St. Patrick Pub", "Tatuapé/SP", "2026-10-30", "", "Evanescence Tributo"),
    (
        "Far From Heaven", "Downtown Metal Fest — Old Town English Pub", "Santo André/SP", "2026-10-31", "",
        "Evanescence Tributo — Downtown Metal Fest (tarde)",
    ),
    ("Maldigo.", "Havana Iracema", "Fortaleza/CE", "2026-11-21", "", "Creep Show"),
    ("The Watchman", "Woodstock Discos", "São Paulo/SP", "2026-11-21", "", "Autoral"),
    ("Lybrian", "Woodstock Discos", "São Paulo/SP", "2026-11-21", "", "Autoral"),
    ("Darkwish", "Madame", "Bela Vista/SP", "2026-11-29", "", "Show Especial"),
    ("Lumynox", "Devil's Pub", "Sorocaba/SP", "2026-12-20", "", "Tributo a Nightwish"),
    ("SymphoniCore", "JAI Club", "São Paulo/SP", "2026-12-20", "", "Estreia"),
    ("Lumynox", "Cervejista Pub Rock Bar", "Indaiatuba/SP", "2027-01-09", "", "Tributo a Nightwish"),
]


def main() -> None:
    conn = db.get_db()

    removidos = 0
    for banda, local, data in REMOVER:
        linha = conn.execute(
            "SELECT id FROM shows WHERE banda = ? AND local = ? AND data = ?", (banda, local, data)
        ).fetchone()
        if not linha:
            continue
        conn.execute("DELETE FROM lembretes WHERE show_id = ?", (linha["id"],))
        conn.execute("DELETE FROM shows WHERE id = ?", (linha["id"],))
        removidos += 1

    inseridos = 0
    pulados = 0
    for banda, local, cidade, data, horario, observacoes in ADICIONAR:
        ja_existe = conn.execute(
            "SELECT 1 FROM shows WHERE banda = ? AND local = ? AND data = ?", (banda, local, data)
        ).fetchone()
        if ja_existe:
            pulados += 1
            continue
        conn.execute(
            "INSERT INTO shows (banda, local, cidade, data, horario, observacoes) VALUES (?, ?, ?, ?, ?, ?)",
            (banda, local, cidade, data, horario, observacoes),
        )
        inseridos += 1

    conn.commit()
    conn.close()

    print(f"[OK] {removidos} show(s) removido(s), {inseridos} show(s) adicionado(s).")
    if pulados:
        print(f"[INFO] {pulados} show(s) ja existiam e foram pulados.")


if __name__ == "__main__":
    main()

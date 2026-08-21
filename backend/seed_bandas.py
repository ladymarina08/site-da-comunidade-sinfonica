"""
Script de importação única: cadastra a lista de bandas da comunidade no banco.

Uso:
    python seed_bandas.py

É seguro rodar mais de uma vez — bandas cujo nome já existe no banco são
puladas (não duplica).
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "comunidade.db"

EMOJI_PADRAO = "🦇"

# (nome com estado/país, gênero/estilo, @instagram ou None)
BANDAS = [
    ("Darkwish (SP)", "Tarja Turunen Experience", "@darkwishbrasil"),
    ("Evoke (SP)", "Floor Jansen Celebration", "@afterforevercoverbr"),
    ("Denying Silence (SP)", "Within Temptation Cover", "@wttributebr"),
    ("Eclíptica (SP)", "Epica Tributo", "@ecliptica.epicatribute"),
    ("SymphoniCore (SP)", "Autoral | Modern Symphonic Metal", "@symphoni.core"),
    ("Loreley (SP)", "Sirenia Cover", "@sireniacover"),
    ("RavenCode (SP)", "Lacuna Coil Cover", "@ravencodelacunatribute"),
    ("Masters Of Destiny (SP)", "Delain Cover", "@delaincover"),
    ("Lovelorn (SP)", "Liv Kristine Tributo", None),
    ("Aellius (RJ)", "Evanescence Cover", "@aelliusmusic"),
    ("Anderuvius (SP)", "Autoral", "@anderuvius"),
    ("Arcanis (RJ)", "Symphonic Metal Cover", "@wearearcanis"),
    ("Bloody Kisses (SP)", "Type O Negative Tributo", "@bloodykissessp"),
    ("Crosses Of Bodom (SP)", "Children Of Bodom Cover", "@crossesofbodom"),
    ("Darkdream (SP)", "Autoral", "@bandadarkdream"),
    ("DeathScars (SP)", "Death Stars Cover", "@deathscarsdeathstarscover_br"),
    ("De Profvndis Clamati (PR)", "Autoral | Funeral Doom Metal", "@deprofvndisclamati"),
    ("Echoes Divine (SP)", "Epica Cover", "@echoesdivine"),
    ("Echoes of Ailyria (SP)", "Autoral", "@echoesofailyria.official"),
    ("Elyra (SC)", "Autoral", "@elyraoficial"),
    ("Eternal (PR)", "Evanescence Tribute", "@eternalcwb"),
    ("Everlast Dream (SP)", "Autoral", "@everlastdreamofficial"),
    ("Evernight (CE)", "Nightwish Cover", "@evernightofficial"),
    ("Evanescence Tribute (SC)", "Evanescence Tributo", "@evanescencetributebrazil"),
    ("Far From Heaven (SP)", "Evanescence Tributo", "@evtributo"),
    ("Ghostlight (CE)", "Avantasia Tributo", "@ghostlight_official"),
    ("Harvest (MG)", "Nightwish Cover", "@harvest.nightwish.cover"),
    ("Horizon Zero (SP)", "Autoral | Modern Metal", "@horizon.zero.oficial"),
    ("Imaginary (BA)", "Metal Sinfônico Cover", "@imaginary.tx"),
    ("Into Oblivion (SP)", "Metal Core/Nu Metal", "@into.oblivionband"),
    ("Jeff Belarmino (DF)", "Autoral | Symphonic Metal", "@jeffbelarmino"),
    ("Karmacode (SP)", "Lacuna Coil Tributo", "@karmacodelctribute"),
    ("Leviathan (SP)", "Therion Cover", "@therioncover"),
    ("Libre (DF)", "Covers Metal Sinfônico", "@libre.metal"),
    ("Lightstrike (SP)", "Autoral | Power Symphonic Metal", "@lightstrike.official"),
    ("Lithium (SP)", "Evanescence Tributo", "@lithium_evanescence.tributo"),
    ("Lumynox (SP)", "Nightwish Tributo", "@lumynoxoficial"),
    ("L'odissea (RS)", "Autoral | Metal Sinfônico", "@l.odissea"),
    ("Magnolia (SC)", "Autoral | Modern Symphonic Metal", "@magnoliabandbrazil"),
    ("Mystical (SP)", "Autoral | Symphonic Metal", "@mysticalband"),
    ("Oceanborn (RS)", "Nightwish Era Tarja Cover", "@oceanborn.official"),
    ("Ode Insone (PB)", "Autoral | Doom Gothic Metal", "@odeinsone"),
    ("Origin (SP)", "Evanescence Cover", "@evanescencecoversp"),
    ("Retrospecto (SP)", "Epica Cover", "@retrospectoepicatribute"),
    ("Santo Graal (SP)", "Autoral | Symphonic Metal", "@santograalband"),
    ("Seyren (PR)", "Nightwish Cover", "@nightwishcoverbr"),
    ("Silent Force (PR)", "Within Temptation Tributo", "@silentforcemetal"),
    ("Sitra Ahra (CE)", "Therion Tributo", "@sitra.ahra"),
    ("Sphynx (PR)", "Hard Rock", "@sphynx.br"),
    ("The Dark Eyes (SP)", "The 69 Eyes Tributo", "@the69eyestribute"),
    ("The Silence Force (Chile)", "Within Temptation Tributo", "@thesilenceforce.wt"),
    ("The Watchman (SP)", "Autoral", "@thewatchmanband"),
    ("Umbra (SP)", "Nightwish Cover", "@banda_umbra"),
    ("Vasco (?)", "Autoral | Symphonic Metal", "@vinissin_souza"),
    ("Vindicta (SP)", "Tristania Cover", "@vindicta.tristania"),
    ("Winterhearts (CE)", "Sonata Arctica Cover", "@winterhearts_"),
    ("Wishmoon (RS)", "Nightwish & Evanescence Tributo", "@wishmoonband"),
    ("Worship (SP)", "Sleep Token Cover", "@worship_stc"),
    ("Aegis (SP)", "Theatre Of Tragedy Tributo", "@aegistottributo"),
]


def main() -> None:
    if not DB_PATH.exists():
        print(
            "Banco de dados não encontrado em backend/comunidade.db.\n"
            "Rode 'python app.py' pelo menos uma vez antes de usar este script."
        )
        return

    conn = sqlite3.connect(DB_PATH)
    inseridas = 0
    puladas = 0

    for nome, genero, instagram in BANDAS:
        ja_existe = conn.execute(
            "SELECT 1 FROM bandas WHERE nome = ?", (nome,)
        ).fetchone()
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

    print(f"[OK] {inseridas} banda(s) cadastrada(s).")
    if puladas:
        print(f"[INFO] {puladas} banda(s) já existiam e foram puladas.")


if __name__ == "__main__":
    main()

"""
Chatbot de regras da tela de Início — responde perguntas comuns sobre a
Comunidade Sinfônica (shows, bandas, redes sociais etc.) consultando os
dados reais do banco. Não usa IA nem serviço externo: é só reconhecimento
de palavras-chave, então só entende perguntas parecidas com o que está
programado aqui.
"""

import sqlite3
from datetime import date


def _data_br(data_iso: str) -> str:
    return "/".join(reversed(data_iso.split("-")))


def _contem_alguma(texto: str, *termos: str) -> bool:
    return any(termo in texto for termo in termos)


def _responder_sobre_banda(texto: str, conn: sqlite3.Connection) -> str | None:
    # Compara com os nomes usados nos shows (não na tabela de bandas), porque é
    # esse o nome usado depois na consulta abaixo — a tabela de bandas guarda o
    # nome com a cidade junto (ex: "Darkwish (SP)"), o que nunca bateria com o
    # que a pessoa digita.
    bandas = conn.execute("SELECT DISTINCT banda FROM shows").fetchall()
    banda_citada = next((linha["banda"] for linha in bandas if linha["banda"].lower() in texto), None)
    if not banda_citada:
        return None

    hoje = date.today().isoformat()
    shows = conn.execute(
        "SELECT local, cidade, data, horario FROM shows WHERE banda = ? AND data >= ? ORDER BY data, horario",
        (banda_citada, hoje),
    ).fetchall()

    if not shows:
        return f'Não encontrei nenhum show futuro cadastrado da {banda_citada}. Fica de olho na Agenda!'

    partes = []
    for show in shows[:3]:
        horario_texto = f' às {show["horario"]}' if show["horario"] else ""
        partes.append(f'{_data_br(show["data"])}{horario_texto} em {show["local"]}, {show["cidade"]}')

    return f'Show(s) da {banda_citada}: ' + "; ".join(partes) + "."


def _responder_proximo_show(conn: sqlite3.Connection) -> str:
    hoje = date.today().isoformat()
    show = conn.execute(
        "SELECT banda, local, cidade, data, horario FROM shows WHERE data >= ? ORDER BY data, horario LIMIT 1",
        (hoje,),
    ).fetchone()

    if not show:
        return "Não tem nenhum show cadastrado na agenda no momento. Volte mais tarde!"

    horario_texto = f' às {show["horario"]}' if show["horario"] else ""
    return (
        f'O próximo show é da {show["banda"]}, em {_data_br(show["data"])}{horario_texto}, '
        f'em {show["local"]}, {show["cidade"]}. Veja mais na Agenda!'
    )


def _responder_lista_bandas(conn: sqlite3.Connection) -> str:
    bandas = conn.execute("SELECT nome FROM bandas ORDER BY nome").fetchall()
    total = len(bandas)
    if total == 0:
        return "Ainda não tem nenhuma banda cadastrada."
    nomes = ", ".join(linha["nome"] for linha in bandas[:8])
    extra = "..." if total > 8 else ""
    return f"A comunidade reúne {total} banda(s) cadastrada(s), incluindo: {nomes}{extra}. Veja a lista completa na página Bandas!"


def responder(pergunta: str, conn: sqlite3.Connection) -> str:
    texto = (pergunta or "").strip().lower()

    if not texto:
        return 'Pode perguntar! Por exemplo: "quando é o próximo show?" ou "quais são as redes sociais?"'

    resposta_banda = _responder_sobre_banda(texto, conn)
    if resposta_banda:
        return resposta_banda

    if _contem_alguma(texto, "proximo show", "próximo show", "quando e o show", "quando é o show", "tem show", "agenda"):
        return _responder_proximo_show(conn)

    if _contem_alguma(texto, "quantas bandas", "quais bandas", "lista de bandas", "bandas da comunidade"):
        return _responder_lista_bandas(conn)

    if _contem_alguma(texto, "instagram", "whatsapp", "rede social", "redes sociais", "contato"):
        return (
            "Nosso Instagram é @comunidadesinfonica e temos um grupo no WhatsApp — os links estão "
            "na página Sobre!"
        )

    if _contem_alguma(texto, "o que e a comunidade", "o que é a comunidade", "sobre a comunidade", "quem fundou", "fundadora", "quem criou"):
        return (
            "A Comunidade Sinfônica nasceu da união entre bandas da cena de metal sinfônico, fundada "
            "por Joy Heit (das bandas Darkwish e SymphoniCore), com o propósito de fortalecer e fazer "
            "crescer a cena. Veja mais na página Sobre!"
        )

    if _contem_alguma(texto, "senha", "esqueci"):
        return 'Pra redefinir sua senha, clique em "Esqueceu a senha?" na tela de login — você recebe um link por e-mail.'

    if _contem_alguma(texto, "playlist", "musica", "música", "spotify"):
        return "Temos playlists da comunidade no Spotify! Dá uma olhada na página Playlists."

    if _contem_alguma(texto, "lembrete", "lembrar"):
        return (
            'Em cada show da Agenda tem um botão "Lembrar-me" — ative e você recebe um e-mail um dia '
            "antes e no dia do show."
        )

    if _contem_alguma(texto, "admin", "administrador"):
        return "Só administradores da comunidade podem gerenciar shows e bandas. Se precisar de algo, fale com a organização pelo Instagram ou WhatsApp."

    return (
        "Não entendi bem sua pergunta. Você pode perguntar sobre: próximos shows, uma banda específica, "
        "playlists, redes sociais, lembretes de show ou sobre a comunidade."
    )

"""
Chatbot de regras da tela de Início — responde perguntas comuns sobre a
Comunidade Sinfônica (shows, bandas, redes sociais etc.) consultando os
dados reais do banco. Não usa IA nem serviço externo: é só reconhecimento
de palavras-chave, então só entende perguntas parecidas com o que está
programado aqui.
"""

import re
import sqlite3
import unicodedata
from datetime import date

MESES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]


def _sem_acento(texto: str) -> str:
    forma_normalizada = unicodedata.normalize("NFKD", texto)
    return "".join(caractere for caractere in forma_normalizada if not unicodedata.combining(caractere))


def _data_br(data_iso: str) -> str:
    return "/".join(reversed(data_iso.split("-")))


def _contem_alguma(texto: str, *termos: str) -> bool:
    return any(termo in texto for termo in termos)


def _contem_palavra(texto: str, nome: str) -> bool:
    # Casa a palavra/frase inteira (não um pedaço de outra palavra), ignorando
    # acento — assim "proximo" ou "sao paulo" (sem acento) também funcionam.
    nome_normalizado = _sem_acento(nome.lower())
    return re.search(rf"\b{re.escape(nome_normalizado)}\b", texto) is not None


def _nome_sem_sufixo(nome_na_tabela_bandas: str) -> str:
    # A tabela de bandas guarda o nome com a cidade junto (ex: "Darkwish (SP)");
    # isso tira o "(SP)" pra comparar e exibir só o nome da banda.
    return re.sub(r"\s*\([A-Z]{2}\)\s*$", "", nome_na_tabela_bandas).strip()


def _shows_futuros_da_banda(banda: str, conn: sqlite3.Connection) -> str | None:
    hoje = date.today().isoformat()
    shows = conn.execute(
        "SELECT local, cidade, data, horario FROM shows WHERE banda = ? AND data >= ? ORDER BY data, horario",
        (banda, hoje),
    ).fetchall()
    if not shows:
        return None

    partes = []
    for show in shows[:3]:
        horario_texto = f' às {show["horario"]}' if show["horario"] else ""
        partes.append(f'• {_data_br(show["data"])}{horario_texto} em {show["local"]}, {show["cidade"]}')
    return f'Show(s) da {banda}:\n' + "\n".join(partes)


def _achar_banda_citada(texto: str, conn: sqlite3.Connection):
    """Devolve (nome_da_banda, linha_da_tabela_bandas_ou_None) se alguma banda
    conhecida (da agenda ou da lista da comunidade) for citada na pergunta."""
    nomes_em_shows = [linha["banda"] for linha in conn.execute("SELECT DISTINCT banda FROM shows").fetchall()]
    banda_citada = next((nome for nome in nomes_em_shows if _contem_palavra(texto, nome)), None)
    if banda_citada:
        linha_bandas = conn.execute(
            "SELECT nome, genero, descricao, instagram FROM bandas WHERE nome LIKE ?", (f"{banda_citada}%",)
        ).fetchone()
        return banda_citada, linha_bandas

    bandas_comunidade = conn.execute("SELECT nome, genero, descricao, instagram FROM bandas").fetchall()
    linha_bandas = next(
        (linha for linha in bandas_comunidade if _contem_palavra(texto, _nome_sem_sufixo(linha["nome"]))), None
    )
    if linha_bandas:
        return _nome_sem_sufixo(linha_bandas["nome"]), linha_bandas

    return None, None


def _responder_instagram_da_banda(texto: str, conn: sqlite3.Connection) -> str | None:
    if not _contem_alguma(texto, "@", "arroba", "instagram"):
        return None

    nome_banda, linha_bandas = _achar_banda_citada(texto, conn)
    if not nome_banda:
        return None

    if not linha_bandas or not linha_bandas["instagram"]:
        return f"Não tenho o Instagram cadastrado da {nome_banda}."
    return f'O Instagram da {nome_banda} é {linha_bandas["instagram"]}.'


def _responder_sobre_banda(texto: str, conn: sqlite3.Connection) -> str | None:
    nome_banda, linha_bandas = _achar_banda_citada(texto, conn)
    if not nome_banda:
        return None

    resposta_shows = _shows_futuros_da_banda(nome_banda, conn)
    if resposta_shows:
        return resposta_shows

    if not linha_bandas:
        return f'Não encontrei nenhum show futuro cadastrado da {nome_banda}. Fica de olho na Agenda!'

    partes = [f'{nome_banda} é uma banda de {linha_bandas["genero"]} da comunidade.']
    if linha_bandas["descricao"]:
        partes.append(linha_bandas["descricao"])
    if linha_bandas["instagram"]:
        partes.append(f'Instagram: {linha_bandas["instagram"]}.')
    partes.append("Não encontrei nenhum show futuro cadastrado dela — fica de olho na Agenda!")
    return " ".join(partes)


def _responder_shows_por_cidade(texto: str, conn: sqlite3.Connection) -> str | None:
    hoje = date.today().isoformat()
    cidades = conn.execute("SELECT DISTINCT cidade FROM shows").fetchall()
    nomes_de_cidade = sorted({linha["cidade"].split("/")[0].strip() for linha in cidades}, key=len, reverse=True)

    cidade_citada = next((nome for nome in nomes_de_cidade if _contem_palavra(texto, nome)), None)
    if not cidade_citada:
        return None

    shows = conn.execute(
        "SELECT banda, data, horario, local FROM shows WHERE cidade LIKE ? AND data >= ? ORDER BY data, horario",
        (f"{cidade_citada}/%", hoje),
    ).fetchall()
    if not shows:
        return f"Não encontrei nenhum show futuro cadastrado em {cidade_citada}."

    partes = []
    for show in shows[:5]:
        horario_texto = f' às {show["horario"]}' if show["horario"] else ""
        partes.append(f'• {show["banda"]} em {_data_br(show["data"])}{horario_texto} ({show["local"]})')
    return f"Show(s) em {cidade_citada}:\n" + "\n".join(partes)


def _responder_shows_do_mes(texto: str, conn: sqlite3.Connection) -> str | None:
    hoje = date.today().isoformat()
    for indice, nome_mes in enumerate(MESES, start=1):
        if not _contem_palavra(texto, nome_mes):
            continue

        shows = conn.execute(
            "SELECT banda, cidade, data, horario FROM shows WHERE strftime('%m', data) = ? AND data >= ? "
            "ORDER BY data, horario",
            (f"{indice:02d}", hoje),
        ).fetchall()
        if not shows:
            return f"Não encontrei nenhum show cadastrado em {nome_mes}."

        partes = []
        for show in shows[:6]:
            horario_texto = f' às {show["horario"]}' if show["horario"] else ""
            partes.append(f'• {show["banda"]} ({_data_br(show["data"])}{horario_texto}, {show["cidade"]})')
        return f"Shows em {nome_mes}:\n" + "\n".join(partes)

    return None


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
    texto = _sem_acento((pergunta or "").strip().lower())

    if not texto:
        return 'Pode perguntar! Por exemplo: "quando é o próximo show?" ou "quais são as redes sociais?"'

    resposta_instagram_banda = _responder_instagram_da_banda(texto, conn)
    if resposta_instagram_banda:
        return resposta_instagram_banda

    resposta_banda = _responder_sobre_banda(texto, conn)
    if resposta_banda:
        return resposta_banda

    resposta_cidade = _responder_shows_por_cidade(texto, conn)
    if resposta_cidade:
        return resposta_cidade

    resposta_mes = _responder_shows_do_mes(texto, conn)
    if resposta_mes:
        return resposta_mes

    if _contem_alguma(texto, "quantas bandas", "quais bandas", "lista de bandas", "bandas da comunidade"):
        return _responder_lista_bandas(conn)

    if _contem_alguma(texto, "proximo show", "quando e o show", "tem show", "agenda", "show", "shows"):
        return _responder_proximo_show(conn)

    if _contem_alguma(texto, "instagram", "whatsapp", "rede social", "redes sociais", "contato"):
        return (
            "Nosso Instagram é @comunidadesinfonica e temos um grupo no WhatsApp — os links estão "
            "na página Sobre!"
        )

    if _contem_alguma(texto, "o que e a comunidade", "sobre a comunidade", "quem fundou", "fundadora", "quem criou"):
        return (
            "A Comunidade Sinfônica nasceu da união entre bandas da cena de metal sinfônico, fundada "
            "por Joy Heit (das bandas Darkwish e SymphoniCore), com o propósito de fortalecer e fazer "
            "crescer a cena. Veja mais na página Sobre!"
        )

    if _contem_alguma(texto, "senha", "esqueci"):
        return 'Pra redefinir sua senha, clique em "Esqueceu a senha?" na tela de login — você recebe um link por e-mail.'

    if _contem_alguma(texto, "playlist", "musica", "spotify"):
        return "Temos playlists da comunidade no Spotify! Dá uma olhada na página Playlists."

    if _contem_alguma(texto, "lembrete", "lembrar"):
        return (
            'Em cada show da Agenda tem um botão "Lembrar-me" — ative e você recebe um e-mail um dia '
            "antes e no dia do show."
        )

    if _contem_alguma(texto, "admin", "administrador"):
        return "Só administradores da comunidade podem gerenciar shows e bandas. Se precisar de algo, fale com a organização pelo Instagram ou WhatsApp."

    return (
        "Não entendi bem sua pergunta. Você pode perguntar sobre: próximos shows (por data, cidade ou mês), "
        "uma banda específica, playlists, redes sociais, lembretes de show ou sobre a comunidade."
    )

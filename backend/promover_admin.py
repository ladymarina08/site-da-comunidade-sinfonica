"""
Promove (ou remove) um usuário já cadastrado como administrador da
Comunidade Sinfônica. Quem for admin ganha acesso ao painel /admin.html
para cadastrar shows e bandas.

A pessoa precisa ter feito o cadastro pelo site (cadastro.html) ANTES de
rodar este script — ele só promove contas que já existem.

Uso:
    python promover_admin.py email@exemplo.com
    python promover_admin.py email@exemplo.com --remover
    python promover_admin.py --listar
"""

import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "comunidade.db"


def conectar() -> sqlite3.Connection:
    if not DB_PATH.exists():
        print(
            "Banco de dados não encontrado em backend/comunidade.db.\n"
            "Rode 'python app.py' pelo menos uma vez (e crie uma conta pelo site) antes de usar este script."
        )
        sys.exit(1)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def listar_usuarios() -> None:
    conn = conectar()
    usuarios = conn.execute("SELECT nome, email, admin FROM usuarios ORDER BY nome").fetchall()
    conn.close()

    if not usuarios:
        print("Nenhum usuário cadastrado ainda.")
        return

    print(f"{'ADMIN':<7} NOME / E-MAIL")
    print("-" * 50)
    for usuario in usuarios:
        marcador = "[ADMIN]" if usuario["admin"] else "       "
        print(f"{marcador} {usuario['nome']} <{usuario['email']}>")


def promover(email: str, remover: bool) -> None:
    conn = conectar()
    usuario = conn.execute("SELECT id, nome FROM usuarios WHERE email = ?", (email,)).fetchone()

    if not usuario:
        print(f"Nenhum usuário encontrado com o e-mail '{email}'.")
        print("A pessoa precisa se cadastrar pelo site (cadastro.html) primeiro.")
        conn.close()
        sys.exit(1)

    novo_valor = 0 if remover else 1
    conn.execute("UPDATE usuarios SET admin = ? WHERE email = ?", (novo_valor, email))
    conn.commit()
    conn.close()

    acao = "removido(a) de administrador(a)" if remover else "promovido(a) a administrador(a)"
    print(f"[OK] {usuario['nome']} <{email}> foi {acao}.")


def main() -> None:
    argumentos = sys.argv[1:]

    if not argumentos or argumentos[0] in ("-h", "--help"):
        print(__doc__)
        return

    if argumentos[0] == "--listar":
        listar_usuarios()
        return

    email = argumentos[0].strip().lower()
    remover = "--remover" in argumentos[1:]
    promover(email, remover)


if __name__ == "__main__":
    main()

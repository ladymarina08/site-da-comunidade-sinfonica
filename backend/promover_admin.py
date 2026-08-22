"""
Promove (ou remove) um usuário já cadastrado como administrador da
Comunidade Sinfônica. Quem for admin ganha acesso ao painel /admin.html
para cadastrar shows e bandas.

A pessoa precisa ter feito o cadastro pelo site (cadastro.html) ANTES de
rodar este script — ele só promove contas que já existem.

Por padrão mexe no banco local (backend/comunidade.db). Pra mexer no banco
do site publicado (Turso), defina TURSO_DATABASE_URL e TURSO_AUTH_TOKEN no
terminal antes de rodar (os mesmos valores que estão no Render, em
Environment) — veja o README para o passo a passo.

Uso:
    python promover_admin.py email@exemplo.com
    python promover_admin.py email@exemplo.com --remover
    python promover_admin.py --listar
"""

import sys

import db


def conectar() -> db.Conexao:
    if not db.USANDO_TURSO and not db.DB_PATH.exists():
        print(
            "Banco de dados local não encontrado em backend/comunidade.db.\n"
            "Rode 'python app.py' pelo menos uma vez (e crie uma conta pelo site) antes de usar este script.\n"
            "Ou, pra mexer no banco do site publicado, defina TURSO_DATABASE_URL e TURSO_AUTH_TOKEN antes de rodar."
        )
        sys.exit(1)
    return db.get_db()


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

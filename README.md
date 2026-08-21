# Comunidade Sinfônica

Site (HTML + CSS + JS puro no front, backend em Python/Flask) para a Comunidade Sinfônica.

## Páginas

- `index.html` — Login (tela inicial)
- `cadastro.html` — Criar conta
- `agenda.html` — Agenda de shows (**exige login**, dados vêm do backend)
- `bandas.html` — Bandas da comunidade (**exige login**, dados vêm do backend)
- `sobre.html` — Sobre a comunidade + redes sociais (**exige login**)
- `admin.html` — Painel para cadastrar/excluir shows e bandas (**exige ser admin**)

## Como rodar

O site agora precisa do backend rodando (ele serve as páginas **e** cuida do login):

```bash
cd backend
pip install -r requirements.txt
python app.py
```

Depois acesse **http://localhost:5000** no navegador. Não abra mais os `.html` direto
(duplo clique) — sem o servidor, o login/cadastro não funciona.

Se estiver usando o Claude Code, também dá pra abrir pelo preview com o nome
`comunidade-sinfonica` (já configurado em `.claude/launch.json`).

## Como editar

- **Texto/conteúdo**: direto em cada `.html`
- **Cores e estilo**: `css/style.css` (variáveis `--black`, `--red`, `--gold`, `--white` no topo do arquivo)
- **Comportamento (menu mobile, login, cadastro, logout)**: `js/script.js`
- **Backend/autenticação**: `backend/app.py`

## Como funciona o login

- As senhas nunca são guardadas em texto puro — usamos hash (`werkzeug.security`).
- Os usuários ficam salvos em `backend/comunidade.db` (SQLite, criado automaticamente
  na primeira execução — **não é versionado no git**, veja `backend/.gitignore`).
- A sessão é guardada num cookie assinado com uma chave local gerada automaticamente em
  `backend/secret.key` (também não versionada).
- `agenda.html`, `bandas.html`, `sobre.html` e `admin.html` verificam a sessão ao carregar
  (`js/script.js`) e redirecionam pra `index.html` se não houver login.

## Como promover alguém a administrador(a)

Só quem for admin vê o link "Admin" no menu e consegue cadastrar/excluir shows e bandas
pelo painel (`admin.html`). Por padrão, todo cadastro novo **não** é admin.

1. A pessoa precisa se cadastrar normalmente pelo site primeiro (`cadastro.html`).
2. Depois, no terminal, dentro da pasta `backend`:

   ```bash
   python promover_admin.py email@exemplo.com
   ```

   Isso marca aquela conta como admin — na próxima vez que ela entrar (ou recarregar a
   página), o link "Admin" aparece no menu.

Outros comandos úteis:

```bash
python promover_admin.py --listar                    # lista todo mundo e quem é admin
python promover_admin.py email@exemplo.com --remover  # tira o admin de alguém
```

## Como funciona a agenda e as bandas agora

`agenda.html` e `bandas.html` não têm mais conteúdo fixo no HTML — a lista é buscada do
backend (`GET /api/shows` e `GET /api/bandas`) toda vez que a página carrega. Quem for
admin cadastra/exclui pelo painel em `admin.html`; a mudança aparece pra todo mundo assim
que a página é recarregada.

## Pendências para você completar

1. **Se tornar admin**: cadastre sua própria conta pelo site e rode `promover_admin.py`
   com o seu e-mail (veja acima) — sem isso ninguém consegue usar o painel.
2. **Redes sociais**: em `sobre.html`, troque os `href="#"` dos cards de rede social pelos links reais (Instagram, WhatsApp, YouTube, TikTok, Facebook).
3. **Texto "Sobre"**: ajuste o texto de apresentação da comunidade em `sobre.html` como preferir.
4. **"Esqueceu a senha?"**: o link existe em `index.html` mas ainda não tem funcionalidade (recuperação de senha por e-mail fica pra uma próxima etapa).
5. **Editar show/banda existente**: hoje o painel só cadastra e exclui — pra corrigir algo é excluir e cadastrar de novo. Editar in-line é uma evolução futura simples de adicionar.
6. **Publicar online**: pra colocar no ar de verdade, você vai precisar de um serviço que rode Python (ex: Render, Railway, PythonAnywhere) — GitHub Pages/Netlify/Vercel (modo estático) não rodam o backend Flask.

## Design

- Paleta preto + vermelho, destaques em dourado e branco.
- Fontes: `UnifrakturCook` (título/logo, estilo gótico), `Cinzel Decorative` (títulos de seção) e `Cormorant Garamond` (texto corrido), via Google Fonts.
- Layout responsivo: menu hambúrguer até 700px de largura, navegação horizontal a partir daí; grids de shows/bandas se reorganizam automaticamente em telas menores.

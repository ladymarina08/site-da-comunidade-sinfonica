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

## Banco de dados: Turso

O site guarda os dados (usuários, shows, bandas) num banco [Turso](https://turso.tech) —
um banco de verdade, hospedado à parte do servidor, gratuito. Isso existe porque o Render
(onde o site roda) não guarda arquivos de forma permanente: qualquer coisa salva
diretamente no disco dele (como um arquivo SQLite) se perde toda vez que o serviço reinicia
por inatividade. Guardando os dados no Turso, eles não dependem do Render pra continuar
existindo.

**Como funciona no código**: `backend/db.py` usa o Turso automaticamente quando as
variáveis `TURSO_DATABASE_URL` e `TURSO_AUTH_TOKEN` estão definidas (produção). Sem elas,
usa um arquivo SQLite local (`backend/comunidade.db`) — mais simples pra rodar no seu PC,
sem precisar de conta em lugar nenhum pra só testar localmente.

## Publicar no Render (grátis)

O GitHub Pages **não serve** pra esse projeto — ele só hospeda HTML/CSS/JS estático, e o
site inteiro (login, agenda, painel admin) depende do backend Flask. O Render roda Python
de verdade, de graça, e já está tudo configurado em `render.yaml` na raiz do projeto.

1. Crie uma conta em [render.com](https://render.com) (dá pra entrar direto com o GitHub).
2. No painel do Render, clique em **"New +" → "Blueprint"**.
3. Selecione o repositório `site-da-comunidade-sinfonica`. O Render lê o `render.yaml`
   sozinho e já configura build, start command e uma `SECRET_KEY` segura automaticamente.
4. Clique em **"Apply"** e espere o primeiro deploy terminar (alguns minutos).
5. Crie uma conta grátis em [turso.tech](https://turso.tech), crie um banco de dados, e
   pegue a **URL** e o **Token** dele (normalmente em algo como "Connect" no painel).
6. No painel do Render → **Environment**, adicione as variáveis:
   - `TURSO_DATABASE_URL` = a URL do banco (começa com `libsql://`)
   - `TURSO_AUTH_TOKEN` = o token
   - `ADMIN_EMAIL` = o(s) e-mail(s) de quem vai ser admin, separados por vírgula sem
     espaço se for mais de um (ex: `voce@gmail.com,parceira@gmail.com`)

   Salvar reinicia o serviço sozinho.
7. Acesse a URL que o Render deu (algo como `https://comunidade-sinfonica.onrender.com`) e
   cadastre as contas normalmente pela tela de cadastro do site — quem estiver no
   `ADMIN_EMAIL` já nasce admin na hora.

Com o Turso configurado, os dados **não desaparecem mais** quando o site "dorme" e acorda
de novo (isso só acontecia antes, guardando tudo num arquivo dentro do próprio Render).
Só uma coisa continua igual: o serviço grátis do Render ainda "dorme" depois de um tempo
sem acesso, e o primeiro acesso do dia demora uns 30-60s pra acordar — isso é só o servidor
ligando de novo, os dados em si ficam salvos no Turso o tempo todo.

Pra promover um admin novo depois que o site já estiver no ar: a pessoa se cadastra
primeiro, e você roda (com as mesmas variáveis do Turso definidas no terminal, veja abaixo)
`python promover_admin.py email@exemplo.com` — ou edita o `ADMIN_EMAIL` no Render antes de
ela se cadastrar, do mesmo jeito que da primeira vez.

## Rodando os scripts (promover_admin.py etc.) contra o site publicado

Por padrão, `promover_admin.py` mexe no banco local do seu PC. Pra ele mexer no banco do
site publicado (Turso), defina as mesmas variáveis que estão no Render antes de rodar:

```bash
# Windows (PowerShell)
$env:TURSO_DATABASE_URL="libsql://sua-url.turso.io"
$env:TURSO_AUTH_TOKEN="seu-token"
python promover_admin.py --listar
```

## Pendências para você completar

1. **Redes sociais**: em `sobre.html`, troque os `href="#"` dos cards de rede social pelos links reais (Instagram, WhatsApp, YouTube, TikTok, Facebook).
2. **Texto "Sobre"**: ajuste o texto de apresentação da comunidade em `sobre.html` como preferir.
3. **"Esqueceu a senha?"**: o link existe em `index.html` mas ainda não tem funcionalidade (recuperação de senha por e-mail fica pra uma próxima etapa).
4. **Editar show/banda existente**: hoje o painel só cadastra e exclui — pra corrigir algo é excluir e cadastrar de novo. Editar in-line é uma evolução futura simples de adicionar.

## Design

- Paleta preto + vermelho, destaques em dourado e branco.
- Fontes: `UnifrakturCook` (título/logo, estilo gótico), `Cinzel Decorative` (títulos de seção) e `Cormorant Garamond` (texto corrido), via Google Fonts.
- Layout responsivo: menu hambúrguer até 700px de largura, navegação horizontal a partir daí; grids de shows/bandas se reorganizam automaticamente em telas menores.

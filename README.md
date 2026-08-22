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

## Banco de dados

O site guarda os dados (usuários, shows, bandas) num arquivo SQLite comum — o mesmo jeito
simples desde o início do projeto. Esse arquivo mora em `DATA_DIR/comunidade.db`, onde
`DATA_DIR` é uma variável de ambiente:

- **Local (seu PC)**: sem essa variável definida, cai automaticamente na pasta
  `backend/comunidade.db` — não precisa configurar nada pra rodar localmente.
- **Produção (Render)**: `DATA_DIR` aponta pro **disco persistente** do serviço (configurado
  em `render.yaml`, montado em `/var/data`) — um "HD" de verdade que não se apaga quando o
  servidor reinicia, diferente do disco padrão do Render (que é temporário e reseta a cada
  vez que o serviço "dorme" e acorda no plano grátis).

> Esse projeto chegou a usar o [Turso](https://turso.tech) (banco remoto) numa fase anterior,
> mas conexões remotas viviam travando/expirando em uso esporádico e chegaram a derrubar o
> site inteiro (o Render só roda um processo). Voltamos pro SQLite simples + disco
> persistente do Render — menos peças, mais confiável pro tamanho desse projeto.

## Publicar no Render

O GitHub Pages **não serve** pra esse projeto — ele só hospeda HTML/CSS/JS estático, e o
site inteiro (login, agenda, painel admin) depende do backend Flask. O Render roda Python
de verdade, e já está tudo configurado em `render.yaml` na raiz do projeto (inclusive o
disco persistente).

Exige um plano pago do Render (o disco persistente não está disponível no plano grátis).

1. Crie uma conta em [render.com](https://render.com) (dá pra entrar direto com o GitHub).
2. No painel do Render, clique em **"New +" → "Blueprint"**.
3. Selecione o repositório `site-da-comunidade-sinfonica`. O Render lê o `render.yaml`
   sozinho e já configura build, start command, o disco persistente (`/var/data`) e uma
   `SECRET_KEY` segura automaticamente.
4. Clique em **"Apply"** e espere o primeiro deploy terminar (alguns minutos). Se o Render
   pedir confirmação de plano/pagamento nesse passo, é normal — o disco exige plano pago.
5. **Antes de cadastrar qualquer conta**, vá no painel → **Environment** → adicione a
   variável `ADMIN_EMAIL` com o(s) e-mail(s) de quem vai ser admin, separados por vírgula
   sem espaço se for mais de um (ex: `voce@gmail.com,parceira@gmail.com`). Salvar reinicia
   o serviço sozinho.
6. Acesse a URL que o Render deu (algo como `https://comunidade-sinfonica.onrender.com`) e
   cadastre as contas normalmente pela tela de cadastro do site — quem estiver no
   `ADMIN_EMAIL` já nasce admin na hora.

Com o disco persistente, os dados não se perdem mais entre deploys nem quando o serviço
reinicia. Pra promover um admin novo depois que o site já estiver no ar: a pessoa se
cadastra primeiro, e você roda `python promover_admin.py email@exemplo.com` — mas apontando
pro banco certo, veja a seção abaixo.

## Rodando os scripts (promover_admin.py etc.) contra o site publicado

Por padrão, `promover_admin.py` mexe no banco local do seu PC (`backend/comunidade.db`).
Pra ele mexer no banco do site publicado, é preciso rodar o script **de dentro do próprio
Render** (ele não tem como acessar o disco persistente do Render direto do seu PC) — use o
"Shell" do serviço no painel do Render:

```bash
cd backend
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

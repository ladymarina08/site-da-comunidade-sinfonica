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

## Publicar no Render (grátis)

O GitHub Pages **não serve** pra esse projeto — ele só hospeda HTML/CSS/JS estático, e o
site inteiro (login, agenda, painel admin) depende do backend Flask. O Render roda Python
de verdade, de graça, e já está tudo configurado em `render.yaml` na raiz do projeto.

1. Crie uma conta em [render.com](https://render.com) (dá pra entrar direto com o GitHub).
2. No painel do Render, clique em **"New +" → "Blueprint"**.
3. Selecione o repositório `site-da-comunidade-sinfonica`. O Render lê o `render.yaml`
   sozinho e já configura build, start command e uma `SECRET_KEY` segura automaticamente.
4. Clique em **"Apply"** e espere o primeiro deploy terminar (alguns minutos).
5. **Antes de cadastrar qualquer conta**, vá no painel do Render → **Environment** →
   adicione a variável `ADMIN_EMAIL` com o(s) e-mail(s) de quem vai ser admin (separados
   por vírgula, sem espaço, se for mais de um — ex: `voce@gmail.com,parceira@gmail.com`).
   Salvar reinicia o serviço sozinho.
6. **Só depois** disso, acesse a URL que o Render deu (algo como
   `https://comunidade-sinfonica.onrender.com`) e cadastre as contas normalmente pela tela
   de cadastro do site — cada uma nasce admin na hora, automaticamente.

⚠️ **A ordem importa**: o cadastro precisa vir *depois* de configurar o `ADMIN_EMAIL`, nunca
antes. Isso porque mudar uma variável de ambiente no Render dispara um novo deploy, e o
deploy reseta o banco — uma conta cadastrada antes seria apagada nesse meio-tempo, antes de
virar admin. Cadastrando depois, a conta já nasce admin na mesma hora, sem depender de
nenhum reinício.

Pra adicionar um admin novo mais tarde num site que já está no ar: edite o `ADMIN_EMAIL`
incluindo o e-mail novo, salve (o serviço reinicia sozinho e o banco reseta), e só então a
pessoa cadastra a conta dela.

**Importante sobre o plano grátis do Render — leia antes de usar com gente de verdade:**
- O serviço "dorme" depois de um tempo sem acesso; o primeiro acesso do dia demora uns
  30-60s pra acordar. Normal, não é bug.
- **O disco só reseta quando sai um deploy novo** (ou seja, quando a gente der `git push`
  de uma atualização) — no dia a dia, entre um push e outro, os dados ficam salvos
  normalmente.
- Quando um deploy novo reseta o banco: as 59 bandas e a agenda atual voltam sozinhas
  (o app se auto-popula com os dados de `backend/seed_bandas.py` e `backend/seed_agenda.py`
  se as tabelas estiverem vazias), e sua conta vira admin de novo automaticamente por causa
  da variável `ADMIN_EMAIL`. Mas **contas de outras pessoas e shows/bandas adicionados
  depois pelo painel admin não sobrevivem** a um reset — pra isso não acontecer de verdade
  (uso com a comunidade toda), o próximo passo é trocar o SQLite por um banco de verdade
  (ex: PostgreSQL, que o Render também oferece grátis por um tempo) — é só avisar quando
  quiser fazer essa migração.

## Pendências para você completar

1. **Redes sociais**: em `sobre.html`, troque os `href="#"` dos cards de rede social pelos links reais (Instagram, WhatsApp, YouTube, TikTok, Facebook).
2. **Texto "Sobre"**: ajuste o texto de apresentação da comunidade em `sobre.html` como preferir.
3. **"Esqueceu a senha?"**: o link existe em `index.html` mas ainda não tem funcionalidade (recuperação de senha por e-mail fica pra uma próxima etapa).
4. **Editar show/banda existente**: hoje o painel só cadastra e exclui — pra corrigir algo é excluir e cadastrar de novo. Editar in-line é uma evolução futura simples de adicionar.

## Design

- Paleta preto + vermelho, destaques em dourado e branco.
- Fontes: `UnifrakturCook` (título/logo, estilo gótico), `Cinzel Decorative` (títulos de seção) e `Cormorant Garamond` (texto corrido), via Google Fonts.
- Layout responsivo: menu hambúrguer até 700px de largura, navegação horizontal a partir daí; grids de shows/bandas se reorganizam automaticamente em telas menores.

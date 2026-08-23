// ===================================================
// Comunidade Sinfônica — comportamento compartilhado
// ===================================================

// Menu mobile (hambúrguer) presente no cabeçalho das páginas internas
const menuToggle = document.getElementById('menuToggle');
const mainNav = document.getElementById('mainNav');

if (menuToggle && mainNav) {
  menuToggle.addEventListener('click', () => {
    const isOpen = mainNav.classList.toggle('open');
    menuToggle.classList.toggle('open', isOpen);
    menuToggle.setAttribute('aria-expanded', String(isOpen));
  });

  // Fecha o menu ao clicar em algum link (evita ficar aberto ao navegar)
  mainNav.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => {
      mainNav.classList.remove('open');
      menuToggle.classList.remove('open');
      menuToggle.setAttribute('aria-expanded', 'false');
    });
  });
}

// ---------- Botão de mostrar/ocultar senha (index.html e cadastro.html) ----------

document.querySelectorAll('.toggle-senha').forEach((botao) => {
  botao.addEventListener('click', () => {
    const campo = document.getElementById(botao.dataset.target);
    if (!campo) return;

    const olhoAberto = botao.querySelector('.icone-olho-aberto');
    const olhoFechado = botao.querySelector('.icone-olho-fechado');
    const estaOculta = campo.type === 'password';

    campo.type = estaOculta ? 'text' : 'password';
    // usa setAttribute/removeAttribute em vez de ".hidden = " porque a
    // propriedade "hidden" não reflete de forma confiável em <svg> em todo
    // navegador — o atributo direto funciona sempre.
    if (estaOculta) {
      olhoAberto.setAttribute('hidden', '');
      olhoFechado.removeAttribute('hidden');
    } else {
      olhoAberto.removeAttribute('hidden');
      olhoFechado.setAttribute('hidden', '');
    }
    botao.setAttribute('aria-label', estaOculta ? 'Ocultar senha' : 'Mostrar senha');
  });
});

// ---------- Helper para chamar a API do backend (backend/app.py) ----------

async function chamarApi(caminho, opcoes = {}) {
  const resposta = await fetch(caminho, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'same-origin',
    ...opcoes,
  });
  const dados = await resposta.json().catch(() => ({}));
  return { status: resposta.status, dados };
}

// ---------- Formulário de login (index.html) ----------

const loginForm = document.getElementById('loginForm');
const loginMsg = document.getElementById('loginMsg');

if (loginForm && loginMsg) {
  loginForm.addEventListener('submit', async (event) => {
    event.preventDefault();

    const email = document.getElementById('email').value;
    const senha = document.getElementById('senha').value;
    const lembrarInput = loginForm.querySelector('[name="lembrar"]');
    const lembrar = lembrarInput ? lembrarInput.checked : false;

    loginMsg.textContent = 'Entrando...';
    loginMsg.classList.add('show');

    const { status, dados } = await chamarApi('/api/login', {
      method: 'POST',
      body: JSON.stringify({ email, senha, lembrar }),
    });

    if (status === 200 && dados.ok) {
      window.location.href = 'agenda.html';
    } else {
      loginMsg.textContent = dados.erro || 'Não foi possível entrar. Tente novamente.';
    }
  });
}

// ---------- Formulário de cadastro (cadastro.html) ----------

const cadastroForm = document.getElementById('cadastroForm');
const cadastroMsg = document.getElementById('cadastroMsg');

if (cadastroForm && cadastroMsg) {
  cadastroForm.addEventListener('submit', async (event) => {
    event.preventDefault();

    const nome = document.getElementById('nome').value;
    const email = document.getElementById('email').value;
    const senha = document.getElementById('senha').value;
    const confirmarSenha = document.getElementById('confirmarSenha').value;

    if (senha !== confirmarSenha) {
      cadastroMsg.textContent = 'As senhas não coincidem.';
      cadastroMsg.classList.add('show');
      return;
    }

    cadastroMsg.textContent = 'Criando conta...';
    cadastroMsg.classList.add('show');

    const { status, dados } = await chamarApi('/api/registrar', {
      method: 'POST',
      body: JSON.stringify({ nome, email, senha }),
    });

    if (status === 200 && dados.ok) {
      window.location.href = 'agenda.html';
    } else {
      cadastroMsg.textContent = dados.erro || 'Não foi possível criar a conta.';
    }
  });
}

// ---------- Esqueci minha senha (esqueci-senha.html) ----------

const esqueciSenhaForm = document.getElementById('esqueciSenhaForm');
const esqueciSenhaMsg = document.getElementById('esqueciSenhaMsg');

if (esqueciSenhaForm && esqueciSenhaMsg) {
  esqueciSenhaForm.addEventListener('submit', async (event) => {
    event.preventDefault();

    const email = document.getElementById('email').value;
    esqueciSenhaMsg.textContent = 'Enviando...';
    esqueciSenhaMsg.classList.add('show');

    const { status, dados } = await chamarApi('/api/esqueci-senha', {
      method: 'POST',
      body: JSON.stringify({ email }),
    });

    if (status === 200 && dados.ok) {
      esqueciSenhaForm.reset();
      esqueciSenhaMsg.textContent = dados.mensagem;
    } else {
      esqueciSenhaMsg.textContent = 'Não foi possível processar o pedido. Tente novamente.';
    }
  });
}

// ---------- Redefinir senha (redefinir-senha.html) ----------

const redefinirSenhaForm = document.getElementById('redefinirSenhaForm');
const redefinirSenhaMsg = document.getElementById('redefinirSenhaMsg');

if (redefinirSenhaForm && redefinirSenhaMsg) {
  const tokenRedefinicao = new URLSearchParams(window.location.search).get('token') || '';

  // Confere se o link ainda é válido assim que a página carrega, pra avisar
  // logo em vez de só depois que a pessoa preencher tudo.
  chamarApi(`/api/validar-token-redefinicao?token=${encodeURIComponent(tokenRedefinicao)}`).then(
    ({ dados }) => {
      if (!dados.valido) {
        redefinirSenhaMsg.textContent = 'Esse link é inválido ou já expirou. Peça um novo em "Esqueceu a senha?".';
        redefinirSenhaMsg.classList.add('show');
        redefinirSenhaForm.querySelectorAll('input, button').forEach((el) => {
          el.disabled = true;
        });
      }
    }
  );

  redefinirSenhaForm.addEventListener('submit', async (event) => {
    event.preventDefault();

    const senha = document.getElementById('senha').value;
    const confirmarSenha = document.getElementById('confirmarSenha').value;

    if (senha !== confirmarSenha) {
      redefinirSenhaMsg.textContent = 'As senhas não coincidem.';
      redefinirSenhaMsg.classList.add('show');
      return;
    }

    redefinirSenhaMsg.textContent = 'Salvando...';
    redefinirSenhaMsg.classList.add('show');

    const { status, dados } = await chamarApi('/api/redefinir-senha', {
      method: 'POST',
      body: JSON.stringify({ token: tokenRedefinicao, senha }),
    });

    if (status === 200 && dados.ok) {
      redefinirSenhaMsg.textContent = 'Senha redefinida! Redirecionando pro login...';
      setTimeout(() => {
        window.location.href = 'index.html';
      }, 2000);
    } else {
      redefinirSenhaMsg.textContent = dados.erro || 'Não foi possível redefinir a senha.';
    }
  });
}

// ---------- Logout (link "Sair" nas páginas internas) ----------

const logoutLink = document.getElementById('logoutLink');

if (logoutLink) {
  logoutLink.addEventListener('click', async (event) => {
    event.preventDefault();
    await chamarApi('/api/logout', { method: 'POST' });
    window.location.href = 'index.html';
  });
}

// ---------- Agenda de shows (exibição pública em agenda.html) ----------

const MESES_PT = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ'];

function formatarDataCard(dataISO) {
  const [, mes, dia] = dataISO.split('-');
  return { dia, mes: MESES_PT[Number(mes) - 1] || '' };
}

function formatarDataBR(dataISO) {
  return dataISO.split('-').reverse().join('/');
}

function montarCardShow(show) {
  const { dia, mes } = formatarDataCard(show.data);

  const artigo = document.createElement('article');
  artigo.className = 'show-card';

  const dataBox = document.createElement('div');
  dataBox.className = 'show-date';
  const spanDia = document.createElement('span');
  spanDia.className = 'day';
  spanDia.textContent = dia;
  const spanMes = document.createElement('span');
  spanMes.className = 'month';
  spanMes.textContent = mes;
  dataBox.append(spanDia, spanMes);

  const info = document.createElement('div');
  info.className = 'show-info';

  const titulo = document.createElement('h2');
  titulo.textContent = show.banda;

  const local = document.createElement('p');
  local.className = 'show-venue';
  local.textContent = `📍 ${show.local}, ${show.cidade}`;

  const horario = document.createElement('p');
  horario.className = 'show-time';
  horario.textContent = show.horario ? `🕗 ${show.horario}` : '🕗 Horário a confirmar';

  info.append(titulo, local, horario);

  if (show.observacoes) {
    const obs = document.createElement('p');
    obs.className = 'show-obs';
    obs.textContent = show.observacoes;
    info.appendChild(obs);
  }

  artigo.append(dataBox, info);
  return artigo;
}

async function carregarAgenda() {
  const grid = document.getElementById('showsGrid');
  const { status, dados } = await chamarApi('/api/shows');
  grid.innerHTML = '';

  if (status !== 200 || !dados.ok) {
    grid.innerHTML = '<p class="empty-state">Não foi possível carregar a agenda.</p>';
    return;
  }
  if (dados.shows.length === 0) {
    grid.innerHTML = '<p class="empty-state">Nenhum show na agenda no momento. Volte em breve!</p>';
    return;
  }
  dados.shows.forEach((show) => grid.appendChild(montarCardShow(show)));
}

// ---------- Bandas da comunidade (exibição pública em bandas.html) ----------

// Ícones do avatar das bandas (substituem o emoji). Embutidos aqui como SVG
// inline (em vez de <img>) pra dar pra recolorir com CSS via currentColor.
// Fonte: SVG Repo (svgrepo.com), recoloridos pra um tom só.
const ICONES_BANDA = [
  '<svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg"><path d="M575.744 717.952c19.072-38.656 19.968-52.672 64.704-93.824a579.2 579.2 0 0 1 43.072-35.776c41.216-38.976 63.872-81.344 29.824-118.4l-119.04-129.408c-34.944-37.952-80.384-17.216-123.648 22.464l-13.312 9.152c-8.064 8.384-16.512 16.64-25.472 24.896-50.304 46.208-70.336 48.128-113.408 61.632l-2.048 1.408c-34.112 4.16-106.496 53.568-140.8 85.056-62.016 56.96-84.288 133.632-49.792 171.264 1.856 1.92 3.968 3.712 5.952 5.504l-0.448 0.384 178.624 194.432 1.024-0.896c37.824 27.008 108.736 9.664 165.888-42.816 41.984-38.592 98.816-116.8 98.88-155.072z" fill="currentColor"/><path d="M859.648 166.528l56.768 61.824-416 382.272-56.768-61.76z" fill="currentColor"/><path d="M515.904 538.112l-3.072 98.944-98.816-3.072 3.072-98.88z" fill="currentColor"/><path d="M810.432 163.008l105.152 114.496-82.624 75.84-105.152-114.496z" fill="currentColor"/><path d="M847.36 153.088l81.472 88.64-139.904 128.64L707.456 281.6z" fill="currentColor"/><path d="M385.152 740.928l-81.472-88.64 25.152-46.976 105.152 114.496z" fill="currentColor"/></svg>', // violão
  '<svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg"><path d="M952.7808 563.4048H172.3904c-26.5728 0-48.0768-21.504-48.0768-48.0768V340.0704c0-26.5728 21.504-48.0768 48.0768-48.0768h780.3904c26.5728 0 48.0768 21.504 48.0768 48.0768v175.2576c0 26.5728-21.5552 48.0768-48.0768 48.0768z" fill="currentColor"/><path d="M282.4704 462.592h-27.9552c-2.9696 0-5.376-2.4064-5.376-5.376V327.68h38.7584v129.536c0 2.9696-2.4576 5.376-5.4272 5.376zM351.488 462.592h-27.9552c-2.9696 0-5.376-2.4064-5.376-5.376V327.68h38.7584v129.536c-0.0512 2.9696-2.4576 5.376-5.4272 5.376zM422.8096 462.592h-27.9552c-2.9696 0-5.376-2.4064-5.376-5.376V327.68h38.7584v129.536c-0.0512 2.9696-2.4576 5.376-5.4272 5.376zM724.1216 462.592h-27.9552c-2.9696 0-5.376-2.4064-5.376-5.376V327.68h38.7584v129.536c-0.0512 2.9696-2.4576 5.376-5.4272 5.376zM793.1392 462.592h-27.9552c-2.9696 0-5.376-2.4064-5.376-5.376V327.68h38.7584v129.536c-0.0512 2.9696-2.4576 5.376-5.4272 5.376zM864.4096 462.592h-27.9552c-2.9696 0-5.376-2.4064-5.376-5.376V327.68h38.7584v129.536c0 2.9696-2.4576 5.376-5.4272 5.376zM611.4304 462.592h-27.9552c-2.9696 0-5.376-2.4064-5.376-5.376V327.68h38.7584v129.536c-0.0512 2.9696-2.4576 5.376-5.4272 5.376zM542.4128 462.592h-27.9552c-2.9696 0-5.376-2.4064-5.376-5.376V327.68H547.84v129.536c-0.0512 2.9696-2.4576 5.376-5.4272 5.376z" fill="currentColor"/><path d="M660.3264 675.7888H170.4448c-61.952 0-112.384-50.432-112.384-112.384 0-45.5168 27.2384-84.736 66.2528-102.3488v-37.4784c-58.6752 19.4048-101.12 74.752-101.12 139.8272 0 81.2032 66.0992 147.3024 147.3024 147.3024h489.8816v-34.9184z" fill="currentColor"/><path d="M660.3264 675.7888h59.8016v34.9184h-59.8016z" fill="currentColor"/></svg>', // gaita
  '<svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg"><path d="M698.624 501.376a170.112 170.112 0 0 1-170.112 170.112h-58.496a170.112 170.112 0 0 1-170.112-170.112V250.048a170.048 170.048 0 0 1 170.112-170.112h58.496a170.112 170.112 0 0 1 170.112 170.112v251.328z" fill="currentColor"/><path d="M725.76 410.624v104.512c0 104.448-87.68 189.12-195.904 189.12H462.464c-108.224 0-195.968-84.672-195.968-189.12V410.624h-31.808v123.904c0 118.912 99.904 215.296 223.04 215.296h76.736c123.264 0 223.104-96.384 223.104-215.296V410.624h-31.808z" fill="currentColor"/><path d="M453.184 719.104h92.16v162.944h-92.16z" fill="currentColor"/><path d="M734.656 944v-12.224c0-40.896-38.976-74.048-87.232-74.048h-296.32c-48.128 0-87.232 33.216-87.232 74.048v12.224h470.784z" fill="currentColor"/></svg>', // microfone
  '<svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg"><path d="M469.184 814.464c0.64-26.432-10.752-88.832 32.96-132.928 44.992-45.504 137.024-58.624 143.04-63.68 16.256-14.784 22.848-33.728 27.584-53.12-45.504 15.04-110.528-34.176-148.48-114.24-23.936-50.56-10.304-123.264-2.56-160.576-26.88-6.848-53.248-4.608-80.064 17.984-21.696 18.368-40.64 78.272-86.208 124.224-64 64.64-153.92 65.664-190.336 86.464-13.696 6.272-31.04 18.88-47.808 35.776a229.76 229.76 0 0 0-24 28.672 171.2 171.2 0 0 0 15.488 225.856l69.312 68.608a171.52 171.52 0 0 0 220.096 17.728c9.984-6.016 21.888-14.976 33.856-26.176 24.32-22.72 40.064-46.208 37.12-54.592z" fill="currentColor"/><path d="M455.616 635.2l-48.384-47.808 432.384-426.112 37.632 37.248z" fill="currentColor"/><path d="M846.592 256.512l-78.784-43.968 124.8-115.648 73.344 38.784z" fill="currentColor"/></svg>', // guitarra elétrica
];

function montarCardBanda(banda) {
  const artigo = document.createElement('article');
  artigo.className = 'band-card';

  const avatar = document.createElement('div');
  avatar.className = 'band-avatar';
  avatar.innerHTML = ICONES_BANDA[banda.id % ICONES_BANDA.length];

  const titulo = document.createElement('h2');
  titulo.textContent = banda.nome;

  const genero = document.createElement('p');
  genero.className = 'band-genre';
  genero.textContent = banda.genero;

  const desc = document.createElement('p');
  desc.className = 'band-desc';
  desc.textContent = banda.descricao || '';

  artigo.append(avatar, titulo, genero, desc);

  if (banda.instagram) {
    const instagram = document.createElement('a');
    instagram.className = 'link-gold band-instagram';
    instagram.href = `https://instagram.com/${banda.instagram.replace(/^@/, '')}`;
    instagram.target = '_blank';
    instagram.rel = 'noopener noreferrer';
    instagram.textContent = `📷 ${banda.instagram}`;
    artigo.appendChild(instagram);
  }

  return artigo;
}

async function carregarBandas() {
  const grid = document.getElementById('bandsGrid');
  const { status, dados } = await chamarApi('/api/bandas');
  grid.innerHTML = '';

  if (status !== 200 || !dados.ok) {
    grid.innerHTML = '<p class="empty-state">Não foi possível carregar as bandas.</p>';
    return;
  }
  if (dados.bandas.length === 0) {
    grid.innerHTML = '<p class="empty-state">Nenhuma banda cadastrada ainda.</p>';
    return;
  }
  dados.bandas.forEach((banda) => grid.appendChild(montarCardBanda(banda)));
}

// ---------- Painel de administração (admin.html) ----------
// Os formulários "Novo show" / "Nova banda" são reaproveitados pra edição:
// clicar em "Editar" preenche os campos e troca o botão pra "Salvar
// alterações" — ao enviar, faz PUT em vez de POST.

const showForm = document.getElementById('showForm');
const showMsg = document.getElementById('showMsg');
const showsList = document.getElementById('showsList');
const showSubmitBtn = document.getElementById('showSubmitBtn');
const showCancelarEdicao = document.getElementById('showCancelarEdicao');
const showFormTitulo = document.getElementById('showFormTitulo');

let editandoShowId = null;

function iniciarEdicaoShow(show) {
  editandoShowId = show.id;
  document.getElementById('showBanda').value = show.banda;
  document.getElementById('showLocal').value = show.local;
  document.getElementById('showCidade').value = show.cidade;
  document.getElementById('showData').value = show.data;
  document.getElementById('showHorario').value = show.horario || '';
  document.getElementById('showObservacoes').value = show.observacoes || '';

  showSubmitBtn.textContent = 'Salvar alterações';
  showFormTitulo.textContent = 'Editar show';
  showCancelarEdicao.hidden = false;
  showMsg.classList.remove('show');
  showForm.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function cancelarEdicaoShow() {
  editandoShowId = null;
  showForm.reset();
  showSubmitBtn.textContent = 'Adicionar show';
  showFormTitulo.textContent = 'Novo show';
  showCancelarEdicao.hidden = true;
  showMsg.classList.remove('show');
}

if (showCancelarEdicao) {
  showCancelarEdicao.addEventListener('click', (event) => {
    event.preventDefault();
    cancelarEdicaoShow();
  });
}

function montarItemAdminShow(show) {
  const item = document.createElement('div');
  item.className = 'admin-list-item';

  const info = document.createElement('div');
  info.className = 'info';
  const nomeForte = document.createElement('strong');
  nomeForte.textContent = show.banda;
  info.appendChild(nomeForte);
  const horarioTexto = show.horario ? `às ${show.horario}` : '(horário a confirmar)';
  info.append(` — ${show.local}, ${show.cidade} • ${formatarDataBR(show.data)} ${horarioTexto}`);
  if (show.observacoes) {
    info.append(` — ${show.observacoes}`);
  }

  const acoes = document.createElement('div');
  acoes.className = 'admin-list-acoes';

  const editar = document.createElement('button');
  editar.type = 'button';
  editar.className = 'btn btn-outline';
  editar.textContent = 'Editar';
  editar.addEventListener('click', () => iniciarEdicaoShow(show));

  const excluir = document.createElement('button');
  excluir.type = 'button';
  excluir.className = 'btn btn-danger';
  excluir.textContent = 'Excluir';
  excluir.addEventListener('click', async () => {
    if (!confirm(`Excluir o show de "${show.banda}"?`)) return;
    if (editandoShowId === show.id) cancelarEdicaoShow();
    await chamarApi(`/api/shows/${show.id}`, { method: 'DELETE' });
    carregarShowsAdmin();
  });

  acoes.append(editar, excluir);
  item.append(info, acoes);
  return item;
}

async function carregarShowsAdmin() {
  const { status, dados } = await chamarApi('/api/shows');
  showsList.innerHTML = '';

  if (status !== 200 || !dados.ok || dados.shows.length === 0) {
    showsList.innerHTML = '<p class="empty-state">Nenhum show cadastrado ainda.</p>';
    return;
  }
  dados.shows.forEach((show) => showsList.appendChild(montarItemAdminShow(show)));
}

if (showForm) {
  showForm.addEventListener('submit', async (event) => {
    event.preventDefault();

    const corpo = {
      banda: document.getElementById('showBanda').value,
      local: document.getElementById('showLocal').value,
      cidade: document.getElementById('showCidade').value,
      data: document.getElementById('showData').value,
      horario: document.getElementById('showHorario').value,
      observacoes: document.getElementById('showObservacoes').value,
    };

    const editando = editandoShowId !== null;
    const { status, dados } = await chamarApi(
      editando ? `/api/shows/${editandoShowId}` : '/api/shows',
      { method: editando ? 'PUT' : 'POST', body: JSON.stringify(corpo) }
    );

    showMsg.classList.add('show');
    if (status === 200 && dados.ok) {
      showMsg.textContent = editando ? 'Show atualizado!' : 'Show adicionado à agenda!';
      cancelarEdicaoShow();
      carregarShowsAdmin();
    } else {
      showMsg.textContent = dados.erro || 'Não foi possível salvar o show.';
    }
  });
}

const bandaForm = document.getElementById('bandaForm');
const bandaMsg = document.getElementById('bandaMsg');
const bandasList = document.getElementById('bandasList');
const bandaSubmitBtn = document.getElementById('bandaSubmitBtn');
const bandaCancelarEdicao = document.getElementById('bandaCancelarEdicao');
const bandaFormTitulo = document.getElementById('bandaFormTitulo');

let editandoBandaId = null;

function iniciarEdicaoBanda(banda) {
  editandoBandaId = banda.id;
  document.getElementById('bandaNome').value = banda.nome;
  document.getElementById('bandaGenero').value = banda.genero;
  document.getElementById('bandaEmoji').value = banda.emoji || '';
  document.getElementById('bandaInstagram').value = banda.instagram || '';
  document.getElementById('bandaDescricao').value = banda.descricao || '';

  bandaSubmitBtn.textContent = 'Salvar alterações';
  bandaFormTitulo.textContent = 'Editar banda';
  bandaCancelarEdicao.hidden = false;
  bandaMsg.classList.remove('show');
  bandaForm.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function cancelarEdicaoBanda() {
  editandoBandaId = null;
  bandaForm.reset();
  bandaSubmitBtn.textContent = 'Adicionar banda';
  bandaFormTitulo.textContent = 'Nova banda';
  bandaCancelarEdicao.hidden = true;
  bandaMsg.classList.remove('show');
}

if (bandaCancelarEdicao) {
  bandaCancelarEdicao.addEventListener('click', (event) => {
    event.preventDefault();
    cancelarEdicaoBanda();
  });
}

function montarItemAdminBanda(banda) {
  const item = document.createElement('div');
  item.className = 'admin-list-item';

  const info = document.createElement('div');
  info.className = 'info';
  const nomeForte = document.createElement('strong');
  nomeForte.textContent = `${banda.emoji || '🎵'} ${banda.nome}`;
  info.appendChild(nomeForte);
  info.append(` — ${banda.genero}${banda.instagram ? ` • ${banda.instagram}` : ''}`);

  const acoes = document.createElement('div');
  acoes.className = 'admin-list-acoes';

  const editar = document.createElement('button');
  editar.type = 'button';
  editar.className = 'btn btn-outline';
  editar.textContent = 'Editar';
  editar.addEventListener('click', () => iniciarEdicaoBanda(banda));

  const excluir = document.createElement('button');
  excluir.type = 'button';
  excluir.className = 'btn btn-danger';
  excluir.textContent = 'Excluir';
  excluir.addEventListener('click', async () => {
    if (!confirm(`Excluir a banda "${banda.nome}"?`)) return;
    if (editandoBandaId === banda.id) cancelarEdicaoBanda();
    await chamarApi(`/api/bandas/${banda.id}`, { method: 'DELETE' });
    carregarBandasAdmin();
  });

  acoes.append(editar, excluir);
  item.append(info, acoes);
  return item;
}

async function carregarBandasAdmin() {
  const { status, dados } = await chamarApi('/api/bandas');
  bandasList.innerHTML = '';

  if (status !== 200 || !dados.ok || dados.bandas.length === 0) {
    bandasList.innerHTML = '<p class="empty-state">Nenhuma banda cadastrada ainda.</p>';
    return;
  }
  dados.bandas.forEach((banda) => bandasList.appendChild(montarItemAdminBanda(banda)));
}

if (bandaForm) {
  bandaForm.addEventListener('submit', async (event) => {
    event.preventDefault();

    const corpo = {
      nome: document.getElementById('bandaNome').value,
      genero: document.getElementById('bandaGenero').value,
      emoji: document.getElementById('bandaEmoji').value,
      instagram: document.getElementById('bandaInstagram').value,
      descricao: document.getElementById('bandaDescricao').value,
    };

    const editando = editandoBandaId !== null;
    const { status, dados } = await chamarApi(
      editando ? `/api/bandas/${editandoBandaId}` : '/api/bandas',
      { method: editando ? 'PUT' : 'POST', body: JSON.stringify(corpo) }
    );

    bandaMsg.classList.add('show');
    if (status === 200 && dados.ok) {
      bandaMsg.textContent = editando ? 'Banda atualizada!' : 'Banda adicionada!';
      cancelarEdicaoBanda();
      carregarBandasAdmin();
    } else {
      bandaMsg.textContent = dados.erro || 'Não foi possível salvar a banda.';
    }
  });
}

// ---------- Proteção das páginas internas + saudação + admin ----------
// Toda página que tem <nav id="mainNav"> é considerada "interna" e exige login.
// Páginas com <body data-admin-only> também exigem que o usuário seja admin.

const userGreeting = document.getElementById('userGreeting');
const adminLink = document.getElementById('adminLink');

if (mainNav) {
  chamarApi('/api/eu').then(({ status, dados }) => {
    if (status !== 200 || !dados.ok) {
      window.location.href = 'index.html';
      return;
    }

    const usuario = dados.usuario;

    if (userGreeting) {
      userGreeting.textContent = `Olá, ${usuario.nome.split(' ')[0]}`;
    }
    if (adminLink && usuario.admin) {
      adminLink.classList.add('show');
    }

    const paginaExigeAdmin = document.body.hasAttribute('data-admin-only');
    if (paginaExigeAdmin && !usuario.admin) {
      window.location.href = 'agenda.html';
      return;
    }

    if (document.getElementById('showsGrid')) carregarAgenda();
    if (document.getElementById('bandsGrid')) carregarBandas();
    if (showsList) carregarShowsAdmin();
    if (bandasList) carregarBandasAdmin();
  });
}

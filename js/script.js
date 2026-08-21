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

function montarCardBanda(banda) {
  const artigo = document.createElement('article');
  artigo.className = 'band-card';

  const avatar = document.createElement('div');
  avatar.className = 'band-avatar';
  avatar.textContent = banda.emoji || '🎵';

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

const showForm = document.getElementById('showForm');
const showMsg = document.getElementById('showMsg');
const showsList = document.getElementById('showsList');

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

  const excluir = document.createElement('button');
  excluir.type = 'button';
  excluir.className = 'btn btn-danger';
  excluir.textContent = 'Excluir';
  excluir.addEventListener('click', async () => {
    if (!confirm(`Excluir o show de "${show.banda}"?`)) return;
    await chamarApi(`/api/shows/${show.id}`, { method: 'DELETE' });
    carregarShowsAdmin();
  });

  item.append(info, excluir);
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

    const { status, dados } = await chamarApi('/api/shows', {
      method: 'POST',
      body: JSON.stringify(corpo),
    });

    showMsg.classList.add('show');
    if (status === 200 && dados.ok) {
      showForm.reset();
      showMsg.textContent = 'Show adicionado à agenda!';
      carregarShowsAdmin();
    } else {
      showMsg.textContent = dados.erro || 'Não foi possível adicionar o show.';
    }
  });
}

const bandaForm = document.getElementById('bandaForm');
const bandaMsg = document.getElementById('bandaMsg');
const bandasList = document.getElementById('bandasList');

function montarItemAdminBanda(banda) {
  const item = document.createElement('div');
  item.className = 'admin-list-item';

  const info = document.createElement('div');
  info.className = 'info';
  const nomeForte = document.createElement('strong');
  nomeForte.textContent = `${banda.emoji || '🎵'} ${banda.nome}`;
  info.appendChild(nomeForte);
  info.append(` — ${banda.genero}${banda.instagram ? ` • ${banda.instagram}` : ''}`);

  const excluir = document.createElement('button');
  excluir.type = 'button';
  excluir.className = 'btn btn-danger';
  excluir.textContent = 'Excluir';
  excluir.addEventListener('click', async () => {
    if (!confirm(`Excluir a banda "${banda.nome}"?`)) return;
    await chamarApi(`/api/bandas/${banda.id}`, { method: 'DELETE' });
    carregarBandasAdmin();
  });

  item.append(info, excluir);
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

    const { status, dados } = await chamarApi('/api/bandas', {
      method: 'POST',
      body: JSON.stringify(corpo),
    });

    bandaMsg.classList.add('show');
    if (status === 200 && dados.ok) {
      bandaForm.reset();
      bandaMsg.textContent = 'Banda adicionada!';
      carregarBandasAdmin();
    } else {
      bandaMsg.textContent = dados.erro || 'Não foi possível adicionar a banda.';
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

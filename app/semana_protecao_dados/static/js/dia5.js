(function () {
  const dados = JSON.parse(document.getElementById('missao-dados').textContent);
  const cenas = dados.cenas;
  const mensagensScore = dados.mensagens_score;

  const elInicio = document.getElementById('missao-inicio');
  const elJogo = document.getElementById('missao-jogo');
  const elFim = document.getElementById('missao-fim');
  const elNum = document.getElementById('cena-num');
  const elAcertos = document.getElementById('cena-acertos');
  const elTitulo = document.getElementById('cena-titulo');
  const elNarrativa = document.getElementById('cena-narrativa');
  const elImg = document.getElementById('cena-img');
  const elAlternativas = document.getElementById('cena-alternativas');
  const elFeedback = document.getElementById('cena-feedback');
  const elFeedbackMarca = document.getElementById('cena-feedback-marca');
  const elFeedbackTexto = document.getElementById('cena-feedback-texto');
  const elBloco = document.getElementById('cena-bloco');

  let idx = 0;
  let acertos = 0;

  document.getElementById('btn-iniciar').addEventListener('click', iniciar);
  document.getElementById('btn-proximo').addEventListener('click', proximo);

  function iniciar() {
    elInicio.hidden = true;
    elJogo.hidden = false;
    mostrarCena();
  }

  function mostrarCena() {
    const c = cenas[idx];
    elNum.textContent = idx + 1;
    elAcertos.textContent = acertos;
    elTitulo.textContent = c.titulo;
    elNarrativa.innerHTML = c.narrativa;

    if (c.imagem) {
      elImg.src = c.imagem;
      elImg.alt = c.titulo;
      elImg.hidden = false;
    } else {
      elImg.hidden = true;
    }

    elAlternativas.innerHTML = c.alternativas.map(a => `
      <button class="spd-alt-btn" data-id="${a.id}">
        <span class="spd-alt-letra">${a.id.toUpperCase()}</span>
        <span class="spd-alt-texto">${escapeHtml(a.texto)}</span>
      </button>
    `).join('');

    elAlternativas.querySelectorAll('.spd-alt-btn').forEach(btn => {
      btn.addEventListener('click', () => responder(btn.dataset.id, btn));
    });

    elFeedback.hidden = true;

    elBloco.classList.remove('saindo');
    elBloco.classList.add('entrando');
    setTimeout(() => elBloco.classList.remove('entrando'), 250);
  }

  function responder(idEscolhido, btn) {
    const cena = cenas[idx];
    const alt = cena.alternativas.find(a => a.id === idEscolhido);

    if (alt.correta) acertos++;
    elAcertos.textContent = acertos;

    elAlternativas.querySelectorAll('.spd-alt-btn').forEach(b => {
      b.disabled = true;
      const aId = b.dataset.id;
      const altDoBtn = cena.alternativas.find(a => a.id === aId);
      if (altDoBtn.correta) b.classList.add('correta');
      if (b === btn && !alt.correta) b.classList.add('errada');
    });

    elFeedbackMarca.textContent = alt.correta ? '✅ Boa decisão' : '⚠️ Cuidado aqui';
    elFeedbackMarca.className = 'spd-feedback-marca ' + (alt.correta ? 'ok' : 'erro');
    elFeedbackTexto.innerHTML = alt.feedback;
    elFeedback.hidden = false;
    elFeedback.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  function proximo() {
    idx++;
    if (idx >= cenas.length) {
      terminar();
      return;
    }
    elBloco.classList.add('saindo');
    setTimeout(mostrarCena, 220);
  }

  function terminar() {
    document.getElementById('resultado-acertos').textContent = acertos;
    document.getElementById('resultado-mensagem').innerHTML =
      mensagensScore[acertos] || mensagensScore[0];

    elJogo.hidden = true;
    elFim.hidden = false;
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
  }
})();
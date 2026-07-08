(function () {
  const dados = JSON.parse(document.getElementById('quiz-dados').textContent);
  const cenarios = dados.cenarios;

  const elInicio = document.getElementById('quiz-inicio');
  const elJogo = document.getElementById('quiz-jogo');
  const elFim = document.getElementById('quiz-fim');
  const elNum = document.getElementById('quiz-num');
  const elTitulo = document.getElementById('cenario-titulo');
  const elContexto = document.getElementById('cenario-contexto');
  const elAlternativas = document.getElementById('cenario-alternativas');
  const elFeedback = document.getElementById('cenario-feedback');
  const elFeedbackMarca = document.getElementById('cenario-feedback-marca');
  const elFeedbackTexto = document.getElementById('cenario-feedback-texto');
  const elBloco = document.getElementById('cenario-bloco');

  let idx = 0;

  document.getElementById('btn-iniciar').addEventListener('click', iniciar);
  document.getElementById('btn-proximo').addEventListener('click', proximo);

  function iniciar() {
    elInicio.hidden = true;
    elJogo.hidden = false;
    mostrarCenario();
  }

  function mostrarCenario() {
    const c = cenarios[idx];
    elNum.textContent = idx + 1;
    elTitulo.textContent = c.titulo;
    elContexto.innerHTML = c.contexto;

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
    const cenario = cenarios[idx];
    const alt = cenario.alternativas.find(a => a.id === idEscolhido);

    // Desabilita todos os botões e marca o escolhido + o correto
    elAlternativas.querySelectorAll('.spd-alt-btn').forEach(b => {
      b.disabled = true;
      const aId = b.dataset.id;
      const altDoBtn = cenario.alternativas.find(a => a.id === aId);
      if (altDoBtn.correta) {
        b.classList.add('correta');
      }
      if (b === btn && !alt.correta) {
        b.classList.add('errada');
      }
    });

    // Renderiza feedback
    elFeedbackMarca.textContent = alt.correta ? '✅ Boa decisão' : '⚠️ Vamos pensar nisso';
    elFeedbackMarca.className = 'spd-feedback-marca ' + (alt.correta ? 'ok' : 'erro');
    elFeedbackTexto.innerHTML = alt.feedback;
    elFeedback.hidden = false;

    elFeedback.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  function proximo() {
    idx++;
    if (idx >= cenarios.length) {
      terminar();
      return;
    }
    elBloco.classList.add('saindo');
    setTimeout(mostrarCenario, 220);
  }

  function terminar() {
    elJogo.hidden = true;
    elFim.hidden = false;
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
  }
})();
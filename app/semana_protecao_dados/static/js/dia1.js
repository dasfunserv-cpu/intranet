(function () {
  const dados = JSON.parse(document.getElementById('quiz-dados').textContent);
  const quiz = dados.quiz;
  const categorias = dados.categorias;
  const urlSubmit = dados.url_submit;

  // Mapa id → nome de categoria, pra exibir na revisão
  const nomeCategoria = {};
  categorias.forEach(c => { nomeCategoria[c.id] = c.nome; });

  const elInicio = document.getElementById('quiz-inicio');
  const elJogo = document.getElementById('quiz-jogo');
  const elFim = document.getElementById('quiz-fim');
  const elNum = document.getElementById('quiz-num');
  const elTempo = document.getElementById('quiz-tempo');
  const elItem = document.getElementById('quiz-item-texto');
  const elBotoes = document.getElementById('quiz-botoes');

  let idx = 0;
  let acertos = 0;
  let tStart = 0;
  let timerInterval = null;
  const respostas = []; // {idEscolhido, correto}

  document.getElementById('btn-iniciar').addEventListener('click', iniciar);
  document.getElementById('btn-enviar-ranking').addEventListener('click', enviarRanking);
  document.getElementById('btn-pular-ranking').addEventListener('click', () => {
    document.getElementById('ranking-form').hidden = true;
  });

  elBotoes.querySelectorAll('.spd-quiz-opcao').forEach(btn => {
    btn.addEventListener('click', () => responder(btn.dataset.id));
  });

  function iniciar() {
    elInicio.hidden = true;
    elJogo.hidden = false;
    tStart = performance.now();
    timerInterval = setInterval(atualizarTimer, 100);
    mostrarItem();
  }

  function atualizarTimer() {
    const s = (performance.now() - tStart) / 1000;
    elTempo.textContent = s.toFixed(1);
  }

    function mostrarItem() {
    elNum.textContent = idx + 1;
    elItem.textContent = quiz[idx].item;
    elBotoes.querySelectorAll('.spd-quiz-opcao').forEach(b => {
        b.disabled = false;
    });

    // Fade-in
    const palco = document.querySelector('.spd-quiz-item');
    palco.classList.remove('saindo');
    palco.classList.add('entrando');
    setTimeout(() => palco.classList.remove('entrando'), 450);
    }

    function responder(idEscolhido) {
    const correto = quiz[idx].resposta;
    const acertou = idEscolhido === correto;
    if (acertou) acertos++;
    respostas.push({ idEscolhido, acertou });

    idx++;
    if (idx >= quiz.length) {
        terminar();
        return;
    }

    // Bloqueia botões durante a transição pra não dar duplo-clique
    elBotoes.querySelectorAll('.spd-quiz-opcao').forEach(b => b.disabled = true);

    // Fade-out, troca, fade-in
    const palco = document.querySelector('.spd-quiz-item');
    palco.classList.add('saindo');
    setTimeout(() => {
        mostrarItem();
    }, 220);
    }
  function terminar() {
    clearInterval(timerInterval);
    const tempoMs = Math.round(performance.now() - tStart);
    const score = acertos * 1000 - Math.round(tempoMs / 1000);

    document.getElementById('resultado-acertos').textContent = acertos;
    document.getElementById('resultado-tempo').textContent = (tempoMs / 1000).toFixed(1);
    document.getElementById('resultado-score').textContent = score;

    renderizarRevisao();

    elJogo.hidden = true;
    elFim.hidden = false;

    window._quizResultado = { acertos, tempo_ms: tempoMs };
  }

  function renderizarRevisao() {
    const lista = document.getElementById('quiz-revisao');
    lista.innerHTML = quiz.map((q, i) => {
      const r = respostas[i];
      const acertou = r.acertou;
      const sua = nomeCategoria[r.idEscolhido] || '—';
      const correta = nomeCategoria[q.resposta];

      return `
        <li class="spd-revisao-item ${acertou ? 'acerto' : 'erro'}">
          <div class="spd-revisao-cabecalho">
            <span class="spd-revisao-marca">${acertou ? '✅' : '❌'}</span>
            <strong>${escapeHtml(q.item)}</strong>
          </div>
          <div class="spd-revisao-respostas">
            ${acertou
              ? `<span>Resposta: <strong>${escapeHtml(correta)}</strong></span>`
              : `<span>Sua resposta: <strong>${escapeHtml(sua)}</strong></span>
                 <span>Resposta correta: <strong>${escapeHtml(correta)}</strong></span>`
            }
          </div>
          <div class="spd-revisao-explicacao">${escapeHtml(q.explicacao)}</div>
        </li>
      `;
    }).join('');
  }

  async function enviarRanking() {
    const nome = document.getElementById('input-nome').value.trim();
    if (!nome) {
      alert('Digite seu nome.');
      return;
    }

    const status = document.getElementById('ranking-status');
    document.getElementById('ranking-form').hidden = true;
    status.hidden = false;
    status.textContent = 'Enviando...';

    try {
      const resp = await fetch(urlSubmit, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nome: nome,
          acertos: window._quizResultado.acertos,
          tempo_ms: window._quizResultado.tempo_ms,
        }),
      });
      const data = await resp.json();

      if (data.aceito) {
        status.textContent = `🎉 Você entrou no Top 5! Posição: ${data.posicao}º`;
      } else if (data.motivo === 'score_inferior') {
        status.textContent = 'Você já tem um score melhor salvo hoje. Mantido o anterior.';
      } else {
        status.textContent = 'Você não entrou no Top 5 dessa vez. Tenta de novo amanhã!';
      }

      atualizarListaRanking(data.ranking);
    } catch (e) {
      status.textContent = 'Erro ao enviar. Tente de novo.';
    }
  }

  function atualizarListaRanking(ranking) {
    const lista = document.getElementById('ranking-lista');
    if (!ranking || ranking.length === 0) {
      lista.innerHTML = '<li class="spd-ranking-vazio">Seja o primeiro!</li>';
      return;
    }
    lista.innerHTML = ranking.map(r =>
      `<li><span class="spd-ranking-nome">${escapeHtml(r.nome)}</span><span class="spd-ranking-score">${r.score}</span></li>`
    ).join('');
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
  }
})();
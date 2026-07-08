(function () {
  const dados = JSON.parse(document.getElementById('quiz-dados').textContent);
  const emails = dados.emails;

  const elInicio = document.getElementById('quiz-inicio');
  const elJogo = document.getElementById('quiz-jogo');
  const elFim = document.getElementById('quiz-fim');
  const elNum = document.getElementById('quiz-num');
  const elNome = document.getElementById('email-nome');
  const elEndereco = document.getElementById('email-endereco');
  const elAssunto = document.getElementById('email-assunto');
  const elCorpo = document.getElementById('email-corpo');
  const elAvatar = document.getElementById('email-avatar');
  const elEmail = document.getElementById('quiz-email');
  const botoes = document.querySelectorAll('.spd-quiz-opcao');

  let idx = 0;
  let acertos = 0;
  const respostas = [];

  document.getElementById('btn-iniciar').addEventListener('click', iniciar);
  botoes.forEach(btn => {
    btn.addEventListener('click', () => responder(btn.dataset.id));
  });

  function iniciar() {
    elInicio.hidden = true;
    elJogo.hidden = false;
    mostrarEmail();
  }

  function mostrarEmail() {
    const e = emails[idx];
    elNum.textContent = idx + 1;
    elNome.textContent = e.remetente_nome;
    elEndereco.textContent = e.remetente_email;
    elAssunto.textContent = e.assunto;
    elCorpo.innerHTML = e.corpo;
    elAvatar.textContent = (e.remetente_nome || '?').charAt(0).toUpperCase();

    botoes.forEach(b => b.disabled = false);

    elEmail.classList.remove('saindo');
    elEmail.classList.add('entrando');
    setTimeout(() => elEmail.classList.remove('entrando'), 250);
  }

  function responder(idEscolhido) {
    const correto = emails[idx].resposta;
    const acertou = idEscolhido === correto;
    if (acertou) acertos++;
    respostas.push({ idEscolhido, acertou });

    idx++;
    if (idx >= emails.length) {
      terminar();
      return;
    }

    botoes.forEach(b => b.disabled = true);
    elEmail.classList.add('saindo');
    setTimeout(mostrarEmail, 220);
  }

  function terminar() {
    document.getElementById('resultado-acertos').textContent = acertos;
    renderizarRevisao();
    elJogo.hidden = true;
    elFim.hidden = false;
  }

  function renderizarRevisao() {
    const lista = document.getElementById('quiz-revisao');
    lista.innerHTML = emails.map((e, i) => {
      const r = respostas[i];
      const acertou = r.acertou;
      const rotuloCorreto = e.resposta === 'phishing' ? '🎣 Phishing' : '✅ Legítimo';
      const rotuloSua = r.idEscolhido === 'phishing' ? '🎣 Phishing' : '✅ Legítimo';

      return `
        <li class="spd-revisao-item ${acertou ? 'acerto' : 'erro'}">
          <div class="spd-revisao-cabecalho">
            <span class="spd-revisao-marca">${acertou ? '✅' : '❌'}</span>
            <strong>${escapeHtml(e.assunto)}</strong>
          </div>
          <div class="spd-revisao-respostas">
            ${acertou
              ? `<span>Resposta: <strong>${rotuloCorreto}</strong></span>`
              : `<span>Sua resposta: <strong>${rotuloSua}</strong></span>
                 <span>Resposta correta: <strong>${rotuloCorreto}</strong></span>`
            }
          </div>
          <div class="spd-revisao-explicacao">
            <strong>Sinais nesse e-mail:</strong>
            <ul class="spd-sinais-lista">
              ${e.sinais.map(s => `<li>${escapeHtml(s)}</li>`).join('')}
            </ul>
          </div>
        </li>
      `;
    }).join('');
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
  }
})();
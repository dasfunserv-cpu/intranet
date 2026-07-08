(function () {
  const palco = document.querySelector('.spd-carrossel-palco');
  if (!palco) return;

  const dicas = palco.querySelectorAll('.spd-dica');
  const btnPrev = document.querySelector('.spd-carrossel-prev');
  const btnNext = document.querySelector('.spd-carrossel-next');
  const barra = document.querySelector('.spd-progresso-preenchido');

  let atual = 0;
  const DURACAO = 8000; // 8 segundos
  let inicio = null;
  let pausado = false;
  let tempoDecorrido = 0; // ms já decorridos ao pausar
  let rafId = null;

  function mostrar(idx) {
    dicas.forEach((d, i) => d.classList.toggle('ativa', i === idx));
    atual = idx;
  }

  function proximo() {
    mostrar((atual + 1) % dicas.length);
  }

  function anterior() {
    mostrar((atual - 1 + dicas.length) % dicas.length);
  }

  // --- Animação da barra com requestAnimationFrame ---

  function iniciarBarra() {
    inicio = performance.now();
    tempoDecorrido = 0;
    pausado = false;
    if (rafId) cancelAnimationFrame(rafId);
    tick();
  }

  function tick() {
    if (pausado) return;

    const agora = performance.now();
    const progresso = tempoDecorrido + (agora - inicio);
    const pct = Math.min(progresso / DURACAO, 1);

    barra.style.width = (pct * 100) + '%';

    if (pct >= 1) {
      proximo();
      iniciarBarra();
      return;
    }

    rafId = requestAnimationFrame(tick);
  }

  function pausar() {
    if (pausado) return;
    pausado = true;
    // Salva quanto já passou
    tempoDecorrido += performance.now() - inicio;
    if (rafId) cancelAnimationFrame(rafId);
  }

  function retomar() {
    if (!pausado) return;
    pausado = false;
    inicio = performance.now();
    tick();
  }

  // --- Eventos ---

  btnNext.addEventListener('click', () => { proximo(); iniciarBarra(); });
  btnPrev.addEventListener('click', () => { anterior(); iniciarBarra(); });

  // Pausa no hover (desktop)
  const carrossel = document.querySelector('.spd-carrossel');


  // Pausa no toque (mobile)
  carrossel.addEventListener('touchstart', () => {
    if (pausado) retomar(); else pausar();
  }, { passive: true });

  // --- Inicializar ---

  mostrar(0);
  iniciarBarra();
})();
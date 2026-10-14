/*
 * Comportamento mobile do PotiMaker: gaveta lateral do menu.
 *
 * A gaveta e a barra inferior so existem abaixo de lg (1024px) — no desktop o
 * menu horizontal do header assume. O CSS esconde os dois lados conforme o
 * breakpoint; aqui cuidamos so da interacao.
 */
(function () {
    'use strict';

    var gaveta = document.getElementById('gaveta');
    var fundo = document.getElementById('gaveta-fundo');
    var btnAbrir = document.getElementById('btn-menu');
    var btnFechar = document.getElementById('btn-fechar-gaveta');

    if (!gaveta || !btnAbrir) return;

    var ultimoFoco = null;

    function abrir() {
        ultimoFoco = document.activeElement;
        gaveta.hidden = false;
        fundo.hidden = false;
        // força um frame antes da classe para a transicao acontecer
        requestAnimationFrame(function () {
            gaveta.classList.add('aberta');
            fundo.classList.add('visivel');
        });
        btnAbrir.setAttribute('aria-expanded', 'true');
        // trava a rolagem do fundo enquanto a gaveta esta aberta
        document.body.style.overflow = 'hidden';
        if (btnFechar) btnFechar.focus();
    }

    function fechar() {
        gaveta.classList.remove('aberta');
        fundo.classList.remove('visivel');
        btnAbrir.setAttribute('aria-expanded', 'false');
        document.body.style.overflow = '';
        // espera a animacao terminar antes de tirar do fluxo
        setTimeout(function () {
            gaveta.hidden = true;
            fundo.hidden = true;
        }, 220);
        if (ultimoFoco) ultimoFoco.focus();
    }

    btnAbrir.addEventListener('click', abrir);
    if (btnFechar) btnFechar.addEventListener('click', fechar);
    fundo.addEventListener('click', fechar);

    // Esc fecha
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && !gaveta.hidden) fechar();
    });

    // Arrastar para a direita fecha (gesto natural em celular)
    var xInicial = null;
    gaveta.addEventListener('touchstart', function (e) {
        xInicial = e.touches[0].clientX;
    }, { passive: true });
    gaveta.addEventListener('touchend', function (e) {
        if (xInicial === null) return;
        var delta = e.changedTouches[0].clientX - xInicial;
        if (delta > 60) fechar();
        xInicial = null;
    }, { passive: true });

    // Ao voltar para desktop, garante que a gaveta nao fique presa aberta
    window.addEventListener('resize', function () {
        if (window.innerWidth >= 1024 && !gaveta.hidden) fechar();
    });
})();

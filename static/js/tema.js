/*
 * Alternador de modo escuro do PotiMaker.
 *
 * O tema fica em [data-tema] no <html> e é persistido no localStorage.
 * Este arquivo é carregado de forma SÍNCRONA no <head>, antes do <body>, para
 * que o tema salvo seja aplicado antes da primeira pintura — se rodasse no fim
 * da página, o usuário veria um flash branco a cada navegação.
 *
 * Sem escolha salva, respeita o prefers-color-scheme do sistema.
 */
(function () {
    'use strict';

    var CHAVE = 'potimaker-tema';

    function temaPreferido() {
        try {
            var salvo = localStorage.getItem(CHAVE);
            if (salvo === 'escuro' || salvo === 'claro') return salvo;
        } catch (e) {
            // localStorage pode estar bloqueado (modo privado/cookies off)
        }
        var prefereEscuro = window.matchMedia
            && window.matchMedia('(prefers-color-scheme: dark)').matches;
        return prefereEscuro ? 'escuro' : 'claro';
    }

    function aplicar(tema) {
        if (tema === 'escuro') {
            document.documentElement.setAttribute('data-tema', 'escuro');
        } else {
            document.documentElement.removeAttribute('data-tema');
        }
        atualizarBotoes(tema);
    }

    function atualizarBotoes(tema) {
        var escuro = tema === 'escuro';
        document.querySelectorAll('.btn-tema').forEach(function (btn) {
            btn.setAttribute('aria-pressed', escuro ? 'true' : 'false');
            btn.setAttribute('title', escuro ? 'Voltar ao modo claro' : 'Ativar modo escuro');
        });
    }

    function alternar() {
        var novo = document.documentElement.getAttribute('data-tema') === 'escuro'
            ? 'claro'
            : 'escuro';
        try {
            localStorage.setItem(CHAVE, novo);
        } catch (e) {
            // Sem persistência, o tema vale só para esta página
        }
        aplicar(novo);
    }

    // Aplica imediatamente (ainda no <head>, antes do body existir)
    aplicar(temaPreferido());

    document.addEventListener('DOMContentLoaded', function () {
        atualizarBotoes(document.documentElement.getAttribute('data-tema') === 'escuro' ? 'escuro' : 'claro');
        document.querySelectorAll('.btn-tema').forEach(function (btn) {
            btn.addEventListener('click', alternar);
        });
        // Libera as transições só agora, senão a aplicação inicial "pisca"
        document.documentElement.classList.add('tema-pronto');
    });

    // Segue o sistema enquanto o usuário não escolher manualmente
    if (window.matchMedia) {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function (e) {
            var temEscolha = false;
            try {
                temEscolha = !!localStorage.getItem(CHAVE);
            } catch (err) {}
            if (!temEscolha) aplicar(e.matches ? 'escuro' : 'claro');
        });
    }

    window.PotiMakerTema = { alternar: alternar, aplicar: aplicar };
})();

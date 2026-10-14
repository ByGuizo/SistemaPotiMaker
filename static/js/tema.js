(function () {
    'use strict';

    var CHAVE = 'potimaker-tema';

    function temaPreferido() {
        try {
            var salvo = localStorage.getItem(CHAVE);
            if (salvo === 'escuro' || salvo === 'claro') return salvo;
        } catch (e) {
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
        }
        aplicar(novo);
    }

    aplicar(temaPreferido());

    document.addEventListener('DOMContentLoaded', function () {
        atualizarBotoes(document.documentElement.getAttribute('data-tema') === 'escuro' ? 'escuro' : 'claro');
        document.querySelectorAll('.btn-tema').forEach(function (btn) {
            btn.addEventListener('click', alternar);
        });
        document.documentElement.classList.add('tema-pronto');
    });

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

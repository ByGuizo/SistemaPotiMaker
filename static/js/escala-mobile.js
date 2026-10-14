/*
 * Escala de horários: duas versões do mesmo formulário.
 *
 * O celular recebe blocos por dia e o desktop a grade 5x6, mas ambos usam os
 * mesmos nomes de campo (celula_<dia>_<slot>). Se as duas fossem enviadas, cada
 * célula chegaria duplicada no POST e `membros.set()` receberia a união das
 * duas — apagando ou duplicando escolhas conforme a versão editada.
 *
 * Solução: no submit, remove do DOM a versão que está escondida (a que o CSS
 * não mostra no breakpoint atual). Só a versão visível é enviada.
 */
(function () {
    'use strict';

    var form = document.getElementById('form-escala');
    if (!form) return;

    var mobile = document.getElementById('escala-mobile');
    var desktop = document.getElementById('escala-desktop');
    if (!mobile || !desktop) return;

    function estaVisivel(el) {
        // offsetParent é null quando o elemento (ou um ancestral) está display:none
        return el.offsetParent !== null || el.getClientRects().length > 0;
    }

    form.addEventListener('submit', function () {
        var inativo = estaVisivel(mobile) ? desktop : mobile;
        inativo.remove();
    });
})();

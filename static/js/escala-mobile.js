(function () {
    'use strict';

    var form = document.getElementById('form-escala');
    if (!form) return;

    var mobile = document.getElementById('escala-mobile');
    var desktop = document.getElementById('escala-desktop');
    if (!mobile || !desktop) return;

    function estaVisivel(el) {
        return el.offsetParent !== null || el.getClientRects().length > 0;
    }

    form.addEventListener('submit', function () {
        var inativo = estaVisivel(mobile) ? desktop : mobile;
        inativo.remove();
    });
})();

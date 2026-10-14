(function () {
    'use strict';

    document.addEventListener('submit', function (evento) {
        var mensagem = evento.target.dataset && evento.target.dataset.confirmar;
        if (mensagem && !window.confirm(mensagem)) {
            evento.preventDefault();
            evento.stopImmediatePropagation();
        }
    }, true);
})();

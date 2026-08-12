/*
 * Campo de membros PotiMaker — substitui o <select multiple> nativo.
 *
 * Interação: o campo é sempre um input de texto. Você digita, ele completa o
 * restante do nome inline (texto selecionado, como a barra de endereço do
 * navegador); Enter ou Tab confirma e vira um chip; o campo limpa sozinho para
 * o próximo. Não é preciso clicar em lista nem segurar Ctrl.
 *
 * Uso: <div class="multi-select" data-nome="celula_0_M1" data-placeholder="...">
 *          <script type="application/json" class="multi-select-dados">
 *              [{"id": "1", "texto": "Ana Pimentel", "selecionado": true}]
 *          </script>
 *      </div>
 *
 * Envia <input type="hidden" name="{data-nome}"> por selecionado — mesmo formato
 * do select multiple, então as views não mudam.
 */
(function () {
    'use strict';

    // Ignora acentos na busca: "josue" encontra "Josue"
    function normalizar(texto) {
        return texto.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
    }

    function inicial(texto) {
        return (texto.trim()[0] || '?').toUpperCase();
    }

    class CampoMembros {
        constructor(raiz) {
            this.raiz = raiz;
            this.nome = raiz.dataset.nome;
            this.placeholder = raiz.dataset.placeholder || 'Digite um nome...';

            const dados = raiz.querySelector('.multi-select-dados');
            this.opcoes = JSON.parse(dados.textContent);
            this.selecionados = new Set(
                this.opcoes.filter((o) => o.selecionado).map((o) => String(o.id))
            );

            this.aberto = false;
            this.indiceAtivo = 0;
            this.montar();
        }

        montar() {
            this.raiz.innerHTML = '';
            this.raiz.classList.add('ms-raiz');

            // Caixa que agrupa os chips + o input de digitação
            this.caixa = document.createElement('div');
            this.caixa.className = 'ms-caixa';
            this.raiz.appendChild(this.caixa);

            this.chips = document.createElement('div');
            this.chips.className = 'ms-chips';
            this.caixa.appendChild(this.chips);

            this.entrada = document.createElement('input');
            this.entrada.type = 'text';
            this.entrada.className = 'ms-entrada';
            this.entrada.placeholder = this.placeholder;
            this.entrada.autocomplete = 'off';
            this.entrada.spellcheck = false;
            this.entrada.setAttribute('role', 'combobox');
            this.entrada.setAttribute('aria-expanded', 'false');
            this.entrada.setAttribute('aria-autocomplete', 'both');
            this.caixa.appendChild(this.entrada);

            // Lista de sugestões (flutuante)
            this.painel = document.createElement('div');
            this.painel.className = 'ms-painel';
            this.painel.hidden = true;
            this.painel.setAttribute('role', 'listbox');
            this.raiz.appendChild(this.painel);

            this.campos = document.createElement('div');
            this.campos.hidden = true;
            this.raiz.appendChild(this.campos);

            this.ligarEventos();
            this.renderizarChips();
            this.renderizarCampos();
        }

        ligarEventos() {
            // Clicar em qualquer lugar da caixa foca o input
            this.caixa.addEventListener('mousedown', (e) => {
                if (e.target.closest('.ms-chip-remover')) return;
                if (e.target !== this.entrada) {
                    e.preventDefault();
                    this.entrada.focus();
                }
            });

            this.entrada.addEventListener('input', (e) => this.aoDigitar(e));
            this.entrada.addEventListener('keydown', (e) => this.aoTeclar(e));
            this.entrada.addEventListener('focus', () => this.abrir());
            this.entrada.addEventListener('blur', () => {
                // Espera o clique na sugestão acontecer antes de fechar
                setTimeout(() => {
                    if (!this.raiz.contains(document.activeElement)) this.fechar();
                }, 120);
            });

            this.reposicionar = () => {
                if (this.aberto) this.posicionarPainel();
            };
            window.addEventListener('scroll', this.reposicionar, true);
            window.addEventListener('resize', this.reposicionar);
        }

        /*
         * Autocomplete inline: completa o restante do nome e deixa o trecho
         * completado selecionado, para que continuar digitando o sobrescreva.
         * Só completa ao inserir texto (não ao apagar), senão trava o Backspace.
         */
        aoDigitar(evento) {
            const apagando = evento.inputType && evento.inputType.startsWith('delete');
            const digitado = this.entrada.value;

            this.indiceAtivo = 0;
            this.abrir();
            this.renderizarPainel();

            if (apagando || !digitado.trim()) return;

            const sugestao = this.sugestoes()[0];
            if (!sugestao) return;

            const alvo = sugestao.texto;
            if (normalizar(alvo).startsWith(normalizar(digitado)) && alvo.length > digitado.length) {
                // Usa o nome canônico inteiro (e não o que foi digitado) para que
                // "jos" vire "Josué Costa", com maiúsculas e acentos corretos.
                this.entrada.value = alvo;
                this.entrada.setSelectionRange(digitado.length, alvo.length);
            }
        }

        aoTeclar(e) {
            const sugestoes = this.sugestoes();

            if (e.key === 'Escape') {
                e.preventDefault();
                this.entrada.value = '';
                this.fechar();
                return;
            }

            if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
                e.preventDefault();
                if (!sugestoes.length) return;
                this.abrir();
                const passo = e.key === 'ArrowDown' ? 1 : -1;
                this.indiceAtivo = (this.indiceAtivo + passo + sugestoes.length) % sugestoes.length;
                this.renderizarPainel();
                this.mostrarNaEntrada(sugestoes[this.indiceAtivo]);
                return;
            }

            // Enter/Tab confirmam a sugestão em destaque
            if (e.key === 'Enter' || e.key === 'Tab') {
                if (this.entrada.value.trim() && sugestoes.length) {
                    e.preventDefault();
                    this.adicionar(sugestoes[this.indiceAtivo] || sugestoes[0]);
                } else if (e.key === 'Enter') {
                    e.preventDefault(); // nunca submete o form sem querer
                }
                return;
            }

            // Backspace com campo vazio remove o último chip
            if (e.key === 'Backspace' && !this.entrada.value) {
                const ids = [...this.selecionados];
                if (ids.length) {
                    this.selecionados.delete(ids[ids.length - 1]);
                    this.aposMudanca();
                }
            }
        }

        mostrarNaEntrada(opcao) {
            this.entrada.value = opcao.texto;
            this.entrada.setSelectionRange(opcao.texto.length, opcao.texto.length);
        }

        // Candidatos: ainda não escolhidos, ordenados por "começa com" antes de "contém"
        sugestoes() {
            const termo = normalizar(this.entrada.value.trim());
            const disponiveis = this.opcoes.filter((o) => !this.selecionados.has(String(o.id)));
            if (!termo) return disponiveis;

            const comeca = [];
            const contem = [];
            disponiveis.forEach((o) => {
                const alvo = normalizar(o.texto);
                if (alvo.startsWith(termo)) comeca.push(o);
                else if (alvo.includes(termo)) contem.push(o);
            });
            return comeca.concat(contem);
        }

        adicionar(opcao) {
            this.selecionados.add(String(opcao.id));
            this.entrada.value = '';
            this.indiceAtivo = 0;
            this.aposMudanca();
            this.renderizarPainel();
            this.entrada.focus();
        }

        remover(id) {
            this.selecionados.delete(String(id));
            this.aposMudanca();
            if (this.aberto) this.renderizarPainel();
        }

        aposMudanca() {
            this.renderizarChips();
            this.renderizarCampos();
        }

        abrir() {
            if (this.aberto) return;
            document.querySelectorAll('.ms-raiz.ms-aberto').forEach((outro) => {
                if (outro !== this.raiz && outro._campoMembros) outro._campoMembros.fechar();
            });
            this.aberto = true;
            this.painel.hidden = false;
            this.raiz.classList.add('ms-aberto');
            this.entrada.setAttribute('aria-expanded', 'true');
            this.renderizarPainel();
            this.posicionarPainel();
        }

        fechar() {
            this.aberto = false;
            this.painel.hidden = true;
            this.raiz.classList.remove('ms-aberto');
            this.entrada.setAttribute('aria-expanded', 'false');
        }

        /*
         * position:fixed porque a tabela da escala vive num overflow-x-auto que
         * recortaria um painel absoluto. Coordenadas recalculadas a cada abertura
         * e durante scroll/resize.
         */
        posicionarPainel() {
            const caixa = this.caixa.getBoundingClientRect();
            const altura = this.painel.offsetHeight || 220;
            const espacoAbaixo = window.innerHeight - caixa.bottom;
            const largura = Math.max(caixa.width, 220);

            this.painel.style.width = `${largura}px`;
            this.painel.style.left = `${Math.min(caixa.left, window.innerWidth - largura - 8)}px`;
            this.painel.style.top = (espacoAbaixo < altura + 12 && caixa.top > espacoAbaixo)
                ? `${caixa.top - altura - 4}px`
                : `${caixa.bottom + 4}px`;
        }

        renderizarChips() {
            this.chips.innerHTML = '';
            this.opcoes
                .filter((o) => this.selecionados.has(String(o.id)))
                .forEach((o) => this.chips.appendChild(this.criarChip(o)));
            this.raiz.classList.toggle('ms-vazio', this.selecionados.size === 0);
        }

        criarChip(opcao) {
            const chip = document.createElement('span');
            chip.className = 'ms-chip';

            const avatar = document.createElement('span');
            avatar.className = 'ms-chip-avatar';
            avatar.textContent = inicial(opcao.texto);
            chip.appendChild(avatar);

            const nome = document.createElement('span');
            nome.className = 'ms-chip-nome';
            nome.textContent = opcao.texto;
            chip.appendChild(nome);

            const remover = document.createElement('button');
            remover.type = 'button';
            remover.className = 'ms-chip-remover';
            remover.innerHTML = '<i class="fa-solid fa-xmark"></i>';
            remover.setAttribute('aria-label', `Remover ${opcao.texto}`);
            remover.addEventListener('click', (e) => {
                e.stopPropagation();
                this.remover(opcao.id);
                this.entrada.focus();
            });
            chip.appendChild(remover);

            return chip;
        }

        renderizarPainel() {
            const sugestoes = this.sugestoes();
            this.painel.innerHTML = '';

            if (!sugestoes.length) {
                const vazio = document.createElement('p');
                vazio.className = 'ms-sem-resultado';
                vazio.textContent = this.entrada.value.trim()
                    ? 'Nenhum membro encontrado.'
                    : 'Todos os membros já foram adicionados.';
                this.painel.appendChild(vazio);
                return;
            }

            const dica = document.createElement('p');
            dica.className = 'ms-dica';
            dica.innerHTML = '<i class="fa-solid fa-keyboard"></i> Enter ou Tab para adicionar';
            this.painel.appendChild(dica);

            const lista = document.createElement('div');
            lista.className = 'ms-lista';
            this.painel.appendChild(lista);

            const termo = this.entrada.value.trim();
            sugestoes.slice(0, 30).forEach((opcao, indice) => {
                const item = document.createElement('div');
                item.className = 'ms-item';
                item.setAttribute('role', 'option');
                item.setAttribute('aria-selected', indice === this.indiceAtivo ? 'true' : 'false');
                if (indice === this.indiceAtivo) item.classList.add('ms-item-ativo');

                const avatar = document.createElement('span');
                avatar.className = 'ms-item-avatar';
                avatar.textContent = inicial(opcao.texto);
                item.appendChild(avatar);

                const rotulo = document.createElement('span');
                rotulo.className = 'ms-item-texto';
                rotulo.appendChild(this.destacar(opcao.texto, termo));
                item.appendChild(rotulo);

                if (indice === this.indiceAtivo) {
                    const tecla = document.createElement('span');
                    tecla.className = 'ms-item-tecla';
                    tecla.textContent = 'Enter';
                    item.appendChild(tecla);
                }

                item.addEventListener('mouseenter', () => {
                    this.indiceAtivo = indice;
                    this.renderizarPainel();
                });
                // mousedown: dispara antes do blur do input
                item.addEventListener('mousedown', (e) => {
                    e.preventDefault();
                    this.adicionar(opcao);
                });

                lista.appendChild(item);
            });
        }

        // Grifa o trecho que casa com o que foi digitado
        destacar(texto, termo) {
            const frag = document.createDocumentFragment();
            const pos = termo ? normalizar(texto).indexOf(normalizar(termo)) : -1;
            if (pos === -1) {
                frag.appendChild(document.createTextNode(texto));
                return frag;
            }
            frag.appendChild(document.createTextNode(texto.slice(0, pos)));
            const marca = document.createElement('mark');
            marca.className = 'ms-marca';
            marca.textContent = texto.slice(pos, pos + termo.length);
            frag.appendChild(marca);
            frag.appendChild(document.createTextNode(texto.slice(pos + termo.length)));
            return frag;
        }

        renderizarCampos() {
            this.campos.innerHTML = '';
            this.selecionados.forEach((id) => {
                const campo = document.createElement('input');
                campo.type = 'hidden';
                campo.name = this.nome;
                campo.value = id;
                this.campos.appendChild(campo);
            });
        }
    }

    function iniciar(escopo) {
        (escopo || document).querySelectorAll('.multi-select').forEach((raiz) => {
            if (raiz._campoMembros) return;
            raiz._campoMembros = new CampoMembros(raiz);
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => iniciar(document));
    } else {
        iniciar(document);
    }

    document.addEventListener('htmx:afterSwap', (e) => iniciar(e.target));

    window.PotiMakerMultiSelect = { iniciar };
})();

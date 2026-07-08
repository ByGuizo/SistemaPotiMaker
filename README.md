# FabLab PotiMaker — Sistema de Gerenciamento

Sistema web de gestão para o **Laboratório de Inovação e Prototipagem (FabLab) do IFRN Campus Canguaretama**. Centraliza o controle de inventário, projetos, membros, agenda de eventos e a escala de horários do laboratório em um só lugar, com uma identidade visual própria (estilo neo-brutalista, cores vibrantes e animações lúdicas).

> "Faça você mesmo, seja um maker."

---

## Sumário

- [Visão geral](#visão-geral)
- [Funcionalidades](#funcionalidades)
- [Stack técnica](#stack-técnica)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Modelo de permissões](#modelo-de-permissões)
- [Como rodar localmente](#como-rodar-localmente)
- [Dados de exemplo (seed)](#dados-de-exemplo-seed)
- [Identidade visual](#identidade-visual)
- [Roadmap / próximos passos](#roadmap--próximos-passos)

---

## Visão geral

O PotiMaker é um sistema Django multi-app pensado para o dia a dia de um laboratório maker escolar: quem está presente, o que tem no inventário, em que pé estão os projetos, quando são os próximos eventos. O acesso é restrito a membros cadastrados — não há área pública, exceto a tela de login.

Existem dois papéis de usuário:

- **Coordenador** — acesso total, incluindo exclusão de itens/projetos/eventos/membros, cadastro de novos membros e edição da escala de horários do laboratório.
- **Membro** — pode navegar por todas as telas, cadastrar e editar itens de inventário, projetos e eventos da agenda. Não pode excluir registros, gerenciar outros membros nem editar a escala de horários.

---

## Funcionalidades

### Dashboard
Painel inicial com contadores (membros ativos, projetos em andamento, itens no inventário, eventos da semana), atalhos de acesso rápido, o card "Quem deve estar agora" (com base na escala de horários) e o status do laboratório (aberto/fechado, membros com entrada registrada no dia, próximo evento) — tudo atualizado via HTMX sem recarregar a página.

### Inventário
Cadastro de itens (equipamentos, ferramentas, consumíveis, componentes eletrônicos) com categoria, quantidade e status (disponível / em uso / em manutenção). Busca e filtros em tempo real.

### Projetos (Kanban)
Quadro Kanban com três colunas — *A Fazer*, *Fazendo*, *Concluído*. Cada projeto tem prioridade, prazo, descrição, membros responsáveis e documento técnico anexável. Mover um card entre colunas é feito com um clique, via HTMX.

### Membros
Listagem e cadastro de membros do laboratório, com busca por nome/e-mail e filtro por tipo (coordenador/membro). Apenas coordenadores podem criar, editar ou excluir membros.

### Agenda
Calendário mensal nativo (implementado com o módulo `calendar` do Python, sem dependência de bibliotecas de calendário em JS), com navegação entre meses e painel lateral de eventos do dia selecionado.

### Perfil do usuário
Cada usuário logado pode acessar seu próprio perfil (clicando no nome no canto superior do header) para ver seus dados, os projetos em que está envolvido e seu histórico de entradas registradas.

### Escala de horários
Grade fixa semanal (5 dias úteis × 6 horários, replicando o cronograma da equipe gestora do laboratório) que define quem deve estar presente em cada horário. O dashboard mostra automaticamente quem está escalado para o momento atual no card "Quem deve estar agora". Apenas coordenadores podem editar a escala completa, atribuindo um ou mais membros a cada célula da grade.

### Status do laboratório
Card independente da escala de horários: deriva "aberto/fechado" e a contagem de membros com entrada registrada no dia a partir do histórico real de presença (`RegistroPresenca`) — mostra o que *de fato* aconteceu, enquanto a escala de horários mostra o que *deveria* acontecer.

---

## Stack técnica

| Camada | Tecnologia |
|---|---|
| Backend | Django 6.0 (Python) |
| Banco de dados (dev) | SQLite |
| Frontend | Django Templates + Tailwind CSS (via CDN) |
| Interatividade | HTMX (fragmentos de HTML renderizados no servidor, sem SPA) |
| Ícones | Font Awesome 6 |
| Tipografia | Space Grotesk (títulos) + Manrope (corpo), via Google Fonts |

Não há build step de frontend (sem Webpack/Vite/npm) — Tailwind, HTMX e Font Awesome são carregados via CDN, o que mantém o projeto simples de rodar e implantar.

---

## Estrutura do projeto

```
SistemaPotiMaker/        # pacote de configuração Django (settings, urls, wsgi/asgi)
core/                    # dashboard agregador, template tags de badges, comando de seed
usuarios/                # model de usuário customizado, autenticação, presença, perfil
inventario/              # modelo e views de itens do inventário
projetos/                # modelo e views do Kanban de projetos
agenda/                  # modelo e views do calendário/eventos
templates/               # base.html e partials compartilhados entre apps
static/                  # CSS customizado, config do Tailwind, HTMX local
```

Cada app de domínio (`usuarios`, `inventario`, `projetos`, `agenda`) segue o mesmo padrão: `models.py`, `forms.py`, `views.py`, `urls.py`, e templates próprios em `app/templates/app/`. Views que respondem a requisições HTMX retornam apenas o fragmento HTML relevante; requisições normais recebem a página completa estendendo `base.html`.

---

## Modelo de permissões

A autenticação é obrigatória em todo o sistema (via `usuarios.middleware.LoginObrigatorioMiddleware`), exceto na tela de login e no admin do Django.

| Ação | Membro | Coordenador |
|---|:---:|:---:|
| Visualizar dashboard, inventário, projetos, membros, agenda | ✅ | ✅ |
| Cadastrar/editar itens do inventário | ✅ | ✅ |
| Cadastrar/editar projetos | ✅ | ✅ |
| Cadastrar/editar eventos da agenda | ✅ | ✅ |
| Mover projetos no Kanban | ✅ | ✅ |
| Ver e editar o próprio perfil | ✅ | ✅ |
| Excluir itens, projetos ou eventos | ❌ | ✅ |
| Cadastrar, editar ou excluir membros | ❌ | ✅ |
| Editar a escala de horários do laboratório | ❌ | ✅ |

---

## Como rodar localmente

Pré-requisitos: Python 3.11+ e um ambiente virtual.

```powershell
# 1. Criar e ativar o ambiente virtual
python -m venv venv
venv\Scripts\activate

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Aplicar as migrations
python manage.py migrate

# 4. Criar um superusuário (acesso ao /admin/)
python manage.py createsuperuser

# 5. (Opcional) Popular com dados de exemplo
python manage.py seed_demo

# 6. Rodar o servidor de desenvolvimento
python manage.py runserver
```

Acesse `http://127.0.0.1:8000/`. Todo o sistema exige login — use o superusuário criado ou um dos usuários do seed.

---

## Dados de exemplo (seed)

O comando `python manage.py seed_demo` popula o banco com usuários, itens de inventário, projetos, eventos, registros de presença e a escala de horários de exemplo — útil para testar o sistema sem precisar cadastrar tudo manualmente. É idempotente (pode ser rodado mais de uma vez sem duplicar dados).

Todos os usuários criados pelo seed têm a senha `potimaker123`.

---

## Identidade visual

O design segue uma linha **neo-brutalista**: bordas pretas grossas, sombras sólidas ("brutal shadows"), paleta vibrante (roxo, fúcsia, amarelo, verde-água) sobre um fundo bege pontilhado. As interações têm animações expressivas — cards que saltam ao hover, entradas em cascata, badges com pulso sutil — para dar uma sensação mais lúdica e "maker" ao sistema. A tela de login tem um design próprio, independente do restante do sistema, com fundo em gradiente animado e formas flutuantes.

O layout base usa um sticky footer (`body` como flex container em coluna, `main` com `flex-1`): o rodapé fica sempre fixado ao final da página em todas as telas, independentemente da quantidade de conteúdo.

---

## Roadmap / próximos passos

- [ ] Migrar de SQLite para PostgreSQL para uso em produção
- [ ] Configurar variáveis de ambiente para `SECRET_KEY` e `DEBUG`
- [ ] Deploy em produção (domínio próprio + HTTPS)
- [ ] Backups automáticos do banco de dados

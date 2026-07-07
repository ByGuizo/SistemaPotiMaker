from django import template

register = template.Library()

CORES_STATUS_ITEM = {
    'DISPONIVEL': 'bg-emerald-400',
    'EM_USO': 'bg-yellow-300',
    'MANUTENCAO': 'bg-red-400',
}
ICONES_STATUS_ITEM = {
    'DISPONIVEL': 'fa-solid fa-circle-check',
    'EM_USO': 'fa-solid fa-hourglass-half',
    'MANUTENCAO': 'fa-solid fa-screwdriver-wrench',
}

CORES_CATEGORIA_ITEM = {
    'ELETRONICO': 'bg-fuchsia-400 text-white',
    'FERRAMENTA': 'bg-purple-500 text-white',
    'CONSUMIVEL': 'bg-white',
    'EQUIPAMENTO': 'bg-yellow-300',
}
ICONES_CATEGORIA_ITEM = {
    'ELETRONICO': 'fa-solid fa-microchip',
    'FERRAMENTA': 'fa-solid fa-wrench',
    'CONSUMIVEL': 'fa-solid fa-flask',
    'EQUIPAMENTO': 'fa-solid fa-print',
}

CORES_PRIORIDADE = {
    'BAIXA': 'bg-emerald-400',
    'MEDIA': 'bg-yellow-300',
    'ALTA': 'bg-red-400',
}
ICONES_PRIORIDADE = {
    'BAIXA': 'fa-solid fa-arrow-down',
    'MEDIA': 'fa-solid fa-equals',
    'ALTA': 'fa-solid fa-arrow-up',
}

CORES_TIPO_USUARIO = {
    'COORD': 'bg-fuchsia-500 text-white',
    'MEMBRO': 'bg-emerald-400',
}
ICONES_TIPO_USUARIO = {
    'COORD': 'fa-solid fa-star',
    'MEMBRO': 'fa-solid fa-user',
}

MAPAS = {
    'status_item': CORES_STATUS_ITEM,
    'categoria_item': CORES_CATEGORIA_ITEM,
    'prioridade': CORES_PRIORIDADE,
    'tipo_usuario': CORES_TIPO_USUARIO,
}

ICONES = {
    'status_item': ICONES_STATUS_ITEM,
    'categoria_item': ICONES_CATEGORIA_ITEM,
    'prioridade': ICONES_PRIORIDADE,
    'tipo_usuario': ICONES_TIPO_USUARIO,
}


@register.inclusion_tag('partials/_badge.html')
def badge(valor, mapa, rotulo=None):
    cor = MAPAS.get(mapa, {}).get(valor, 'bg-gray-200')
    icone = ICONES.get(mapa, {}).get(valor, '')
    return {'rotulo': rotulo or valor, 'cor': cor, 'icone': icone}

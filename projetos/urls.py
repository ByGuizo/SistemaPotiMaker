from django.urls import path

from . import views

app_name = 'projetos'

urlpatterns = [
    path('', views.kanban, name='kanban'),
    path('atividades/nova/', views.nova_atividade, name='nova_atividade'),
    path('atividades/<int:pk>/editar/', views.editar_atividade, name='editar_atividade'),
    path('atividades/<int:pk>/excluir/', views.excluir_atividade, name='excluir_atividade'),
    path('atividades/<int:pk>/mover/<str:direcao>/', views.mover_atividade, name='mover_atividade'),
    path('lista/', views.lista_projetos, name='lista_projetos'),
    path('novo/', views.novo_projeto, name='novo_projeto'),
    path('<int:pk>/editar/', views.editar_projeto, name='editar_projeto'),
    path('<int:pk>/excluir/', views.excluir_projeto, name='excluir_projeto'),
]

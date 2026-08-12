from django.urls import path

from . import views

app_name = 'usuarios'

urlpatterns = [
    path('login/', views.PotiMakerLoginView.as_view(), name='login'),
    path('logout/', views.PotiMakerLogoutView.as_view(), name='logout'),
    path('cadastro/', views.cadastro, name='cadastro'),
    path('perfil/', views.perfil, name='perfil'),
    path('membros/', views.lista_membros, name='lista_membros'),
    path('membros/<int:pk>/editar/', views.editar_membro, name='editar_membro'),
    path('membros/<int:pk>/excluir/', views.excluir_membro, name='excluir_membro'),
    path('cadastros/<int:pk>/aprovar/', views.aprovar_cadastro, name='aprovar_cadastro'),
    path('cadastros/<int:pk>/negar/', views.negar_cadastro, name='negar_cadastro'),
    path('horarios/editar/', views.editar_horarios, name='editar_horarios'),
]

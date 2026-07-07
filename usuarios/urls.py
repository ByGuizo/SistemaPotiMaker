from django.urls import path

from . import views

app_name = 'usuarios'

urlpatterns = [
    path('login/', views.PotiMakerLoginView.as_view(), name='login'),
    path('logout/', views.PotiMakerLogoutView.as_view(), name='logout'),
    path('perfil/', views.perfil, name='perfil'),
    path('membros/', views.lista_membros, name='lista_membros'),
    path('membros/novo/', views.novo_membro, name='novo_membro'),
    path('membros/<int:pk>/editar/', views.editar_membro, name='editar_membro'),
    path('membros/<int:pk>/excluir/', views.excluir_membro, name='excluir_membro'),
    path('presenca/registrar/', views.registrar_presenca, name='registrar_presenca'),
]

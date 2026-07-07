from django.urls import path

from . import views

app_name = 'inventario'

urlpatterns = [
    path('', views.lista_itens, name='lista_itens'),
    path('novo/', views.novo_item, name='novo_item'),
    path('<int:pk>/editar/', views.editar_item, name='editar_item'),
    path('<int:pk>/excluir/', views.excluir_item, name='excluir_item'),
]

from django.urls import path
from prediction import views

urlpatterns = [
    path('', views.index, name='index'),  # トップページ
    path('search/', views.search, name='search'),  # 検索結果ページ
]

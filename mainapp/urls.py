from django.urls import path, include, re_path
from .views import *
from rest_framework import routers


router = routers.DefaultRouter()
router.register(r'country', CountryAPIViewSet)


urlpatterns = [
    path('', ProfilesView.as_view(), name='index'),
    path('register/', RegisterUser.as_view(), name='register'),
    path('login/', LoginUser.as_view(), name='slogin'),
    path('logout/', logout_user, name='slogout'),
    path('profile/<int:profile_id>/', ProfileView.as_view(), name='profile'),
    path('profile-redacting/<int:profile_id>/', ProfileUpdateView.as_view(), name='profile-redacting'),
    path('profile-language-level/<int:profile_id>/<int:language>/', LanguageLevelUpdateView.as_view(), name='profile-language-level'),

    #API pathes
    path('api/v1/', include(router.urls)),
    path('api/v1/auth/', include('djoser.urls')),
    re_path(r'auth/', include('djoser.urls.authtoken'))

]


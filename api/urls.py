from . import views
from django.urls import include, path
from rest_framework_nested import routers

router = routers.DefaultRouter()
router.register('accounts', views.AccountViewSet)
router.register('appointments', views.AppointmentViewSet,
                basename='appointments')
router.register('centers', views.VaccinationCenterViewSet)
router.register('records', views.VaccinationRecordViewSet)
router.register('statistic', views.VaxMalaysiaViewSet)

centers_router = routers.NestedDefaultRouter(
    router, 'centers', lookup='center')
centers_router.register(
    'timeslots', views.VaccinationTimeslotViewSet, basename='center-timeslots')

urlpatterns = router.urls + centers_router.urls

urlpatterns += [path('auth/jwt/create', views.CustomTokenObtainPairView.as_view(),
                     name='token_obtain_pair'),
                path('auth/', include('djoser.urls')),
                path('auth/', include('djoser.urls.jwt'))]

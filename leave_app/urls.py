from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.utils import extend_schema, extend_schema_view
from drf_spectacular.types import OpenApiTypes
from .views import UserViewSet, LeaveRequestViewSet, LeaveTransitionViewSet

# Extend JWT views with Swagger documentation
@extend_schema_view(
    post=extend_schema(
        summary="Obtain JWT token",
        description="Authenticate user and obtain JWT access and refresh tokens.",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'username': {'type': 'string', 'description': 'User username'},
                    'password': {'type': 'string', 'description': 'User password'}
                },
                'required': ['username', 'password']
            }
        },
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'access': {'type': 'string', 'description': 'JWT access token'},
                    'refresh': {'type': 'string', 'description': 'JWT refresh token'}
                }
            },
            401: OpenApiTypes.OBJECT
        },
        tags=["Authentication"]
    )
)
class DocumentedTokenObtainPairView(TokenObtainPairView):
    pass

@extend_schema_view(
    post=extend_schema(
        summary="Refresh JWT token",
        description="Refresh JWT access token using refresh token.",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'refresh': {'type': 'string', 'description': 'JWT refresh token'}
                },
                'required': ['refresh']
            }
        },
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'access': {'type': 'string', 'description': 'New JWT access token'}
                }
            },
            401: OpenApiTypes.OBJECT
        },
        tags=["Authentication"]
    )
)
class DocumentedTokenRefreshView(TokenRefreshView):
    pass

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'leaves', LeaveRequestViewSet, basename='leave')
router.register(r'audit-log', LeaveTransitionViewSet, basename='audit-log')

urlpatterns = [
    path('auth/token/', DocumentedTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', DocumentedTokenRefreshView.as_view(), name='token_refresh'),
    path('', include(router.urls)),
] 
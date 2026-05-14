"""
Custom middleware for API versioning and loyalty program features
"""
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token
from rest_framework import status
import json


class APIVersioningMiddleware(MiddlewareMixin):
    """
    Middleware to handle API versioning and enforce version compatibility.
    """
    
    SUPPORTED_VERSIONS = ['v1']
    DEFAULT_VERSION = 'v1'
    
    def process_request(self, request):
        # Only apply to API requests
        if not request.path.startswith('/api/'):
            return None
            
        # Extract version from URL or header
        version = self.get_api_version(request)
        
        # Validate version
        if version not in self.SUPPORTED_VERSIONS:
            return JsonResponse({
                'error': f'API version {version} is not supported',
                'supported_versions': self.SUPPORTED_VERSIONS,
                'message': f'Please use one of the supported API versions: {", ".join(self.SUPPORTED_VERSIONS)}'
            }, status=400)
        
        # Set version in request for later use
        request.api_version = version
        return None
    
    def get_api_version(self, request):
        """Extract API version from request"""
        # Try to get from URL path (e.g., /api/v1/...)
        path_parts = request.path.strip('/').split('/')
        if len(path_parts) >= 2 and path_parts[1].startswith('v'):
            return path_parts[1]
        
        # Try to get from header
        version = request.META.get('HTTP_API_VERSION')
        if version:
            return version
        
        # Try to get from query parameter
        version = request.GET.get('version')
        if version:
            return version
        
        # Return default version
        return self.DEFAULT_VERSION


class LoyaltyMembershipMiddleware(MiddlewareMixin):
    """
    Middleware to attach loyalty membership information to authenticated users.
    """
    
    def process_request(self, request):
        # Only process for authenticated users on loyalty endpoints
        if (not request.user.is_authenticated or 
            not request.path.startswith('/api/loyalty/')):
            return None
            
        try:
            from .models import LoyaltyMembership
            membership = LoyaltyMembership.objects.select_related('tier').get(
                user=request.user
            )
            request.loyalty_membership = membership
        except LoyaltyMembership.DoesNotExist:
            request.loyalty_membership = None
            
        return None


class RateLimitMiddleware(MiddlewareMixin):
    """
    Custom rate limiting middleware with tier-based limits.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        # Only apply to API requests
        if not request.path.startswith('/api/'):
            return None
            
        # Check rate limits based on user tier
        if hasattr(request, 'user') and request.user.is_authenticated:
            if not self.check_tier_based_rate_limit(request):
                return JsonResponse({
                    'error': 'Rate limit exceeded',
                    'message': 'You have exceeded the API rate limit for your tier',
                    'retry_after': 3600  # 1 hour
                }, status=429)
        
        return None
    
    def check_tier_based_rate_limit(self, request):
        """Check rate limits based on user's loyalty tier"""
        # For now, return True - in production, implement Redis-based rate limiting
        # with different limits per tier
        return True


class APISecurityMiddleware(MiddlewareMixin):
    """
    Security middleware for API requests.
    """
    
    def process_request(self, request):
        # Only apply to API requests
        if not request.path.startswith('/api/'):
            return None
            
        # Add security headers
        response = None
        
        # Validate content type for POST/PUT/PATCH requests
        if request.method in ['POST', 'PUT', 'PATCH']:
            content_type = request.META.get('CONTENT_TYPE', '')
            if not content_type.startswith('application/json'):
                # Allow form data for some endpoints
                allowed_form_endpoints = ['/api/auth/', '/api/token/']
                if not any(request.path.startswith(ep) for ep in allowed_form_endpoints):
                    return JsonResponse({
                        'error': 'Invalid content type',
                        'message': 'API requests must use application/json content type'
                    }, status=400)
        
        return response
    
    def process_response(self, request, response):
        # Add security headers to API responses
        if request.path.startswith('/api/'):
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'DENY'
            response['X-XSS-Protection'] = '1; mode=block'
            response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response


class APILoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log API requests and responses.
    """
    
    def process_request(self, request):
        # Only log API requests
        if not request.path.startswith('/api/'):
            return None
        
        # Log API request details
        import logging
        logger = logging.getLogger('api')
        
        logger.info(f'API Request: {request.method} {request.path}', extra={
            'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
            'ip': self.get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'api_version': getattr(request, 'api_version', 'unknown'),
        })
        
        return None
    
    def process_response(self, request, response):
        # Log API response
        if request.path.startswith('/api/'):
            import logging
            logger = logging.getLogger('api')
            
            logger.info(f'API Response: {response.status_code}', extra={
                'path': request.path,
                'method': request.method,
                'status_code': response.status_code,
                'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
            })
        
        return response
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class TokenAuthenticationMiddleware(MiddlewareMixin):
    """
    Custom token authentication middleware for API requests.
    """
    
    def process_request(self, request):
        # Only apply to API requests
        if not request.path.startswith('/api/'):
            return None
        
        # Skip authentication for public endpoints
        public_endpoints = [
            '/api/docs/',
            '/api/redoc/',
            '/api/swagger.json',
            '/api/swagger.yaml',
            '/api/loyalty/tiers/public/',
            '/api/loyalty/rewards/public/',
            '/api/loyalty/promotions/public/',
        ]
        
        if any(request.path.startswith(ep) for ep in public_endpoints):
            return None
        
        # Check for token authentication
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Token '):
            token_key = auth_header.split(' ')[1]
            try:
                token = Token.objects.select_related('user').get(key=token_key)
                request.user = token.user
            except Token.DoesNotExist:
                return JsonResponse({
                    'error': 'Invalid token',
                    'message': 'The provided authentication token is invalid'
                }, status=401)
        
        return None


class CORSMiddleware(MiddlewareMixin):
    """
    Custom CORS middleware for API requests.
    """
    
    def process_response(self, request, response):
        # Only apply to API requests
        if request.path.startswith('/api/'):
            # Allow specific origins in production
            allowed_origins = [
                'http://localhost:3000',  # React dev server
                'http://localhost:8000',  # Django dev server
                'https://novaryo.com',    # Production domain
            ]
            
            origin = request.META.get('HTTP_ORIGIN')
            if origin in allowed_origins:
                response['Access-Control-Allow-Origin'] = origin
            
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = (
                'Accept, Accept-Language, Content-Language, Content-Type, '
                'Authorization, X-Requested-With, X-CSRFToken'
            )
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Max-Age'] = '86400'  # 24 hours
        
        return response


class HealthCheckMiddleware(MiddlewareMixin):
    """
    Middleware to handle health check endpoints.
    """
    
    def process_request(self, request):
        if request.path == '/api/health/':
            from django.db import connection
            from django.core.cache import cache
            
            health_status = {
                'status': 'healthy',
                'timestamp': timezone.now().isoformat(),
                'version': getattr(request, 'api_version', 'v1'),
                'services': {}
            }
            
            # Check database connection
            try:
                with connection.cursor() as cursor:
                    cursor.execute('SELECT 1')
                health_status['services']['database'] = 'healthy'
            except Exception as e:
                health_status['services']['database'] = f'unhealthy: {str(e)}'
                health_status['status'] = 'unhealthy'
            
            # Check cache connection
            try:
                cache.get('health_check')
                health_status['services']['cache'] = 'healthy'
            except Exception as e:
                health_status['services']['cache'] = f'unhealthy: {str(e)}'
            
            return JsonResponse(health_status)
        
        return None
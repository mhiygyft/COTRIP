"""
Swagger/OpenAPI documentation settings for COTRIPVn API
"""
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

# API Schema configuration
schema_view = get_schema_view(
    openapi.Info(
        title="COTRIPVn Travel Platform API",
        default_version='v1',
        description="""
        # COTRIPVn Travel Platform REST API
        
        **"Plan smarter. Travel better with COTRIPVn."**
        
        Complete RESTful API for the COTRIPVn travel booking platform with integrated loyalty program.
        
        ## Features
        
        ### 🏆 Loyalty Program API
        - **Tiers & Memberships**: Manage loyalty tiers and user memberships
        - **Points System**: Track points transactions, earnings, and redemptions  
        - **Rewards Catalog**: Browse and redeem rewards with points
        - **Promotions**: Access active promotions and bonus campaigns
        - **Analytics**: Get detailed statistics and tier progress
        
        ### 🔐 Authentication
        - Token-based authentication
        - Session authentication for web clients
        - Permission-based access control
        
        ### 📊 Features
        - Comprehensive filtering and search capabilities
        - Pagination for large datasets
        - Bulk operations for administrative tasks
        - Real-time data validation
        - Detailed error responses
        
        ## Getting Started
        
        ### Authentication
        Most endpoints require authentication. Include your authentication token in the header:
        ```
        Authorization: Token your-token-here
        ```
        
        ### Public Endpoints
        Some endpoints are publicly accessible without authentication:
        - `/api/loyalty/tiers/public/` - Public tier information
        - `/api/loyalty/rewards/public/` - Public rewards catalog
        - `/api/loyalty/promotions/public/` - Public promotions
        
        ### Pagination
        List endpoints support pagination with `page` and `page_size` parameters:
        ```
        GET /api/loyalty/rewards/?page=2&page_size=20
        ```
        
        ### Filtering
        Most endpoints support filtering via query parameters:
        ```
        GET /api/loyalty/transactions/?transaction_type=earn&points__gte=100
        ```
        
        ### Error Handling
        The API returns standard HTTP status codes with detailed error messages:
        - `200 OK` - Successful request
        - `201 Created` - Resource created successfully
        - `400 Bad Request` - Invalid request data
        - `401 Unauthorized` - Authentication required
        - `403 Forbidden` - Insufficient permissions
        - `404 Not Found` - Resource not found
        - `500 Internal Server Error` - Server error
        
        ## Rate Limiting
        API requests are rate-limited to ensure fair usage:
        - **Authenticated users**: 1000 requests/hour
        - **Anonymous users**: 100 requests/hour
        
        ## Support
        For API support, contact: api-support@cotripvn.com
        """,
        terms_of_service="https://cotripvn.com/terms/",
        contact=openapi.Contact(
            name="COTRIPVn API Team",
            email="api-support@cotripvn.com",
            url="https://cotripvn.com/contact/"
        ),
        license=openapi.License(
            name="MIT License",
            url="https://opensource.org/licenses/MIT"
        ),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    authentication_classes=[],
)

# Custom API documentation settings
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Token Authentication': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': 'Enter: Token your-token-here'
        },
        'Session Authentication': {
            'type': 'apiKey',
            'name': 'sessionid',
            'in': 'cookie',
            'description': 'Django session authentication'
        }
    },
    'USE_SESSION_AUTH': True,
    'JSON_EDITOR': True,
    'SUPPORTED_SUBMIT_METHODS': [
        'get',
        'post',
        'put',
        'delete',
        'patch'
    ],
    'OPERATIONS_SORTER': 'alpha',
    'TAGS_SORTER': 'alpha',
    'DOC_EXPANSION': 'none',
    'DEEP_LINKING': True,
    'SHOW_EXTENSIONS': True,
    'DEFAULT_MODEL_RENDERING': 'model',
    'VALIDATOR_URL': None,
}

# ReDoc settings
REDOC_SETTINGS = {
    'LAZY_RENDERING': True,
    'HIDE_HOSTNAME': False,
    'EXPAND_RESPONSES': ['200', '201'],
    'PATH_IN_MIDDLE': True,
    'NATIVE_SCROLLBARS': False,
    'REQUIRED_PROPS_FIRST': True,
}

# API response examples
LOYALTY_API_EXAMPLES = {
    'membership_stats_response': {
        'total_points': 15420,
        'lifetime_points': 45200,
        'tier_qualifying_points': 15420,
        'current_tier': {
            'id': 2,
            'name': 'Silver',
            'color': '#C0C0C0',
            'min_points': 10000,
            'points_multiplier': 1.25
        },
        'next_tier': {
            'id': 3,
            'name': 'Gold',
            'color': '#FFD700',
            'min_points': 25000,
            'points_multiplier': 1.5
        },
        'points_to_next_tier': 9580,
        'tier_expires_at': '2025-12-31T23:59:59Z',
        'total_redemptions': 8,
        'last_activity': '2024-09-26T10:30:00Z'
    },
    'points_calculation_response': {
        'base_points': 500,
        'tier_multiplier': 1.25,
        'promotion_bonus': 100,
        'total_points': 725,
        'tier_qualifying_points': 625
    },
    'reward_availability_response': [
        {
            'reward': {
                'id': 1,
                'name': '$50 Flight Credit',
                'points_required': 5000,
                'category': 'travel'
            },
            'can_redeem': True,
            'reason': None,
            'points_needed': None,
            'tier_required': None
        },
        {
            'reward': {
                'id': 2,
                'name': 'Premium Cabin Upgrade',
                'points_required': 15000,
                'category': 'travel'
            },
            'can_redeem': False,
            'reason': 'Tier requirement not met',
            'points_needed': None,
            'tier_required': {
                'id': 3,
                'name': 'Gold',
                'min_points': 25000
            }
        }
    ]
}

# Custom schema tags for better organization
API_TAGS = [
    {
        'name': 'Authentication',
        'description': 'User authentication and authorization endpoints'
    },
    {
        'name': 'Loyalty - Tiers',
        'description': 'Loyalty tier management and information'
    },
    {
        'name': 'Loyalty - Memberships', 
        'description': 'User loyalty membership management and statistics'
    },
    {
        'name': 'Loyalty - Points',
        'description': 'Points transactions and calculations'
    },
    {
        'name': 'Loyalty - Rewards',
        'description': 'Rewards catalog and redemption system'
    },
    {
        'name': 'Loyalty - Promotions',
        'description': 'Promotional campaigns and bonus offers'
    },
    {
        'name': 'Bookings',
        'description': 'Flight, hotel, and package booking management'
    },
    {
        'name': 'Users',
        'description': 'User profile and account management'
    }
]
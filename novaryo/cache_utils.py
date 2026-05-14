"""
Cache utilities and decorators for performance optimization
"""
import hashlib
import json
from functools import wraps
from typing import Any, Optional, Union, Dict

from django.core.cache import cache, caches
from django.core.cache.utils import make_template_fragment_key
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from django.conf import settings
import logging

logger = logging.getLogger('novaryo.cache')


def get_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Generate a consistent cache key from prefix and parameters.
    
    Args:
        prefix: Cache key prefix
        *args: Positional arguments to include in key
        **kwargs: Keyword arguments to include in key
    
    Returns:
        Generated cache key string
    """
    key_parts = [str(prefix)]
    
    # Add positional arguments
    for arg in args:
        if isinstance(arg, (dict, list)):
            key_parts.append(hashlib.md5(json.dumps(arg, sort_keys=True).encode()).hexdigest())
        else:
            key_parts.append(str(arg))
    
    # Add keyword arguments
    for key, value in sorted(kwargs.items()):
        if isinstance(value, (dict, list)):
            key_parts.append(f"{key}:{hashlib.md5(json.dumps(value, sort_keys=True).encode()).hexdigest()}")
        else:
            key_parts.append(f"{key}:{value}")
    
    cache_key = ':'.join(key_parts)
    logger.debug(f"Generated cache key: {cache_key}")
    return cache_key


def cache_function(timeout: int = 300, cache_alias: str = 'default', key_prefix: str = ''):
    """
    Decorator to cache function results.
    
    Args:
        timeout: Cache timeout in seconds
        cache_alias: Cache backend alias
        key_prefix: Prefix for cache key
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_backend = caches[cache_alias]
            
            # Generate cache key
            func_name = f"{func.__module__}.{func.__name__}"
            cache_key = get_cache_key(key_prefix or func_name, *args, **kwargs)
            
            # Try to get from cache
            result = cache_backend.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return result
            
            # Execute function and cache result
            logger.debug(f"Cache miss for key: {cache_key}")
            result = func(*args, **kwargs)
            cache_backend.set(cache_key, result, timeout)
            logger.debug(f"Cached result for key: {cache_key}")
            
            return result
        return wrapper
    return decorator


def cache_loyalty_data(timeout: int = 600):
    """
    Decorator specifically for caching loyalty program data.
    
    Args:
        timeout: Cache timeout in seconds (default: 10 minutes)
    """
    return cache_function(timeout=timeout, cache_alias='loyalty', key_prefix='loyalty')


def cache_api_response(timeout: int = 180):
    """
    Decorator for caching API responses.
    
    Args:
        timeout: Cache timeout in seconds (default: 3 minutes)
    """
    return cache_function(timeout=timeout, cache_alias='api', key_prefix='api')


class CacheManager:
    """
    Utility class for managing cache operations.
    """
    
    @staticmethod
    def invalidate_user_cache(user_id: int):
        """
        Invalidate all cached data for a specific user.
        
        Args:
            user_id: User ID to invalidate cache for
        """
        cache_patterns = [
            f'loyalty:user:{user_id}:*',
            f'api:user:{user_id}:*',
            f'membership:{user_id}:*',
            f'points:{user_id}:*',
            f'rewards:{user_id}:*',
        ]
        
        for pattern in cache_patterns:
            CacheManager._delete_pattern(pattern)
        
        logger.info(f"Invalidated cache for user {user_id}")
    
    @staticmethod
    def invalidate_loyalty_cache():
        """Invalidate all loyalty program cached data."""
        loyalty_cache = caches['loyalty']
        loyalty_cache.clear()
        logger.info("Cleared loyalty cache")
    
    @staticmethod
    def invalidate_api_cache():
        """Invalidate all API response cached data."""
        api_cache = caches['api']
        api_cache.clear()
        logger.info("Cleared API cache")
    
    @staticmethod
    def get_cache_stats():
        """
        Get cache statistics across all cache backends.
        
        Returns:
            Dictionary with cache statistics
        """
        stats = {}
        
        for alias, cache_backend in caches.all():
            try:
                # This would work with Redis backend
                if hasattr(cache_backend, '_cache'):
                    client = cache_backend._cache.get_client()
                    info = client.info()
                    stats[alias] = {
                        'hits': info.get('keyspace_hits', 0),
                        'misses': info.get('keyspace_misses', 0),
                        'keys': info.get('db0', {}).get('keys', 0) if 'db0' in info else 0,
                        'memory_usage': info.get('used_memory_human', '0B'),
                    }
                else:
                    stats[alias] = {'status': 'unavailable'}
            except Exception as e:
                stats[alias] = {'error': str(e)}
        
        return stats
    
    @staticmethod
    def _delete_pattern(pattern: str):
        """Delete cache keys matching pattern (Redis-specific)."""
        try:
            default_cache = cache
            if hasattr(default_cache, '_cache'):
                client = default_cache._cache.get_client()
                keys = client.keys(pattern)
                if keys:
                    client.delete(*keys)
                    logger.debug(f"Deleted {len(keys)} keys matching pattern: {pattern}")
        except Exception as e:
            logger.error(f"Error deleting cache pattern {pattern}: {e}")


def cache_template_fragment(fragment_name: str, timeout: int = 300, *vary_on):
    """
    Cache template fragments with automatic invalidation.
    
    Args:
        fragment_name: Name of the template fragment
        timeout: Cache timeout in seconds
        *vary_on: Variables to vary the cache on
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key for template fragment
            cache_key = make_template_fragment_key(fragment_name, vary_on)
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator


# Specific cache decorators for common use cases
def cache_user_loyalty_data(timeout: int = 600):
    """Cache user-specific loyalty data."""
    def decorator(func):
        @wraps(func)
        def wrapper(user_id, *args, **kwargs):
            cache_key = f"user_loyalty:{user_id}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            result = caches['loyalty'].get(cache_key)
            if result is not None:
                return result
            
            result = func(user_id, *args, **kwargs)
            caches['loyalty'].set(cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator


def cache_membership_stats(timeout: int = 300):
    """Cache membership statistics."""
    def decorator(func):
        @wraps(func)
        def wrapper(membership_id, *args, **kwargs):
            cache_key = f"membership_stats:{membership_id}"
            
            result = caches['loyalty'].get(cache_key)
            if result is not None:
                return result
            
            result = func(membership_id, *args, **kwargs)
            caches['loyalty'].set(cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator


def cache_rewards_catalog(timeout: int = 900):
    """Cache rewards catalog."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"rewards_catalog:{hash(str(args) + str(kwargs))}"
            
            result = caches['loyalty'].get(cache_key)
            if result is not None:
                return result
            
            result = func(*args, **kwargs)
            caches['loyalty'].set(cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator


# View decorators
def cached_view(timeout: int = 300, cache_alias: str = 'default'):
    """
    Decorator for caching entire view responses.
    
    Args:
        timeout: Cache timeout in seconds
        cache_alias: Cache backend alias
    """
    def decorator(view_func):
        @method_decorator(cache_page(timeout, cache=cache_alias))
        @method_decorator(vary_on_headers('User-Agent', 'Accept-Language'))
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            return view_func(*args, **kwargs)
        return wrapper
    return decorator


def cache_per_user(timeout: int = 300):
    """Cache view per user."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return view_func(request, *args, **kwargs)
            
            cache_key = f"user_view:{request.user.id}:{view_func.__name__}:{hash(str(args) + str(kwargs))}"
            
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            result = view_func(request, *args, **kwargs)
            cache.set(cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator


# Cache warming functions
def warm_loyalty_cache():
    """Pre-populate loyalty cache with frequently accessed data."""
    from loyalty.models import LoyaltyTier, Reward
    
    logger.info("Warming loyalty cache...")
    
    # Cache loyalty tiers
    tiers = list(LoyaltyTier.objects.filter(is_active=True).order_by('order'))
    caches['loyalty'].set('active_tiers', tiers, timeout=3600)
    
    # Cache active rewards
    rewards = list(Reward.objects.filter(is_active=True).select_related('min_tier_required'))
    caches['loyalty'].set('active_rewards', rewards, timeout=3600)
    
    logger.info("Loyalty cache warmed successfully")


def warm_api_cache():
    """Pre-populate API cache with frequently accessed endpoints."""
    logger.info("Warming API cache...")
    
    # This would make requests to frequently accessed API endpoints
    # to populate the cache before users request them
    
    logger.info("API cache warmed successfully")


# Context processor for cache statistics (development only)
def cache_context_processor(request):
    """Add cache statistics to template context (development only)."""
    if settings.DEBUG:
        return {
            'cache_stats': CacheManager.get_cache_stats()
        }
    return {}


# Signal handlers for cache invalidation
def invalidate_cache_on_save(sender, instance, **kwargs):
    """Signal handler to invalidate cache when models are saved."""
    model_name = sender._meta.label_lower
    
    if 'loyalty' in model_name:
        CacheManager.invalidate_loyalty_cache()
    
    logger.debug(f"Invalidated cache for model: {model_name}")


def invalidate_cache_on_delete(sender, instance, **kwargs):
    """Signal handler to invalidate cache when models are deleted."""
    model_name = sender._meta.label_lower
    
    if 'loyalty' in model_name:
        CacheManager.invalidate_loyalty_cache()
    
    logger.debug(f"Invalidated cache for deleted model: {model_name}")
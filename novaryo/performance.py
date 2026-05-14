"""
Performance monitoring and optimization utilities
"""
import time
import logging
from functools import wraps
from contextlib import contextmanager
from typing import Any, Dict, Optional, Callable
from django.conf import settings
from django.db import connection
from django.core.cache import cache
from django.utils import timezone
from django.http import HttpResponse
import json

logger = logging.getLogger('novaryo.performance')


class PerformanceMonitor:
    """Utility class for performance monitoring"""
    
    @staticmethod
    def get_db_query_count():
        """Get current database query count"""
        return len(connection.queries)
    
    @staticmethod
    def get_cache_stats():
        """Get cache performance statistics"""
        try:
            # This would work with Redis backend
            from django.core.cache.backends.redis import RedisCache
            cache_backend = cache._cache
            
            if isinstance(cache_backend, RedisCache):
                client = cache_backend._cache.get_client()
                info = client.info()
                return {
                    'hits': info.get('keyspace_hits', 0),
                    'misses': info.get('keyspace_misses', 0),
                    'hit_rate': info.get('keyspace_hits', 0) / max(1, info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0)) * 100,
                    'memory_usage': info.get('used_memory_human', '0B'),
                    'connected_clients': info.get('connected_clients', 0),
                }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {'error': str(e)}
    
    @staticmethod
    def get_system_metrics():
        """Get basic system performance metrics"""
        import psutil
        
        try:
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent,
                'active_connections': len(connection.queries),
            }
        except ImportError:
            return {'error': 'psutil not installed'}
        except Exception as e:
            return {'error': str(e)}


def performance_monitor(func_name: str = None):
    """
    Decorator to monitor function performance.
    
    Args:
        func_name: Optional custom function name for logging
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            start_queries = len(connection.queries)
            
            function_name = func_name or f"{func.__module__}.{func.__name__}"
            
            try:
                result = func(*args, **kwargs)
                
                # Calculate metrics
                execution_time = (time.time() - start_time) * 1000  # Convert to ms
                query_count = len(connection.queries) - start_queries
                
                # Log performance metrics
                logger.info(
                    f"Performance: {function_name} - "
                    f"Time: {execution_time:.2f}ms, "
                    f"Queries: {query_count}",
                    extra={
                        'function': function_name,
                        'execution_time_ms': execution_time,
                        'query_count': query_count,
                        'args_count': len(args),
                        'kwargs_count': len(kwargs),
                    }
                )
                
                # Warn about slow operations
                if execution_time > 1000:  # More than 1 second
                    logger.warning(
                        f"Slow operation detected: {function_name} took {execution_time:.2f}ms"
                    )
                
                # Warn about excessive queries
                if query_count > 10:
                    logger.warning(
                        f"High query count: {function_name} executed {query_count} queries"
                    )
                
                return result
                
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                logger.error(
                    f"Performance (Error): {function_name} - "
                    f"Time: {execution_time:.2f}ms, "
                    f"Error: {str(e)}",
                    extra={
                        'function': function_name,
                        'execution_time_ms': execution_time,
                        'error': str(e),
                    }
                )
                raise
                
        return wrapper
    return decorator


@contextmanager
def performance_context(operation_name: str):
    """
    Context manager for monitoring performance of code blocks.
    
    Usage:
        with performance_context('complex_calculation'):
            # Your code here
            pass
    """
    start_time = time.time()
    start_queries = len(connection.queries)
    
    try:
        yield
    finally:
        execution_time = (time.time() - start_time) * 1000
        query_count = len(connection.queries) - start_queries
        
        logger.info(
            f"Performance Context: {operation_name} - "
            f"Time: {execution_time:.2f}ms, "
            f"Queries: {query_count}",
            extra={
                'operation': operation_name,
                'execution_time_ms': execution_time,
                'query_count': query_count,
            }
        )


def slow_query_detector(threshold_ms: float = 100):
    """
    Decorator to detect and log slow database queries.
    
    Args:
        threshold_ms: Threshold in milliseconds to consider a query slow
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            initial_queries = len(connection.queries)
            
            result = func(*args, **kwargs)
            
            # Analyze new queries
            new_queries = connection.queries[initial_queries:]
            
            for query in new_queries:
                time_taken = float(query['time']) * 1000  # Convert to ms
                
                if time_taken > threshold_ms:
                    logger.warning(
                        f"Slow query detected in {func.__name__}: "
                        f"{time_taken:.2f}ms - {query['sql'][:200]}...",
                        extra={
                            'function': func.__name__,
                            'query_time_ms': time_taken,
                            'sql_preview': query['sql'][:200],
                        }
                    )
            
            return result
        return wrapper
    return decorator


class QueryCountMiddleware:
    """Middleware to track database query counts per request"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_queries = len(connection.queries)
        start_time = time.time()
        
        response = self.get_response(request)
        
        # Calculate metrics
        query_count = len(connection.queries) - start_queries
        execution_time = (time.time() - start_time) * 1000
        
        # Add headers for development
        if settings.DEBUG:
            response['X-DB-Query-Count'] = str(query_count)
            response['X-Response-Time'] = f"{execution_time:.2f}ms"
        
        # Log performance metrics
        logger.info(
            f"Request: {request.method} {request.path} - "
            f"Time: {execution_time:.2f}ms, "
            f"Queries: {query_count}, "
            f"Status: {response.status_code}",
            extra={
                'method': request.method,
                'path': request.path,
                'execution_time_ms': execution_time,
                'query_count': query_count,
                'status_code': response.status_code,
                'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
            }
        )
        
        # Warn about slow requests
        if execution_time > 2000:  # More than 2 seconds
            logger.warning(
                f"Slow request: {request.method} {request.path} took {execution_time:.2f}ms"
            )
        
        return response


def cache_performance_monitor(cache_key: str, timeout: int = 300):
    """
    Decorator to monitor cache performance for functions.
    
    Args:
        cache_key: Cache key to use
        timeout: Cache timeout in seconds
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Try to get from cache
            start_time = time.time()
            cached_result = cache.get(cache_key)
            cache_time = (time.time() - start_time) * 1000
            
            if cached_result is not None:
                logger.info(
                    f"Cache hit: {func.__name__} - {cache_time:.2f}ms",
                    extra={
                        'function': func.__name__,
                        'cache_result': 'hit',
                        'cache_time_ms': cache_time,
                    }
                )
                return cached_result
            
            # Cache miss - execute function
            logger.info(
                f"Cache miss: {func.__name__}",
                extra={
                    'function': func.__name__,
                    'cache_result': 'miss',
                }
            )
            
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000
            
            # Cache the result
            cache.set(cache_key, result, timeout)
            
            logger.info(
                f"Cache set: {func.__name__} - {execution_time:.2f}ms",
                extra={
                    'function': func.__name__,
                    'execution_time_ms': execution_time,
                    'cache_timeout': timeout,
                }
            )
            
            return result
        return wrapper
    return decorator


class PerformanceReport:
    """Generate performance reports"""
    
    @staticmethod
    def generate_loyalty_performance_report():
        """Generate performance report for loyalty operations"""
        from loyalty.models import LoyaltyMembership, PointsTransaction, Reward
        
        with performance_context('loyalty_performance_report'):
            report = {
                'timestamp': timezone.now().isoformat(),
                'database_stats': {
                    'total_memberships': LoyaltyMembership.objects.count(),
                    'active_memberships': LoyaltyMembership.objects.filter(is_active=True).count(),
                    'total_transactions': PointsTransaction.objects.count(),
                    'total_rewards': Reward.objects.count(),
                },
                'cache_stats': PerformanceMonitor.get_cache_stats(),
                'system_metrics': PerformanceMonitor.get_system_metrics(),
            }
            
            return report
    
    @staticmethod
    def generate_api_performance_report():
        """Generate performance report for API operations"""
        report = {
            'timestamp': timezone.now().isoformat(),
            'cache_stats': PerformanceMonitor.get_cache_stats(),
            'system_metrics': PerformanceMonitor.get_system_metrics(),
        }
        
        # Add Silk data if available
        try:
            from silk.models import Request
            
            # Get recent request statistics
            recent_requests = Request.objects.filter(
                start_time__gte=timezone.now() - timezone.timedelta(hours=1)
            )
            
            if recent_requests.exists():
                avg_response_time = recent_requests.aggregate(
                    avg_time=models.Avg('time_taken')
                )['avg_time']
                
                report['api_stats'] = {
                    'requests_last_hour': recent_requests.count(),
                    'avg_response_time_ms': avg_response_time * 1000 if avg_response_time else 0,
                    'slowest_endpoints': list(
                        recent_requests.order_by('-time_taken')[:5].values(
                            'path', 'time_taken', 'num_sql_queries'
                        )
                    )
                }
        except ImportError:
            report['api_stats'] = {'error': 'Silk not available'}
        
        return report


# Django management command helpers
def log_performance_summary():
    """Log a summary of performance metrics"""
    loyalty_report = PerformanceReport.generate_loyalty_performance_report()
    api_report = PerformanceReport.generate_api_performance_report()
    
    logger.info("Performance Summary", extra={
        'loyalty_report': loyalty_report,
        'api_report': api_report,
    })


# Template context processor for performance data (development only)
def performance_context_processor(request):
    """Add performance data to template context (development only)"""
    if settings.DEBUG and request.user.is_staff:
        return {
            'performance_data': {
                'query_count': len(connection.queries),
                'cache_stats': PerformanceMonitor.get_cache_stats(),
            }
        }
    return {}


# Custom Django admin actions for performance monitoring
def export_performance_data(modeladmin, request, queryset):
    """Export performance data as JSON"""
    report = PerformanceReport.generate_loyalty_performance_report()
    
    response = HttpResponse(
        json.dumps(report, indent=2),
        content_type='application/json'
    )
    response['Content-Disposition'] = 'attachment; filename="performance_report.json"'
    
    return response


export_performance_data.short_description = "Export performance data"
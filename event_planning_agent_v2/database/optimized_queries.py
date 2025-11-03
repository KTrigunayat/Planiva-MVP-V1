"""
Optimized database queries with performance enhancements.
Provides efficient vendor search, caching, and query optimization.
"""

import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from functools import lru_cache
from sqlalchemy import text, and_, or_, func, select
from sqlalchemy.orm import Session
from cachetools import TTLCache

from .models import Venue, Caterer, Photographer, MakeupArtist, EventPlan
from .connection import get_sync_session
from ..config.settings import get_settings

logger = logging.getLogger(__name__)


class OptimizedQueryManager:
    """
    Optimized query manager with caching and performance enhancements.
    Provides efficient database operations for vendor search and event planning.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.db_settings = self.settings.database
        
        # Query result cache
        self._query_cache = None
        if self.db_settings.enable_query_cache:
            self._query_cache = TTLCache(
                maxsize=self.db_settings.query_cache_size,
                ttl=self.db_settings.query_cache_ttl
            )
        
        # Performance metrics
        self._query_count = 0
        self._cache_hits = 0
        self._total_query_time = 0.0
    
    def _generate_cache_key(self, query_type: str, **kwargs) -> str:
        """Generate cache key for query results"""
        import hashlib
        import json
        
        cache_data = {
            'query_type': query_type,
            **kwargs
        }
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[Any]:
        """Get cached query result if available"""
        if not self._query_cache:
            return None
        
        cached_result = self._query_cache.get(cache_key)
        if cached_result is not None:
            self._cache_hits += 1
            logger.debug(f"Query cache hit for key: {cache_key[:8]}...")
            return cached_result
        
        return None
    
    def _cache_result(self, cache_key: str, result: Any):
        """Cache query result with TTL"""
        if self._query_cache:
            self._query_cache[cache_key] = result
            logger.debug(f"Cached query result for key: {cache_key[:8]}...")
    
    def _execute_with_metrics(self, query_func, *args, **kwargs):
        """Execute query with performance metrics tracking"""
        start_time = time.time()
        self._query_count += 1
        
        try:
            result = query_func(*args, **kwargs)
            execution_time = time.time() - start_time
            self._total_query_time += execution_time
            
            logger.debug(f"Query executed in {execution_time:.3f}s")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Query failed after {execution_time:.3f}s: {e}")
            raise
    
    def search_venues_optimized(
        self,
        location_city: Optional[str] = None,
        min_capacity: Optional[int] = None,
        max_capacity: Optional[int] = None,
        max_rental_cost: Optional[int] = None,
        venue_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Optimized venue search with caching and efficient queries.
        
        Args:
            location_city: City to search in
            min_capacity: Minimum seating capacity
            max_capacity: Maximum seating capacity
            max_rental_cost: Maximum rental cost
            venue_type: Type of venue
            limit: Maximum number of results
            
        Returns:
            List of venue dictionaries
        """
        # Generate cache key
        cache_key = self._generate_cache_key(
            'search_venues',
            location_city=location_city,
            min_capacity=min_capacity,
            max_capacity=max_capacity,
            max_rental_cost=max_rental_cost,
            venue_type=venue_type,
            limit=limit
        )
        
        # Check cache
        cached_result = self._get_cached_result(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Execute optimized query
        def _execute_venue_search():
            with get_sync_session() as session:
                # Build optimized query with proper indexing
                query = session.query(Venue)
                
                # Apply filters with index-friendly conditions
                if location_city:
                    query = query.filter(Venue.location_city.ilike(f'%{location_city}%'))
                
                if min_capacity is not None:
                    query = query.filter(Venue.ideal_capacity >= min_capacity)
                
                if max_capacity is not None:
                    query = query.filter(Venue.max_seating_capacity <= max_capacity)
                
                if max_rental_cost is not None:
                    query = query.filter(Venue.rental_cost <= max_rental_cost)
                
                if venue_type:
                    query = query.filter(Venue.area_type.ilike(f'%{venue_type}%'))
                
                # Optimize ordering for performance
                query = query.order_by(
                    Venue.rental_cost.asc(),  # Use indexed column for ordering
                    Venue.ideal_capacity.desc()
                )
                
                # Apply limit
                query = query.limit(limit)
                
                # Execute and convert to dictionaries
                venues = query.all()
                
                result = []
                for venue in venues:
                    venue_dict = {
                        'vendor_id': str(venue.vendor_id),
                        'name': venue.name,
                        'location_city': venue.location_city,
                        'location_full': venue.location_full,
                        'ideal_capacity': venue.ideal_capacity,
                        'max_seating_capacity': venue.max_seating_capacity,
                        'rental_cost': venue.rental_cost,
                        'min_veg_price': venue.min_veg_price,
                        'room_count': venue.room_count,
                        'room_cost': venue.room_cost,
                        'area_type': venue.area_type,
                        'policies': venue.policies,
                        'decor_options': venue.decor_options,
                        'attributes': venue.attributes
                    }
                    result.append(venue_dict)
                
                return result
        
        result = self._execute_with_metrics(_execute_venue_search)
        
        # Cache result
        self._cache_result(cache_key, result)
        
        return result
    
    def search_caterers_optimized(
        self,
        location_city: Optional[str] = None,
        max_veg_price: Optional[int] = None,
        max_non_veg_price: Optional[int] = None,
        min_guest_capacity: Optional[int] = None,
        veg_only: Optional[bool] = None,
        cuisine_preferences: Optional[List[str]] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Optimized caterer search with caching and efficient queries.
        
        Args:
            location_city: City to search in
            max_veg_price: Maximum vegetarian price per plate
            max_non_veg_price: Maximum non-vegetarian price per plate
            min_guest_capacity: Minimum guest capacity required
            veg_only: Whether caterer serves only vegetarian food
            cuisine_preferences: List of preferred cuisines
            limit: Maximum number of results
            
        Returns:
            List of caterer dictionaries
        """
        # Generate cache key
        cache_key = self._generate_cache_key(
            'search_caterers',
            location_city=location_city,
            max_veg_price=max_veg_price,
            max_non_veg_price=max_non_veg_price,
            min_guest_capacity=min_guest_capacity,
            veg_only=veg_only,
            cuisine_preferences=cuisine_preferences,
            limit=limit
        )
        
        # Check cache
        cached_result = self._get_cached_result(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Execute optimized query
        def _execute_caterer_search():
            with get_sync_session() as session:
                # Build optimized query
                query = session.query(Caterer)
                
                # Apply filters with index-friendly conditions
                if location_city:
                    query = query.filter(Caterer.location_city.ilike(f'%{location_city}%'))
                
                if max_veg_price is not None:
                    query = query.filter(Caterer.min_veg_price <= max_veg_price)
                
                if max_non_veg_price is not None:
                    query = query.filter(Caterer.min_non_veg_price <= max_non_veg_price)
                
                if min_guest_capacity is not None:
                    query = query.filter(Caterer.max_guest_capacity >= min_guest_capacity)
                
                if veg_only is not None:
                    query = query.filter(Caterer.veg_only == veg_only)
                
                # Cuisine preference filtering using JSONB
                if cuisine_preferences:
                    cuisine_conditions = []
                    for cuisine in cuisine_preferences:
                        cuisine_conditions.append(
                            Caterer.attributes['cuisines'].astext.ilike(f'%{cuisine}%')
                        )
                    if cuisine_conditions:
                        query = query.filter(or_(*cuisine_conditions))
                
                # Optimize ordering
                query = query.order_by(
                    Caterer.min_veg_price.asc(),
                    Caterer.max_guest_capacity.desc()
                )
                
                # Apply limit
                query = query.limit(limit)
                
                # Execute and convert to dictionaries
                caterers = query.all()
                
                result = []
                for caterer in caterers:
                    caterer_dict = {
                        'vendor_id': str(caterer.vendor_id),
                        'name': caterer.name,
                        'location_city': caterer.location_city,
                        'location_full': caterer.location_full,
                        'veg_only': caterer.veg_only,
                        'min_veg_price': caterer.min_veg_price,
                        'min_non_veg_price': caterer.min_non_veg_price,
                        'max_guest_capacity': caterer.max_guest_capacity,
                        'attributes': caterer.attributes
                    }
                    result.append(caterer_dict)
                
                return result
        
        result = self._execute_with_metrics(_execute_caterer_search)
        
        # Cache result
        self._cache_result(cache_key, result)
        
        return result
    
    def search_photographers_optimized(
        self,
        location_city: Optional[str] = None,
        max_photo_price: Optional[int] = None,
        video_required: Optional[bool] = None,
        style_preferences: Optional[List[str]] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Optimized photographer search with caching and efficient queries.
        
        Args:
            location_city: City to search in
            max_photo_price: Maximum photo package price
            video_required: Whether video services are required
            style_preferences: List of preferred photography styles
            limit: Maximum number of results
            
        Returns:
            List of photographer dictionaries
        """
        # Generate cache key
        cache_key = self._generate_cache_key(
            'search_photographers',
            location_city=location_city,
            max_photo_price=max_photo_price,
            video_required=video_required,
            style_preferences=style_preferences,
            limit=limit
        )
        
        # Check cache
        cached_result = self._get_cached_result(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Execute optimized query
        def _execute_photographer_search():
            with get_sync_session() as session:
                # Build optimized query
                query = session.query(Photographer)
                
                # Apply filters
                if location_city:
                    query = query.filter(Photographer.location_city.ilike(f'%{location_city}%'))
                
                if max_photo_price is not None:
                    query = query.filter(Photographer.photo_package_price <= max_photo_price)
                
                if video_required is not None:
                    query = query.filter(Photographer.video_available == video_required)
                
                # Style preference filtering
                if style_preferences:
                    style_conditions = []
                    for style in style_preferences:
                        style_conditions.append(
                            Photographer.attributes['styles'].astext.ilike(f'%{style}%')
                        )
                    if style_conditions:
                        query = query.filter(or_(*style_conditions))
                
                # Optimize ordering
                query = query.order_by(Photographer.photo_package_price.asc())
                
                # Apply limit
                query = query.limit(limit)
                
                # Execute and convert to dictionaries
                photographers = query.all()
                
                result = []
                for photographer in photographers:
                    photographer_dict = {
                        'vendor_id': str(photographer.vendor_id),
                        'name': photographer.name,
                        'location_city': photographer.location_city,
                        'location_full': photographer.location_full,
                        'photo_package_price': photographer.photo_package_price,
                        'video_available': photographer.video_available,
                        'attributes': photographer.attributes
                    }
                    result.append(photographer_dict)
                
                return result
        
        result = self._execute_with_metrics(_execute_photographer_search)
        
        # Cache result
        self._cache_result(cache_key, result)
        
        return result
    
    def search_makeup_artists_optimized(
        self,
        location_city: Optional[str] = None,
        max_bridal_price: Optional[int] = None,
        on_site_required: Optional[bool] = None,
        style_preferences: Optional[List[str]] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Optimized makeup artist search with caching and efficient queries.
        
        Args:
            location_city: City to search in
            max_bridal_price: Maximum bridal makeup price
            on_site_required: Whether on-site service is required
            style_preferences: List of preferred makeup styles
            limit: Maximum number of results
            
        Returns:
            List of makeup artist dictionaries
        """
        # Generate cache key
        cache_key = self._generate_cache_key(
            'search_makeup_artists',
            location_city=location_city,
            max_bridal_price=max_bridal_price,
            on_site_required=on_site_required,
            style_preferences=style_preferences,
            limit=limit
        )
        
        # Check cache
        cached_result = self._get_cached_result(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Execute optimized query
        def _execute_makeup_artist_search():
            with get_sync_session() as session:
                # Build optimized query
                query = session.query(MakeupArtist)
                
                # Apply filters
                if location_city:
                    query = query.filter(MakeupArtist.location_city.ilike(f'%{location_city}%'))
                
                if max_bridal_price is not None:
                    query = query.filter(MakeupArtist.bridal_makeup_price <= max_bridal_price)
                
                if on_site_required is not None:
                    query = query.filter(MakeupArtist.on_site_service == on_site_required)
                
                # Style preference filtering
                if style_preferences:
                    style_conditions = []
                    for style in style_preferences:
                        style_conditions.append(
                            MakeupArtist.attributes['styles'].astext.ilike(f'%{style}%')
                        )
                    if style_conditions:
                        query = query.filter(or_(*style_conditions))
                
                # Optimize ordering
                query = query.order_by(MakeupArtist.bridal_makeup_price.asc())
                
                # Apply limit
                query = query.limit(limit)
                
                # Execute and convert to dictionaries
                makeup_artists = query.all()
                
                result = []
                for artist in makeup_artists:
                    artist_dict = {
                        'vendor_id': str(artist.vendor_id),
                        'name': artist.name,
                        'location_city': artist.location_city,
                        'location_full': artist.location_full,
                        'bridal_makeup_price': artist.bridal_makeup_price,
                        'on_site_service': artist.on_site_service,
                        'attributes': artist.attributes
                    }
                    result.append(artist_dict)
                
                return result
        
        result = self._execute_with_metrics(_execute_makeup_artist_search)
        
        # Cache result
        self._cache_result(cache_key, result)
        
        return result
    
    def get_vendor_by_id_optimized(
        self,
        vendor_id: str,
        vendor_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get vendor by ID with caching optimization.
        
        Args:
            vendor_id: Vendor UUID
            vendor_type: Type of vendor (venue, caterer, photographer, makeup_artist)
            
        Returns:
            Vendor dictionary or None if not found
        """
        # Generate cache key
        cache_key = self._generate_cache_key(
            'get_vendor_by_id',
            vendor_id=vendor_id,
            vendor_type=vendor_type
        )
        
        # Check cache
        cached_result = self._get_cached_result(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Execute query
        def _execute_vendor_lookup():
            with get_sync_session() as session:
                vendor_model_map = {
                    'venue': Venue,
                    'caterer': Caterer,
                    'photographer': Photographer,
                    'makeup_artist': MakeupArtist
                }
                
                model_class = vendor_model_map.get(vendor_type)
                if not model_class:
                    return None
                
                vendor = session.query(model_class).filter(
                    model_class.vendor_id == vendor_id
                ).first()
                
                if not vendor:
                    return None
                
                # Convert to dictionary based on vendor type
                if vendor_type == 'venue':
                    return {
                        'vendor_id': str(vendor.vendor_id),
                        'name': vendor.name,
                        'location_city': vendor.location_city,
                        'location_full': vendor.location_full,
                        'ideal_capacity': vendor.ideal_capacity,
                        'max_seating_capacity': vendor.max_seating_capacity,
                        'rental_cost': vendor.rental_cost,
                        'min_veg_price': vendor.min_veg_price,
                        'room_count': vendor.room_count,
                        'room_cost': vendor.room_cost,
                        'area_type': vendor.area_type,
                        'policies': vendor.policies,
                        'decor_options': vendor.decor_options,
                        'attributes': vendor.attributes
                    }
                elif vendor_type == 'caterer':
                    return {
                        'vendor_id': str(vendor.vendor_id),
                        'name': vendor.name,
                        'location_city': vendor.location_city,
                        'location_full': vendor.location_full,
                        'veg_only': vendor.veg_only,
                        'min_veg_price': vendor.min_veg_price,
                        'min_non_veg_price': vendor.min_non_veg_price,
                        'max_guest_capacity': vendor.max_guest_capacity,
                        'attributes': vendor.attributes
                    }
                elif vendor_type == 'photographer':
                    return {
                        'vendor_id': str(vendor.vendor_id),
                        'name': vendor.name,
                        'location_city': vendor.location_city,
                        'location_full': vendor.location_full,
                        'photo_package_price': vendor.photo_package_price,
                        'video_available': vendor.video_available,
                        'attributes': vendor.attributes
                    }
                elif vendor_type == 'makeup_artist':
                    return {
                        'vendor_id': str(vendor.vendor_id),
                        'name': vendor.name,
                        'location_city': vendor.location_city,
                        'location_full': vendor.location_full,
                        'bridal_makeup_price': vendor.bridal_makeup_price,
                        'on_site_service': vendor.on_site_service,
                        'attributes': vendor.attributes
                    }
                
                return None
        
        result = self._execute_with_metrics(_execute_vendor_lookup)
        
        # Cache result
        if result:
            self._cache_result(cache_key, result)
        
        return result
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get query performance metrics"""
        cache_hit_rate = (self._cache_hits / self._query_count) if self._query_count > 0 else 0
        avg_query_time = (self._total_query_time / self._query_count) if self._query_count > 0 else 0
        
        return {
            "total_queries": self._query_count,
            "cache_hits": self._cache_hits,
            "cache_hit_rate": cache_hit_rate,
            "avg_query_time": avg_query_time,
            "total_query_time": self._total_query_time,
            "cache_size": len(self._query_cache) if self._query_cache else 0
        }
    
    def clear_cache(self):
        """Clear query cache"""
        if self._query_cache:
            self._query_cache.clear()
            logger.info("Query cache cleared")


# Global query manager instance
_query_manager: Optional[OptimizedQueryManager] = None


def get_query_manager() -> OptimizedQueryManager:
    """Get global query manager instance"""
    global _query_manager
    if _query_manager is None:
        _query_manager = OptimizedQueryManager()
    return _query_manager


# Convenience functions for optimized queries
def search_venues_optimized(**kwargs) -> List[Dict[str, Any]]:
    """Convenience function for optimized venue search"""
    return get_query_manager().search_venues_optimized(**kwargs)


def search_caterers_optimized(**kwargs) -> List[Dict[str, Any]]:
    """Convenience function for optimized caterer search"""
    return get_query_manager().search_caterers_optimized(**kwargs)


def search_photographers_optimized(**kwargs) -> List[Dict[str, Any]]:
    """Convenience function for optimized photographer search"""
    return get_query_manager().search_photographers_optimized(**kwargs)


def search_makeup_artists_optimized(**kwargs) -> List[Dict[str, Any]]:
    """Convenience function for optimized makeup artist search"""
    return get_query_manager().search_makeup_artists_optimized(**kwargs)


def get_vendor_by_id_optimized(vendor_id: str, vendor_type: str) -> Optional[Dict[str, Any]]:
    """Convenience function for optimized vendor lookup"""
    return get_query_manager().get_vendor_by_id_optimized(vendor_id, vendor_type)
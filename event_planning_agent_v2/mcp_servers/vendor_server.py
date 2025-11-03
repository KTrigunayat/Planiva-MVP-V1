"""
Vendor Data MCP Server for Event Planning Agent

This MCP server provides enhanced vendor data processing capabilities including:
- Enhanced vendor search with ML-based ranking
- Vendor compatibility checking
- Real-time vendor availability checking
"""

import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)
import mcp.types as types

from ..database.models import Venue, Caterer, Photographer, MakeupArtist
from ..database.setup import DatabaseSetup
from ..config.settings import get_settings

logger = logging.getLogger(__name__)


class VendorDataServer:
    """MCP server for enhanced vendor data processing"""
    
    def __init__(self):
        self.settings = get_settings()
        self.db_setup = DatabaseSetup()
        self.server = Server("vendor-data-server")
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self._setup_tools()
    
    def _setup_tools(self):
        """Setup MCP tools for vendor operations"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """List available vendor data tools"""
            return [
                Tool(
                    name="enhanced_vendor_search",
                    description="Enhanced vendor search with ML-based ranking capabilities",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "service_type": {
                                "type": "string",
                                "enum": ["venue", "caterer", "photographer", "makeup_artist"],
                                "description": "Type of vendor service"
                            },
                            "filters": {
                                "type": "object",
                                "description": "Hard filters for vendor search",
                                "properties": {
                                    "location_city": {"type": "string"},
                                    "budget": {"type": "number"},
                                    "capacity_min": {"type": "integer"},
                                    "required_amenities": {"type": "array", "items": {"type": "string"}},
                                    "dietary_options": {"type": "array", "items": {"type": "string"}},
                                    "video_required": {"type": "boolean"}
                                }
                            },
                            "preferences": {
                                "type": "object",
                                "description": "Soft preferences for ML-based ranking",
                                "properties": {
                                    "style_keywords": {"type": "array", "items": {"type": "string"}},
                                    "cuisine_preferences": {"type": "array", "items": {"type": "string"}},
                                    "photography_style": {"type": "string"},
                                    "client_vision": {"type": "string"}
                                }
                            },
                            "limit": {"type": "integer", "default": 5}
                        },
                        "required": ["service_type", "filters"]
                    }
                ),
                Tool(
                    name="vendor_compatibility_check",
                    description="Check compatibility between selected vendors",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "vendors": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "vendor_id": {"type": "string"},
                                        "service_type": {"type": "string"},
                                        "location_city": {"type": "string"},
                                        "attributes": {"type": "object"}
                                    }
                                }
                            },
                            "event_date": {"type": "string", "format": "date"},
                            "guest_count": {"type": "integer"}
                        },
                        "required": ["vendors", "event_date", "guest_count"]
                    }
                ),
                Tool(
                    name="vendor_availability_check",
                    description="Real-time vendor availability checking",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "vendor_id": {"type": "string"},
                            "service_type": {"type": "string"},
                            "event_date": {"type": "string", "format": "date"},
                            "duration_hours": {"type": "integer", "default": 8}
                        },
                        "required": ["vendor_id", "service_type", "event_date"]
                    }
                ),
                Tool(
                    name="vendor_similarity_search",
                    description="Find similar vendors using ML-based similarity",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "reference_vendor_id": {"type": "string"},
                            "service_type": {"type": "string"},
                            "similarity_threshold": {"type": "number", "default": 0.7},
                            "limit": {"type": "integer", "default": 5}
                        },
                        "required": ["reference_vendor_id", "service_type"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
            """Handle tool calls"""
            try:
                if name == "enhanced_vendor_search":
                    result = await self.enhanced_vendor_search(**arguments)
                elif name == "vendor_compatibility_check":
                    result = await self.vendor_compatibility_check(**arguments)
                elif name == "vendor_availability_check":
                    result = await self.vendor_availability_check(**arguments)
                elif name == "vendor_similarity_search":
                    result = await self.vendor_similarity_search(**arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
                
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
                
            except Exception as e:
                logger.error(f"Tool call failed for {name}: {e}")
                return [types.TextContent(
                    type="text", 
                    text=json.dumps({"error": str(e), "tool": name})
                )]
    
    async def enhanced_vendor_search(
        self,
        service_type: str,
        filters: Dict[str, Any],
        preferences: Optional[Dict[str, Any]] = None,
        limit: int = 5
    ) -> Dict[str, Any]:
        """Enhanced vendor search with ML-based ranking capabilities"""
        
        try:
            # Get base vendor data using existing logic
            base_results = await self._get_filtered_vendors(service_type, filters)
            
            if not base_results:
                return {
                    "vendors": [],
                    "total_found": 0,
                    "search_metadata": {
                        "service_type": service_type,
                        "filters_applied": filters,
                        "ml_ranking_applied": False
                    }
                }
            
            # Apply ML-based ranking if preferences provided
            if preferences:
                ranked_results = await self._apply_ml_ranking(
                    base_results, preferences, service_type
                )
            else:
                ranked_results = base_results
            
            # Limit results
            final_results = ranked_results[:limit]
            
            # Add enhanced metadata
            for vendor in final_results:
                vendor['search_metadata'] = {
                    'ranking_score': vendor.get('ranking_score', 0.0),
                    'ml_confidence': vendor.get('ml_confidence', 0.0),
                    'compatibility_score': vendor.get('compatibility_score', 0.0)
                }
            
            return {
                "vendors": final_results,
                "total_found": len(base_results),
                "returned_count": len(final_results),
                "search_metadata": {
                    "service_type": service_type,
                    "filters_applied": filters,
                    "preferences_applied": preferences or {},
                    "ml_ranking_applied": preferences is not None,
                    "search_timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Enhanced vendor search failed: {e}")
            raise
    
    async def _get_filtered_vendors(
        self, 
        service_type: str, 
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get vendors using existing filtering logic"""
        
        # Map service types to models
        model_map = {
            'venue': Venue,
            'caterer': Caterer,
            'photographer': Photographer,
            'makeup_artist': MakeupArtist
        }
        
        if service_type not in model_map:
            raise ValueError(f"Unknown service type: {service_type}")
        
        model_class = model_map[service_type]
        
        with self.db_setup.get_session() as session:
            query = session.query(model_class)
            
            # Apply location filter
            if 'location_city' in filters:
                query = query.filter(model_class.location_city == filters['location_city'])
            
            # Apply budget filter
            if 'budget' in filters:
                budget = filters['budget']
                if service_type == 'venue':
                    query = query.filter(model_class.min_veg_price <= budget)
                elif service_type == 'caterer':
                    query = query.filter(model_class.min_veg_price <= budget)
                elif service_type == 'photographer':
                    query = query.filter(model_class.photo_package_price <= budget)
                elif service_type == 'makeup_artist':
                    query = query.filter(model_class.bridal_makeup_price <= budget)
            
            # Apply capacity filter for venues
            if service_type == 'venue' and 'capacity_min' in filters:
                query = query.filter(model_class.max_seating_capacity >= filters['capacity_min'])
            
            # Apply video requirement for photographers
            if service_type == 'photographer' and filters.get('video_required'):
                query = query.filter(model_class.video_available == True)
            
            # Execute query
            vendors = query.all()
            
            # Convert to dictionaries
            result = []
            for vendor in vendors:
                vendor_dict = {
                    'id': str(vendor.id),
                    'name': vendor.name,
                    'location_city': vendor.location_city,
                    'location_full': vendor.location_full,
                    'attributes': vendor.attributes or {}
                }
                
                # Add service-specific fields
                if service_type == 'venue':
                    vendor_dict.update({
                        'max_seating_capacity': vendor.max_seating_capacity,
                        'min_veg_price': vendor.min_veg_price,
                        'rental_cost': vendor.rental_cost,
                        'room_count': vendor.room_count
                    })
                elif service_type == 'caterer':
                    vendor_dict.update({
                        'min_veg_price': vendor.min_veg_price,
                        'min_non_veg_price': vendor.min_non_veg_price,
                        'veg_only': vendor.veg_only
                    })
                elif service_type == 'photographer':
                    vendor_dict.update({
                        'photo_package_price': vendor.photo_package_price,
                        'video_available': vendor.video_available
                    })
                elif service_type == 'makeup_artist':
                    vendor_dict.update({
                        'bridal_makeup_price': vendor.bridal_makeup_price,
                        'on_site_service': vendor.on_site_service
                    })
                
                result.append(vendor_dict)
            
            return result
    
    async def _apply_ml_ranking(
        self,
        vendors: List[Dict[str, Any]],
        preferences: Dict[str, Any],
        service_type: str
    ) -> List[Dict[str, Any]]:
        """Apply ML-based ranking to vendor results"""
        
        if not vendors:
            return vendors
        
        try:
            # Extract text features for similarity calculation
            vendor_texts = []
            for vendor in vendors:
                text_features = []
                
                # Add name and location
                text_features.append(vendor.get('name', ''))
                text_features.append(vendor.get('location_full', ''))
                
                # Add attributes text
                attributes = vendor.get('attributes', {})
                if 'about' in attributes:
                    text_features.append(attributes['about'])
                
                # Add service-specific features
                if service_type == 'venue':
                    if 'area_type' in vendor:
                        text_features.append(vendor['area_type'])
                elif service_type == 'caterer':
                    if 'cuisines' in attributes:
                        text_features.extend(attributes.get('cuisines', []))
                elif service_type == 'photographer':
                    if 'services' in attributes:
                        text_features.extend(attributes.get('services', []))
                    if 'styles' in attributes:
                        text_features.extend(attributes.get('styles', []))
                
                vendor_texts.append(' '.join(text_features))
            
            # Create preference text
            preference_text = self._create_preference_text(preferences, service_type)
            
            # Calculate similarity scores
            all_texts = vendor_texts + [preference_text]
            
            if len(all_texts) > 1:
                tfidf_matrix = self.tfidf_vectorizer.fit_transform(all_texts)
                similarity_scores = cosine_similarity(
                    tfidf_matrix[-1:], tfidf_matrix[:-1]
                ).flatten()
            else:
                similarity_scores = [0.0] * len(vendors)
            
            # Add ML scores to vendors
            for i, vendor in enumerate(vendors):
                ml_score = float(similarity_scores[i])
                
                # Calculate combined ranking score
                price_score = self._calculate_price_score(vendor, service_type, preferences)
                
                # Weighted combination
                combined_score = (0.6 * ml_score) + (0.4 * price_score)
                
                vendor['ml_confidence'] = ml_score
                vendor['price_score'] = price_score
                vendor['ranking_score'] = combined_score
            
            # Sort by combined score
            vendors.sort(key=lambda x: x['ranking_score'], reverse=True)
            
            return vendors
            
        except Exception as e:
            logger.warning(f"ML ranking failed, using original order: {e}")
            return vendors
    
    def _create_preference_text(
        self, 
        preferences: Dict[str, Any], 
        service_type: str
    ) -> str:
        """Create text representation of preferences for similarity matching"""
        
        text_parts = []
        
        # Add client vision
        if 'client_vision' in preferences:
            text_parts.append(preferences['client_vision'])
        
        # Add style keywords
        if 'style_keywords' in preferences:
            text_parts.extend(preferences['style_keywords'])
        
        # Add service-specific preferences
        if service_type == 'caterer' and 'cuisine_preferences' in preferences:
            text_parts.extend(preferences['cuisine_preferences'])
        
        if service_type == 'photographer' and 'photography_style' in preferences:
            text_parts.append(preferences['photography_style'])
        
        return ' '.join(text_parts)
    
    def _calculate_price_score(
        self, 
        vendor: Dict[str, Any], 
        service_type: str, 
        preferences: Dict[str, Any]
    ) -> float:
        """Calculate price-based score for vendor"""
        
        budget = preferences.get('budget', 0)
        if not budget:
            return 0.5  # Neutral score if no budget
        
        # Get vendor price based on service type
        price = 0
        if service_type == 'venue':
            price = vendor.get('min_veg_price', 0)
        elif service_type == 'caterer':
            price = vendor.get('min_veg_price', 0)
        elif service_type == 'photographer':
            price = vendor.get('photo_package_price', 0)
        elif service_type == 'makeup_artist':
            price = vendor.get('bridal_makeup_price', 0)
        
        if price <= 0:
            return 0.5  # Neutral score if no price
        
        # Calculate score (higher score for better value)
        if price <= budget:
            return 1.0 - (price / budget)
        else:
            return 0.0  # Over budget
    
    async def vendor_compatibility_check(
        self,
        vendors: List[Dict[str, Any]],
        event_date: str,
        guest_count: int
    ) -> Dict[str, Any]:
        """Check compatibility between selected vendors"""
        
        try:
            compatibility_results = {
                "overall_compatible": True,
                "compatibility_score": 1.0,
                "issues": [],
                "recommendations": [],
                "vendor_analysis": {}
            }
            
            # Check location compatibility
            locations = set()
            for vendor in vendors:
                location = vendor.get('location_city')
                if location:
                    locations.add(location)
            
            if len(locations) > 1:
                compatibility_results["issues"].append({
                    "type": "location_mismatch",
                    "severity": "medium",
                    "description": f"Vendors are in different cities: {', '.join(locations)}",
                    "impact": "May increase travel costs and coordination complexity"
                })
                compatibility_results["compatibility_score"] *= 0.8
            
            # Check capacity compatibility
            venue_capacity = None
            caterer_capacity = None
            
            for vendor in vendors:
                service_type = vendor.get('service_type', '')
                
                if service_type == 'venue':
                    venue_capacity = vendor.get('max_seating_capacity')
                elif service_type == 'caterer':
                    # Assume caterer can handle guest count if not specified
                    caterer_capacity = guest_count
            
            if venue_capacity and venue_capacity < guest_count:
                compatibility_results["issues"].append({
                    "type": "capacity_insufficient",
                    "severity": "high",
                    "description": f"Venue capacity ({venue_capacity}) is less than guest count ({guest_count})",
                    "impact": "Event cannot accommodate all guests"
                })
                compatibility_results["overall_compatible"] = False
                compatibility_results["compatibility_score"] *= 0.3
            
            # Check date availability (simulated)
            event_date_obj = datetime.strptime(event_date, "%Y-%m-%d").date()
            
            for vendor in vendors:
                vendor_id = vendor.get('id')
                service_type = vendor.get('service_type', '')
                
                # Simulate availability check
                availability = await self._simulate_vendor_availability(
                    vendor_id, service_type, event_date_obj
                )
                
                compatibility_results["vendor_analysis"][vendor_id] = {
                    "name": vendor.get('name'),
                    "service_type": service_type,
                    "available": availability["available"],
                    "availability_confidence": availability["confidence"]
                }
                
                if not availability["available"]:
                    compatibility_results["issues"].append({
                        "type": "vendor_unavailable",
                        "severity": "high",
                        "description": f"{vendor.get('name')} may not be available on {event_date}",
                        "impact": "Need to find alternative vendor"
                    })
                    compatibility_results["overall_compatible"] = False
                    compatibility_results["compatibility_score"] *= 0.5
            
            # Generate recommendations
            if compatibility_results["issues"]:
                compatibility_results["recommendations"] = self._generate_compatibility_recommendations(
                    compatibility_results["issues"]
                )
            
            return compatibility_results
            
        except Exception as e:
            logger.error(f"Compatibility check failed: {e}")
            raise
    
    async def _simulate_vendor_availability(
        self, 
        vendor_id: str, 
        service_type: str, 
        event_date: date
    ) -> Dict[str, Any]:
        """Simulate vendor availability check"""
        
        # In a real implementation, this would check:
        # - Vendor's booking calendar
        # - Seasonal availability patterns
        # - Vendor-specific constraints
        
        # For now, simulate based on date patterns
        day_of_week = event_date.weekday()
        
        # Weekends are more likely to be booked
        if day_of_week in [5, 6]:  # Saturday, Sunday
            availability_chance = 0.7
        else:
            availability_chance = 0.9
        
        # Photographers might have different patterns
        if service_type == 'photographer':
            availability_chance *= 0.8  # Generally busier
        
        # Simulate some randomness based on vendor_id
        import hashlib
        vendor_hash = int(hashlib.md5(vendor_id.encode()).hexdigest()[:8], 16)
        random_factor = (vendor_hash % 100) / 100.0
        
        available = random_factor < availability_chance
        confidence = availability_chance if available else (1 - availability_chance)
        
        return {
            "available": available,
            "confidence": confidence,
            "checked_date": event_date.isoformat(),
            "simulation_note": "This is a simulated availability check"
        }
    
    def _generate_compatibility_recommendations(
        self, 
        issues: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations based on compatibility issues"""
        
        recommendations = []
        
        for issue in issues:
            issue_type = issue.get('type')
            
            if issue_type == 'location_mismatch':
                recommendations.append(
                    "Consider selecting vendors from the same city to reduce coordination complexity and travel costs"
                )
            elif issue_type == 'capacity_insufficient':
                recommendations.append(
                    "Select a venue with higher capacity or reduce guest count to match venue limitations"
                )
            elif issue_type == 'vendor_unavailable':
                recommendations.append(
                    "Check alternative dates or search for backup vendors with similar profiles"
                )
        
        return recommendations
    
    async def vendor_availability_check(
        self,
        vendor_id: str,
        service_type: str,
        event_date: str,
        duration_hours: int = 8
    ) -> Dict[str, Any]:
        """Real-time vendor availability checking"""
        
        try:
            event_date_obj = datetime.strptime(event_date, "%Y-%m-%d").date()
            
            # Get vendor details
            vendor = await self._get_vendor_by_id(vendor_id, service_type)
            if not vendor:
                return {
                    "available": False,
                    "error": "Vendor not found",
                    "vendor_id": vendor_id
                }
            
            # Check availability
            availability = await self._simulate_vendor_availability(
                vendor_id, service_type, event_date_obj
            )
            
            # Add additional details
            result = {
                "vendor_id": vendor_id,
                "vendor_name": vendor.get('name'),
                "service_type": service_type,
                "requested_date": event_date,
                "duration_hours": duration_hours,
                "available": availability["available"],
                "confidence": availability["confidence"],
                "checked_at": datetime.now().isoformat(),
                "alternative_dates": []
            }
            
            # If not available, suggest alternative dates
            if not availability["available"]:
                result["alternative_dates"] = await self._suggest_alternative_dates(
                    vendor_id, service_type, event_date_obj
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Availability check failed: {e}")
            raise
    
    async def _get_vendor_by_id(
        self, 
        vendor_id: str, 
        service_type: str
    ) -> Optional[Dict[str, Any]]:
        """Get vendor details by ID"""
        
        model_map = {
            'venue': Venue,
            'caterer': Caterer,
            'photographer': Photographer,
            'makeup_artist': MakeupArtist
        }
        
        if service_type not in model_map:
            return None
        
        model_class = model_map[service_type]
        
        with self.db_setup.get_session() as session:
            vendor = session.query(model_class).filter(
                model_class.id == vendor_id
            ).first()
            
            if not vendor:
                return None
            
            return {
                'id': str(vendor.id),
                'name': vendor.name,
                'location_city': vendor.location_city,
                'attributes': vendor.attributes or {}
            }
    
    async def _suggest_alternative_dates(
        self,
        vendor_id: str,
        service_type: str,
        original_date: date
    ) -> List[str]:
        """Suggest alternative dates when vendor is not available"""
        
        alternatives = []
        
        # Check dates within 2 weeks of original date
        for days_offset in [-7, -3, -1, 1, 3, 7, 14]:
            from datetime import timedelta
            alt_date = original_date + timedelta(days=days_offset)
            
            availability = await self._simulate_vendor_availability(
                vendor_id, service_type, alt_date
            )
            
            if availability["available"]:
                alternatives.append(alt_date.isoformat())
            
            if len(alternatives) >= 3:
                break
        
        return alternatives
    
    async def vendor_similarity_search(
        self,
        reference_vendor_id: str,
        service_type: str,
        similarity_threshold: float = 0.7,
        limit: int = 5
    ) -> Dict[str, Any]:
        """Find similar vendors using ML-based similarity"""
        
        try:
            # Get reference vendor
            reference_vendor = await self._get_vendor_by_id(reference_vendor_id, service_type)
            if not reference_vendor:
                return {
                    "similar_vendors": [],
                    "error": "Reference vendor not found"
                }
            
            # Get all vendors of the same type
            all_vendors = await self._get_filtered_vendors(service_type, {})
            
            # Remove reference vendor from candidates
            candidates = [v for v in all_vendors if v['id'] != reference_vendor_id]
            
            if not candidates:
                return {
                    "similar_vendors": [],
                    "reference_vendor": reference_vendor,
                    "message": "No other vendors found for comparison"
                }
            
            # Calculate similarities
            similar_vendors = await self._calculate_vendor_similarities(
                reference_vendor, candidates, service_type
            )
            
            # Filter by threshold and limit
            filtered_vendors = [
                v for v in similar_vendors 
                if v['similarity_score'] >= similarity_threshold
            ]
            
            result_vendors = filtered_vendors[:limit]
            
            return {
                "reference_vendor": reference_vendor,
                "similar_vendors": result_vendors,
                "total_candidates": len(candidates),
                "above_threshold": len(filtered_vendors),
                "returned_count": len(result_vendors),
                "similarity_threshold": similarity_threshold,
                "search_metadata": {
                    "service_type": service_type,
                    "search_timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            raise
    
    async def _calculate_vendor_similarities(
        self,
        reference_vendor: Dict[str, Any],
        candidates: List[Dict[str, Any]],
        service_type: str
    ) -> List[Dict[str, Any]]:
        """Calculate similarity scores between reference vendor and candidates"""
        
        try:
            # Extract text features
            all_vendors = [reference_vendor] + candidates
            vendor_texts = []
            
            for vendor in all_vendors:
                text_features = []
                text_features.append(vendor.get('name', ''))
                text_features.append(vendor.get('location_city', ''))
                
                attributes = vendor.get('attributes', {})
                if 'about' in attributes:
                    text_features.append(attributes['about'])
                
                # Add service-specific features
                if service_type == 'caterer' and 'cuisines' in attributes:
                    text_features.extend(attributes.get('cuisines', []))
                elif service_type == 'photographer':
                    if 'services' in attributes:
                        text_features.extend(attributes.get('services', []))
                    if 'styles' in attributes:
                        text_features.extend(attributes.get('styles', []))
                
                vendor_texts.append(' '.join(text_features))
            
            # Calculate TF-IDF similarities
            if len(vendor_texts) > 1:
                tfidf_matrix = self.tfidf_vectorizer.fit_transform(vendor_texts)
                similarity_scores = cosine_similarity(
                    tfidf_matrix[0:1], tfidf_matrix[1:]
                ).flatten()
            else:
                similarity_scores = []
            
            # Add similarity scores to candidates
            for i, candidate in enumerate(candidates):
                if i < len(similarity_scores):
                    candidate['similarity_score'] = float(similarity_scores[i])
                else:
                    candidate['similarity_score'] = 0.0
            
            # Sort by similarity score
            candidates.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            return candidates
            
        except Exception as e:
            logger.warning(f"Similarity calculation failed: {e}")
            # Return candidates with zero similarity scores
            for candidate in candidates:
                candidate['similarity_score'] = 0.0
            return candidates
    
    async def run_server(self, host: str = "localhost", port: int = 8001):
        """Run the MCP server"""
        logger.info(f"Starting Vendor Data MCP Server on {host}:{port}")
        
        # Initialize server
        async with self.server.run_server() as server:
            await server.serve_forever()


# Server instance for external usage
vendor_server = VendorDataServer()


if __name__ == "__main__":
    import asyncio
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Run server
    asyncio.run(vendor_server.run_server())
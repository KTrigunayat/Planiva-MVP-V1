"""
Calculation MCP Server for Event Planning Agent

This MCP server provides enhanced calculation capabilities including:
- Enhanced fitness score calculation with ML features
- Advanced budget allocation optimization algorithms
- Cost prediction with confidence intervals
"""

import json
import logging
import asyncio
import math
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import numpy as np
from scipy.optimize import minimize
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

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

from ..config.settings import get_settings

logger = logging.getLogger(__name__)


class CalculationServer:
    """MCP server for complex calculations and optimizations"""
    
    def __init__(self):
        self.settings = get_settings()
        self.server = Server("calculation-server")
        
        # ML models for cost prediction
        self.cost_predictor = None
        self.scaler = StandardScaler()
        
        # Historical data for ML training (simulated)
        self._initialize_ml_models()
        self._setup_tools()
    
    def _initialize_ml_models(self):
        """Initialize ML models for cost prediction"""
        try:
            # Simulate historical event data for training
            historical_data = self._generate_historical_data()
            
            if historical_data:
                features = np.array([d['features'] for d in historical_data])
                costs = np.array([d['total_cost'] for d in historical_data])
                
                # Scale features
                features_scaled = self.scaler.fit_transform(features)
                
                # Train cost predictor
                self.cost_predictor = LinearRegression()
                self.cost_predictor.fit(features_scaled, costs)
                
                logger.info("✅ ML models initialized for cost prediction")
            else:
                logger.warning("⚠️ No historical data available, using fallback calculations")
                
        except Exception as e:
            logger.warning(f"⚠️ ML model initialization failed: {e}")
            self.cost_predictor = None
    
    def _generate_historical_data(self) -> List[Dict[str, Any]]:
        """Generate simulated historical event data for ML training"""
        
        # Simulate 100 historical events
        historical_events = []
        
        for i in range(100):
            # Random event parameters
            guest_count = np.random.randint(50, 1000)
            venue_type = np.random.choice([0, 1, 2])  # 0=banquet, 1=hotel, 2=outdoor
            cuisine_count = np.random.randint(1, 4)
            photography_type = np.random.choice([0, 1])  # 0=basic, 1=premium
            city_tier = np.random.choice([0, 1, 2])  # 0=tier1, 1=tier2, 2=tier3
            
            # Features: [guest_count, venue_type, cuisine_count, photography_type, city_tier]
            features = [guest_count, venue_type, cuisine_count, photography_type, city_tier]
            
            # Simulate total cost based on realistic patterns
            base_cost = guest_count * 1500  # Base cost per guest
            venue_multiplier = [1.0, 1.5, 0.8][venue_type]
            cuisine_multiplier = 1.0 + (cuisine_count - 1) * 0.2
            photo_multiplier = [1.0, 1.8][photography_type]
            city_multiplier = [1.5, 1.0, 0.7][city_tier]
            
            total_cost = base_cost * venue_multiplier * cuisine_multiplier * photo_multiplier * city_multiplier
            
            # Add some noise
            total_cost *= np.random.uniform(0.8, 1.2)
            
            historical_events.append({
                'features': features,
                'total_cost': total_cost,
                'guest_count': guest_count
            })
        
        return historical_events
    
    def _setup_tools(self):
        """Setup MCP tools for calculation operations"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """List available calculation tools"""
            return [
                Tool(
                    name="fitness_score_calculation",
                    description="Enhanced fitness score calculation with ML features",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "vendor_combination": {
                                "type": "object",
                                "description": "Combination of vendors for scoring",
                                "properties": {
                                    "venue": {"type": "object"},
                                    "caterer": {"type": "object"},
                                    "photographer": {"type": "object"},
                                    "makeup_artist": {"type": "object"}
                                }
                            },
                            "client_preferences": {
                                "type": "object",
                                "description": "Client preferences and requirements",
                                "properties": {
                                    "budget": {"type": "number"},
                                    "guest_count": {"type": "integer"},
                                    "style_preferences": {"type": "array", "items": {"type": "string"}},
                                    "location_preference": {"type": "string"},
                                    "priority_weights": {"type": "object"}
                                }
                            },
                            "scoring_options": {
                                "type": "object",
                                "properties": {
                                    "include_ml_features": {"type": "boolean", "default": True},
                                    "weight_price": {"type": "number", "default": 0.4},
                                    "weight_quality": {"type": "number", "default": 0.3},
                                    "weight_compatibility": {"type": "number", "default": 0.3}
                                }
                            }
                        },
                        "required": ["vendor_combination", "client_preferences"]
                    }
                ),
                Tool(
                    name="budget_optimization",
                    description="Advanced budget allocation optimization algorithms",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "total_budget": {"type": "number"},
                            "service_requirements": {
                                "type": "object",
                                "properties": {
                                    "venue": {"type": "object"},
                                    "caterer": {"type": "object"},
                                    "photographer": {"type": "object"},
                                    "makeup_artist": {"type": "object"}
                                }
                            },
                            "client_priorities": {
                                "type": "object",
                                "description": "Client priority weights for each service",
                                "properties": {
                                    "venue": {"type": "number", "default": 0.4},
                                    "caterer": {"type": "number", "default": 0.3},
                                    "photographer": {"type": "number", "default": 0.2},
                                    "makeup_artist": {"type": "number", "default": 0.1}
                                }
                            },
                            "optimization_strategy": {
                                "type": "string",
                                "enum": ["balanced", "quality_focused", "budget_conscious"],
                                "default": "balanced"
                            }
                        },
                        "required": ["total_budget", "service_requirements"]
                    }
                ),
                Tool(
                    name="cost_prediction",
                    description="Predict total costs with confidence intervals",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "event_parameters": {
                                "type": "object",
                                "properties": {
                                    "guest_count": {"type": "integer"},
                                    "venue_type": {"type": "string"},
                                    "cuisine_types": {"type": "array", "items": {"type": "string"}},
                                    "photography_level": {"type": "string"},
                                    "location_city": {"type": "string"},
                                    "event_duration": {"type": "number", "default": 8}
                                },
                                "required": ["guest_count", "venue_type", "location_city"]
                            },
                            "confidence_level": {"type": "number", "default": 0.95}
                        },
                        "required": ["event_parameters"]
                    }
                ),
                Tool(
                    name="vendor_value_analysis",
                    description="Analyze value proposition of vendor combinations",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "vendors": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "service_type": {"type": "string"},
                                        "price": {"type": "number"},
                                        "quality_score": {"type": "number"},
                                        "features": {"type": "array", "items": {"type": "string"}}
                                    }
                                }
                            },
                            "market_benchmarks": {"type": "object"},
                            "analysis_depth": {"type": "string", "enum": ["basic", "detailed"], "default": "detailed"}
                        },
                        "required": ["vendors"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
            """Handle tool calls"""
            try:
                if name == "fitness_score_calculation":
                    result = await self.fitness_score_calculation(**arguments)
                elif name == "budget_optimization":
                    result = await self.budget_optimization(**arguments)
                elif name == "cost_prediction":
                    result = await self.cost_prediction(**arguments)
                elif name == "vendor_value_analysis":
                    result = await self.vendor_value_analysis(**arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
                
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
                
            except Exception as e:
                logger.error(f"Tool call failed for {name}: {e}")
                return [types.TextContent(
                    type="text", 
                    text=json.dumps({"error": str(e), "tool": name})
                )]
    
    async def fitness_score_calculation(
        self,
        vendor_combination: Dict[str, Any],
        client_preferences: Dict[str, Any],
        scoring_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Enhanced fitness score calculation with ML features"""
        
        if not scoring_options:
            scoring_options = {
                "include_ml_features": True,
                "weight_price": 0.4,
                "weight_quality": 0.3,
                "weight_compatibility": 0.3
            }
        
        try:
            # Calculate individual component scores
            price_score = await self._calculate_price_score(vendor_combination, client_preferences)
            quality_score = await self._calculate_quality_score(vendor_combination, client_preferences)
            compatibility_score = await self._calculate_compatibility_score(vendor_combination, client_preferences)
            
            # Apply ML enhancements if enabled
            ml_adjustment = 0.0
            if scoring_options.get("include_ml_features", True):
                ml_adjustment = await self._calculate_ml_adjustment(vendor_combination, client_preferences)
            
            # Calculate weighted fitness score
            weights = {
                "price": scoring_options.get("weight_price", 0.4),
                "quality": scoring_options.get("weight_quality", 0.3),
                "compatibility": scoring_options.get("weight_compatibility", 0.3)
            }
            
            base_score = (
                weights["price"] * price_score +
                weights["quality"] * quality_score +
                weights["compatibility"] * compatibility_score
            )
            
            # Apply ML adjustment
            final_score = min(1.0, max(0.0, base_score + ml_adjustment))
            
            # Calculate confidence interval
            confidence_interval = await self._calculate_score_confidence(
                vendor_combination, client_preferences, final_score
            )
            
            return {
                "fitness_score": final_score,
                "component_scores": {
                    "price_score": price_score,
                    "quality_score": quality_score,
                    "compatibility_score": compatibility_score,
                    "ml_adjustment": ml_adjustment
                },
                "score_weights": weights,
                "confidence_interval": confidence_interval,
                "score_breakdown": {
                    "price_contribution": weights["price"] * price_score,
                    "quality_contribution": weights["quality"] * quality_score,
                    "compatibility_contribution": weights["compatibility"] * compatibility_score
                },
                "calculation_metadata": {
                    "ml_features_used": scoring_options.get("include_ml_features", True),
                    "calculation_timestamp": datetime.now().isoformat(),
                    "algorithm_version": "2.0"
                }
            }
            
        except Exception as e:
            logger.error(f"Fitness score calculation failed: {e}")
            raise
    
    async def _calculate_price_score(
        self, 
        vendor_combination: Dict[str, Any], 
        client_preferences: Dict[str, Any]
    ) -> float:
        """Calculate price-based score component"""
        
        total_budget = client_preferences.get("budget", 0)
        if not total_budget:
            return 0.5  # Neutral score if no budget
        
        total_cost = 0
        guest_count = client_preferences.get("guest_count", 100)
        
        # Calculate total cost from vendor combination
        for service_type, vendor in vendor_combination.items():
            if not vendor:
                continue
                
            if service_type == "venue":
                cost = vendor.get("rental_cost", vendor.get("min_veg_price", 0))
            elif service_type == "caterer":
                per_plate = vendor.get("min_veg_price", 0)
                cost = per_plate * guest_count
            elif service_type == "photographer":
                cost = vendor.get("photo_package_price", 0)
            elif service_type == "makeup_artist":
                cost = vendor.get("bridal_makeup_price", 0)
            else:
                cost = 0
            
            total_cost += cost
        
        if total_cost <= 0:
            return 0.5
        
        # Calculate price score (higher score for better value)
        if total_cost <= total_budget:
            # Under budget - score based on how much budget is saved
            savings_ratio = (total_budget - total_cost) / total_budget
            return 0.7 + (0.3 * savings_ratio)  # Score between 0.7 and 1.0
        else:
            # Over budget - penalize based on overage
            overage_ratio = (total_cost - total_budget) / total_budget
            return max(0.0, 0.7 - (2.0 * overage_ratio))  # Penalty for going over budget
    
    async def _calculate_quality_score(
        self, 
        vendor_combination: Dict[str, Any], 
        client_preferences: Dict[str, Any]
    ) -> float:
        """Calculate quality-based score component"""
        
        quality_scores = []
        
        for service_type, vendor in vendor_combination.items():
            if not vendor:
                continue
            
            # Base quality score from vendor attributes
            base_quality = 0.7  # Default quality score
            
            # Adjust based on vendor attributes
            attributes = vendor.get("attributes", {})
            
            if service_type == "venue":
                # Higher quality for venues with more amenities
                if "amenities" in attributes:
                    amenity_count = len(attributes["amenities"])
                    base_quality += min(0.2, amenity_count * 0.05)
                
                # Quality bonus for capacity match
                capacity = vendor.get("max_seating_capacity", 0)
                guest_count = client_preferences.get("guest_count", 100)
                if capacity >= guest_count * 1.2:  # Good capacity buffer
                    base_quality += 0.1
            
            elif service_type == "caterer":
                # Quality based on cuisine variety
                cuisines = attributes.get("cuisines", [])
                if len(cuisines) >= 3:
                    base_quality += 0.1
                
                # Quality bonus for dietary options
                if vendor.get("veg_only") == False:  # Offers both veg and non-veg
                    base_quality += 0.05
            
            elif service_type == "photographer":
                # Quality based on services offered
                if vendor.get("video_available"):
                    base_quality += 0.15
                
                services = attributes.get("services", [])
                if len(services) >= 3:
                    base_quality += 0.1
            
            elif service_type == "makeup_artist":
                # Quality based on service flexibility
                if vendor.get("on_site_service"):
                    base_quality += 0.1
            
            quality_scores.append(min(1.0, base_quality))
        
        return sum(quality_scores) / len(quality_scores) if quality_scores else 0.5
    
    async def _calculate_compatibility_score(
        self, 
        vendor_combination: Dict[str, Any], 
        client_preferences: Dict[str, Any]
    ) -> float:
        """Calculate compatibility score between vendors and preferences"""
        
        compatibility_factors = []
        
        # Location compatibility
        locations = set()
        for vendor in vendor_combination.values():
            if vendor and vendor.get("location_city"):
                locations.add(vendor["location_city"])
        
        if len(locations) <= 1:
            compatibility_factors.append(1.0)  # All in same city
        else:
            compatibility_factors.append(0.6)  # Multiple cities
        
        # Style compatibility
        style_preferences = client_preferences.get("style_preferences", [])
        if style_preferences:
            style_matches = 0
            total_vendors = 0
            
            for service_type, vendor in vendor_combination.items():
                if not vendor:
                    continue
                
                total_vendors += 1
                vendor_text = ""
                
                # Collect vendor description text
                attributes = vendor.get("attributes", {})
                if "about" in attributes:
                    vendor_text += attributes["about"].lower()
                
                # Check for style matches
                for style in style_preferences:
                    if style.lower() in vendor_text:
                        style_matches += 1
                        break
            
            if total_vendors > 0:
                style_score = style_matches / total_vendors
                compatibility_factors.append(style_score)
        
        # Budget distribution compatibility
        budget_distribution = await self._analyze_budget_distribution(vendor_combination, client_preferences)
        compatibility_factors.append(budget_distribution["balance_score"])
        
        return sum(compatibility_factors) / len(compatibility_factors) if compatibility_factors else 0.5
    
    async def _calculate_ml_adjustment(
        self, 
        vendor_combination: Dict[str, Any], 
        client_preferences: Dict[str, Any]
    ) -> float:
        """Calculate ML-based adjustment to fitness score"""
        
        if not self.cost_predictor:
            return 0.0  # No ML model available
        
        try:
            # Extract features for ML model
            guest_count = client_preferences.get("guest_count", 100)
            
            # Encode venue type
            venue = vendor_combination.get("venue", {})
            venue_type = 0  # Default to banquet hall
            if "hotel" in venue.get("name", "").lower():
                venue_type = 1
            elif "outdoor" in venue.get("attributes", {}).get("about", "").lower():
                venue_type = 2
            
            # Count cuisine types
            caterer = vendor_combination.get("caterer", {})
            cuisines = caterer.get("attributes", {}).get("cuisines", [])
            cuisine_count = len(cuisines) if cuisines else 1
            
            # Photography type
            photographer = vendor_combination.get("photographer", {})
            photography_type = 1 if photographer.get("video_available") else 0
            
            # City tier (simplified)
            location = client_preferences.get("location_preference", "bangalore")
            city_tier = 0 if location.lower() in ["bangalore", "mumbai", "delhi"] else 1
            
            # Create feature vector
            features = np.array([[guest_count, venue_type, cuisine_count, photography_type, city_tier]])
            features_scaled = self.scaler.transform(features)
            
            # Predict cost
            predicted_cost = self.cost_predictor.predict(features_scaled)[0]
            
            # Calculate actual cost
            actual_cost = 0
            for service_type, vendor in vendor_combination.items():
                if not vendor:
                    continue
                
                if service_type == "venue":
                    actual_cost += vendor.get("rental_cost", vendor.get("min_veg_price", 0))
                elif service_type == "caterer":
                    actual_cost += vendor.get("min_veg_price", 0) * guest_count
                elif service_type == "photographer":
                    actual_cost += vendor.get("photo_package_price", 0)
                elif service_type == "makeup_artist":
                    actual_cost += vendor.get("bridal_makeup_price", 0)
            
            # Calculate adjustment based on prediction vs actual
            if predicted_cost > 0:
                cost_ratio = actual_cost / predicted_cost
                
                if cost_ratio < 0.8:  # Significantly cheaper than predicted
                    return 0.1  # Positive adjustment
                elif cost_ratio > 1.2:  # Significantly more expensive
                    return -0.1  # Negative adjustment
                else:
                    return 0.0  # No adjustment
            
            return 0.0
            
        except Exception as e:
            logger.warning(f"ML adjustment calculation failed: {e}")
            return 0.0
    
    async def _calculate_score_confidence(
        self, 
        vendor_combination: Dict[str, Any], 
        client_preferences: Dict[str, Any], 
        fitness_score: float
    ) -> Dict[str, float]:
        """Calculate confidence interval for fitness score"""
        
        # Factors that affect confidence
        confidence_factors = []
        
        # Data completeness
        complete_vendors = sum(1 for v in vendor_combination.values() if v)
        completeness = complete_vendors / 4.0  # Assuming 4 service types
        confidence_factors.append(completeness)
        
        # Price data availability
        price_data_available = 0
        for vendor in vendor_combination.values():
            if vendor and any(key in vendor for key in ["rental_cost", "min_veg_price", "photo_package_price", "bridal_makeup_price"]):
                price_data_available += 1
        
        price_confidence = price_data_available / max(1, complete_vendors)
        confidence_factors.append(price_confidence)
        
        # Preference matching confidence
        style_prefs = client_preferences.get("style_preferences", [])
        pref_confidence = 0.8 if style_prefs else 0.6
        confidence_factors.append(pref_confidence)
        
        # Overall confidence
        overall_confidence = sum(confidence_factors) / len(confidence_factors)
        
        # Calculate confidence interval
        margin = (1 - overall_confidence) * 0.2  # Max margin of 0.2
        
        return {
            "lower_bound": max(0.0, fitness_score - margin),
            "upper_bound": min(1.0, fitness_score + margin),
            "confidence_level": overall_confidence
        }
    
    async def budget_optimization(
        self,
        total_budget: float,
        service_requirements: Dict[str, Any],
        client_priorities: Optional[Dict[str, float]] = None,
        optimization_strategy: str = "balanced"
    ) -> Dict[str, Any]:
        """Advanced budget allocation optimization algorithms"""
        
        if not client_priorities:
            client_priorities = {
                "venue": 0.4,
                "caterer": 0.3,
                "photographer": 0.2,
                "makeup_artist": 0.1
            }
        
        try:
            # Define optimization strategies
            strategies = {
                "balanced": {"risk_tolerance": 0.5, "quality_weight": 0.5},
                "quality_focused": {"risk_tolerance": 0.3, "quality_weight": 0.8},
                "budget_conscious": {"risk_tolerance": 0.8, "quality_weight": 0.2}
            }
            
            strategy_params = strategies.get(optimization_strategy, strategies["balanced"])
            
            # Calculate base allocations using priorities
            base_allocations = {}
            for service, priority in client_priorities.items():
                base_allocations[service] = total_budget * priority
            
            # Optimize allocations using constraints
            optimized_allocations = await self._optimize_budget_allocation(
                total_budget, service_requirements, base_allocations, strategy_params
            )
            
            # Generate multiple allocation scenarios
            scenarios = await self._generate_allocation_scenarios(
                total_budget, service_requirements, client_priorities, strategy_params
            )
            
            # Calculate expected outcomes for each scenario
            scenario_analysis = []
            for scenario in scenarios:
                analysis = await self._analyze_allocation_scenario(scenario, service_requirements)
                scenario_analysis.append(analysis)
            
            # Select recommended scenario
            recommended_scenario = max(scenario_analysis, key=lambda x: x["overall_score"])
            
            return {
                "recommended_allocation": recommended_scenario["allocation"],
                "optimization_results": {
                    "total_budget": total_budget,
                    "strategy_used": optimization_strategy,
                    "allocation_efficiency": recommended_scenario["efficiency_score"],
                    "risk_assessment": recommended_scenario["risk_score"],
                    "expected_quality": recommended_scenario["quality_score"]
                },
                "alternative_scenarios": scenario_analysis,
                "allocation_breakdown": {
                    service: {
                        "allocated_amount": amount,
                        "percentage_of_budget": (amount / total_budget) * 100,
                        "priority_weight": client_priorities.get(service, 0)
                    }
                    for service, amount in recommended_scenario["allocation"].items()
                },
                "optimization_metadata": {
                    "algorithm_used": "constrained_optimization",
                    "scenarios_evaluated": len(scenarios),
                    "optimization_timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Budget optimization failed: {e}")
            raise
    
    async def _optimize_budget_allocation(
        self,
        total_budget: float,
        service_requirements: Dict[str, Any],
        base_allocations: Dict[str, float],
        strategy_params: Dict[str, float]
    ) -> Dict[str, float]:
        """Optimize budget allocation using mathematical optimization"""
        
        services = list(base_allocations.keys())
        
        # Define objective function
        def objective(allocations):
            # Minimize negative utility (maximize utility)
            utility = 0
            for i, service in enumerate(services):
                allocation = allocations[i]
                base_allocation = base_allocations[service]
                
                # Utility increases with allocation but with diminishing returns
                if allocation > 0:
                    utility += math.log(allocation) * strategy_params["quality_weight"]
                
                # Penalty for deviating from base allocation
                deviation_penalty = abs(allocation - base_allocation) / base_allocation
                utility -= deviation_penalty * (1 - strategy_params["risk_tolerance"])
            
            return -utility  # Minimize negative utility
        
        # Constraints
        def budget_constraint(allocations):
            return total_budget - sum(allocations)
        
        # Minimum allocation constraints
        def min_allocation_constraint(allocations, service_idx):
            service = services[service_idx]
            min_allocation = base_allocations[service] * 0.5  # At least 50% of base
            return allocations[service_idx] - min_allocation
        
        # Set up optimization
        initial_guess = [base_allocations[service] for service in services]
        
        constraints = [
            {"type": "eq", "fun": budget_constraint}
        ]
        
        # Add minimum allocation constraints
        for i in range(len(services)):
            constraints.append({
                "type": "ineq", 
                "fun": lambda x, idx=i: min_allocation_constraint(x, idx)
            })
        
        # Bounds (allocations must be positive)
        bounds = [(base_allocations[service] * 0.1, total_budget * 0.8) for service in services]
        
        try:
            # Solve optimization
            result = minimize(
                objective, 
                initial_guess, 
                method='SLSQP', 
                bounds=bounds, 
                constraints=constraints
            )
            
            if result.success:
                optimized = {services[i]: result.x[i] for i in range(len(services))}
            else:
                # Fallback to base allocations if optimization fails
                optimized = base_allocations.copy()
            
            return optimized
            
        except Exception as e:
            logger.warning(f"Optimization failed, using base allocations: {e}")
            return base_allocations.copy()
    
    async def _generate_allocation_scenarios(
        self,
        total_budget: float,
        service_requirements: Dict[str, Any],
        client_priorities: Dict[str, float],
        strategy_params: Dict[str, float]
    ) -> List[Dict[str, float]]:
        """Generate multiple budget allocation scenarios"""
        
        scenarios = []
        
        # Scenario 1: Priority-based allocation
        priority_allocation = {}
        for service, priority in client_priorities.items():
            priority_allocation[service] = total_budget * priority
        scenarios.append(priority_allocation)
        
        # Scenario 2: Equal allocation
        equal_amount = total_budget / len(client_priorities)
        equal_allocation = {service: equal_amount for service in client_priorities.keys()}
        scenarios.append(equal_allocation)
        
        # Scenario 3: Venue-focused allocation
        venue_focused = client_priorities.copy()
        venue_focused["venue"] = min(0.6, venue_focused["venue"] + 0.2)
        # Redistribute the extra from other services
        remaining_weight = 1.0 - venue_focused["venue"]
        other_services = [s for s in venue_focused.keys() if s != "venue"]
        for service in other_services:
            venue_focused[service] = remaining_weight / len(other_services)
        
        venue_focused_allocation = {service: total_budget * weight for service, weight in venue_focused.items()}
        scenarios.append(venue_focused_allocation)
        
        # Scenario 4: Experience-focused allocation (photography + makeup)
        experience_focused = client_priorities.copy()
        experience_focused["photographer"] = min(0.35, experience_focused["photographer"] + 0.15)
        experience_focused["makeup_artist"] = min(0.25, experience_focused["makeup_artist"] + 0.15)
        
        # Redistribute
        total_experience = experience_focused["photographer"] + experience_focused["makeup_artist"]
        remaining = 1.0 - total_experience
        experience_focused["venue"] = remaining * 0.6
        experience_focused["caterer"] = remaining * 0.4
        
        experience_focused_allocation = {service: total_budget * weight for service, weight in experience_focused.items()}
        scenarios.append(experience_focused_allocation)
        
        return scenarios
    
    async def _analyze_allocation_scenario(
        self, 
        allocation: Dict[str, float], 
        service_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze a budget allocation scenario"""
        
        # Calculate efficiency score
        efficiency_score = 0.0
        quality_score = 0.0
        risk_score = 0.0
        
        total_allocated = sum(allocation.values())
        
        for service, amount in allocation.items():
            # Efficiency: how well the allocation matches typical market rates
            market_rate = self._get_market_rate(service, service_requirements.get(service, {}))
            if market_rate > 0:
                efficiency = min(1.0, amount / market_rate)
                efficiency_score += efficiency
            
            # Quality: higher allocations generally mean higher quality options
            max_reasonable = market_rate * 2 if market_rate > 0 else amount
            quality = min(1.0, amount / max_reasonable) if max_reasonable > 0 else 0.5
            quality_score += quality
            
            # Risk: very low or very high allocations are risky
            if market_rate > 0:
                ratio = amount / market_rate
                if ratio < 0.5 or ratio > 3.0:
                    risk_score += 0.25  # High risk
                else:
                    risk_score += 0.05  # Low risk
        
        # Normalize scores
        num_services = len(allocation)
        efficiency_score /= num_services
        quality_score /= num_services
        risk_score = 1.0 - (risk_score / num_services)  # Invert risk (higher is better)
        
        # Overall score
        overall_score = (efficiency_score * 0.4) + (quality_score * 0.4) + (risk_score * 0.2)
        
        return {
            "allocation": allocation,
            "efficiency_score": efficiency_score,
            "quality_score": quality_score,
            "risk_score": risk_score,
            "overall_score": overall_score,
            "total_allocated": total_allocated,
            "budget_utilization": total_allocated / sum(allocation.values()) if allocation else 0
        }
    
    def _get_market_rate(self, service: str, requirements: Dict[str, Any]) -> float:
        """Get typical market rate for a service"""
        
        # Simplified market rates (in practice, this would use real market data)
        base_rates = {
            "venue": 500000,  # Base venue cost
            "caterer": 150000,  # Base catering cost for 100 guests
            "photographer": 80000,  # Base photography package
            "makeup_artist": 25000  # Base makeup service
        }
        
        base_rate = base_rates.get(service, 100000)
        
        # Adjust based on requirements
        guest_count = requirements.get("guest_count", 100)
        if service == "caterer":
            base_rate = (base_rate / 100) * guest_count  # Scale with guest count
        
        return base_rate
    
    async def _analyze_budget_distribution(
        self, 
        vendor_combination: Dict[str, Any], 
        client_preferences: Dict[str, Any]
    ) -> Dict[str, float]:
        """Analyze how well budget is distributed across services"""
        
        total_cost = 0
        service_costs = {}
        guest_count = client_preferences.get("guest_count", 100)
        
        for service_type, vendor in vendor_combination.items():
            if not vendor:
                service_costs[service_type] = 0
                continue
            
            if service_type == "venue":
                cost = vendor.get("rental_cost", vendor.get("min_veg_price", 0))
            elif service_type == "caterer":
                cost = vendor.get("min_veg_price", 0) * guest_count
            elif service_type == "photographer":
                cost = vendor.get("photo_package_price", 0)
            elif service_type == "makeup_artist":
                cost = vendor.get("bridal_makeup_price", 0)
            else:
                cost = 0
            
            service_costs[service_type] = cost
            total_cost += cost
        
        # Calculate distribution balance
        if total_cost > 0:
            proportions = {service: cost / total_cost for service, cost in service_costs.items()}
            
            # Ideal proportions (industry standard)
            ideal_proportions = {"venue": 0.4, "caterer": 0.35, "photographer": 0.15, "makeup_artist": 0.1}
            
            # Calculate balance score
            balance_score = 0.0
            for service in ideal_proportions:
                actual = proportions.get(service, 0)
                ideal = ideal_proportions[service]
                deviation = abs(actual - ideal)
                balance_score += max(0, 1 - (deviation * 2))  # Penalize large deviations
            
            balance_score /= len(ideal_proportions)
        else:
            balance_score = 0.5
        
        return {
            "balance_score": balance_score,
            "service_proportions": proportions if total_cost > 0 else {},
            "total_cost": total_cost
        }
    
    async def cost_prediction(
        self,
        event_parameters: Dict[str, Any],
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """Predict total costs with confidence intervals"""
        
        try:
            guest_count = event_parameters["guest_count"]
            venue_type = event_parameters["venue_type"]
            location_city = event_parameters["location_city"]
            
            # Base cost calculation
            base_cost_per_guest = self._get_base_cost_per_guest(location_city)
            base_total_cost = base_cost_per_guest * guest_count
            
            # Venue type multiplier
            venue_multipliers = {
                "banquet_hall": 1.0,
                "hotel": 1.4,
                "outdoor": 0.8,
                "resort": 1.6,
                "palace": 2.0
            }
            venue_multiplier = venue_multipliers.get(venue_type.lower(), 1.0)
            
            # Cuisine complexity multiplier
            cuisine_types = event_parameters.get("cuisine_types", ["indian"])
            cuisine_multiplier = 1.0 + (len(cuisine_types) - 1) * 0.15
            
            # Photography level multiplier
            photography_level = event_parameters.get("photography_level", "standard")
            photo_multipliers = {"basic": 0.8, "standard": 1.0, "premium": 1.5, "luxury": 2.0}
            photo_multiplier = photo_multipliers.get(photography_level.lower(), 1.0)
            
            # Calculate predicted cost
            predicted_cost = base_total_cost * venue_multiplier * cuisine_multiplier * photo_multiplier
            
            # Use ML model if available
            if self.cost_predictor:
                ml_prediction = await self._get_ml_cost_prediction(event_parameters)
                # Blend traditional and ML predictions
                predicted_cost = (predicted_cost * 0.6) + (ml_prediction * 0.4)
            
            # Calculate confidence interval
            uncertainty_factor = self._calculate_prediction_uncertainty(event_parameters)
            margin = predicted_cost * uncertainty_factor * (1 - confidence_level + 0.1)
            
            # Service breakdown
            service_breakdown = self._calculate_service_breakdown(predicted_cost, event_parameters)
            
            # Market comparison
            market_comparison = await self._get_market_comparison(predicted_cost, event_parameters)
            
            return {
                "predicted_total_cost": predicted_cost,
                "confidence_interval": {
                    "lower_bound": predicted_cost - margin,
                    "upper_bound": predicted_cost + margin,
                    "confidence_level": confidence_level
                },
                "cost_per_guest": predicted_cost / guest_count,
                "service_breakdown": service_breakdown,
                "market_comparison": market_comparison,
                "prediction_factors": {
                    "base_cost_per_guest": base_cost_per_guest,
                    "venue_multiplier": venue_multiplier,
                    "cuisine_multiplier": cuisine_multiplier,
                    "photography_multiplier": photo_multiplier,
                    "location_factor": self._get_location_factor(location_city)
                },
                "prediction_metadata": {
                    "ml_model_used": self.cost_predictor is not None,
                    "uncertainty_factor": uncertainty_factor,
                    "prediction_timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Cost prediction failed: {e}")
            raise
    
    def _get_base_cost_per_guest(self, location_city: str) -> float:
        """Get base cost per guest based on location"""
        
        # City-based cost factors
        city_factors = {
            "mumbai": 2500,
            "delhi": 2200,
            "bangalore": 2000,
            "hyderabad": 1800,
            "chennai": 1900,
            "pune": 1700,
            "kochi": 1600,
            "ahmedabad": 1500
        }
        
        return city_factors.get(location_city.lower(), 1800)  # Default to mid-tier city
    
    def _get_location_factor(self, location_city: str) -> float:
        """Get location cost factor"""
        
        tier1_cities = ["mumbai", "delhi", "bangalore"]
        tier2_cities = ["hyderabad", "chennai", "pune"]
        
        if location_city.lower() in tier1_cities:
            return 1.2
        elif location_city.lower() in tier2_cities:
            return 1.0
        else:
            return 0.8
    
    async def _get_ml_cost_prediction(self, event_parameters: Dict[str, Any]) -> float:
        """Get cost prediction from ML model"""
        
        if not self.cost_predictor:
            return 0
        
        try:
            # Encode parameters for ML model
            guest_count = event_parameters["guest_count"]
            
            venue_type_encoding = {"banquet_hall": 0, "hotel": 1, "outdoor": 2, "resort": 1, "palace": 1}
            venue_type = venue_type_encoding.get(event_parameters["venue_type"].lower(), 0)
            
            cuisine_count = len(event_parameters.get("cuisine_types", ["indian"]))
            
            photo_encoding = {"basic": 0, "standard": 0, "premium": 1, "luxury": 1}
            photography_type = photo_encoding.get(event_parameters.get("photography_level", "standard").lower(), 0)
            
            city_encoding = {"mumbai": 0, "delhi": 0, "bangalore": 0}
            city_tier = 0 if event_parameters["location_city"].lower() in city_encoding else 1
            
            # Create feature vector
            features = np.array([[guest_count, venue_type, cuisine_count, photography_type, city_tier]])
            features_scaled = self.scaler.transform(features)
            
            # Predict
            prediction = self.cost_predictor.predict(features_scaled)[0]
            return max(0, prediction)
            
        except Exception as e:
            logger.warning(f"ML cost prediction failed: {e}")
            return 0
    
    def _calculate_prediction_uncertainty(self, event_parameters: Dict[str, Any]) -> float:
        """Calculate uncertainty factor for cost prediction"""
        
        uncertainty = 0.1  # Base uncertainty
        
        # Higher uncertainty for larger events
        guest_count = event_parameters["guest_count"]
        if guest_count > 500:
            uncertainty += 0.05
        elif guest_count < 50:
            uncertainty += 0.03
        
        # Higher uncertainty for complex events
        cuisine_count = len(event_parameters.get("cuisine_types", []))
        if cuisine_count > 3:
            uncertainty += 0.02
        
        # Higher uncertainty for premium services
        photography_level = event_parameters.get("photography_level", "standard")
        if photography_level.lower() in ["premium", "luxury"]:
            uncertainty += 0.03
        
        return min(0.25, uncertainty)  # Cap at 25%
    
    def _calculate_service_breakdown(
        self, 
        total_cost: float, 
        event_parameters: Dict[str, Any]
    ) -> Dict[str, Dict[str, float]]:
        """Calculate cost breakdown by service"""
        
        # Standard industry proportions
        proportions = {
            "venue": 0.40,
            "catering": 0.35,
            "photography": 0.15,
            "makeup_and_styling": 0.10
        }
        
        # Adjust proportions based on event parameters
        photography_level = event_parameters.get("photography_level", "standard")
        if photography_level.lower() in ["premium", "luxury"]:
            proportions["photography"] += 0.05
            proportions["venue"] -= 0.03
            proportions["catering"] -= 0.02
        
        venue_type = event_parameters.get("venue_type", "banquet_hall")
        if venue_type.lower() in ["resort", "palace"]:
            proportions["venue"] += 0.10
            proportions["catering"] -= 0.05
            proportions["photography"] -= 0.03
            proportions["makeup_and_styling"] -= 0.02
        
        # Calculate breakdown
        breakdown = {}
        for service, proportion in proportions.items():
            cost = total_cost * proportion
            breakdown[service] = {
                "estimated_cost": cost,
                "percentage": proportion * 100,
                "cost_per_guest": cost / event_parameters["guest_count"]
            }
        
        return breakdown
    
    async def _get_market_comparison(
        self, 
        predicted_cost: float, 
        event_parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare predicted cost with market benchmarks"""
        
        guest_count = event_parameters["guest_count"]
        cost_per_guest = predicted_cost / guest_count
        
        # Market benchmarks by city tier
        location_city = event_parameters["location_city"]
        
        if location_city.lower() in ["mumbai", "delhi", "bangalore"]:
            market_ranges = {"low": 1800, "medium": 2500, "high": 3500}
        elif location_city.lower() in ["hyderabad", "chennai", "pune"]:
            market_ranges = {"low": 1500, "medium": 2000, "high": 2800}
        else:
            market_ranges = {"low": 1200, "medium": 1600, "high": 2200}
        
        # Determine market position
        if cost_per_guest <= market_ranges["low"]:
            market_position = "budget_friendly"
        elif cost_per_guest <= market_ranges["medium"]:
            market_position = "mid_range"
        elif cost_per_guest <= market_ranges["high"]:
            market_position = "premium"
        else:
            market_position = "luxury"
        
        return {
            "market_position": market_position,
            "cost_per_guest": cost_per_guest,
            "market_benchmarks": market_ranges,
            "percentile_estimate": self._calculate_market_percentile(cost_per_guest, market_ranges),
            "comparison_note": self._generate_comparison_note(market_position, cost_per_guest, market_ranges)
        }
    
    def _calculate_market_percentile(self, cost_per_guest: float, market_ranges: Dict[str, float]) -> int:
        """Calculate approximate market percentile"""
        
        if cost_per_guest <= market_ranges["low"]:
            return 25
        elif cost_per_guest <= market_ranges["medium"]:
            return 50
        elif cost_per_guest <= market_ranges["high"]:
            return 75
        else:
            return 90
    
    def _generate_comparison_note(
        self, 
        market_position: str, 
        cost_per_guest: float, 
        market_ranges: Dict[str, float]
    ) -> str:
        """Generate human-readable comparison note"""
        
        notes = {
            "budget_friendly": f"This estimate (₹{cost_per_guest:,.0f}/guest) is in the budget-friendly range, offering good value for money.",
            "mid_range": f"This estimate (₹{cost_per_guest:,.0f}/guest) is in the mid-range category, providing a good balance of quality and cost.",
            "premium": f"This estimate (₹{cost_per_guest:,.0f}/guest) is in the premium range, indicating higher quality services and venues.",
            "luxury": f"This estimate (₹{cost_per_guest:,.0f}/guest) is in the luxury category, representing top-tier services and venues."
        }
        
        return notes.get(market_position, "Cost estimate calculated based on event parameters.")
    
    async def vendor_value_analysis(
        self,
        vendors: List[Dict[str, Any]],
        market_benchmarks: Optional[Dict[str, Any]] = None,
        analysis_depth: str = "detailed"
    ) -> Dict[str, Any]:
        """Analyze value proposition of vendor combinations"""
        
        try:
            if not vendors:
                return {"error": "No vendors provided for analysis"}
            
            # Calculate value scores for each vendor
            vendor_analyses = []
            
            for vendor in vendors:
                analysis = await self._analyze_single_vendor_value(vendor, market_benchmarks)
                vendor_analyses.append(analysis)
            
            # Overall portfolio analysis
            portfolio_analysis = await self._analyze_vendor_portfolio(vendor_analyses)
            
            # Generate recommendations
            recommendations = self._generate_value_recommendations(vendor_analyses, portfolio_analysis)
            
            result = {
                "vendor_analyses": vendor_analyses,
                "portfolio_summary": portfolio_analysis,
                "recommendations": recommendations,
                "analysis_metadata": {
                    "analysis_depth": analysis_depth,
                    "vendors_analyzed": len(vendors),
                    "analysis_timestamp": datetime.now().isoformat()
                }
            }
            
            # Add detailed insights if requested
            if analysis_depth == "detailed":
                result["detailed_insights"] = await self._generate_detailed_insights(vendor_analyses)
            
            return result
            
        except Exception as e:
            logger.error(f"Vendor value analysis failed: {e}")
            raise
    
    async def _analyze_single_vendor_value(
        self, 
        vendor: Dict[str, Any], 
        market_benchmarks: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze value proposition of a single vendor"""
        
        service_type = vendor.get("service_type", "unknown")
        price = vendor.get("price", 0)
        quality_score = vendor.get("quality_score", 0.7)
        features = vendor.get("features", [])
        
        # Calculate value metrics
        value_analysis = {
            "vendor_info": {
                "service_type": service_type,
                "price": price,
                "quality_score": quality_score,
                "feature_count": len(features)
            },
            "value_metrics": {},
            "market_comparison": {},
            "strengths": [],
            "weaknesses": []
        }
        
        # Price-to-quality ratio
        if price > 0 and quality_score > 0:
            value_ratio = quality_score / (price / 100000)  # Normalize price
            value_analysis["value_metrics"]["price_quality_ratio"] = value_ratio
        
        # Feature value score
        feature_value = len(features) * 0.1  # Each feature adds 10% value
        value_analysis["value_metrics"]["feature_value_score"] = min(1.0, feature_value)
        
        # Market comparison if benchmarks available
        if market_benchmarks and service_type in market_benchmarks:
            benchmark = market_benchmarks[service_type]
            market_price = benchmark.get("average_price", price)
            
            if market_price > 0:
                price_competitiveness = 1.0 - ((price - market_price) / market_price)
                value_analysis["market_comparison"]["price_competitiveness"] = price_competitiveness
                
                if price < market_price * 0.8:
                    value_analysis["strengths"].append("Significantly below market price")
                elif price > market_price * 1.2:
                    value_analysis["weaknesses"].append("Above market price")
        
        # Quality assessment
        if quality_score >= 0.8:
            value_analysis["strengths"].append("High quality score")
        elif quality_score < 0.6:
            value_analysis["weaknesses"].append("Below average quality score")
        
        # Feature assessment
        if len(features) >= 5:
            value_analysis["strengths"].append("Rich feature set")
        elif len(features) < 2:
            value_analysis["weaknesses"].append("Limited features")
        
        # Overall value score
        value_components = [
            value_analysis["value_metrics"].get("price_quality_ratio", 0.5),
            value_analysis["value_metrics"].get("feature_value_score", 0.5),
            value_analysis["market_comparison"].get("price_competitiveness", 0.5)
        ]
        
        overall_value = sum(value_components) / len(value_components)
        value_analysis["overall_value_score"] = overall_value
        
        return value_analysis
    
    async def _analyze_vendor_portfolio(self, vendor_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the overall vendor portfolio"""
        
        if not vendor_analyses:
            return {}
        
        # Calculate portfolio metrics
        total_cost = sum(v["vendor_info"]["price"] for v in vendor_analyses)
        avg_quality = sum(v["vendor_info"]["quality_score"] for v in vendor_analyses) / len(vendor_analyses)
        avg_value = sum(v["overall_value_score"] for v in vendor_analyses) / len(vendor_analyses)
        
        # Service type distribution
        service_types = [v["vendor_info"]["service_type"] for v in vendor_analyses]
        service_distribution = {st: service_types.count(st) for st in set(service_types)}
        
        # Risk assessment
        risk_factors = []
        if any(v["overall_value_score"] < 0.4 for v in vendor_analyses):
            risk_factors.append("Some vendors have low value scores")
        
        if total_cost > 0:
            cost_concentration = max(v["vendor_info"]["price"] / total_cost for v in vendor_analyses)
            if cost_concentration > 0.6:
                risk_factors.append("High cost concentration in single vendor")
        
        return {
            "portfolio_metrics": {
                "total_estimated_cost": total_cost,
                "average_quality_score": avg_quality,
                "average_value_score": avg_value,
                "vendor_count": len(vendor_analyses)
            },
            "service_distribution": service_distribution,
            "risk_assessment": {
                "risk_level": "high" if len(risk_factors) > 2 else "medium" if risk_factors else "low",
                "risk_factors": risk_factors
            },
            "portfolio_balance": self._assess_portfolio_balance(vendor_analyses)
        }
    
    def _assess_portfolio_balance(self, vendor_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess balance of the vendor portfolio"""
        
        # Quality balance
        quality_scores = [v["vendor_info"]["quality_score"] for v in vendor_analyses]
        quality_std = np.std(quality_scores) if len(quality_scores) > 1 else 0
        
        # Price balance
        prices = [v["vendor_info"]["price"] for v in vendor_analyses if v["vendor_info"]["price"] > 0]
        price_balance = "balanced"
        
        if prices:
            price_ratio = max(prices) / min(prices) if min(prices) > 0 else 1
            if price_ratio > 10:
                price_balance = "unbalanced"
            elif price_ratio > 5:
                price_balance = "moderately_unbalanced"
        
        return {
            "quality_consistency": "high" if quality_std < 0.1 else "medium" if quality_std < 0.2 else "low",
            "price_balance": price_balance,
            "overall_balance_score": 1.0 - min(1.0, quality_std + (0.1 if price_balance != "balanced" else 0))
        }
    
    def _generate_value_recommendations(
        self, 
        vendor_analyses: List[Dict[str, Any]], 
        portfolio_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate value-based recommendations"""
        
        recommendations = []
        
        # Individual vendor recommendations
        for analysis in vendor_analyses:
            service_type = analysis["vendor_info"]["service_type"]
            value_score = analysis["overall_value_score"]
            
            if value_score < 0.4:
                recommendations.append(f"Consider alternative {service_type} vendors for better value")
            elif value_score > 0.8:
                recommendations.append(f"Excellent value found for {service_type} service")
        
        # Portfolio recommendations
        portfolio_metrics = portfolio_analysis.get("portfolio_metrics", {})
        avg_value = portfolio_metrics.get("average_value_score", 0.5)
        
        if avg_value < 0.5:
            recommendations.append("Overall portfolio value is below average - consider vendor alternatives")
        elif avg_value > 0.7:
            recommendations.append("Strong overall portfolio value - good vendor selection")
        
        # Risk-based recommendations
        risk_assessment = portfolio_analysis.get("risk_assessment", {})
        risk_factors = risk_assessment.get("risk_factors", [])
        
        for risk_factor in risk_factors:
            if "low value" in risk_factor:
                recommendations.append("Review vendors with low value scores for potential replacements")
            elif "cost concentration" in risk_factor:
                recommendations.append("Consider diversifying costs across vendors to reduce risk")
        
        return recommendations
    
    async def _generate_detailed_insights(self, vendor_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate detailed insights for vendor analysis"""
        
        insights = {
            "cost_efficiency_analysis": {},
            "quality_distribution": {},
            "feature_analysis": {},
            "optimization_opportunities": []
        }
        
        # Cost efficiency analysis
        prices = [v["vendor_info"]["price"] for v in vendor_analyses if v["vendor_info"]["price"] > 0]
        if prices:
            insights["cost_efficiency_analysis"] = {
                "total_cost": sum(prices),
                "average_cost": sum(prices) / len(prices),
                "cost_range": {"min": min(prices), "max": max(prices)},
                "cost_distribution": "even" if max(prices) / min(prices) < 3 else "uneven"
            }
        
        # Quality distribution
        quality_scores = [v["vendor_info"]["quality_score"] for v in vendor_analyses]
        insights["quality_distribution"] = {
            "average_quality": sum(quality_scores) / len(quality_scores),
            "quality_range": {"min": min(quality_scores), "max": max(quality_scores)},
            "consistency": "high" if max(quality_scores) - min(quality_scores) < 0.2 else "medium"
        }
        
        # Feature analysis
        all_features = []
        for analysis in vendor_analyses:
            all_features.extend(analysis["vendor_info"].get("features", []))
        
        insights["feature_analysis"] = {
            "total_unique_features": len(set(all_features)),
            "average_features_per_vendor": len(all_features) / len(vendor_analyses),
            "feature_overlap": len(all_features) - len(set(all_features))
        }
        
        # Optimization opportunities
        for analysis in vendor_analyses:
            if analysis["overall_value_score"] < 0.5:
                service_type = analysis["vendor_info"]["service_type"]
                insights["optimization_opportunities"].append(
                    f"Optimize {service_type} selection for better value"
                )
        
        return insights
    
    async def run_server(self, host: str = "localhost", port: int = 8002):
        """Run the MCP server"""
        logger.info(f"Starting Calculation MCP Server on {host}:{port}")
        
        # Initialize server
        async with self.server.run_server() as server:
            await server.serve_forever()


# Server instance for external usage
calculation_server = CalculationServer()


if __name__ == "__main__":
    import asyncio
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Run server
    asyncio.run(calculation_server.run_server())
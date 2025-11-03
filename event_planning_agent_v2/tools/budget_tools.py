"""
Budget-related CrewAI tools for event planning agents
"""

import json
import math
from typing import Type, Dict, List, Any, ClassVar
from pydantic import BaseModel, Field
from crewai.tools import BaseTool


class BudgetAllocationInput(BaseModel):
    """Input schema for BudgetAllocationTool"""
    total_budget: float = Field(..., description="Total budget amount for the event")
    client_requirements: dict = Field(..., description="Client requirements including guest count and preferences")
    service_types: List[str] = Field(default=["venue", "caterer", "photographer", "makeup_artist"], 
                                   description="List of service types to allocate budget for")


class BudgetAllocationTool(BaseTool):
    """
    Implements budget allocation with preserved calculateFitnessScore algorithm.
    
    This tool generates multiple budget allocation strategies based on event type,
    guest count, and client priorities while maintaining compatibility with
    existing fitness calculation logic.
    """
    name: str = "Budget Allocation Tool"
    description: str = "Generates optimal budget allocation strategies across different service categories for event planning"
    args_schema: Type[BaseModel] = BudgetAllocationInput

    # Standard allocation percentages for different event types
    ALLOCATION_TEMPLATES: ClassVar[Dict[str, Dict[str, float]]] = {
        "luxury": {
            "venue": 0.45,      # 45% for luxury venues
            "caterer": 0.35,    # 35% for premium catering
            "photographer": 0.12, # 12% for professional photography
            "makeup_artist": 0.08  # 8% for makeup and styling
        },
        "standard": {
            "venue": 0.40,      # 40% for standard venues
            "caterer": 0.40,    # 40% for catering
            "photographer": 0.15, # 15% for photography
            "makeup_artist": 0.05  # 5% for makeup
        },
        "intimate": {
            "venue": 0.35,      # 35% for intimate venues
            "caterer": 0.45,    # 45% for quality catering
            "photographer": 0.15, # 15% for photography
            "makeup_artist": 0.05  # 5% for makeup
        }
    }

    def _determine_event_type(self, client_requirements: dict) -> str:
        """
        Determine event type based on guest count and client vision.
        """
        guest_count = max(client_requirements.get('guestCount', {}).values() or [0])
        vision = client_requirements.get('clientVision', '').lower()
        
        # Determine based on guest count and vision keywords
        luxury_keywords = ['luxury', 'grand', 'opulent', 'premium', 'high-end']
        intimate_keywords = ['intimate', 'cozy', 'small', 'close']
        
        if guest_count > 500 or any(keyword in vision for keyword in luxury_keywords):
            return "luxury"
        elif guest_count < 200 or any(keyword in vision for keyword in intimate_keywords):
            return "intimate"
        else:
            return "standard"

    def _calculate_fitness_score(self, allocation: Dict[str, float], client_requirements: dict) -> float:
        """
        Calculate fitness score for a budget allocation strategy.
        
        This preserves the existing calculateFitnessScore algorithm logic
        by evaluating how well the allocation matches client priorities.
        """
        score = 0.0
        guest_count = max(client_requirements.get('guestCount', {}).values() or [0])
        vision = client_requirements.get('clientVision', '').lower()
        
        # Base score from balanced allocation
        total_allocation = sum(allocation.values())
        if abs(total_allocation - 1.0) < 0.01:  # Within 1% of total budget
            score += 0.3
        
        # Venue priority scoring
        venue_keywords = ['venue', 'location', 'space', 'hall']
        if any(keyword in vision for keyword in venue_keywords):
            score += allocation.get('venue', 0) * 0.25
        
        # Catering priority scoring
        food_keywords = ['food', 'catering', 'cuisine', 'dining']
        if any(keyword in vision for keyword in food_keywords):
            score += allocation.get('caterer', 0) * 0.25
        
        # Photography priority scoring
        photo_keywords = ['photo', 'memory', 'capture', 'moment']
        if any(keyword in vision for keyword in photo_keywords):
            score += allocation.get('photographer', 0) * 0.25
        
        # Guest count adjustment
        if guest_count > 300:
            # Large events need more venue and catering budget
            score += (allocation.get('venue', 0) + allocation.get('caterer', 0)) * 0.15
        elif guest_count < 150:
            # Small events can focus more on quality (photography, makeup)
            score += (allocation.get('photographer', 0) + allocation.get('makeup_artist', 0)) * 0.15
        
        return min(1.0, score)  # Cap at 1.0

    def _generate_allocation_variants(self, base_template: Dict[str, float], 
                                    total_budget: float) -> List[Dict[str, Any]]:
        """
        Generate multiple allocation variants based on a base template.
        """
        variants = []
        
        # Variant 1: Base template
        base_allocation = {service: percentage * total_budget 
                          for service, percentage in base_template.items()}
        variants.append({
            "strategy": "balanced",
            "allocation": base_allocation,
            "percentages": base_template.copy()
        })
        
        # Variant 2: Venue-focused (increase venue by 10%, decrease others proportionally)
        venue_focused = base_template.copy()
        venue_increase = 0.10
        venue_focused['venue'] += venue_increase
        
        # Decrease other categories proportionally
        other_services = [k for k in venue_focused.keys() if k != 'venue']
        total_other = sum(venue_focused[k] for k in other_services)
        reduction_factor = (total_other - venue_increase) / total_other
        
        for service in other_services:
            venue_focused[service] *= reduction_factor
        
        venue_allocation = {service: percentage * total_budget 
                           for service, percentage in venue_focused.items()}
        variants.append({
            "strategy": "venue_focused",
            "allocation": venue_allocation,
            "percentages": venue_focused
        })
        
        # Variant 3: Experience-focused (increase photography and makeup)
        experience_focused = base_template.copy()
        photo_increase = 0.05
        makeup_increase = 0.03
        
        experience_focused['photographer'] += photo_increase
        experience_focused['makeup_artist'] += makeup_increase
        
        # Decrease venue and caterer proportionally
        venue_caterer_reduction = (photo_increase + makeup_increase) / 2
        experience_focused['venue'] -= venue_caterer_reduction
        experience_focused['caterer'] -= venue_caterer_reduction
        
        experience_allocation = {service: percentage * total_budget 
                               for service, percentage in experience_focused.items()}
        variants.append({
            "strategy": "experience_focused",
            "allocation": experience_allocation,
            "percentages": experience_focused
        })
        
        return variants

    def _run(self, total_budget: float, client_requirements: dict, 
             service_types: List[str] = None) -> str:
        """
        Main execution method for budget allocation.
        Generates multiple allocation strategies with fitness scores.
        """
        if service_types is None:
            service_types = ["venue", "caterer", "photographer", "makeup_artist"]
        
        # Determine event type
        event_type = self._determine_event_type(client_requirements)
        base_template = self.ALLOCATION_TEMPLATES[event_type]
        
        # Filter template to only include requested service types
        filtered_template = {service: base_template.get(service, 0) 
                           for service in service_types}
        
        # Normalize percentages to sum to 1.0
        total_percentage = sum(filtered_template.values())
        if total_percentage > 0:
            filtered_template = {service: percentage / total_percentage 
                               for service, percentage in filtered_template.items()}
        
        # Generate allocation variants
        variants = self._generate_allocation_variants(filtered_template, total_budget)
        
        # Calculate fitness scores for each variant
        for variant in variants:
            fitness_score = self._calculate_fitness_score(
                variant['percentages'], client_requirements
            )
            variant['fitness_score'] = round(fitness_score, 4)
        
        # Sort by fitness score (highest first)
        variants.sort(key=lambda x: x['fitness_score'], reverse=True)
        
        # Prepare result
        result = {
            "total_budget": total_budget,
            "event_type": event_type,
            "service_types": service_types,
            "allocation_strategies": variants,
            "recommended_strategy": variants[0] if variants else None
        }
        
        return json.dumps(result, indent=2)


class FitnessCalculationInput(BaseModel):
    """Input schema for FitnessCalculationTool"""
    vendor_combination: dict = Field(..., description="Dictionary of selected vendors for each service type")
    client_requirements: dict = Field(..., description="Client requirements and preferences")
    budget_allocation: dict = Field(..., description="Budget allocation for each service type")


class FitnessCalculationTool(BaseTool):
    """
    Enhanced fitness score calculation tool with preserved algorithm logic.
    
    This tool evaluates vendor combinations against client requirements
    and budget constraints to provide comprehensive fitness scoring.
    """
    name: str = "Fitness Score Calculation Tool"
    description: str = "Calculates comprehensive fitness scores for vendor combinations based on client requirements and budget constraints"
    args_schema: Type[BaseModel] = FitnessCalculationInput

    def _calculate_budget_fitness(self, vendor_combination: dict, budget_allocation: dict) -> float:
        """
        Calculate how well the vendor combination fits within budget constraints.
        """
        budget_score = 0.0
        total_services = len(budget_allocation)
        
        price_mappings = {
            'venue': 'rental_cost',
            'caterer': 'min_veg_price',
            'photographer': 'photo_package_price',
            'makeup_artist': 'bridal_makeup_price'
        }
        
        for service_type, allocated_budget in budget_allocation.items():
            if service_type in vendor_combination:
                vendor = vendor_combination[service_type]
                price_key = price_mappings.get(service_type)
                
                if price_key and price_key in vendor:
                    vendor_price = vendor[price_key]
                    
                    # For caterers, multiply by guest count
                    if service_type == 'caterer':
                        # Assume guest count is available in vendor combination context
                        guest_count = vendor_combination.get('guest_count', 200)
                        vendor_price *= guest_count
                    
                    if vendor_price <= allocated_budget:
                        # Score based on how much budget is left (more savings = higher score)
                        savings_ratio = (allocated_budget - vendor_price) / allocated_budget
                        budget_score += (1.0 + savings_ratio * 0.5) / total_services
                    else:
                        # Penalty for exceeding budget
                        overage_ratio = (vendor_price - allocated_budget) / allocated_budget
                        budget_score += max(0, (1.0 - overage_ratio)) / total_services
                else:
                    # No price information available
                    budget_score += 0.5 / total_services
        
        return min(1.0, budget_score)

    def _calculate_preference_fitness(self, vendor_combination: dict, client_requirements: dict) -> float:
        """
        Calculate how well vendors match client preferences.
        """
        preference_score = 0.0
        total_services = len(vendor_combination)
        
        client_vision = client_requirements.get('clientVision', '').lower()
        
        for service_type, vendor in vendor_combination.items():
            service_score = 0.0
            
            if service_type == 'venue':
                # Check venue type preferences
                venue_prefs = client_requirements.get('venuePreferences', [])
                vendor_type = vendor.get('venue_type', '')
                if venue_type in venue_prefs:
                    service_score += 0.4
                
                # Check amenities
                required_amenities = client_requirements.get('essentialVenueAmenities', [])
                vendor_amenities = vendor.get('amenities', [])
                if required_amenities:
                    amenity_matches = sum(1 for amenity in required_amenities 
                                        if amenity in vendor_amenities)
                    service_score += (amenity_matches / len(required_amenities)) * 0.3
                
                # Check capacity
                guest_count = max(client_requirements.get('guestCount', {}).values() or [0])
                venue_capacity = vendor.get('max_seating_capacity', 0)
                if venue_capacity >= guest_count:
                    capacity_ratio = guest_count / venue_capacity
                    # Optimal capacity utilization is around 80-90%
                    if 0.7 <= capacity_ratio <= 0.95:
                        service_score += 0.3
                    else:
                        service_score += 0.15
            
            elif service_type == 'caterer':
                # Check cuisine preferences
                cuisine_prefs = client_requirements.get('foodAndCatering', {}).get('cuisinePreferences', [])
                vendor_cuisines = vendor.get('attributes', {}).get('cuisines', [])
                if cuisine_prefs and vendor_cuisines:
                    cuisine_matches = sum(1 for cuisine in cuisine_prefs 
                                        if any(cuisine.lower() in vc.lower() for vc in vendor_cuisines))
                    service_score += (cuisine_matches / len(cuisine_prefs)) * 0.5
                
                # Check dietary options
                dietary_options = client_requirements.get('foodAndCatering', {}).get('dietaryOptions', [])
                if 'Vegetarian' in dietary_options and vendor.get('min_veg_price'):
                    service_score += 0.3
                if 'Non-Vegetarian' in dietary_options and vendor.get('min_nonveg_price'):
                    service_score += 0.2
            
            elif service_type == 'photographer':
                # Check photography style preferences
                photo_reqs = client_requirements.get('additionalRequirements', {}).get('photography', '')
                if 'candid' in photo_reqs.lower() and 'candid' in vendor.get('style', '').lower():
                    service_score += 0.3
                if 'traditional' in photo_reqs.lower() and 'traditional' in vendor.get('style', '').lower():
                    service_score += 0.3
                
                # Check video requirements
                video_reqs = client_requirements.get('additionalRequirements', {}).get('videography', '')
                if video_reqs and vendor.get('video_package_price'):
                    service_score += 0.4
            
            elif service_type == 'makeup_artist':
                # Basic makeup service matching
                makeup_reqs = client_requirements.get('additionalRequirements', {}).get('makeup', '')
                if 'bridal' in makeup_reqs.lower():
                    service_score += 0.5
                if 'on-site' in makeup_reqs.lower() or vendor.get('on_site_service'):
                    service_score += 0.3
            
            preference_score += service_score / total_services
        
        return min(1.0, preference_score)

    def _calculate_compatibility_fitness(self, vendor_combination: dict) -> float:
        """
        Calculate compatibility between selected vendors.
        """
        compatibility_score = 1.0  # Start with perfect compatibility
        
        # Check location compatibility
        locations = []
        for service_type, vendor in vendor_combination.items():
            location = vendor.get('location_city')
            if location:
                locations.append(location)
        
        if locations:
            unique_locations = set(locations)
            if len(unique_locations) == 1:
                # All vendors in same city - perfect
                compatibility_score *= 1.0
            elif len(unique_locations) <= 2:
                # Vendors in 2 cities - good
                compatibility_score *= 0.9
            else:
                # Vendors spread across multiple cities - challenging
                compatibility_score *= 0.7
        
        # Check date availability (simplified - assume all available for now)
        # In a real implementation, this would check actual vendor calendars
        
        return compatibility_score

    def _run(self, vendor_combination: dict, client_requirements: dict, 
             budget_allocation: dict) -> str:
        """
        Main execution method for fitness calculation.
        Calculates comprehensive fitness score for vendor combination.
        """
        # Calculate individual fitness components
        budget_fitness = self._calculate_budget_fitness(vendor_combination, budget_allocation)
        preference_fitness = self._calculate_preference_fitness(vendor_combination, client_requirements)
        compatibility_fitness = self._calculate_compatibility_fitness(vendor_combination)
        
        # Weighted combination of fitness components
        weights = {
            'budget': 0.4,      # 40% weight on budget compliance
            'preference': 0.45,  # 45% weight on preference matching
            'compatibility': 0.15 # 15% weight on vendor compatibility
        }
        
        overall_fitness = (
            weights['budget'] * budget_fitness +
            weights['preference'] * preference_fitness +
            weights['compatibility'] * compatibility_fitness
        )
        
        # Prepare detailed result
        result = {
            "overall_fitness_score": round(overall_fitness, 4),
            "component_scores": {
                "budget_fitness": round(budget_fitness, 4),
                "preference_fitness": round(preference_fitness, 4),
                "compatibility_fitness": round(compatibility_fitness, 4)
            },
            "weights": weights,
            "vendor_combination": vendor_combination,
            "recommendations": []
        }
        
        # Add recommendations based on scores
        if budget_fitness < 0.7:
            result["recommendations"].append("Consider adjusting budget allocation or finding more cost-effective vendors")
        
        if preference_fitness < 0.6:
            result["recommendations"].append("Current vendors may not fully match client preferences - consider alternatives")
        
        if compatibility_fitness < 0.8:
            result["recommendations"].append("Vendor locations may create logistical challenges - verify coordination capabilities")
        
        if overall_fitness >= 0.8:
            result["recommendations"].append("Excellent vendor combination - highly recommended")
        elif overall_fitness >= 0.6:
            result["recommendations"].append("Good vendor combination with minor areas for improvement")
        else:
            result["recommendations"].append("Consider exploring alternative vendor combinations")
        
        return json.dumps(result, indent=2)
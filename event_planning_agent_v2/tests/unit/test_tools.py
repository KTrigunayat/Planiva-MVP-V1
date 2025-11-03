"""
Unit tests for CrewAI tools
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date
from decimal import Decimal

from tools.vendor_tools import HybridFilterTool, VendorDatabaseTool, VendorRankingTool
from tools.budget_tools import BudgetAllocationTool, FitnessCalculationTool
from tools.timeline_tools import ConflictDetectionTool, TimelineGenerationTool
from tools.blueprint_tools import BlueprintGenerationTool, DocumentFormattingTool


class TestVendorTools:
    """Test vendor-related tools"""
    
    def test_hybrid_filter_tool_initialization(self):
        """Test HybridFilterTool can be initialized"""
        tool = HybridFilterTool()
        assert tool.name == "Hybrid Client Form Processor"
        assert hasattr(tool, 'llm')
    
    def test_hybrid_filter_tool_hard_filters(self):
        """Test hard filter extraction logic"""
        tool = HybridFilterTool()
        
        client_data = {
            'clientVision': 'We want a wedding in Bangalore',
            'guestCount': {'Reception': 300},
            'venuePreferences': ['Hotel'],
            'essentialVenueAmenities': ['Parking', 'AC']
        }
        
        hard_filters = tool._extract_hard_filters(client_data, 'venue')
        
        assert hard_filters['location_city'] == 'Bangalore'
        assert hard_filters['capacity_min'] == 300
        assert 'Hotel' in hard_filters['venue_type']
        assert 'Parking' in hard_filters['required_amenities']
    
    def test_vendor_database_tool_initialization(self):
        """Test VendorDatabaseTool can be initialized"""
        tool = VendorDatabaseTool()
        assert tool.name == "Vendor Database Search & Rank Tool"
        assert 'venue' in tool.TABLE_CONFIG
        assert 'caterer' in tool.TABLE_CONFIG


class TestBudgetTools:
    """Test budget-related tools"""
    
    def test_budget_allocation_tool_initialization(self):
        """Test BudgetAllocationTool can be initialized"""
        tool = BudgetAllocationTool()
        assert tool.name == "Budget Allocation Tool"
        assert 'luxury' in tool.ALLOCATION_TEMPLATES
        assert 'standard' in tool.ALLOCATION_TEMPLATES
        assert 'intimate' in tool.ALLOCATION_TEMPLATES
    
    def test_budget_allocation_event_type_detection(self):
        """Test event type detection logic"""
        tool = BudgetAllocationTool()
        
        # Test luxury event detection
        luxury_requirements = {
            'guestCount': {'Reception': 600},
            'clientVision': 'We want a grand and luxurious celebration'
        }
        event_type = tool._determine_event_type(luxury_requirements)
        assert event_type == 'luxury'
        
        # Test intimate event detection
        intimate_requirements = {
            'guestCount': {'Reception': 100},
            'clientVision': 'We want an intimate, cozy celebration'
        }
        event_type = tool._determine_event_type(intimate_requirements)
        assert event_type == 'intimate'
        
        # Test standard event detection
        standard_requirements = {
            'guestCount': {'Reception': 250},
            'clientVision': 'We want a beautiful wedding celebration'
        }
        event_type = tool._determine_event_type(standard_requirements)
        assert event_type == 'standard'
    
    def test_budget_allocation_fitness_scoring(self):
        """Test fitness scoring for budget allocations"""
        tool = BudgetAllocationTool()
        
        # Test balanced allocation
        balanced_allocation = {
            'venue': 0.40,
            'caterer': 0.40,
            'photographer': 0.15,
            'makeup_artist': 0.05
        }
        
        client_requirements = {
            'guestCount': {'Reception': 250},
            'clientVision': 'Modern venue with great food and photography'
        }
        
        score = tool._calculate_fitness_score(balanced_allocation, client_requirements)
        assert 0 <= score <= 1
        assert score > 0.3  # Should get reasonable score for balanced allocation
    
    def test_budget_allocation_variant_generation(self):
        """Test generation of budget allocation variants"""
        tool = BudgetAllocationTool()
        
        base_template = {
            'venue': 0.40,
            'caterer': 0.40,
            'photographer': 0.15,
            'makeup_artist': 0.05
        }
        
        variants = tool._generate_allocation_variants(base_template, 1000000)
        
        assert len(variants) == 3
        assert variants[0]['strategy'] == 'balanced'
        assert variants[1]['strategy'] == 'venue_focused'
        assert variants[2]['strategy'] == 'experience_focused'
        
        # Check that all variants sum to approximately the total budget
        for variant in variants:
            total_allocation = sum(variant['allocation'].values())
            assert abs(total_allocation - 1000000) < 1000  # Within ₹1000 tolerance
    
    def test_budget_allocation_tool_execution(self):
        """Test complete budget allocation tool execution"""
        tool = BudgetAllocationTool()
        
        client_requirements = {
            'guestCount': {'Reception': 300},
            'clientVision': 'Luxury wedding with premium vendors'
        }
        
        result = tool._run(
            total_budget=1500000,
            client_requirements=client_requirements,
            service_types=['venue', 'caterer', 'photographer', 'makeup_artist']
        )
        
        result_data = json.loads(result)
        
        assert result_data['total_budget'] == 1500000
        assert result_data['event_type'] == 'luxury'
        assert len(result_data['allocation_strategies']) == 3
        assert 'recommended_strategy' in result_data
        assert result_data['recommended_strategy'] is not None
        
        # Check that all strategies have fitness scores
        for strategy in result_data['allocation_strategies']:
            assert 'fitness_score' in strategy
            assert 0 <= strategy['fitness_score'] <= 1
    
    def test_fitness_calculation_tool_initialization(self):
        """Test FitnessCalculationTool can be initialized"""
        tool = FitnessCalculationTool()
        assert tool.name == "Fitness Score Calculation Tool"
        assert hasattr(tool, '_calculate_budget_fitness')
        assert hasattr(tool, '_calculate_preference_fitness')
        assert hasattr(tool, '_calculate_compatibility_fitness')
    
    def test_fitness_calculation_budget_fitness(self):
        """Test budget fitness calculation"""
        tool = FitnessCalculationTool()
        
        vendor_combination = {
            'venue': {'rental_cost': 300000},
            'caterer': {'min_veg_price': 800},
            'photographer': {'photo_package_price': 80000},
            'makeup_artist': {'bridal_makeup_price': 25000},
            'guest_count': 250
        }
        
        budget_allocation = {
            'venue': 350000,
            'caterer': 220000,  # 800 * 250 + buffer
            'photographer': 100000,
            'makeup_artist': 30000
        }
        
        budget_fitness = tool._calculate_budget_fitness(vendor_combination, budget_allocation)
        
        assert 0 <= budget_fitness <= 1
        assert budget_fitness > 0.7  # Should be high since vendors are within budget
    
    def test_fitness_calculation_preference_fitness(self):
        """Test preference fitness calculation"""
        tool = FitnessCalculationTool()
        
        vendor_combination = {
            'venue': {
                'venue_type': 'Hotel',
                'max_seating_capacity': 300,
                'amenities': ['Parking', 'AC', 'Sound System']
            },
            'caterer': {
                'attributes': {'cuisines': ['Indian', 'Continental']}
            }
        }
        
        client_requirements = {
            'guestCount': {'Reception': 250},
            'venuePreferences': ['Hotel'],
            'essentialVenueAmenities': ['Parking', 'AC'],
            'foodAndCatering': {'cuisinePreferences': ['Indian']}
        }
        
        preference_fitness = tool._calculate_preference_fitness(vendor_combination, client_requirements)
        
        assert 0 <= preference_fitness <= 1
        assert preference_fitness > 0.5  # Should be decent given good matches
    
    def test_fitness_calculation_compatibility_fitness(self):
        """Test compatibility fitness calculation"""
        tool = FitnessCalculationTool()
        
        # Test same city vendors (high compatibility)
        same_city_combination = {
            'venue': {'location_city': 'Bangalore'},
            'caterer': {'location_city': 'Bangalore'},
            'photographer': {'location_city': 'Bangalore'}
        }
        
        compatibility_score = tool._calculate_compatibility_fitness(same_city_combination)
        assert compatibility_score == 1.0
        
        # Test multi-city vendors (lower compatibility)
        multi_city_combination = {
            'venue': {'location_city': 'Bangalore'},
            'caterer': {'location_city': 'Mumbai'},
            'photographer': {'location_city': 'Delhi'}
        }
        
        compatibility_score = tool._calculate_compatibility_fitness(multi_city_combination)
        assert compatibility_score < 1.0
        assert compatibility_score >= 0.6  # Should still be reasonable
    
    def test_fitness_calculation_tool_execution(self):
        """Test complete fitness calculation tool execution"""
        tool = FitnessCalculationTool()
        
        vendor_combination = {
            'venue': {
                'rental_cost': 300000,
                'venue_type': 'Hotel',
                'max_seating_capacity': 300,
                'location_city': 'Bangalore'
            },
            'caterer': {
                'min_veg_price': 800,
                'location_city': 'Bangalore',
                'attributes': {'cuisines': ['Indian', 'Continental']}
            }
        }
        
        client_requirements = {
            'guestCount': {'Reception': 250},
            'clientVision': 'Modern wedding in Bangalore',
            'venuePreferences': ['Hotel'],
            'foodAndCatering': {'cuisinePreferences': ['Indian']}
        }
        
        budget_allocation = {
            'venue': 350000,
            'caterer': 220000
        }
        
        result = tool._run(vendor_combination, client_requirements, budget_allocation)
        result_data = json.loads(result)
        
        assert 'overall_fitness_score' in result_data
        assert 'component_scores' in result_data
        assert 'recommendations' in result_data
        
        # Check component scores
        components = result_data['component_scores']
        assert 'budget_fitness' in components
        assert 'preference_fitness' in components
        assert 'compatibility_fitness' in components
        
        # Check overall score is reasonable
        overall_score = result_data['overall_fitness_score']
        assert 0 <= overall_score <= 1
        
        # Check weights are applied correctly
        weights = result_data['weights']
        expected_score = (
            weights['budget'] * components['budget_fitness'] +
            weights['preference'] * components['preference_fitness'] +
            weights['compatibility'] * components['compatibility_fitness']
        )
        assert abs(overall_score - expected_score) < 0.001


class TestTimelineTools:
    """Test timeline-related tools"""
    
    def test_conflict_detection_tool_initialization(self):
        """Test ConflictDetectionTool can be initialized"""
        tool = ConflictDetectionTool()
        assert tool.name == "Conflict Detection Tool"
        assert 'venue' in tool.VENDOR_CONSTRAINTS
        assert 'photographer' in tool.VENDOR_CONSTRAINTS
    
    def test_conflict_detection_date_parsing(self):
        """Test date parsing functionality"""
        tool = ConflictDetectionTool()
        
        parsed_date = tool._parse_event_date('2024-12-25')
        assert parsed_date.year == 2024
        assert parsed_date.month == 12
        assert parsed_date.day == 25
    
    def test_timeline_generation_tool_initialization(self):
        """Test TimelineGenerationTool can be initialized"""
        tool = TimelineGenerationTool()
        assert tool.name == "Timeline Generation Tool"
        assert 'wedding' in tool.TIMELINE_TEMPLATES
        assert hasattr(tool, 'llm')


class TestBlueprintTools:
    """Test blueprint-related tools"""
    
    def test_blueprint_generation_tool_initialization(self):
        """Test BlueprintGenerationTool can be initialized"""
        tool = BlueprintGenerationTool()
        assert tool.name == "Blueprint Generation Tool"
        assert hasattr(tool, 'llm')
    
    def test_document_formatting_tool_initialization(self):
        """Test DocumentFormattingTool can be initialized"""
        tool = DocumentFormattingTool()
        assert tool.name == "Document Formatting Tool"


class TestToolIntegration:
    """Test tool integration and workflow"""
    
    def test_tool_workflow_compatibility(self):
        """Test that tools can work together in a workflow"""
        # Test data
        client_data = {
            'clientName': 'Test Client',
            'guestCount': {'Reception': 200},
            'clientVision': 'Modern elegant wedding in Bangalore',
            'venuePreferences': ['Hotel'],
            'budget': 1000000
        }
        
        # Test HybridFilterTool output format
        filter_tool = HybridFilterTool()
        
        # Mock LLM response for testing
        with patch.object(filter_tool, 'llm') as mock_llm:
            mock_llm.invoke.return_value = '{"style": ["modern", "elegant"]}'
            
            filter_result = filter_tool._run(client_data, 'venue')
            filter_data = json.loads(filter_result)
            
            assert filter_data['service_type'] == 'venue'
            assert 'hard_filters' in filter_data
            assert 'soft_preferences' in filter_data
        
        # Test BudgetAllocationTool
        budget_tool = BudgetAllocationTool()
        budget_result = budget_tool._run(1000000, client_data)
        budget_data = json.loads(budget_result)
        
        assert budget_data['total_budget'] == 1000000
        assert 'allocation_strategies' in budget_data
        assert len(budget_data['allocation_strategies']) > 0
    
    def test_tool_error_handling(self):
        """Test tool error handling"""
        # Test VendorDatabaseTool with invalid JSON
        vendor_tool = VendorDatabaseTool()
        result = vendor_tool._run("invalid json")
        assert "Error:" in result
        
        # Test ConflictDetectionTool with invalid date
        conflict_tool = ConflictDetectionTool()
        with pytest.raises(ValueError):
            conflict_tool._parse_event_date("invalid-date")


if __name__ == "__main__":
    # Run basic tests
    print("Running CrewAI Tools Tests...")
    
    # Test tool initialization
    tools = [
        HybridFilterTool(),
        VendorDatabaseTool(), 
        VendorRankingTool(),
        BudgetAllocationTool(),
        FitnessCalculationTool(),
        ConflictDetectionTool(),
        TimelineGenerationTool(),
        BlueprintGenerationTool(),
        DocumentFormattingTool()
    ]
    
    print(f"✅ Successfully initialized {len(tools)} tools")
    
    # Test basic functionality
    test_client_data = {
        'clientName': 'Test Wedding',
        'guestCount': {'Reception': 250},
        'clientVision': 'Elegant modern wedding in Bangalore',
        'venuePreferences': ['Hotel'],
        'budget': 800000
    }
    
    # Test budget allocation
    budget_tool = BudgetAllocationTool()
    budget_result = budget_tool._run(800000, test_client_data)
    budget_data = json.loads(budget_result)
    print(f"✅ Budget allocation generated {len(budget_data['allocation_strategies'])} strategies")
    
    # Test conflict detection
    conflict_tool = ConflictDetectionTool()
    test_vendor_combo = {
        'venue': {'name': 'Test Venue', 'location_city': 'Bangalore'},
        'caterer': {'name': 'Test Caterer', 'location_city': 'Bangalore'}
    }
    test_timeline = {
        'activities': [
            {'name': 'Setup', 'start_time': '10:00', 'duration': 2.0},
            {'name': 'Ceremony', 'start_time': '12:00', 'duration': 1.5}
        ]
    }
    
    conflict_result = conflict_tool._run(test_vendor_combo, '2024-12-25', test_timeline)
    conflict_data = json.loads(conflict_result)
    print(f"✅ Conflict detection completed with feasibility score: {conflict_data['feasibility_score']}")
    
    print("🎉 All basic tool tests passed!")
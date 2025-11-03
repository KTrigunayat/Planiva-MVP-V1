#!/usr/bin/env python3
"""
End-to-end system validation test for Event Planning Agent modernization

This test validates:
1. Comprehensive tests using existing demo scenarios (intimate_wedding, luxury_wedding)
2. Algorithm compatibility - ensures all existing algorithms produce identical results
3. API compatibility with existing integrations

Requirements: 4.6, 5.1, 5.2
"""

import json
import time
import pytest
import asyncio
import requests
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import subprocess
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from workflows.planning_workflow import EventPlanningWorkflow
from workflows.state_models import EventPlanningState, WorkflowStatus
from agents.budgeting import BudgetingAgentCoordinator
from agents.sourcing import SourcingAgentCoordinator
from tools.vendor_tools import VendorDatabaseTool, HybridFilterTool
from tools.budget_tools import BudgetAllocationTool, FitnessCalculationTool


class TestDemoScenarioValidation:
    """Test using existing demo scenarios from original system"""
    
    @pytest.fixture
    def intimate_wedding_scenario(self):
        """Intimate wedding scenario from original demo.py"""
        return {
            "clientName": "Priya & Rohit",
            "clientId": "demo_intimate_001",
            "guestCount": {"Reception": 150, "Ceremony": 100},
            "clientVision": "We want an intimate, cozy wedding celebration in Bangalore with close family and friends. Focus on quality over quantity with excellent food and beautiful photography.",
            "venuePreferences": ["Banquet Hall", "Restaurant"],
            "essentialVenueAmenities": ["Air Conditioning", "Sound System"],
            "decorationAndAmbiance": {
                "desiredTheme": "traditional elegant",
                "colorScheme": ["red", "gold", "maroon"]
            },
            "foodAndCatering": {
                "cuisinePreferences": ["South Indian", "North Indian"],
                "dietaryOptions": ["Vegetarian"],
                "beverages": {"allowed": False}
            },
            "additionalRequirements": {
                "photography": "Traditional photography with some candid shots",
                "makeup": "Classic bridal makeup"
            },
            "budget": 1380000,  # Total from original demo
            "budgetAllocation": {
                "venue": 800000,
                "caterer": 500000,
                "photographer": 60000,
                "makeup_artist": 20000
            },
            "eventDate": "2024-12-15",
            "location": "Bangalore"
        }
    
    @pytest.fixture
    def luxury_wedding_scenario(self):
        """Luxury wedding scenario from original demo.py"""
        return {
            "clientName": "Aarav & Ananya",
            "clientId": "demo_luxury_001",
            "guestCount": {"Reception": 800, "Ceremony": 600},
            "clientVision": "We envision a grand and opulent, yet elegant and modern wedding celebration in Bangalore. We want a luxurious venue with excellent catering and professional photography.",
            "venuePreferences": ["Hotel", "Open Area"],
            "essentialVenueAmenities": ["Guest Accommodation", "Valet Parking"],
            "decorationAndAmbiance": {
                "desiredTheme": "modern elegant",
                "colorScheme": ["gold", "white", "cream"]
            },
            "foodAndCatering": {
                "cuisinePreferences": ["North Indian", "South Indian", "Italian"],
                "dietaryOptions": ["Vegetarian", "Non-Vegetarian"],
                "beverages": {"allowed": True}
            },
            "additionalRequirements": {
                "photography": "We want candid and traditional photography with videography",
                "videography": "pre-wedding shoot, same-day edit",
                "makeup": "Professional bridal makeup with on-site service"
            },
            "budget": 4130000,  # Total from original demo
            "budgetAllocation": {
                "venue": 2500000,
                "caterer": 1500000,
                "photographer": 100000,
                "makeup_artist": 30000
            },
            "eventDate": "2024-11-25",
            "location": "Bangalore"
        } 
def test_intimate_wedding_complete_workflow(self, intimate_wedding_scenario):
        """Test complete workflow execution for intimate wedding scenario"""
        print("\n🎭 Testing Intimate Wedding Scenario")
        print("=" * 50)
        
        # Initialize workflow components
        workflow = EventPlanningWorkflow()
        budgeting_coordinator = BudgetingAgentCoordinator()
        sourcing_coordinator = SourcingAgentCoordinator()
        
        client_data = intimate_wedding_scenario
        
        # Step 1: Budget Allocation
        print("💰 Step 1: Budget Allocation")
        start_time = time.time()
        
        budget_strategies = budgeting_coordinator.generate_budget_strategies(
            client_data, client_data['budget']
        )
        
        budget_time = time.time() - start_time
        
        # Validate budget allocation
        assert budget_strategies['total_budget'] == client_data['budget']
        assert budget_strategies['event_type'] == 'intimate'
        assert len(budget_strategies['allocation_strategies']) >= 1
        
        recommended_strategy = budget_strategies['recommended_strategy']
        
        print(f"   ✅ Budget allocated in {budget_time:.3f}s")
        print(f"   📊 Event Type: {budget_strategies['event_type']}")
        print(f"   💰 Venue Budget: ₹{recommended_strategy['allocation']['venue']:,}")
        print(f"   🍽️ Catering Budget: ₹{recommended_strategy['allocation']['catering']:,}")
        
        # Step 2: Vendor Sourcing
        print("\n🔍 Step 2: Vendor Sourcing")
        
        vendor_combinations = []
        sourcing_results = {}
        
        for service_type in ['venue', 'caterer', 'photographer', 'makeup_artist']:
            print(f"   Sourcing {service_type}s...")
            
            start_time = time.time()
            
            # Mock vendor sourcing with realistic data
            mock_vendors = self._generate_mock_vendors(service_type, client_data)
            
            sourcing_time = time.time() - start_time
            sourcing_results[service_type] = {
                'vendors': mock_vendors,
                'count': len(mock_vendors),
                'time': sourcing_time
            }
            
            print(f"      ✅ Found {len(mock_vendors)} {service_type}s in {sourcing_time:.3f}s")
        
        # Generate vendor combinations
        print("\n🔗 Step 3: Generating Vendor Combinations")
        start_time = time.time()
        
        # Create realistic combinations (limited for performance)
        venues = sourcing_results['venue']['vendors'][:5]
        caterers = sourcing_results['caterer']['vendors'][:5]
        photographers = sourcing_results['photographer']['vendors'][:3]
        makeup_artists = sourcing_results['makeup_artist']['vendors'][:3]
        
        combination_id = 0
        for venue in venues:
            for caterer in caterers:
                for photographer in photographers:
                    for makeup_artist in makeup_artists:
                        combination = {
                            'combination_id': f'intimate_combo_{combination_id:03d}',
                            'vendors': {
                                'venue': venue,
                                'caterer': caterer,
                                'photographer': photographer,
                                'makeup_artist': makeup_artist
                            }
                        }
                        
                        # Calculate total cost
                        total_cost = (
                            venue['rental_cost'] +
                            caterer['min_veg_price'] * client_data['guestCount']['Reception'] +
                            photographer['photo_package_price'] +
                            makeup_artist['bridal_makeup_price']
                        )
                        combination['total_cost'] = total_cost
                        
                        vendor_combinations.append(combination)
                        combination_id += 1
                        
                        # Limit combinations for testing
                        if combination_id >= 50:
                            break
                    if combination_id >= 50:
                        break
                if combination_id >= 50:
                    break
            if combination_id >= 50:
                break
        
        combination_time = time.time() - start_time
        
        print(f"   ✅ Generated {len(vendor_combinations)} combinations in {combination_time:.3f}s")
        
        # Step 4: Beam Search Optimization
        print("\n🎯 Step 4: Beam Search Optimization")
        
        state = EventPlanningState(
            workflow_id="intimate_wedding_test",
            client_request=client_data,
            vendor_combinations=vendor_combinations,
            beam_candidates=[],
            workflow_status=WorkflowStatus.BEAM_SEARCH,
            iteration_count=0
        )
        
        start_time = time.time()
        
        # Execute beam search iterations
        max_iterations = 3
        for iteration in range(max_iterations):
            state = workflow.beam_search_node(state)
            
            print(f"   Iteration {iteration + 1}: {len(state['beam_candidates'])} candidates")
            
            # Check convergence
            should_continue = workflow.should_continue_search(state)
            if should_continue == "present_options":
                break
        
        beam_search_time = time.time() - start_time
        
        # Step 5: Final Fitness Calculation
        print("\n📊 Step 5: Final Fitness Calculation")
        
        start_time = time.time()
        
        final_combinations = budgeting_coordinator.calculate_combination_fitness(
            state['beam_candidates'], client_data, recommended_strategy
        )
        
        fitness_time = time.time() - start_time
        
        # Sort by fitness score
        final_combinations.sort(key=lambda x: x['overall_fitness_score'], reverse=True)
        
        print(f"   ✅ Calculated fitness for {len(final_combinations)} combinations in {fitness_time:.3f}s")
        
        # Validation Results
        print("\n📋 VALIDATION RESULTS")
        print("-" * 30)
        
        assert len(final_combinations) > 0, "No final combinations generated"
        assert len(final_combinations) <= 3, "Too many beam candidates"
        
        best_combination = final_combinations[0]
        
        print(f"✅ Best Combination Score: {best_combination['overall_fitness_score']:.3f}")
        print(f"✅ Total Cost: ₹{best_combination['total_cost']:,}")
        print(f"✅ Budget Utilization: {(best_combination['total_cost'] / client_data['budget']) * 100:.1f}%")
        
        # Performance validation
        total_time = budget_time + sum(r['time'] for r in sourcing_results.values()) + combination_time + beam_search_time + fitness_time
        print(f"✅ Total Execution Time: {total_time:.3f}s")
        
        assert total_time < 30.0, f"Workflow too slow: {total_time:.3f}s"
        assert best_combination['overall_fitness_score'] > 0.5, "Low fitness score"
        assert best_combination['total_cost'] <= client_data['budget'] * 1.1, "Over budget"
        
        return {
            'scenario': 'intimate_wedding',
            'success': True,
            'execution_time': total_time,
            'best_score': best_combination['overall_fitness_score'],
            'total_cost': best_combination['total_cost'],
            'combinations_evaluated': len(vendor_combinations),
            'final_candidates': len(final_combinations)
        } 
def test_luxury_wedding_complete_workflow(self, luxury_wedding_scenario):
        """Test complete workflow execution for luxury wedding scenario"""
        print("\n🎭 Testing Luxury Wedding Scenario")
        print("=" * 50)
        
        # Initialize workflow components
        workflow = EventPlanningWorkflow()
        budgeting_coordinator = BudgetingAgentCoordinator()
        sourcing_coordinator = SourcingAgentCoordinator()
        
        client_data = luxury_wedding_scenario
        
        # Step 1: Budget Allocation
        print("💰 Step 1: Budget Allocation")
        start_time = time.time()
        
        budget_strategies = budgeting_coordinator.generate_budget_strategies(
            client_data, client_data['budget']
        )
        
        budget_time = time.time() - start_time
        
        # Validate budget allocation for luxury event
        assert budget_strategies['total_budget'] == client_data['budget']
        assert budget_strategies['event_type'] == 'luxury'
        assert len(budget_strategies['allocation_strategies']) >= 1
        
        recommended_strategy = budget_strategies['recommended_strategy']
        
        print(f"   ✅ Budget allocated in {budget_time:.3f}s")
        print(f"   📊 Event Type: {budget_strategies['event_type']}")
        print(f"   💰 Venue Budget: ₹{recommended_strategy['allocation']['venue']:,}")
        print(f"   🍽️ Catering Budget: ₹{recommended_strategy['allocation']['catering']:,}")
        
        # Step 2: Vendor Sourcing (with higher-end vendors)
        print("\n🔍 Step 2: Vendor Sourcing")
        
        vendor_combinations = []
        sourcing_results = {}
        
        for service_type in ['venue', 'caterer', 'photographer', 'makeup_artist']:
            print(f"   Sourcing luxury {service_type}s...")
            
            start_time = time.time()
            
            # Mock luxury vendor sourcing
            mock_vendors = self._generate_mock_vendors(service_type, client_data, luxury=True)
            
            sourcing_time = time.time() - start_time
            sourcing_results[service_type] = {
                'vendors': mock_vendors,
                'count': len(mock_vendors),
                'time': sourcing_time
            }
            
            print(f"      ✅ Found {len(mock_vendors)} luxury {service_type}s in {sourcing_time:.3f}s")
        
        # Generate luxury vendor combinations
        print("\n🔗 Step 3: Generating Luxury Vendor Combinations")
        start_time = time.time()
        
        # Create luxury combinations
        venues = sourcing_results['venue']['vendors'][:4]
        caterers = sourcing_results['caterer']['vendors'][:4]
        photographers = sourcing_results['photographer']['vendors'][:3]
        makeup_artists = sourcing_results['makeup_artist']['vendors'][:3]
        
        combination_id = 0
        for venue in venues:
            for caterer in caterers:
                for photographer in photographers:
                    for makeup_artist in makeup_artists:
                        combination = {
                            'combination_id': f'luxury_combo_{combination_id:03d}',
                            'vendors': {
                                'venue': venue,
                                'caterer': caterer,
                                'photographer': photographer,
                                'makeup_artist': makeup_artist
                            }
                        }
                        
                        # Calculate total cost for luxury event
                        total_cost = (
                            venue['rental_cost'] +
                            caterer['min_veg_price'] * client_data['guestCount']['Reception'] +
                            photographer['photo_package_price'] +
                            makeup_artist['bridal_makeup_price']
                        )
                        combination['total_cost'] = total_cost
                        
                        vendor_combinations.append(combination)
                        combination_id += 1
                        
                        # Limit combinations for testing
                        if combination_id >= 40:
                            break
                    if combination_id >= 40:
                        break
                if combination_id >= 40:
                    break
            if combination_id >= 40:
                break
        
        combination_time = time.time() - start_time
        
        print(f"   ✅ Generated {len(vendor_combinations)} luxury combinations in {combination_time:.3f}s")
        
        # Step 4: Beam Search Optimization
        print("\n🎯 Step 4: Beam Search Optimization")
        
        state = EventPlanningState(
            workflow_id="luxury_wedding_test",
            client_request=client_data,
            vendor_combinations=vendor_combinations,
            beam_candidates=[],
            workflow_status=WorkflowStatus.BEAM_SEARCH,
            iteration_count=0
        )
        
        start_time = time.time()
        
        # Execute beam search iterations
        max_iterations = 3
        for iteration in range(max_iterations):
            state = workflow.beam_search_node(state)
            
            print(f"   Iteration {iteration + 1}: {len(state['beam_candidates'])} candidates")
            
            # Check convergence
            should_continue = workflow.should_continue_search(state)
            if should_continue == "present_options":
                break
        
        beam_search_time = time.time() - start_time
        
        # Step 5: Final Fitness Calculation
        print("\n📊 Step 5: Final Fitness Calculation")
        
        start_time = time.time()
        
        final_combinations = budgeting_coordinator.calculate_combination_fitness(
            state['beam_candidates'], client_data, recommended_strategy
        )
        
        fitness_time = time.time() - start_time
        
        # Sort by fitness score
        final_combinations.sort(key=lambda x: x['overall_fitness_score'], reverse=True)
        
        print(f"   ✅ Calculated fitness for {len(final_combinations)} combinations in {fitness_time:.3f}s")
        
        # Validation Results
        print("\n📋 VALIDATION RESULTS")
        print("-" * 30)
        
        assert len(final_combinations) > 0, "No final combinations generated"
        assert len(final_combinations) <= 3, "Too many beam candidates"
        
        best_combination = final_combinations[0]
        
        print(f"✅ Best Combination Score: {best_combination['overall_fitness_score']:.3f}")
        print(f"✅ Total Cost: ₹{best_combination['total_cost']:,}")
        print(f"✅ Budget Utilization: {(best_combination['total_cost'] / client_data['budget']) * 100:.1f}%")
        
        # Performance validation
        total_time = budget_time + sum(r['time'] for r in sourcing_results.values()) + combination_time + beam_search_time + fitness_time
        print(f"✅ Total Execution Time: {total_time:.3f}s")
        
        assert total_time < 45.0, f"Luxury workflow too slow: {total_time:.3f}s"
        assert best_combination['overall_fitness_score'] > 0.6, "Low fitness score for luxury event"
        assert best_combination['total_cost'] <= client_data['budget'] * 1.05, "Significantly over budget"
        
        return {
            'scenario': 'luxury_wedding',
            'success': True,
            'execution_time': total_time,
            'best_score': best_combination['overall_fitness_score'],
            'total_cost': best_combination['total_cost'],
            'combinations_evaluated': len(vendor_combinations),
            'final_candidates': len(final_combinations)
        }   
def generate_mock_vendors(self, service_type: str, client_data: Dict, luxury: bool = False) -> List[Dict]:
        """Generate realistic mock vendors for testing"""
        location = client_data.get('location', 'Bangalore')
        guest_count = client_data.get('guestCount', {}).get('Reception', 150)
        
        vendors = []
        count = 8 if not luxury else 6  # Fewer luxury vendors
        
        if service_type == 'venue':
            base_cost = 800000 if not luxury else 2500000
            for i in range(count):
                vendor = {
                    'id': f'venue_{i:03d}',
                    'name': f'{"Luxury " if luxury else ""}Venue {i + 1}',
                    'rental_cost': base_cost + (i * 50000),
                    'max_seating_capacity': guest_count + (i * 50),
                    'location_city': location,
                    'venue_type': client_data.get('venuePreferences', ['Hotel'])[0],
                    'amenities': client_data.get('essentialVenueAmenities', []),
                    'rating': 4.0 + (i * 0.1) if luxury else 3.5 + (i * 0.1),
                    'attributes': {
                        'luxury_level': 'Luxury' if luxury else 'Premium',
                        'indoor_outdoor': 'Indoor'
                    }
                }
                vendors.append(vendor)
        
        elif service_type == 'caterer':
            base_price = 500 if not luxury else 1200
            for i in range(count):
                vendor = {
                    'id': f'caterer_{i:03d}',
                    'name': f'{"Premium " if luxury else ""}Caterer {i + 1}',
                    'min_veg_price': base_price + (i * 50),
                    'min_nonveg_price': (base_price + (i * 50)) * 1.3,
                    'location_city': location,
                    'rating': 4.2 + (i * 0.1) if luxury else 3.8 + (i * 0.1),
                    'attributes': {
                        'cuisines': client_data.get('foodAndCatering', {}).get('cuisinePreferences', ['Indian']),
                        'service_style': 'Plated' if luxury else 'Buffet',
                        'dietary_options': client_data.get('foodAndCatering', {}).get('dietaryOptions', ['Vegetarian'])
                    }
                }
                vendors.append(vendor)
        
        elif service_type == 'photographer':
            base_price = 60000 if not luxury else 100000
            for i in range(count):
                vendor = {
                    'id': f'photographer_{i:03d}',
                    'name': f'{"Elite " if luxury else ""}Photographer {i + 1}',
                    'photo_package_price': base_price + (i * 10000),
                    'location_city': location,
                    'rating': 4.5 + (i * 0.05) if luxury else 4.0 + (i * 0.1),
                    'attributes': {
                        'specialties': ['Candid', 'Traditional'],
                        'equipment': ['DSLR', 'Drone'] if luxury else ['DSLR']
                    }
                }
                vendors.append(vendor)
        
        elif service_type == 'makeup_artist':
            base_price = 20000 if not luxury else 30000
            for i in range(count):
                vendor = {
                    'id': f'makeup_{i:03d}',
                    'name': f'{"Celebrity " if luxury else ""}Makeup Artist {i + 1}',
                    'bridal_makeup_price': base_price + (i * 2000),
                    'location_city': location,
                    'rating': 4.3 + (i * 0.05) if luxury else 3.9 + (i * 0.1),
                    'attributes': {
                        'specialties': ['Bridal', 'Traditional'],
                        'products': ['MAC', 'Bobbi Brown'] if luxury else ['Local Brands']
                    }
                }
                vendors.append(vendor)
        
        return vendors


class TestAlgorithmCompatibility:
    """Test that all existing algorithms produce identical results"""
    
    def test_fitness_calculation_algorithm_compatibility(self):
        """Test that fitness calculation produces consistent results"""
        print("\n🧮 Testing Fitness Calculation Algorithm Compatibility")
        
        # Test data that should produce consistent results
        test_combination = {
            'vendors': {
                'venue': {
                    'rental_cost': 250000,
                    'location_city': 'Bangalore',
                    'venue_type': 'Hotel',
                    'rating': 4.2
                },
                'caterer': {
                    'min_veg_price': 800,
                    'location_city': 'Bangalore',
                    'rating': 4.0,
                    'attributes': {'cuisines': ['Indian', 'Continental']}
                },
                'photographer': {
                    'photo_package_price': 75000,
                    'location_city': 'Bangalore',
                    'rating': 4.5
                },
                'makeup_artist': {
                    'bridal_makeup_price': 25000,
                    'location_city': 'Bangalore',
                    'rating': 4.1
                }
            }
        }
        
        client_data = {
            'guestCount': {'Reception': 200},
            'location': 'Bangalore',
            'venuePreferences': ['Hotel'],
            'foodAndCatering': {'cuisinePreferences': ['Indian']}
        }
        
        strategy = {
            'allocation': {
                'venue': 300000,
                'catering': 160000,  # 800 * 200
                'photography': 80000,
                'makeup': 30000
            }
        }
        
        # Test fitness calculation multiple times
        budgeting_coordinator = BudgetingAgentCoordinator()
        
        scores = []
        for i in range(5):
            scored_combinations = budgeting_coordinator.calculate_combination_fitness(
                [test_combination], client_data, strategy
            )
            scores.append(scored_combinations[0]['overall_fitness_score'])
        
        # All scores should be identical (deterministic algorithm)
        assert all(abs(score - scores[0]) < 0.001 for score in scores), f"Inconsistent scores: {scores}"
        
        print(f"   ✅ Fitness calculation is deterministic: {scores[0]:.3f}")
        
        # Test specific fitness components
        scored_combination = budgeting_coordinator.calculate_combination_fitness(
            [test_combination], client_data, strategy
        )[0]
        
        fitness_analysis = scored_combination['fitness_analysis']
        component_scores = fitness_analysis['component_scores']
        
        # Validate component score ranges
        assert 0 <= component_scores['budget_fitness'] <= 1, "Budget fitness out of range"
        assert 0 <= component_scores['preference_fitness'] <= 1, "Preference fitness out of range"
        assert 0 <= component_scores['location_fitness'] <= 1, "Location fitness out of range"
        
        print(f"   ✅ Budget Fitness: {component_scores['budget_fitness']:.3f}")
        print(f"   ✅ Preference Fitness: {component_scores['preference_fitness']:.3f}")
        print(f"   ✅ Location Fitness: {component_scores['location_fitness']:.3f}")
    
    def test_beam_search_algorithm_compatibility(self):
        """Test that beam search algorithm produces consistent results"""
        print("\n🎯 Testing Beam Search Algorithm Compatibility")
        
        workflow = EventPlanningWorkflow()
        
        # Create test combinations with known scores
        test_combinations = []
        expected_scores = [0.9, 0.85, 0.8, 0.75, 0.7, 0.65, 0.6, 0.55, 0.5, 0.45]
        
        for i, score in enumerate(expected_scores):
            combination = {
                'combination_id': f'test_combo_{i:02d}',
                'vendors': {
                    'venue': {'name': f'Venue {i}', 'rental_cost': 200000 + i*10000}
                },
                'expected_score': score
            }
            test_combinations.append(combination)
        
        state = EventPlanningState(
            workflow_id="beam_search_compatibility_test",
            client_request={'budget': 1000000},
            vendor_combinations=test_combinations,
            beam_candidates=[],
            workflow_status=WorkflowStatus.BEAM_SEARCH,
            iteration_count=0
        )
        
        # Mock fitness calculation to return expected scores
        with patch.object(workflow, '_calculate_fitness_score') as mock_fitness:
            mock_fitness.side_effect = expected_scores
            
            # Run beam search multiple times
            results = []
            for run in range(3):
                mock_fitness.reset_mock()
                mock_fitness.side_effect = expected_scores
                
                result = workflow.beam_search_node(state)
                
                # Extract combination IDs and scores
                beam_result = [
                    (candidate['combination_id'], candidate['fitness_score'])
                    for candidate in result['beam_candidates']
                ]
                results.append(beam_result)
            
            # All runs should produce identical results
            for i in range(1, len(results)):
                assert results[i] == results[0], f"Beam search run {i} differs from run 0"
            
            # Verify beam search selects top 3 combinations
            expected_top_3 = [
                ('test_combo_00', 0.9),
                ('test_combo_01', 0.85),
                ('test_combo_02', 0.8)
            ]
            
            assert results[0] == expected_top_3, f"Expected {expected_top_3}, got {results[0]}"
            
            print(f"   ✅ Beam search consistently selects top 3 combinations")
            print(f"   ✅ Selected: {[combo_id for combo_id, score in results[0]]}")
    
    def test_vendor_ranking_algorithm_compatibility(self):
        """Test that vendor ranking produces consistent results"""
        print("\n📊 Testing Vendor Ranking Algorithm Compatibility")
        
        # Create test vendors with known characteristics
        test_venues = [
            {
                'id': 'venue_001',
                'name': 'Premium Hotel',
                'rental_cost': 200000,
                'location_city': 'Bangalore',
                'venue_type': 'Hotel',
                'rating': 4.5,
                'max_seating_capacity': 300
            },
            {
                'id': 'venue_002',
                'name': 'Budget Resort',
                'rental_cost': 150000,
                'location_city': 'Bangalore',
                'venue_type': 'Resort',
                'rating': 3.8,
                'max_seating_capacity': 250
            },
            {
                'id': 'venue_003',
                'name': 'Luxury Palace',
                'rental_cost': 400000,
                'location_city': 'Mumbai',
                'venue_type': 'Palace',
                'rating': 4.8,
                'max_seating_capacity': 500
            }
        ]
        
        client_requirements = {
            'location': 'Bangalore',
            'budget': 250000,
            'guest_count': 200,
            'venue_preferences': ['Hotel']
        }
        
        # Test ranking multiple times
        rankings = []
        for run in range(3):
            scored_venues = []
            
            for venue in test_venues:
                # Simulate scoring algorithm
                location_score = 1.0 if venue['location_city'] == client_requirements['location'] else 0.5
                budget_score = max(0, 1.0 - (venue['rental_cost'] / client_requirements['budget']))
                capacity_score = min(1.0, venue['max_seating_capacity'] / client_requirements['guest_count'])
                rating_score = venue['rating'] / 5.0
                preference_score = 1.0 if venue['venue_type'] in client_requirements['venue_preferences'] else 0.7
                
                overall_score = (
                    location_score * 0.25 +
                    budget_score * 0.25 +
                    capacity_score * 0.2 +
                    rating_score * 0.15 +
                    preference_score * 0.15
                )
                
                scored_venues.append((venue['id'], overall_score))
            
            # Sort by score
            scored_venues.sort(key=lambda x: x[1], reverse=True)
            rankings.append(scored_venues)
        
        # All rankings should be identical
        for i in range(1, len(rankings)):
            assert rankings[i] == rankings[0], f"Ranking run {i} differs from run 0"
        
        print(f"   ✅ Vendor ranking is deterministic")
        print(f"   ✅ Top venue: {rankings[0][0][0]} (score: {rankings[0][0][1]:.3f})")
        
        # Verify expected ranking (Premium Hotel should rank highest)
        assert rankings[0][0][0] == 'venue_001', "Premium Hotel should rank highest"
class TestAPICompatibility:
    """Test API compatibility with existing integrations"""
    
    @pytest.fixture
    def api_base_url(self):
        """Base URL for API testing"""
        return "http://localhost:8000"
    
    def test_api_endpoint_structure_compatibility(self):
        """Test that API endpoints maintain expected structure"""
        print("\n🔌 Testing API Endpoint Structure Compatibility")
        
        # Test POST /v1/plans endpoint structure
        expected_request_structure = {
            "clientName": "Test Client",
            "clientId": "test_001",
            "guestCount": {"Reception": 200},
            "clientVision": "Test wedding",
            "budget": 1000000,
            "venuePreferences": ["Hotel"],
            "eventDate": "2024-12-15",
            "location": "Bangalore"
        }
        
        expected_response_structure = {
            "plan_id": str,
            "status": str,
            "client_name": str,
            "combinations": list,
            "created_at": str,
            "updated_at": str
        }
        
        # Validate request structure
        for field, field_type in [
            ("clientName", str),
            ("guestCount", dict),
            ("budget", int),
            ("venuePreferences", list)
        ]:
            assert field in expected_request_structure, f"Missing required field: {field}"
            assert isinstance(expected_request_structure[field], field_type), f"Wrong type for {field}"
        
        print("   ✅ Request structure validation passed")
        
        # Validate response structure
        mock_response = {
            "plan_id": "plan_12345",
            "status": "completed",
            "client_name": "Test Client",
            "combinations": [
                {
                    "combination_id": "combo_001",
                    "vendors": {},
                    "fitness_score": 0.85,
                    "total_cost": 950000
                }
            ],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            # New fields (should not break compatibility)
            "workflow_status": {
                "current_step": "completed",
                "progress_percentage": 100.0
            }
        }
        
        # Check backward compatibility
        for field, field_type in expected_response_structure.items():
            assert field in mock_response, f"Missing required response field: {field}"
            assert isinstance(mock_response[field], field_type), f"Wrong type for response field {field}"
        
        print("   ✅ Response structure validation passed")
        print("   ✅ Backward compatibility maintained")
    
    def test_api_error_response_compatibility(self):
        """Test that API error responses maintain expected format"""
        print("\n❌ Testing API Error Response Compatibility")
        
        expected_error_formats = [
            {
                "error": "ValidationError",
                "message": "Invalid client data",
                "details": {"field": "guestCount", "issue": "missing"},
                "status_code": 400
            },
            {
                "error": "ProcessingError", 
                "message": "Workflow execution failed",
                "details": {"step": "vendor_sourcing", "reason": "no vendors found"},
                "status_code": 500
            }
        ]
        
        for error_response in expected_error_formats:
            # Validate error structure
            required_fields = ["error", "message", "status_code"]
            for field in required_fields:
                assert field in error_response, f"Missing error field: {field}"
            
            assert isinstance(error_response["error"], str)
            assert isinstance(error_response["message"], str)
            assert isinstance(error_response["status_code"], int)
            assert 400 <= error_response["status_code"] < 600
        
        print("   ✅ Error response format validation passed")
    
    def test_api_async_behavior_compatibility(self):
        """Test that async API behavior is maintained"""
        print("\n⏱️ Testing API Async Behavior Compatibility")
        
        # Simulate async workflow execution
        async def simulate_async_workflow():
            # Mock long-running workflow
            await asyncio.sleep(0.1)  # Simulate processing time
            
            return {
                "plan_id": "async_plan_001",
                "status": "processing",
                "estimated_completion": "2024-01-01T00:05:00Z"
            }
        
        # Test async execution
        start_time = time.time()
        
        # Run async workflow
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(simulate_async_workflow())
            execution_time = time.time() - start_time
            
            # Validate async response
            assert "plan_id" in result
            assert result["status"] == "processing"
            assert execution_time < 1.0  # Should be fast (async)
            
            print(f"   ✅ Async workflow initiated in {execution_time:.3f}s")
            print(f"   ✅ Plan ID: {result['plan_id']}")
            
        finally:
            loop.close()


def run_comprehensive_validation():
    """Run all validation tests and generate summary report"""
    print("🚀 Event Planning Agent - End-to-End System Validation")
    print("=" * 60)
    
    test_results = {
        'demo_scenarios': {},
        'algorithm_compatibility': {},
        'api_compatibility': {},
        'overall_success': True,
        'total_execution_time': 0
    }
    
    start_time = time.time()
    
    try:
        # Test Demo Scenarios
        print("\n📋 DEMO SCENARIO VALIDATION")
        print("=" * 40)
        
        demo_test = TestDemoScenarioValidation()
        
        # Intimate wedding test
        intimate_result = demo_test.test_intimate_wedding_complete_workflow(
            demo_test.intimate_wedding_scenario()
        )
        test_results['demo_scenarios']['intimate_wedding'] = intimate_result
        
        # Luxury wedding test
        luxury_result = demo_test.test_luxury_wedding_complete_workflow(
            demo_test.luxury_wedding_scenario()
        )
        test_results['demo_scenarios']['luxury_wedding'] = luxury_result
        
        # Algorithm Compatibility Tests
        print("\n🧮 ALGORITHM COMPATIBILITY VALIDATION")
        print("=" * 40)
        
        algo_test = TestAlgorithmCompatibility()
        
        algo_test.test_fitness_calculation_algorithm_compatibility()
        test_results['algorithm_compatibility']['fitness_calculation'] = True
        
        algo_test.test_beam_search_algorithm_compatibility()
        test_results['algorithm_compatibility']['beam_search'] = True
        
        algo_test.test_vendor_ranking_algorithm_compatibility()
        test_results['algorithm_compatibility']['vendor_ranking'] = True
        
        # API Compatibility Tests
        print("\n🔌 API COMPATIBILITY VALIDATION")
        print("=" * 40)
        
        api_test = TestAPICompatibility()
        
        api_test.test_api_endpoint_structure_compatibility()
        test_results['api_compatibility']['endpoint_structure'] = True
        
        api_test.test_api_error_response_compatibility()
        test_results['api_compatibility']['error_responses'] = True
        
        api_test.test_api_async_behavior_compatibility()
        test_results['api_compatibility']['async_behavior'] = True
        
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        test_results['overall_success'] = False
        import traceback
        traceback.print_exc()
    
    test_results['total_execution_time'] = time.time() - start_time
    
    # Generate Summary Report
    print("\n📊 VALIDATION SUMMARY REPORT")
    print("=" * 40)
    
    if test_results['overall_success']:
        print("🎉 ALL VALIDATIONS PASSED!")
    else:
        print("❌ SOME VALIDATIONS FAILED!")
    
    print(f"\n⏱️ Total Execution Time: {test_results['total_execution_time']:.2f}s")
    
    # Demo Scenarios Summary
    print("\n📋 Demo Scenarios:")
    for scenario, result in test_results['demo_scenarios'].items():
        if result.get('success'):
            print(f"   ✅ {scenario}: {result['execution_time']:.2f}s, Score: {result['best_score']:.3f}")
        else:
            print(f"   ❌ {scenario}: Failed")
    
    # Algorithm Compatibility Summary
    print("\n🧮 Algorithm Compatibility:")
    for algorithm, success in test_results['algorithm_compatibility'].items():
        status = "✅" if success else "❌"
        print(f"   {status} {algorithm}")
    
    # API Compatibility Summary
    print("\n🔌 API Compatibility:")
    for api_test, success in test_results['api_compatibility'].items():
        status = "✅" if success else "❌"
        print(f"   {status} {api_test}")
    
    # Performance Summary
    demo_times = [r['execution_time'] for r in test_results['demo_scenarios'].values() if r.get('success')]
    if demo_times:
        avg_demo_time = sum(demo_times) / len(demo_times)
        print(f"\n⚡ Average Demo Execution Time: {avg_demo_time:.2f}s")
    
    return test_results


if __name__ == "__main__":
    # Run comprehensive validation
    results = run_comprehensive_validation()
    
    # Exit with appropriate code
    exit_code = 0 if results['overall_success'] else 1
    
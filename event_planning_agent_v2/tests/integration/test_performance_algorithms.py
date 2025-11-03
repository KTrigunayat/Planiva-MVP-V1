"""
Performance tests for beam search and vendor ranking algorithms
"""

import time
import pytest
import json
import threading
import psutil
import os
from unittest.mock import Mock, patch
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from workflows.planning_workflow import EventPlanningWorkflow
from workflows.state_models import EventPlanningState, WorkflowStatus
from agents.budgeting import BudgetingAgentCoordinator
from tools.vendor_tools import VendorDatabaseTool, HybridFilterTool


class TestBeamSearchPerformance:
    """Performance tests for beam search algorithm"""
    
    @pytest.fixture
    def large_combination_dataset(self):
        """Generate large dataset of vendor combinations for performance testing"""
        combinations = []
        
        # Generate 500 vendor combinations
        for i in range(500):
            combination = {
                "combination_id": f"combo_{i:04d}",
                "vendors": {
                    "venue": {
                        "id": f"venue_{i}",
                        "name": f"Venue {i}",
                        "rental_cost": 200000 + (i * 1000),
                        "max_seating_capacity": 100 + (i * 2),
                        "location_city": "Mumbai" if i % 3 == 0 else "Bangalore" if i % 3 == 1 else "Delhi",
                        "venue_type": "Hotel" if i % 4 == 0 else "Resort" if i % 4 == 1 else "Banquet Hall",
                        "rating": 3.0 + (i % 20) * 0.1
                    },
                    "caterer": {
                        "id": f"caterer_{i}",
                        "name": f"Caterer {i}",
                        "min_veg_price": 800 + (i * 10),
                        "min_nonveg_price": 1000 + (i * 15),
                        "location_city": "Mumbai" if i % 3 == 0 else "Bangalore" if i % 3 == 1 else "Delhi",
                        "rating": 3.5 + (i % 15) * 0.1
                    },
                    "photographer": {
                        "id": f"photographer_{i}",
                        "name": f"Photographer {i}",
                        "photo_package_price": 50000 + (i * 500),
                        "location_city": "Mumbai" if i % 3 == 0 else "Bangalore" if i % 3 == 1 else "Delhi",
                        "rating": 4.0 + (i % 10) * 0.1
                    },
                    "makeup_artist": {
                        "id": f"makeup_{i}",
                        "name": f"Makeup Artist {i}",
                        "bridal_makeup_price": 20000 + (i * 200),
                        "location_city": "Mumbai" if i % 3 == 0 else "Bangalore" if i % 3 == 1 else "Delhi",
                        "rating": 3.8 + (i % 12) * 0.1
                    }
                },
                "total_cost": 270000 + (i * 1725),
                "metadata": {
                    "generation_index": i,
                    "complexity_score": (i % 100) / 100.0
                }
            }
            combinations.append(combination)
        
        return combinations
    
    @pytest.fixture
    def performance_client_data(self):
        """Client data for performance testing"""
        return {
            "clientName": "Performance Test Client",
            "clientId": "perf_client_001",
            "guestCount": {
                "Reception": 300,
                "Ceremony": 250
            },
            "clientVision": "Elegant celebration with premium vendors",
            "budget": 1500000,
            "venuePreferences": ["Hotel", "Resort"],
            "essentialVenueAmenities": ["Parking", "AC", "Sound System"],
            "foodAndCatering": {
                "cuisinePreferences": ["Indian", "Continental"],
                "dietaryOptions": ["Vegetarian", "Non-Vegetarian"]
            },
            "eventDate": "2024-12-15",
            "location": "Mumbai"
        }
    
    def test_beam_search_scalability(self, large_combination_dataset, performance_client_data):
        """Test beam search performance with increasing dataset sizes"""
        workflow = EventPlanningWorkflow()
        
        # Test with different dataset sizes
        dataset_sizes = [50, 100, 200, 500]
        performance_results = {}
        
        for size in dataset_sizes:
            combinations_subset = large_combination_dataset[:size]
            
            state = EventPlanningState(
                workflow_id=f"perf_test_{size}",
                client_request=performance_client_data,
                vendor_combinations=combinations_subset,
                beam_candidates=[],
                workflow_status=WorkflowStatus.BEAM_SEARCH,
                iteration_count=0
            )
            
            # Mock fitness calculation for consistent performance testing
            with patch.object(workflow, '_calculate_fitness_score') as mock_fitness:
                # Generate deterministic fitness scores
                mock_fitness.side_effect = [0.5 + (i % 100) * 0.005 for i in range(size)]
                
                start_time = time.time()
                result = workflow.beam_search_node(state)
                execution_time = time.time() - start_time
                
                performance_results[size] = {
                    "execution_time": execution_time,
                    "combinations_processed": size,
                    "beam_candidates": len(result["beam_candidates"]),
                    "throughput": size / execution_time if execution_time > 0 else float('inf')
                }
                
                # Verify beam search correctness
                assert len(result["beam_candidates"]) <= 3  # Beam width = 3
                assert result["iteration_count"] == 1
                
                # Verify fitness calculation was called for each combination
                assert mock_fitness.call_count == size
                
                mock_fitness.reset_mock()
        
        # Performance assertions
        for size in dataset_sizes:
            perf = performance_results[size]
            
            # Execution time should scale reasonably (not exponentially)
            if size <= 100:
                assert perf["execution_time"] < 1.0, f"Size {size} took {perf['execution_time']:.3f}s"
            elif size <= 200:
                assert perf["execution_time"] < 2.0, f"Size {size} took {perf['execution_time']:.3f}s"
            else:
                assert perf["execution_time"] < 5.0, f"Size {size} took {perf['execution_time']:.3f}s"
            
            # Throughput should be reasonable
            assert perf["throughput"] > 20, f"Throughput too low: {perf['throughput']:.1f} combinations/sec"
        
        # Print performance summary
        print("\nBeam Search Performance Results:")
        for size, perf in performance_results.items():
            print(f"Size {size:3d}: {perf['execution_time']:.3f}s, "
                  f"{perf['throughput']:.1f} combinations/sec")
    
    def test_beam_search_memory_efficiency(self, large_combination_dataset, performance_client_data):
        """Test beam search memory usage with large datasets"""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        workflow = EventPlanningWorkflow()
        
        # Test with progressively larger datasets
        for size in [100, 200, 300, 500]:
            combinations_subset = large_combination_dataset[:size]
            
            state = EventPlanningState(
                workflow_id=f"memory_test_{size}",
                client_request=performance_client_data,
                vendor_combinations=combinations_subset,
                beam_candidates=[],
                workflow_status=WorkflowStatus.BEAM_SEARCH,
                iteration_count=0
            )
            
            with patch.object(workflow, '_calculate_fitness_score') as mock_fitness:
                mock_fitness.side_effect = [0.5 + (i % 100) * 0.005 for i in range(size)]
                
                result = workflow.beam_search_node(state)
                
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = current_memory - initial_memory
                
                # Memory usage should not grow excessively
                assert memory_increase < 100, f"Memory usage too high: {memory_increase:.1f}MB for {size} combinations"
                
                # Beam search should limit output size regardless of input size
                assert len(result["beam_candidates"]) <= 3
    
    def test_beam_search_concurrent_execution(self, large_combination_dataset, performance_client_data):
        """Test beam search performance under concurrent execution"""
        workflow = EventPlanningWorkflow()
        
        def execute_beam_search(thread_id, combinations):
            state = EventPlanningState(
                workflow_id=f"concurrent_test_{thread_id}",
                client_request=performance_client_data,
                vendor_combinations=combinations,
                beam_candidates=[],
                workflow_status=WorkflowStatus.BEAM_SEARCH,
                iteration_count=0
            )
            
            with patch.object(workflow, '_calculate_fitness_score') as mock_fitness:
                mock_fitness.side_effect = [0.5 + (i % 100) * 0.005 for i in range(len(combinations))]
                
                start_time = time.time()
                result = workflow.beam_search_node(state)
                execution_time = time.time() - start_time
                
                return {
                    "thread_id": thread_id,
                    "execution_time": execution_time,
                    "combinations_processed": len(combinations),
                    "beam_candidates": len(result["beam_candidates"])
                }
        
        # Execute concurrent beam searches
        num_threads = 4
        combinations_per_thread = 100
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = []
            
            start_time = time.time()
            
            for i in range(num_threads):
                thread_combinations = large_combination_dataset[i*combinations_per_thread:(i+1)*combinations_per_thread]
                future = executor.submit(execute_beam_search, i, thread_combinations)
                futures.append(future)
            
            results = []
            for future in as_completed(futures):
                results.append(future.result())
            
            total_time = time.time() - start_time
        
        # Verify all threads completed successfully
        assert len(results) == num_threads
        
        # Performance assertions
        for result in results:
            assert result["execution_time"] < 3.0  # Each thread should complete quickly
            assert result["beam_candidates"] <= 3
            assert result["combinations_processed"] == combinations_per_thread
        
        # Total concurrent execution should be faster than sequential
        sequential_time_estimate = sum(r["execution_time"] for r in results)
        assert total_time < sequential_time_estimate * 0.8  # At least 20% improvement
        
        print(f"\nConcurrent Execution Results:")
        print(f"Total time: {total_time:.3f}s")
        print(f"Sequential estimate: {sequential_time_estimate:.3f}s")
        print(f"Speedup: {sequential_time_estimate/total_time:.2f}x")


class TestVendorRankingPerformance:
    """Performance tests for vendor ranking algorithms"""
    
    @pytest.fixture
    def large_vendor_dataset(self):
        """Generate large vendor dataset for performance testing"""
        vendors = {
            "venues": [],
            "caterers": [],
            "photographers": [],
            "makeup_artists": []
        }
        
        # Generate 1000 vendors of each type
        for i in range(1000):
            # Venues
            venue = {
                "id": f"venue_{i:04d}",
                "name": f"Venue {i}",
                "rental_cost": 150000 + (i * 500),
                "max_seating_capacity": 50 + (i * 2),
                "location_city": ["Mumbai", "Bangalore", "Delhi", "Chennai", "Hyderabad"][i % 5],
                "venue_type": ["Hotel", "Resort", "Banquet Hall", "Garden", "Palace"][i % 5],
                "amenities": ["Parking", "AC", "Sound System", "Bridal Suite", "Garden"][:((i % 5) + 1)],
                "rating": 3.0 + (i % 20) * 0.1,
                "attributes": {
                    "luxury_level": ["Standard", "Premium", "Luxury"][i % 3],
                    "indoor_outdoor": "Indoor" if i % 2 == 0 else "Outdoor"
                }
            }
            vendors["venues"].append(venue)
            
            # Caterers
            caterer = {
                "id": f"caterer_{i:04d}",
                "name": f"Caterer {i}",
                "min_veg_price": 600 + (i * 5),
                "min_nonveg_price": 800 + (i * 8),
                "location_city": ["Mumbai", "Bangalore", "Delhi", "Chennai", "Hyderabad"][i % 5],
                "rating": 3.5 + (i % 15) * 0.1,
                "attributes": {
                    "cuisines": ["Indian", "Continental", "Chinese", "Italian", "Thai"][:((i % 5) + 1)],
                    "service_style": ["Buffet", "Plated", "Family Style"][i % 3],
                    "dietary_options": ["Vegetarian", "Non-Vegetarian", "Vegan", "Jain"][:((i % 4) + 1)]
                }
            }
            vendors["caterers"].append(caterer)
            
            # Photographers
            photographer = {
                "id": f"photographer_{i:04d}",
                "name": f"Photographer {i}",
                "photo_package_price": 40000 + (i * 300),
                "location_city": ["Mumbai", "Bangalore", "Delhi", "Chennai", "Hyderabad"][i % 5],
                "rating": 4.0 + (i % 10) * 0.1,
                "attributes": {
                    "specialties": ["Candid", "Traditional", "Pre-wedding", "Drone"][:((i % 4) + 1)],
                    "equipment": ["DSLR", "Mirrorless", "Drone", "Lighting"][:((i % 4) + 1)]
                }
            }
            vendors["photographers"].append(photographer)
            
            # Makeup Artists
            makeup_artist = {
                "id": f"makeup_{i:04d}",
                "name": f"Makeup Artist {i}",
                "bridal_makeup_price": 15000 + (i * 100),
                "location_city": ["Mumbai", "Bangalore", "Delhi", "Chennai", "Hyderabad"][i % 5],
                "rating": 3.8 + (i % 12) * 0.1,
                "attributes": {
                    "specialties": ["Bridal", "Party", "Traditional", "Contemporary"][:((i % 4) + 1)],
                    "products": ["MAC", "Bobbi Brown", "Huda Beauty", "Local Brands"][:((i % 4) + 1)]
                }
            }
            vendors["makeup_artists"].append(makeup_artist)
        
        return vendors
    
    def test_vendor_filtering_performance(self, large_vendor_dataset):
        """Test vendor filtering performance with large datasets"""
        # Test filtering performance for each vendor type
        filter_results = {}
        
        client_requirements = {
            "location": "Mumbai",
            "budget_per_vendor": {
                "venue": 300000,
                "caterer": 1000,  # per person
                "photographer": 80000,
                "makeup_artist": 25000
            },
            "guest_count": 200,
            "preferences": {
                "venue_type": "Hotel",
                "cuisine": "Indian",
                "photography_style": "Candid"
            }
        }
        
        for vendor_type, vendors in large_vendor_dataset.items():
            start_time = time.time()
            
            # Apply filters based on vendor type
            filtered_vendors = []
            
            if vendor_type == "venues":
                for vendor in vendors:
                    if (vendor["location_city"] == client_requirements["location"] and
                        vendor["rental_cost"] <= client_requirements["budget_per_vendor"]["venue"] and
                        vendor["max_seating_capacity"] >= 200 and
                        vendor["venue_type"] == client_requirements["preferences"]["venue_type"]):
                        filtered_vendors.append(vendor)
            
            elif vendor_type == "caterers":
                for vendor in vendors:
                    if (vendor["location_city"] == client_requirements["location"] and
                        vendor["min_veg_price"] <= client_requirements["budget_per_vendor"]["caterer"] and
                        "Indian" in vendor["attributes"]["cuisines"]):
                        filtered_vendors.append(vendor)
            
            elif vendor_type == "photographers":
                for vendor in vendors:
                    if (vendor["location_city"] == client_requirements["location"] and
                        vendor["photo_package_price"] <= client_requirements["budget_per_vendor"]["photographer"] and
                        "Candid" in vendor["attributes"]["specialties"]):
                        filtered_vendors.append(vendor)
            
            elif vendor_type == "makeup_artists":
                for vendor in vendors:
                    if (vendor["location_city"] == client_requirements["location"] and
                        vendor["bridal_makeup_price"] <= client_requirements["budget_per_vendor"]["makeup_artist"]):
                        filtered_vendors.append(vendor)
            
            filtering_time = time.time() - start_time
            
            filter_results[vendor_type] = {
                "total_vendors": len(vendors),
                "filtered_vendors": len(filtered_vendors),
                "filtering_time": filtering_time,
                "throughput": len(vendors) / filtering_time if filtering_time > 0 else float('inf')
            }
            
            # Performance assertions
            assert filtering_time < 1.0, f"{vendor_type} filtering took {filtering_time:.3f}s"
            assert filter_results[vendor_type]["throughput"] > 500, f"Low throughput for {vendor_type}"
        
        # Print filtering performance summary
        print("\nVendor Filtering Performance Results:")
        for vendor_type, result in filter_results.items():
            print(f"{vendor_type:15s}: {result['filtering_time']:.3f}s, "
                  f"{result['throughput']:.0f} vendors/sec, "
                  f"{result['filtered_vendors']}/{result['total_vendors']} matched")
    
    def test_vendor_scoring_performance(self, large_vendor_dataset):
        """Test vendor scoring algorithm performance"""
        budgeting_coordinator = BudgetingAgentCoordinator()
        
        client_data = {
            "guestCount": {"Reception": 200},
            "budget": 1000000,
            "location": "Mumbai",
            "venuePreferences": ["Hotel", "Resort"],
            "foodAndCatering": {
                "cuisinePreferences": ["Indian", "Continental"]
            }
        }
        
        scoring_results = {}
        
        for vendor_type, vendors in large_vendor_dataset.items():
            # Take subset for scoring performance test
            vendors_subset = vendors[:200]  # Test with 200 vendors
            
            start_time = time.time()
            
            # Mock scoring algorithm
            scored_vendors = []
            for vendor in vendors_subset:
                # Simulate complex scoring calculation
                location_score = 1.0 if vendor["location_city"] == "Mumbai" else 0.5
                rating_score = vendor["rating"] / 5.0
                
                # Type-specific scoring
                if vendor_type == "venues":
                    capacity_score = min(vendor["max_seating_capacity"] / 200, 1.0)
                    cost_score = max(0, 1.0 - (vendor["rental_cost"] / 500000))
                    overall_score = (location_score * 0.3 + rating_score * 0.3 + 
                                   capacity_score * 0.2 + cost_score * 0.2)
                
                elif vendor_type == "caterers":
                    cost_score = max(0, 1.0 - (vendor["min_veg_price"] / 1500))
                    cuisine_score = 1.0 if "Indian" in vendor["attributes"]["cuisines"] else 0.7
                    overall_score = (location_score * 0.3 + rating_score * 0.3 + 
                                   cost_score * 0.2 + cuisine_score * 0.2)
                
                else:  # photographers, makeup_artists
                    cost_field = "photo_package_price" if vendor_type == "photographers" else "bridal_makeup_price"
                    max_cost = 100000 if vendor_type == "photographers" else 30000
                    cost_score = max(0, 1.0 - (vendor[cost_field] / max_cost))
                    overall_score = (location_score * 0.4 + rating_score * 0.4 + cost_score * 0.2)
                
                scored_vendors.append((vendor, overall_score))
            
            # Sort by score
            scored_vendors.sort(key=lambda x: x[1], reverse=True)
            top_vendors = scored_vendors[:10]
            
            scoring_time = time.time() - start_time
            
            scoring_results[vendor_type] = {
                "vendors_scored": len(vendors_subset),
                "scoring_time": scoring_time,
                "throughput": len(vendors_subset) / scoring_time if scoring_time > 0 else float('inf'),
                "top_score": top_vendors[0][1] if top_vendors else 0
            }
            
            # Performance assertions
            assert scoring_time < 2.0, f"{vendor_type} scoring took {scoring_time:.3f}s"
            assert scoring_results[vendor_type]["throughput"] > 50, f"Low scoring throughput for {vendor_type}"
            
            # Verify scoring correctness
            assert len(top_vendors) <= 10
            if len(top_vendors) > 1:
                assert top_vendors[0][1] >= top_vendors[1][1]  # Properly sorted
        
        # Print scoring performance summary
        print("\nVendor Scoring Performance Results:")
        for vendor_type, result in scoring_results.items():
            print(f"{vendor_type:15s}: {result['scoring_time']:.3f}s, "
                  f"{result['throughput']:.0f} vendors/sec, "
                  f"top score: {result['top_score']:.3f}")
    
    def test_vendor_combination_generation_performance(self, large_vendor_dataset):
        """Test performance of generating vendor combinations"""
        # Use smaller subsets for combination generation
        venues = large_vendor_dataset["venues"][:20]
        caterers = large_vendor_dataset["caterers"][:20]
        photographers = large_vendor_dataset["photographers"][:15]
        makeup_artists = large_vendor_dataset["makeup_artists"][:15]
        
        start_time = time.time()
        
        # Generate all possible combinations
        combinations = []
        combination_count = 0
        
        for venue in venues:
            for caterer in caterers:
                for photographer in photographers:
                    for makeup_artist in makeup_artists:
                        combination = {
                            "combination_id": f"combo_{combination_count:06d}",
                            "vendors": {
                                "venue": venue,
                                "caterer": caterer,
                                "photographer": photographer,
                                "makeup_artist": makeup_artist
                            },
                            "total_cost": (venue["rental_cost"] + 
                                         caterer["min_veg_price"] * 200 +  # 200 guests
                                         photographer["photo_package_price"] +
                                         makeup_artist["bridal_makeup_price"])
                        }
                        combinations.append(combination)
                        combination_count += 1
                        
                        # Limit combinations for performance testing
                        if combination_count >= 1000:
                            break
                    if combination_count >= 1000:
                        break
                if combination_count >= 1000:
                    break
            if combination_count >= 1000:
                break
        
        generation_time = time.time() - start_time
        
        # Performance assertions
        assert generation_time < 5.0, f"Combination generation took {generation_time:.3f}s"
        assert len(combinations) > 0
        
        # Test combination filtering by budget
        budget_limit = 800000
        start_time = time.time()
        
        budget_filtered = [combo for combo in combinations if combo["total_cost"] <= budget_limit]
        
        filtering_time = time.time() - start_time
        
        # Performance assertions for filtering
        assert filtering_time < 1.0, f"Combination filtering took {filtering_time:.3f}s"
        
        print(f"\nCombination Generation Performance:")
        print(f"Generated {len(combinations)} combinations in {generation_time:.3f}s")
        print(f"Filtered to {len(budget_filtered)} within budget in {filtering_time:.3f}s")
        print(f"Generation rate: {len(combinations)/generation_time:.0f} combinations/sec")


class TestAlgorithmStressTests:
    """Stress tests for algorithms under extreme conditions"""
    
    def test_beam_search_with_identical_scores(self):
        """Test beam search behavior with identical fitness scores"""
        workflow = EventPlanningWorkflow()
        
        # Create combinations with identical scores
        combinations = []
        for i in range(100):
            combination = {
                "combination_id": f"identical_{i}",
                "vendors": {"venue": {"name": f"Venue {i}"}},
                "total_cost": 500000
            }
            combinations.append(combination)
        
        state = EventPlanningState(
            workflow_id="identical_scores_test",
            client_request={"budget": 1000000},
            vendor_combinations=combinations,
            beam_candidates=[],
            workflow_status=WorkflowStatus.BEAM_SEARCH,
            iteration_count=0
        )
        
        # Mock identical fitness scores
        with patch.object(workflow, '_calculate_fitness_score') as mock_fitness:
            mock_fitness.return_value = 0.75  # All combinations get same score
            
            start_time = time.time()
            result = workflow.beam_search_node(state)
            execution_time = time.time() - start_time
            
            # Should handle identical scores gracefully
            assert execution_time < 2.0
            assert len(result["beam_candidates"]) <= 3
            
            # All selected candidates should have the same score
            for candidate in result["beam_candidates"]:
                assert candidate["fitness_score"] == 0.75
    
    def test_vendor_ranking_with_extreme_values(self):
        """Test vendor ranking with extreme cost and rating values"""
        # Create vendors with extreme values
        extreme_vendors = [
            {
                "id": "extreme_cheap",
                "name": "Extremely Cheap Venue",
                "rental_cost": 1,  # Extremely low cost
                "rating": 1.0,  # Very low rating
                "location_city": "Mumbai"
            },
            {
                "id": "extreme_expensive",
                "name": "Extremely Expensive Venue", 
                "rental_cost": 10000000,  # Extremely high cost
                "rating": 5.0,  # Perfect rating
                "location_city": "Mumbai"
            },
            {
                "id": "normal_venue",
                "name": "Normal Venue",
                "rental_cost": 250000,  # Normal cost
                "rating": 4.0,  # Good rating
                "location_city": "Mumbai"
            }
        ]
        
        # Test scoring with extreme values
        start_time = time.time()
        
        scored_vendors = []
        for vendor in extreme_vendors:
            # Simulate scoring algorithm
            cost_score = max(0, min(1, 1.0 - (vendor["rental_cost"] / 1000000)))  # Normalize to 1M
            rating_score = vendor["rating"] / 5.0
            overall_score = (cost_score * 0.5 + rating_score * 0.5)
            
            scored_vendors.append((vendor, overall_score))
        
        scoring_time = time.time() - start_time
        
        # Sort by score
        scored_vendors.sort(key=lambda x: x[1], reverse=True)
        
        # Performance and correctness assertions
        assert scoring_time < 0.1  # Should be very fast for 3 vendors
        assert len(scored_vendors) == 3
        
        # Verify scoring handles extreme values correctly
        scores = [score for _, score in scored_vendors]
        assert all(0 <= score <= 1 for score in scores)  # Scores should be normalized
        
        print(f"\nExtreme Value Scoring Results:")
        for vendor, score in scored_vendors:
            print(f"{vendor['name']}: {score:.3f} (cost: {vendor['rental_cost']}, rating: {vendor['rating']})")
    
    def test_concurrent_algorithm_execution(self):
        """Test algorithm performance under high concurrency"""
        import threading
        import queue
        
        results_queue = queue.Queue()
        errors_queue = queue.Queue()
        
        def worker_thread(thread_id, iterations):
            try:
                workflow = EventPlanningWorkflow()
                
                for i in range(iterations):
                    # Create test combinations
                    combinations = [
                        {
                            "combination_id": f"thread_{thread_id}_combo_{i}",
                            "vendors": {"venue": {"name": f"Venue {i}"}},
                            "total_cost": 400000 + (i * 1000)
                        }
                    ]
                    
                    state = EventPlanningState(
                        workflow_id=f"thread_{thread_id}_workflow_{i}",
                        client_request={"budget": 1000000},
                        vendor_combinations=combinations,
                        beam_candidates=[],
                        workflow_status=WorkflowStatus.BEAM_SEARCH,
                        iteration_count=0
                    )
                    
                    with patch.object(workflow, '_calculate_fitness_score') as mock_fitness:
                        mock_fitness.return_value = 0.8
                        
                        result = workflow.beam_search_node(state)
                        
                        results_queue.put({
                            "thread_id": thread_id,
                            "iteration": i,
                            "success": True,
                            "beam_candidates": len(result["beam_candidates"])
                        })
                        
            except Exception as e:
                errors_queue.put({
                    "thread_id": thread_id,
                    "error": str(e)
                })
        
        # Start multiple worker threads
        num_threads = 8
        iterations_per_thread = 10
        threads = []
        
        start_time = time.time()
        
        for i in range(num_threads):
            thread = threading.Thread(target=worker_thread, args=(i, iterations_per_thread))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=30)  # 30 second timeout
        
        total_time = time.time() - start_time
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        errors = []
        while not errors_queue.empty():
            errors.append(errors_queue.get())
        
        # Performance assertions
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == num_threads * iterations_per_thread
        assert total_time < 15.0  # Should complete within 15 seconds
        
        # Verify all operations succeeded
        for result in results:
            assert result["success"] is True
            assert result["beam_candidates"] >= 0
        
        print(f"\nConcurrency Test Results:")
        print(f"Threads: {num_threads}, Iterations per thread: {iterations_per_thread}")
        print(f"Total operations: {len(results)}")
        print(f"Total time: {total_time:.3f}s")
        print(f"Operations per second: {len(results)/total_time:.1f}")


if __name__ == "__main__":
    # Run performance tests
    print("Running Algorithm Performance Tests...")
    
    try:
        # Test beam search performance
        workflow = EventPlanningWorkflow()
        
        # Create test combinations
        test_combinations = []
        for i in range(50):
            combination = {
                "combination_id": f"test_{i}",
                "vendors": {"venue": {"name": f"Venue {i}"}},
                "total_cost": 400000 + (i * 1000)
            }
            test_combinations.append(combination)
        
        state = EventPlanningState(
            workflow_id="performance_test",
            client_request={"budget": 1000000},
            vendor_combinations=test_combinations,
            beam_candidates=[],
            workflow_status=WorkflowStatus.BEAM_SEARCH,
            iteration_count=0
        )
        
        # Mock fitness calculation
        with patch.object(workflow, '_calculate_fitness_score') as mock_fitness:
            mock_fitness.side_effect = [0.5 + (i % 50) * 0.01 for i in range(50)]
            
            start_time = time.time()
            result = workflow.beam_search_node(state)
            execution_time = time.time() - start_time
            
            assert execution_time < 1.0
            assert len(result["beam_candidates"]) <= 3
            
            print(f"✅ Beam search performance test passed ({execution_time:.3f}s)")
        
        # Test vendor filtering performance
        vendors = []
        for i in range(100):
            vendor = {
                "id": f"vendor_{i}",
                "name": f"Vendor {i}",
                "rental_cost": 200000 + (i * 1000),
                "location_city": "Mumbai" if i % 2 == 0 else "Bangalore",
                "rating": 3.0 + (i % 20) * 0.1
            }
            vendors.append(vendor)
        
        start_time = time.time()
        filtered_vendors = [v for v in vendors if v["location_city"] == "Mumbai" and v["rental_cost"] <= 300000]
        filtering_time = time.time() - start_time
        
        assert filtering_time < 0.1
        assert len(filtered_vendors) > 0
        
        print(f"✅ Vendor filtering performance test passed ({filtering_time:.4f}s)")
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        exit(1)
    
    print("🎉 All performance tests passed!")
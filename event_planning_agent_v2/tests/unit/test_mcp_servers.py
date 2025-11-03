"""
Unit tests for MCP servers
"""

import json
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta

from mcp_servers.vendor_server import VendorDataServer, enhanced_vendor_search, vendor_compatibility_check
from mcp_servers.calculation_server import CalculationServer, fitness_score_calculation, budget_optimization
from mcp_servers.monitoring_server import MonitoringServer, log_agent_interaction, track_workflow_performance


class TestVendorDataServer:
    """Test Vendor Data MCP Server functionality"""
    
    def test_vendor_server_initialization(self):
        """Test VendorDataServer can be initialized"""
        server = VendorDataServer()
        assert hasattr(server, 'enhanced_vendor_search')
        assert hasattr(server, 'vendor_compatibility_check')
        assert hasattr(server, 'vendor_availability_check')
    
    @pytest.mark.asyncio
    async def test_enhanced_vendor_search_basic(self):
        """Test basic enhanced vendor search functionality"""
        # Mock database connection
        with patch('mcp_servers.vendor_server.get_database_connection') as mock_db:
            mock_cursor = Mock()
            mock_db.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
            
            # Mock query results
            mock_cursor.fetchall.return_value = [
                {
                    'id': 'venue_1',
                    'name': 'Grand Hotel',
                    'service_type': 'venue',
                    'location_city': 'Bangalore',
                    'rental_cost': 300000,
                    'max_seating_capacity': 300,
                    'venue_type': 'Hotel'
                },
                {
                    'id': 'venue_2',
                    'name': 'Garden Resort',
                    'service_type': 'venue',
                    'location_city': 'Bangalore',
                    'rental_cost': 250000,
                    'max_seating_capacity': 250,
                    'venue_type': 'Resort'
                }
            ]
            
            result = await enhanced_vendor_search(
                service_type="venue",
                filters={
                    "location_city": "Bangalore",
                    "budget": 350000,
                    "capacity_min": 200
                },
                preferences={
                    "style_keywords": ["modern", "elegant"],
                    "client_vision": "Modern elegant wedding venue"
                }
            )
            
            assert 'vendors' in result
            assert len(result['vendors']) == 2
            assert result['search_metadata']['total_found'] == 2
            assert result['search_metadata']['filters_applied']['location_city'] == 'Bangalore'
    
    @pytest.mark.asyncio
    async def test_enhanced_vendor_search_with_ml_ranking(self):
        """Test enhanced vendor search with ML-based ranking"""
        with patch('mcp_servers.vendor_server.get_database_connection') as mock_db:
            mock_cursor = Mock()
            mock_db.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
            
            # Mock vendors with different attributes
            mock_cursor.fetchall.return_value = [
                {
                    'id': 'venue_1',
                    'name': 'Modern Hotel',
                    'service_type': 'venue',
                    'location_city': 'Bangalore',
                    'rental_cost': 300000,
                    'attributes': {'style': 'modern', 'amenities': ['AC', 'Parking']}
                },
                {
                    'id': 'venue_2',
                    'name': 'Traditional Hall',
                    'service_type': 'venue',
                    'location_city': 'Bangalore',
                    'rental_cost': 200000,
                    'attributes': {'style': 'traditional', 'amenities': ['Parking']}
                }
            ]
            
            result = await enhanced_vendor_search(
                service_type="venue",
                filters={"location_city": "Bangalore"},
                preferences={
                    "style_keywords": ["modern", "contemporary"],
                    "client_vision": "We want a modern, stylish venue"
                }
            )
            
            # Check that ML ranking is applied
            vendors = result['vendors']
            assert len(vendors) == 2
            
            # Modern hotel should rank higher due to style match
            modern_vendor = next(v for v in vendors if v['name'] == 'Modern Hotel')
            traditional_vendor = next(v for v in vendors if v['name'] == 'Traditional Hall')
            
            assert modern_vendor['ml_score'] > traditional_vendor['ml_score']
    
    @pytest.mark.asyncio
    async def test_vendor_compatibility_check(self):
        """Test vendor compatibility checking"""
        test_vendors = [
            {
                "vendor_id": "venue_1",
                "service_type": "venue",
                "location_city": "Bangalore",
                "attributes": {"capacity": 300, "setup_time": 4}
            },
            {
                "vendor_id": "caterer_1",
                "service_type": "caterer",
                "location_city": "Bangalore",
                "attributes": {"cuisines": ["Indian", "Continental"], "setup_time": 2}
            },
            {
                "vendor_id": "photographer_1",
                "service_type": "photographer",
                "location_city": "Mumbai",  # Different city
                "attributes": {"travel_available": True}
            }
        ]
        
        result = await vendor_compatibility_check(
            vendors=test_vendors,
            event_date="2024-12-15",
            guest_count=250
        )
        
        assert 'overall_compatible' in result
        assert 'compatibility_analysis' in result
        assert 'recommendations' in result
        
        # Check location compatibility analysis
        location_analysis = result['compatibility_analysis']['location_compatibility']
        assert location_analysis['same_city_vendors'] == 2
        assert location_analysis['different_city_vendors'] == 1
        
        # Check capacity compatibility
        capacity_analysis = result['compatibility_analysis']['capacity_compatibility']
        assert capacity_analysis['adequate_capacity'] is True
    
    @pytest.mark.asyncio
    async def test_vendor_availability_check(self):
        """Test real-time vendor availability checking"""
        from mcp_servers.vendor_server import vendor_availability_check
        
        with patch('mcp_servers.vendor_server.get_database_connection') as mock_db:
            mock_cursor = Mock()
            mock_db.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
            
            # Mock availability check - vendor is available
            mock_cursor.fetchone.return_value = None  # No conflicting bookings
            
            result = await vendor_availability_check(
                vendor_id="venue_1",
                event_date="2024-12-15",
                service_type="venue"
            )
            
            assert result['available'] is True
            assert result['vendor_id'] == "venue_1"
            assert result['checked_date'] == "2024-12-15"
    
    def test_vendor_server_error_handling(self):
        """Test error handling in vendor server"""
        server = VendorDataServer()
        
        # Test with invalid service type
        with pytest.raises(ValueError):
            asyncio.run(enhanced_vendor_search(
                service_type="invalid_service",
                filters={},
                preferences={}
            ))


class TestCalculationServer:
    """Test Calculation MCP Server functionality"""
    
    def test_calculation_server_initialization(self):
        """Test CalculationServer can be initialized"""
        server = CalculationServer()
        assert hasattr(server, 'fitness_score_calculation')
        assert hasattr(server, 'budget_optimization')
        assert hasattr(server, 'cost_prediction')
    
    @pytest.mark.asyncio
    async def test_fitness_score_calculation(self):
        """Test fitness score calculation with ML features"""
        vendor_combination = {
            "venue": {
                "id": "venue_1",
                "name": "Grand Hotel",
                "rental_cost": 300000,
                "max_seating_capacity": 300,
                "location_city": "Bangalore",
                "attributes": {"style": "modern", "amenities": ["AC", "Parking"]}
            },
            "caterer": {
                "id": "caterer_1",
                "name": "Delicious Catering",
                "min_veg_price": 800,
                "location_city": "Bangalore",
                "attributes": {"cuisines": ["Indian", "Continental"]}
            }
        }
        
        client_preferences = {
            "budget": 1000000,
            "guest_count": 250,
            "style_preferences": ["modern", "elegant"],
            "location_preference": "Bangalore",
            "cuisine_preferences": ["Indian"]
        }
        
        result = await fitness_score_calculation(
            vendor_combination=vendor_combination,
            client_preferences=client_preferences
        )
        
        assert 'fitness_score' in result
        assert 'component_scores' in result
        assert 'ml_features' in result
        assert 'confidence_interval' in result
        
        # Check fitness score is reasonable
        fitness_score = result['fitness_score']
        assert 0 <= fitness_score <= 1
        
        # Check component scores
        components = result['component_scores']
        assert 'budget_compliance' in components
        assert 'preference_match' in components
        assert 'vendor_compatibility' in components
        assert 'location_convenience' in components
        
        # Check ML features
        ml_features = result['ml_features']
        assert 'style_similarity_score' in ml_features
        assert 'price_competitiveness' in ml_features
        assert 'vendor_reputation_score' in ml_features
    
    @pytest.mark.asyncio
    async def test_budget_optimization(self):
        """Test advanced budget allocation optimization"""
        service_requirements = {
            "venue": {
                "guest_count": 250,
                "location": "Bangalore",
                "style_preference": "modern"
            },
            "caterer": {
                "guest_count": 250,
                "cuisine_preferences": ["Indian", "Continental"],
                "dietary_requirements": ["Vegetarian", "Vegan"]
            },
            "photographer": {
                "coverage_hours": 8,
                "style": "candid",
                "video_required": True
            },
            "makeup_artist": {
                "service_type": "bridal",
                "on_site": True
            }
        }
        
        result = await budget_optimization(
            total_budget=1200000,
            service_requirements=service_requirements
        )
        
        assert 'optimized_allocation' in result
        assert 'optimization_results' in result
        assert 'market_analysis' in result
        assert 'recommendations' in result
        
        # Check optimized allocation
        allocation = result['optimized_allocation']
        assert 'venue' in allocation
        assert 'caterer' in allocation
        assert 'photographer' in allocation
        assert 'makeup_artist' in allocation
        
        # Check total allocation equals budget
        total_allocated = sum(allocation.values())
        assert abs(total_allocated - 1200000) < 1000  # Within ₹1000 tolerance
        
        # Check optimization results
        opt_results = result['optimization_results']
        assert 'allocation_efficiency' in opt_results
        assert 'cost_savings_potential' in opt_results
        assert 'risk_assessment' in opt_results
    
    @pytest.mark.asyncio
    async def test_cost_prediction(self):
        """Test cost prediction with confidence intervals"""
        from mcp_servers.calculation_server import cost_prediction
        
        event_parameters = {
            "guest_count": 300,
            "venue_type": "hotel",
            "location_city": "Bangalore",
            "cuisine_types": ["Indian", "Continental"],
            "photography_level": "premium",
            "event_duration_hours": 6,
            "season": "peak"  # Wedding season
        }
        
        result = await cost_prediction(event_parameters=event_parameters)
        
        assert 'predicted_total_cost' in result
        assert 'service_breakdown' in result
        assert 'confidence_intervals' in result
        assert 'market_factors' in result
        
        # Check predicted cost is reasonable
        predicted_cost = result['predicted_total_cost']
        assert predicted_cost > 0
        assert predicted_cost < 10000000  # Reasonable upper bound
        
        # Check service breakdown
        breakdown = result['service_breakdown']
        assert 'venue' in breakdown
        assert 'caterer' in breakdown
        assert 'photographer' in breakdown
        
        # Check confidence intervals
        confidence = result['confidence_intervals']
        assert 'lower_bound' in confidence
        assert 'upper_bound' in confidence
        assert confidence['lower_bound'] < predicted_cost < confidence['upper_bound']
    
    def test_calculation_server_error_handling(self):
        """Test error handling in calculation server"""
        # Test with invalid budget
        with pytest.raises(ValueError):
            asyncio.run(budget_optimization(
                total_budget=-1000,  # Negative budget
                service_requirements={}
            ))
        
        # Test with missing required parameters
        with pytest.raises(KeyError):
            asyncio.run(fitness_score_calculation(
                vendor_combination={},  # Empty combination
                client_preferences={}
            ))


class TestMonitoringServer:
    """Test Monitoring MCP Server functionality"""
    
    def test_monitoring_server_initialization(self):
        """Test MonitoringServer can be initialized"""
        server = MonitoringServer()
        assert hasattr(server, 'log_agent_interaction')
        assert hasattr(server, 'track_workflow_performance')
        assert hasattr(server, 'generate_health_report')
    
    @pytest.mark.asyncio
    async def test_log_agent_interaction(self):
        """Test agent interaction logging"""
        with patch('mcp_servers.monitoring_server.get_database_connection') as mock_db:
            mock_cursor = Mock()
            mock_db.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
            
            result = await log_agent_interaction(
                agent_name="budgeting_agent",
                action="calculate_fitness_score",
                duration_ms=1500,
                success=True,
                input_data={"vendor_combination": {"venue": {}}},
                output_data={"fitness_score": 0.85}
            )
            
            assert 'interaction_id' in result
            assert result['logged_successfully'] is True
            assert result['agent_name'] == "budgeting_agent"
            assert result['action'] == "calculate_fitness_score"
            
            # Verify database insert was called
            mock_cursor.execute.assert_called_once()
            call_args = mock_cursor.execute.call_args[0]
            assert 'INSERT INTO agent_interactions' in call_args[0]
    
    @pytest.mark.asyncio
    async def test_track_workflow_performance_start(self):
        """Test workflow performance tracking - start"""
        with patch('mcp_servers.monitoring_server.get_database_connection') as mock_db:
            mock_cursor = Mock()
            mock_db.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
            
            workflow_id = "test_workflow_123"
            
            result = await track_workflow_performance(
                workflow_id=workflow_id,
                workflow_type="event_planning",
                action="start"
            )
            
            assert result['workflow_id'] == workflow_id
            assert result['action'] == "start"
            assert result['tracking_started'] is True
            assert 'start_time' in result
    
    @pytest.mark.asyncio
    async def test_track_workflow_performance_complete(self):
        """Test workflow performance tracking - complete"""
        with patch('mcp_servers.monitoring_server.get_database_connection') as mock_db:
            mock_cursor = Mock()
            mock_db.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
            
            # Mock existing workflow record
            mock_cursor.fetchone.return_value = {
                'workflow_id': 'test_workflow_123',
                'start_time': datetime.now() - timedelta(minutes=5),
                'workflow_type': 'event_planning'
            }
            
            workflow_id = "test_workflow_123"
            
            result = await track_workflow_performance(
                workflow_id=workflow_id,
                workflow_type="event_planning",
                action="complete",
                performance_metrics={
                    "iterations": 3,
                    "combinations_evaluated": 15,
                    "final_score": 0.85,
                    "beam_width": 3
                }
            )
            
            assert result['workflow_id'] == workflow_id
            assert result['action'] == "complete"
            assert result['tracking_completed'] is True
            assert 'total_duration_ms' in result
            assert result['performance_metrics']['iterations'] == 3
            assert result['performance_metrics']['final_score'] == 0.85
    
    @pytest.mark.asyncio
    async def test_generate_health_report_summary(self):
        """Test health report generation - summary"""
        from mcp_servers.monitoring_server import generate_health_report
        
        with patch('mcp_servers.monitoring_server.get_database_connection') as mock_db:
            mock_cursor = Mock()
            mock_db.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
            
            # Mock health metrics
            mock_cursor.fetchone.side_effect = [
                {'count': 150},  # Total workflows
                {'count': 145},  # Successful workflows
                {'avg_duration': 45000},  # Average duration
                {'count': 1200}  # Total agent interactions
            ]
            
            result = await generate_health_report(
                report_type="summary",
                time_range_hours=24
            )
            
            assert 'system_health' in result
            assert 'workflow_statistics' in result
            assert 'agent_performance' in result
            assert 'recommendations' in result
            
            # Check system health
            health = result['system_health']
            assert health['status'] in ['healthy', 'warning', 'critical']
            assert 'uptime_hours' in health
            
            # Check workflow statistics
            workflow_stats = result['workflow_statistics']
            assert workflow_stats['total_workflows'] == 150
            assert workflow_stats['successful_workflows'] == 145
            assert workflow_stats['success_rate'] > 0.9  # Should be high
            assert workflow_stats['average_duration_ms'] == 45000
    
    @pytest.mark.asyncio
    async def test_generate_health_report_detailed(self):
        """Test health report generation - detailed"""
        from mcp_servers.monitoring_server import generate_health_report
        
        with patch('mcp_servers.monitoring_server.get_database_connection') as mock_db:
            mock_cursor = Mock()
            mock_db.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
            
            # Mock detailed metrics
            mock_cursor.fetchall.side_effect = [
                [  # Agent performance by type
                    {'agent_name': 'orchestrator_agent', 'avg_duration': 2000, 'success_rate': 0.98},
                    {'agent_name': 'budgeting_agent', 'avg_duration': 3500, 'success_rate': 0.95},
                    {'agent_name': 'sourcing_agent', 'avg_duration': 5000, 'success_rate': 0.92}
                ],
                [  # Error patterns
                    {'error_type': 'database_timeout', 'count': 5},
                    {'error_type': 'llm_timeout', 'count': 3}
                ]
            ]
            
            result = await generate_health_report(
                report_type="detailed",
                time_range_hours=24
            )
            
            assert 'agent_performance_breakdown' in result
            assert 'error_analysis' in result
            assert 'performance_trends' in result
            
            # Check agent performance breakdown
            agent_perf = result['agent_performance_breakdown']
            assert len(agent_perf) == 3
            assert agent_perf[0]['agent_name'] == 'orchestrator_agent'
            assert agent_perf[0]['success_rate'] == 0.98
            
            # Check error analysis
            error_analysis = result['error_analysis']
            assert len(error_analysis['error_patterns']) == 2
            assert error_analysis['total_errors'] == 8
    
    def test_monitoring_server_error_handling(self):
        """Test error handling in monitoring server"""
        # Test with invalid time range
        with pytest.raises(ValueError):
            asyncio.run(generate_health_report(
                report_type="summary",
                time_range_hours=-1  # Negative time range
            ))
        
        # Test with invalid report type
        with pytest.raises(ValueError):
            asyncio.run(generate_health_report(
                report_type="invalid_type",
                time_range_hours=24
            ))


class TestMCPServerIntegration:
    """Test MCP server integration and workflow"""
    
    @pytest.mark.asyncio
    async def test_vendor_to_calculation_server_workflow(self):
        """Test workflow from vendor search to fitness calculation"""
        # Step 1: Search for vendors
        with patch('mcp_servers.vendor_server.get_database_connection') as mock_vendor_db:
            mock_cursor = Mock()
            mock_vendor_db.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
            
            mock_cursor.fetchall.return_value = [
                {
                    'id': 'venue_1',
                    'name': 'Grand Hotel',
                    'service_type': 'venue',
                    'rental_cost': 300000,
                    'location_city': 'Bangalore'
                }
            ]
            
            vendor_result = await enhanced_vendor_search(
                service_type="venue",
                filters={"location_city": "Bangalore"},
                preferences={"style_keywords": ["modern"]}
            )
            
            # Step 2: Use vendor in fitness calculation
            vendor_combination = {
                "venue": vendor_result['vendors'][0]
            }
            
            client_preferences = {
                "budget": 1000000,
                "guest_count": 250,
                "style_preferences": ["modern"]
            }
            
            fitness_result = await fitness_score_calculation(
                vendor_combination=vendor_combination,
                client_preferences=client_preferences
            )
            
            assert 'fitness_score' in fitness_result
            assert fitness_result['fitness_score'] > 0
    
    @pytest.mark.asyncio
    async def test_calculation_to_monitoring_server_workflow(self):
        """Test workflow from calculation to monitoring"""
        # Step 1: Perform budget optimization
        service_requirements = {
            "venue": {"guest_count": 200},
            "caterer": {"guest_count": 200}
        }
        
        budget_result = await budget_optimization(
            total_budget=800000,
            service_requirements=service_requirements
        )
        
        # Step 2: Log the optimization performance
        with patch('mcp_servers.monitoring_server.get_database_connection') as mock_monitor_db:
            mock_cursor = Mock()
            mock_monitor_db.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
            
            log_result = await log_agent_interaction(
                agent_name="calculation_server",
                action="budget_optimization",
                duration_ms=2500,
                success=True,
                input_data={"total_budget": 800000},
                output_data=budget_result
            )
            
            assert log_result['logged_successfully'] is True
            assert log_result['agent_name'] == "calculation_server"
    
    def test_mcp_server_error_propagation(self):
        """Test error propagation between MCP servers"""
        # Test that errors in one server don't crash others
        with patch('mcp_servers.vendor_server.get_database_connection') as mock_db:
            mock_db.side_effect = Exception("Database connection failed")
            
            # Vendor server should handle the error gracefully
            with pytest.raises(Exception):
                asyncio.run(enhanced_vendor_search(
                    service_type="venue",
                    filters={},
                    preferences={}
                ))
        
        # Other servers should still work
        result = asyncio.run(fitness_score_calculation(
            vendor_combination={"venue": {"rental_cost": 300000}},
            client_preferences={"budget": 1000000, "guest_count": 250}
        ))
        
        assert 'fitness_score' in result


if __name__ == "__main__":
    # Run basic MCP server tests
    print("Running MCP Server Unit Tests...")
    
    # Test server initialization
    try:
        vendor_server = VendorDataServer()
        calculation_server = CalculationServer()
        monitoring_server = MonitoringServer()
        print("✅ Successfully initialized all MCP servers")
    except Exception as e:
        print(f"❌ MCP server initialization failed: {e}")
        exit(1)
    
    # Test basic functionality
    try:
        # Test vendor search (mocked)
        with patch('mcp_servers.vendor_server.get_database_connection'):
            result = asyncio.run(enhanced_vendor_search(
                service_type="venue",
                filters={"location_city": "Bangalore"},
                preferences={"style_keywords": ["modern"]}
            ))
            assert 'vendors' in result
        
        # Test fitness calculation
        result = asyncio.run(fitness_score_calculation(
            vendor_combination={"venue": {"rental_cost": 300000}},
            client_preferences={"budget": 1000000, "guest_count": 250}
        ))
        assert 'fitness_score' in result
        
        # Test monitoring (mocked)
        with patch('mcp_servers.monitoring_server.get_database_connection'):
            result = asyncio.run(log_agent_interaction(
                agent_name="test_agent",
                action="test_action",
                duration_ms=1000,
                success=True,
                input_data={},
                output_data={}
            ))
            assert 'interaction_id' in result
        
        print("✅ MCP server basic functionality tests passed")
        
    except Exception as e:
        print(f"❌ MCP server functionality tests failed: {e}")
        exit(1)
    
    print("🎉 All MCP server unit tests passed!")
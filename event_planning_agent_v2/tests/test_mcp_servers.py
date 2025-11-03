"""
Test script for MCP servers functionality
"""

import asyncio
import json
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_vendor_server():
    """Test vendor data MCP server"""
    logger.info("Testing Vendor Data MCP Server...")
    
    try:
        from ..mcp_servers.vendor_server import vendor_server
        
        # Test enhanced vendor search
        search_result = await vendor_server.enhanced_vendor_search(
            service_type="venue",
            filters={
                "location_city": "Bangalore",
                "budget": 500000,
                "capacity_min": 200
            },
            preferences={
                "style_keywords": ["modern", "elegant"],
                "client_vision": "We want a modern elegant wedding venue"
            }
        )
        
        logger.info(f"✅ Vendor search test passed: Found {len(search_result.get('vendors', []))} vendors")
        
        # Test vendor compatibility check
        test_vendors = [
            {
                "vendor_id": "test_venue_1",
                "service_type": "venue",
                "location_city": "Bangalore",
                "attributes": {"capacity": 300}
            },
            {
                "vendor_id": "test_caterer_1", 
                "service_type": "caterer",
                "location_city": "Bangalore",
                "attributes": {"cuisines": ["Indian", "Continental"]}
            }
        ]
        
        compatibility_result = await vendor_server.vendor_compatibility_check(
            vendors=test_vendors,
            event_date="2024-12-15",
            guest_count=250
        )
        
        logger.info(f"✅ Compatibility check test passed: Overall compatible = {compatibility_result.get('overall_compatible')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Vendor server test failed: {e}")
        return False


async def test_calculation_server():
    """Test calculation MCP server"""
    logger.info("Testing Calculation MCP Server...")
    
    try:
        from ..mcp_servers.calculation_server import calculation_server
        
        # Test fitness score calculation
        vendor_combination = {
            "venue": {
                "id": "venue_1",
                "name": "Test Venue",
                "rental_cost": 400000,
                "max_seating_capacity": 300,
                "attributes": {"about": "Modern elegant venue"}
            },
            "caterer": {
                "id": "caterer_1",
                "name": "Test Caterer",
                "min_veg_price": 800,
                "attributes": {"cuisines": ["Indian", "Continental"]}
            }
        }
        
        client_preferences = {
            "budget": 1000000,
            "guest_count": 250,
            "style_preferences": ["modern", "elegant"]
        }
        
        fitness_result = await calculation_server.fitness_score_calculation(
            vendor_combination=vendor_combination,
            client_preferences=client_preferences
        )
        
        logger.info(f"✅ Fitness score test passed: Score = {fitness_result.get('fitness_score'):.3f}")
        
        # Test budget optimization
        budget_result = await calculation_server.budget_optimization(
            total_budget=1000000,
            service_requirements={
                "venue": {"guest_count": 250},
                "caterer": {"guest_count": 250},
                "photographer": {"level": "standard"},
                "makeup_artist": {"service_type": "bridal"}
            }
        )
        
        logger.info(f"✅ Budget optimization test passed: Efficiency = {budget_result.get('optimization_results', {}).get('allocation_efficiency', 0):.3f}")
        
        # Test cost prediction
        cost_result = await calculation_server.cost_prediction(
            event_parameters={
                "guest_count": 250,
                "venue_type": "hotel",
                "location_city": "Bangalore",
                "cuisine_types": ["Indian", "Continental"],
                "photography_level": "standard"
            }
        )
        
        logger.info(f"✅ Cost prediction test passed: Predicted cost = ₹{cost_result.get('predicted_total_cost', 0):,.0f}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Calculation server test failed: {e}")
        return False


async def test_monitoring_server():
    """Test monitoring MCP server"""
    logger.info("Testing Monitoring MCP Server...")
    
    try:
        from ..mcp_servers.monitoring_server import monitoring_server
        
        # Test agent interaction logging
        log_result = await monitoring_server.log_agent_interaction(
            agent_name="test_agent",
            action="test_action",
            duration_ms=1500,
            success=True,
            input_data={"test": "data"},
            output_data={"result": "success"}
        )
        
        logger.info(f"✅ Agent interaction logging test passed: ID = {log_result.get('interaction_id')}")
        
        # Test workflow performance tracking
        workflow_id = f"test_workflow_{int(datetime.now().timestamp())}"
        
        # Start workflow
        start_result = await monitoring_server.track_workflow_performance(
            workflow_id=workflow_id,
            workflow_type="event_planning",
            action="start"
        )
        
        # Complete workflow
        complete_result = await monitoring_server.track_workflow_performance(
            workflow_id=workflow_id,
            workflow_type="event_planning",
            action="complete",
            performance_metrics={
                "iterations": 3,
                "combinations_evaluated": 15,
                "final_score": 0.85
            }
        )
        
        logger.info(f"✅ Workflow tracking test passed: Duration = {complete_result.get('total_duration_ms', 0)}ms")
        
        # Test health report generation
        health_result = await monitoring_server.generate_health_report(
            report_type="summary",
            time_range_hours=1
        )
        
        logger.info(f"✅ Health report test passed: Status = {health_result.get('system_health', {}).get('status')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Monitoring server test failed: {e}")
        return False


async def run_all_tests():
    """Run all MCP server tests"""
    logger.info("🚀 Starting MCP Server Tests...")
    
    test_results = {
        "vendor_server": False,
        "calculation_server": False,
        "monitoring_server": False
    }
    
    # Run tests
    test_results["vendor_server"] = await test_vendor_server()
    test_results["calculation_server"] = await test_calculation_server()
    test_results["monitoring_server"] = await test_monitoring_server()
    
    # Summary
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    logger.info(f"\n📊 Test Results Summary:")
    logger.info(f"   Passed: {passed_tests}/{total_tests}")
    
    for server, passed in test_results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        logger.info(f"   {server}: {status}")
    
    if passed_tests == total_tests:
        logger.info("🎉 All MCP server tests passed!")
        return True
    else:
        logger.error("❌ Some MCP server tests failed!")
        return False


if __name__ == "__main__":
    # Run tests
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)
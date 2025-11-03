"""
Test script for progress tracking components
"""
import sys
import os

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from components.progress import (
    WorkflowSteps,
    ProgressBar,
    AgentActivityDisplay,
    ErrorDisplay,
    WorkflowController,
    RealTimeStatusUpdater
)

def test_workflow_steps():
    """Test WorkflowSteps functionality"""
    print("Testing WorkflowSteps...")
    
    # Test step info retrieval
    step_info = WorkflowSteps.get_step_info('budget_allocation')
    assert step_info['title'] == "💰 Analyzing Budget Requirements"
    assert 'Budgeting Agent' in step_info['agents']
    
    # Test step ordering
    steps = WorkflowSteps.get_step_order()
    assert len(steps) == 6
    assert steps[0] == 'initialization'
    assert steps[-1] == 'blueprint_generation'
    
    # Test progress calculation
    progress = WorkflowSteps.calculate_progress_percentage('vendor_sourcing', 50.0)
    assert 30 <= progress <= 50  # Should be around 41.67%
    
    print("✅ WorkflowSteps tests passed")

def test_real_time_updater():
    """Test RealTimeStatusUpdater functionality"""
    print("Testing RealTimeStatusUpdater...")
    
    # Test initialization
    updater = RealTimeStatusUpdater('test-plan-123', update_interval=5)
    assert updater.plan_id == 'test-plan-123'
    assert updater.update_interval == 5
    assert not updater.is_running
    
    # Test monitoring controls
    updater.start_monitoring()
    assert updater.is_running
    
    updater.stop_monitoring()
    assert not updater.is_running
    
    print("✅ RealTimeStatusUpdater tests passed")

def test_component_imports():
    """Test that all components can be imported without errors"""
    print("Testing component imports...")
    
    # Test that all classes are properly defined
    assert WorkflowSteps is not None
    assert ProgressBar is not None
    assert AgentActivityDisplay is not None
    assert ErrorDisplay is not None
    assert WorkflowController is not None
    assert RealTimeStatusUpdater is not None
    
    # Test that key methods exist
    assert hasattr(WorkflowSteps, 'get_step_info')
    assert hasattr(WorkflowSteps, 'calculate_progress_percentage')
    assert hasattr(ProgressBar, 'render')
    assert hasattr(AgentActivityDisplay, 'render')
    assert hasattr(ErrorDisplay, 'render')
    assert hasattr(RealTimeStatusUpdater, 'update_status')
    
    print("✅ Component import tests passed")

def main():
    """Run all tests"""
    print("Running progress component tests...\n")
    
    try:
        test_component_imports()
        test_workflow_steps()
        test_real_time_updater()
        
        print("\n🎉 All tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
"""
Simple diagnostic test for API/LLM Tool imports
"""

import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(parent_dir))

print("Testing imports...")

try:
    from agents.task_management.tools.api_llm_tool import APILLMTool
    print("✓ APILLMTool imported successfully")
except Exception as e:
    print(f"✗ Failed to import APILLMTool: {e}")
    sys.exit(1)

try:
    from agents.task_management.models.consolidated_models import ConsolidatedTaskData, ConsolidatedTask
    print("✓ Consolidated models imported successfully")
except Exception as e:
    print(f"✗ Failed to import consolidated models: {e}")
    sys.exit(1)

try:
    from agents.task_management.models.data_models import EnhancedTask, Resource
    print("✓ Data models imported successfully")
except Exception as e:
    print(f"✗ Failed to import data models: {e}")
    sys.exit(1)

print("\n✓ All imports successful!")
print("\nTesting APILLMTool instantiation...")

try:
    tool = APILLMTool()
    print(f"✓ APILLMTool instantiated successfully with model: {tool.llm_model}")
except Exception as e:
    print(f"✗ Failed to instantiate APILLMTool: {e}")
    sys.exit(1)

print("\n✓ All basic tests passed!")

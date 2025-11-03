#!/usr/bin/env python3
"""
Simplified workflow that directly uses the tools without complex agent orchestration
"""

import json
from event_tools import HybridFilterTool, VendorDatabaseTool

class SimpleVendorSourcing:
    """Simple vendor sourcing workflow using tools directly"""
    
    def __init__(self):
        self.filter_tool = HybridFilterTool()
        self.database_tool = VendorDatabaseTool()
    
    def source_vendors(self, service_type: str, client_data: dict) -> str:
        """
        Source vendors for a given service type and client data
        
        Args:
            service_type: Type of service (venue, caterer, photographer, makeup_artist)
            client_data: Client requirements and preferences
            
        Returns:
            JSON string of ranked vendors
        """
        try:
            print(f"🔍 Sourcing {service_type}s...")
            
            # Step 1: Generate filters
            print("   📋 Generating search filters...")
            filter_result = self.filter_tool._run(client_data, service_type)
            
            # Parse and add budget if not present
            filters = json.loads(filter_result)
            if 'budget' not in filters['hard_filters']:
                filters['hard_filters']['budget'] = client_data.get('budget', 1000000)
            
            filter_json = json.dumps(filters)
            print(f"   ✅ Filters generated: {filters['service_type']}")
            
            # Step 2: Query database
            print("   🗄️ Querying database...")
            vendor_result = self.database_tool._run(filter_json)
            
            if vendor_result.startswith("Error:"):
                print(f"   ❌ Database error: {vendor_result}")
                return json.dumps([])
            
            vendors = json.loads(vendor_result)
            print(f"   ✅ Found {len(vendors)} {service_type}s")
            
            if vendors:
                print(f"   🥇 Top recommendation: {vendors[0]['name']}")
                print(f"   ⭐ Score: {vendors[0]['ranking_score']}")
            
            return vendor_result
            
        except Exception as e:
            print(f"   ❌ Error in sourcing workflow: {e}")
            return json.dumps([])

# Create a tool wrapper for compatibility with existing code
class SimpleSourcingTool:
    """Tool wrapper for the simple sourcing workflow"""
    
    def __init__(self):
        self.sourcing = SimpleVendorSourcing()
    
    def _run(self, service_type: str, client_data: dict) -> str:
        return self.sourcing.source_vendors(service_type, client_data)

# Test function
def test_simple_workflow():
    """Test the simple workflow"""
    print("🧪 Testing Simple Vendor Sourcing Workflow")
    print("=" * 50)
    
    # Test data
    test_client_data = {
        "clientName": "Test Wedding",
        "guestCount": {"Reception": 300},
        "clientVision": "Modern elegant wedding in Bangalore with great food and photography",
        "venuePreferences": ["Hotel", "Banquet Hall"],
        "essentialVenueAmenities": ["Parking", "AC"],
        "decorationAndAmbiance": {"desiredTheme": "modern elegant"},
        "foodAndCatering": {
            "cuisinePreferences": ["North Indian", "South Indian"],
            "dietaryOptions": ["Vegetarian", "Non-Vegetarian"]
        },
        "additionalRequirements": {
            "photography": "Candid and traditional photography",
            "makeup": "Professional bridal makeup"
        },
        "budget": 800000
    }
    
    sourcing = SimpleVendorSourcing()
    
    # Test different service types
    service_types = ["venue", "caterer", "photographer", "makeup_artist"]
    budgets = {"venue": 400000, "caterer": 200000, "photographer": 80000, "makeup_artist": 25000}
    
    results = {}
    
    for service_type in service_types:
        print(f"\n🔍 Testing {service_type} sourcing...")
        
        # Set appropriate budget for this service type
        test_data = test_client_data.copy()
        test_data["budget"] = budgets[service_type]
        
        try:
            result = sourcing.source_vendors(service_type, test_data)
            vendors = json.loads(result)
            results[service_type] = vendors
            
            if vendors:
                print(f"   ✅ Success: {len(vendors)} options found")
                print(f"   🏆 Top choice: {vendors[0]['name']}")
            else:
                print(f"   ⚠️ No {service_type}s found within budget")
                
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            results[service_type] = []
    
    # Summary
    print(f"\n📊 Test Summary:")
    print("-" * 30)
    for service_type, vendors in results.items():
        status = "✅" if vendors else "❌"
        print(f"{status} {service_type.title()}: {len(vendors)} recommendations")
    
    return results

if __name__ == "__main__":
    test_simple_workflow()
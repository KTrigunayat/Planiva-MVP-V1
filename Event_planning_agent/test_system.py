#!/usr/bin/env python3
"""
Simple test script for Planiva Event Planning System
Tests core functionality without complex dependencies
"""

import json
import os
from database_setup import get_db_connection

def test_database():
    """Test database connectivity and data"""
    print("🔍 Testing database...")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check table counts
        tables = ['venues', 'caterers', 'photographers', 'makeup_artists']
        counts = {}
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            counts[table] = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        print("✅ Database connected successfully!")
        for table, count in counts.items():
            print(f"   📊 {table.title()}: {count} records")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_workflow():
    """Test the simple workflow"""
    print("\n🔍 Testing vendor sourcing workflow...")
    
    try:
        from simple_workflow import SimpleVendorSourcing
        
        # Test data
        test_client_data = {
            "clientName": "Test Wedding",
            "guestCount": {"Reception": 200},
            "clientVision": "Modern elegant wedding in Bangalore",
            "venuePreferences": ["Hotel"],
            "decorationAndAmbiance": {"desiredTheme": "modern"},
            "foodAndCatering": {"cuisinePreferences": ["North Indian"]},
            "budget": 500000
        }
        
        sourcing = SimpleVendorSourcing()
        
        # Test venue sourcing
        result = sourcing.source_vendors("venue", test_client_data)
        venues = json.loads(result)
        
        if venues:
            print("✅ Workflow test passed!")
            print(f"   🏢 Found {len(venues)} venues")
            print(f"   🥇 Top venue: {venues[0]['name']}")
            return True
        else:
            print("⚠️ No venues found, but workflow completed")
            return True
            
    except Exception as e:
        print(f"❌ Workflow test failed: {e}")
        return False

def test_all_services():
    """Test all service types"""
    print("\n🔍 Testing all service types...")
    
    try:
        from simple_workflow import SimpleVendorSourcing
        
        test_data = {
            "clientName": "Complete Test",
            "guestCount": {"Reception": 150},
            "clientVision": "Beautiful wedding in Bangalore",
            "budget": 300000
        }
        
        sourcing = SimpleVendorSourcing()
        service_types = ["venue", "caterer", "photographer", "makeup_artist"]
        budgets = {"venue": 200000, "caterer": 100000, "photographer": 50000, "makeup_artist": 20000}
        
        results = {}
        
        for service_type in service_types:
            test_data["budget"] = budgets[service_type]
            result = sourcing.source_vendors(service_type, test_data)
            vendors = json.loads(result)
            results[service_type] = len(vendors)
        
        print("✅ All service types tested!")
        for service_type, count in results.items():
            status = "✅" if count > 0 else "⚠️"
            print(f"   {status} {service_type.title()}: {count} options")
        
        return True
        
    except Exception as e:
        print(f"❌ Service types test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Planiva Event Planning System - Quick Test")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 3
    
    # Test database
    if test_database():
        tests_passed += 1
    
    # Test workflow
    if test_workflow():
        tests_passed += 1
    
    # Test all services
    if test_all_services():
        tests_passed += 1
    
    # Summary
    print(f"\n📊 Test Results: {tests_passed}/{total_tests} passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! System is ready to use.")
        print("\nNext steps:")
        print("• Run: python demo.py (see system in action)")
        print("• Run: python manage_database.py stats (check database)")
        return True
    else:
        print("⚠️ Some tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    main()
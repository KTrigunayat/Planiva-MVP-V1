#!/usr/bin/env python3
"""
Demo script for Planiva Event Planning System
Shows how to use the system for different wedding scenarios
"""

import json
from simple_workflow import SimpleSourcingTool

def demo_luxury_wedding():
    """Demo: Luxury wedding in Bangalore"""
    print("🎭 DEMO: Luxury Wedding Planning")
    print("=" * 50)
    
    client_data = {
        "clientName": "Aarav & Ananya",
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
        }
    }
    
    sourcing_tool = SimpleSourcingTool()
    
    # Budget allocation
    budgets = {
        "venue": 2500000,
        "caterer": 1500000,
        "photographer": 100000,
        "makeup_artist": 30000
    }
    
    print(f"👰 Client: {client_data['clientName']}")
    print(f"👥 Guests: {client_data['guestCount']['Reception']} (Reception)")
    print(f"💰 Total Budget: ₹{sum(budgets.values()):,}")
    print(f"📍 Location: Bangalore")
    print(f"🎨 Theme: {client_data['decorationAndAmbiance']['desiredTheme']}")
    print()
    
    recommendations = {}
    
    for service_type, budget in budgets.items():
        print(f"🔍 Finding {service_type}s (Budget: ₹{budget:,})...")
        
        try:
            test_data = client_data.copy()
            test_data["budget"] = budget
            
            result = sourcing_tool._run(service_type, test_data)
            vendors = json.loads(result)
            recommendations[service_type] = vendors
            
            if vendors:
                top_vendor = vendors[0]
                print(f"   🥇 Top Recommendation: {top_vendor['name']}")
                print(f"   📍 Location: {top_vendor.get('location_city', 'N/A')}")
                print(f"   ⭐ Score: {top_vendor.get('ranking_score', 'N/A')}")
                
                # Show price info
                price_key = {
                    'venue': 'rental_cost',
                    'caterer': 'min_veg_price', 
                    'photographer': 'photo_package_price',
                    'makeup_artist': 'bridal_makeup_price'
                }.get(service_type)
                
                if price_key and price_key in top_vendor:
                    price = top_vendor[price_key]
                    if service_type == 'caterer':
                        print(f"   💰 Price: ₹{price}/plate (veg)")
                    else:
                        print(f"   💰 Price: ₹{price:,}")
                
                print(f"   📊 Found {len(vendors)} total options")
            else:
                print(f"   ❌ No {service_type}s found within budget")
            
            print()
            
        except Exception as e:
            print(f"   ❌ Error finding {service_type}s: {e}")
            print()
    
    # Summary
    print("📋 WEDDING PLAN SUMMARY")
    print("-" * 30)
    
    total_estimated_cost = 0
    
    for service_type, vendors in recommendations.items():
        if vendors:
            vendor = vendors[0]
            print(f"🏆 {service_type.title()}: {vendor['name']}")
            
            # Calculate estimated cost
            price_key = {
                'venue': 'rental_cost',
                'caterer': 'min_veg_price', 
                'photographer': 'photo_package_price',
                'makeup_artist': 'bridal_makeup_price'
            }.get(service_type)
            
            if price_key and price_key in vendor:
                price = vendor[price_key]
                if service_type == 'caterer':
                    estimated_cost = price * client_data['guestCount']['Reception']
                else:
                    estimated_cost = price
                
                total_estimated_cost += estimated_cost
                print(f"   💰 Estimated Cost: ₹{estimated_cost:,}")
        else:
            print(f"❌ {service_type.title()}: No options found")
    
    print(f"\n💰 Total Estimated Cost: ₹{total_estimated_cost:,}")
    print(f"💰 Budget Remaining: ₹{sum(budgets.values()) - total_estimated_cost:,}")

def demo_intimate_wedding():
    """Demo: Intimate wedding in Bangalore"""
    print("\n🎭 DEMO: Intimate Wedding Planning")
    print("=" * 50)
    
    client_data = {
        "clientName": "Priya & Rohit",
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
        }
    }
    
    sourcing_tool = SimpleSourcingTool()
    
    # Budget allocation for intimate wedding
    budgets = {
        "venue": 800000,
        "caterer": 500000,
        "photographer": 60000,
        "makeup_artist": 20000
    }
    
    print(f"👰 Client: {client_data['clientName']}")
    print(f"👥 Guests: {client_data['guestCount']['Reception']} (Reception)")
    print(f"💰 Total Budget: ₹{sum(budgets.values()):,}")
    print(f"🎨 Theme: {client_data['decorationAndAmbiance']['desiredTheme']}")
    print()
    
    # Just show venue and caterer for this demo
    for service_type in ["venue", "caterer"]:
        budget = budgets[service_type]
        print(f"🔍 Finding {service_type}s (Budget: ₹{budget:,})...")
        
        try:
            test_data = client_data.copy()
            test_data["budget"] = budget
            
            result = sourcing_tool._run(service_type, test_data)
            vendors = json.loads(result)
            
            if vendors:
                print(f"   ✅ Found {len(vendors)} options")
                for i, vendor in enumerate(vendors[:3], 1):
                    print(f"   {i}. {vendor['name']} (Score: {vendor.get('ranking_score', 'N/A')})")
            else:
                print(f"   ❌ No {service_type}s found")
            
            print()
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            print()

def main():
    """Run all demos"""
    print("🎉 Welcome to Planiva Event Planning System Demo!")
    print("This demo shows how the AI system finds vendors for different wedding scenarios.\n")
    
    try:
        # Run luxury wedding demo
        demo_luxury_wedding()
        
        # Run intimate wedding demo  
        demo_intimate_wedding()
        
        print("\n🎊 Demo completed successfully!")
        print("\nThe system can handle various wedding scenarios by:")
        print("• Understanding client vision and preferences")
        print("• Filtering vendors based on hard requirements (budget, location, capacity)")
        print("• Ranking vendors using AI-powered preference matching")
        print("• Providing personalized recommendations with explanations")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        print("Make sure you've run the setup and have data loaded in the database.")

if __name__ == "__main__":
    main()
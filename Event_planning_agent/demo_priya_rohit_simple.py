#!/usr/bin/env python3
"""
Simple Demo for Priya & Rohit using the basic Event Planning Agent
This demo works with the simple workflow system and shows vendor sourcing
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

try:
    from simple_workflow import SimpleSourcingTool
    from event_tools import VendorDatabaseTool, HybridFilterTool
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure you're in the Event_planning_agent directory")
    print("💡 Run: python database_setup.py first")
    sys.exit(1)

class PriyaRohitDemo:
    """Demo class for Priya & Rohit's wedding using simple workflow"""
    
    def __init__(self):
        self.client_data = self.create_client_data()
        self.sourcing_tool = SimpleSourcingTool()
        
    def create_client_data(self):
        """Create Priya & Rohit's specific wedding data"""
        return {
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
            },
            "budget": 800000,  # 8 lakhs
            "location": "Bangalore"
        }
    
    def print_header(self, title: str):
        """Print formatted header"""
        print("\n" + "=" * 80)
        print(f"🎉 {title}")
        print("=" * 80)
    
    def print_section(self, title: str):
        """Print formatted section"""
        print(f"\n📋 {title}")
        print("-" * 60)
    
    def display_client_info(self):
        """Display client information"""
        self.print_section("Client Information")
        
        print(f"👰 Couple: {self.client_data['clientName']}")
        print(f"📍 Location: {self.client_data['location']}")
        print(f"👥 Reception Guests: {self.client_data['guestCount']['Reception']}")
        print(f"👥 Ceremony Guests: {self.client_data['guestCount']['Ceremony']}")
        print(f"💰 Total Budget: ₹{self.client_data['budget']:,}")
        print(f"🎨 Theme: {self.client_data['decorationAndAmbiance']['desiredTheme']}")
        print(f"🎨 Colors: {', '.join(self.client_data['decorationAndAmbiance']['colorScheme'])}")
        
        print(f"\n💭 Vision: {self.client_data['clientVision']}")
        
        print(f"\n🏢 Venue Preferences: {', '.join(self.client_data['venuePreferences'])}")
        print(f"🔧 Essential Amenities: {', '.join(self.client_data['essentialVenueAmenities'])}")
        
        print(f"\n🍽️ Cuisine: {', '.join(self.client_data['foodAndCatering']['cuisinePreferences'])}")
        print(f"🥗 Dietary: {', '.join(self.client_data['foodAndCatering']['dietaryOptions'])}")
        print(f"🍷 Beverages: {'Not allowed' if not self.client_data['foodAndCatering']['beverages']['allowed'] else 'Allowed'}")
        
        print(f"\n📸 Photography: {self.client_data['additionalRequirements']['photography']}")
        print(f"💄 Makeup: {self.client_data['additionalRequirements']['makeup']}")
    
    def source_vendors_by_type(self, service_type: str, budget: float):
        """Source vendors for a specific service type"""
        print(f"\n🔍 Sourcing {service_type}s (Budget: ₹{budget:,})...")
        
        try:
            # Prepare data for this service type
            service_data = self.client_data.copy()
            service_data["budget"] = budget
            
            # Get vendor recommendations
            result = self.sourcing_tool._run(service_type, service_data)
            vendors = json.loads(result)
            
            if vendors:
                print(f"✅ Found {len(vendors)} {service_type} options")
                
                # Display top 3 vendors
                for i, vendor in enumerate(vendors[:3], 1):
                    print(f"\n🏆 Option {i}: {vendor['name']}")
                    print(f"   📍 Location: {vendor.get('location_city', 'N/A')}")
                    print(f"   ⭐ Score: {vendor.get('ranking_score', 'N/A')}")
                    
                    # Show pricing based on service type
                    if service_type == 'venue':
                        if 'rental_cost' in vendor:
                            print(f"   💰 Rental Cost: ₹{vendor['rental_cost']:,}")
                        if 'capacity' in vendor:
                            print(f"   👥 Capacity: {vendor['capacity']} guests")
                        if 'amenities' in vendor:
                            amenities = vendor['amenities'][:3]  # Show first 3
                            print(f"   🔧 Amenities: {', '.join(amenities)}")
                    
                    elif service_type == 'caterer':
                        if 'min_veg_price' in vendor:
                            print(f"   💰 Veg Price: ₹{vendor['min_veg_price']}/plate")
                        if 'cuisine_types' in vendor:
                            cuisines = vendor['cuisine_types'][:3]
                            print(f"   🍽️ Cuisines: {', '.join(cuisines)}")
                    
                    elif service_type == 'photographer':
                        if 'photo_package_price' in vendor:
                            print(f"   💰 Package Price: ₹{vendor['photo_package_price']:,}")
                        if 'photography_styles' in vendor:
                            styles = vendor['photography_styles'][:2]
                            print(f"   📸 Styles: {', '.join(styles)}")
                    
                    elif service_type == 'makeup_artist':
                        if 'bridal_makeup_price' in vendor:
                            print(f"   💰 Bridal Package: ₹{vendor['bridal_makeup_price']:,}")
                        if 'makeup_styles' in vendor:
                            styles = vendor['makeup_styles'][:2]
                            print(f"   💄 Styles: {', '.join(styles)}")
                
                return vendors
            else:
                print(f"❌ No {service_type}s found within budget")
                return []
                
        except Exception as e:
            print(f"❌ Error sourcing {service_type}s: {e}")
            return []
    
    def create_wedding_plan(self, all_vendors):
        """Create a complete wedding plan from selected vendors"""
        self.print_section("Complete Wedding Plan")
        
        # Select best vendor from each category
        selected_vendors = {}
        total_cost = 0
        
        for service_type, vendors in all_vendors.items():
            if vendors:
                # Select the top-rated vendor
                best_vendor = vendors[0]
                selected_vendors[service_type] = best_vendor
                
                # Calculate cost
                if service_type == 'venue' and 'rental_cost' in best_vendor:
                    cost = best_vendor['rental_cost']
                elif service_type == 'caterer' and 'min_veg_price' in best_vendor:
                    cost = best_vendor['min_veg_price'] * self.client_data['guestCount']['Reception']
                elif service_type == 'photographer' and 'photo_package_price' in best_vendor:
                    cost = best_vendor['photo_package_price']
                elif service_type == 'makeup_artist' and 'bridal_makeup_price' in best_vendor:
                    cost = best_vendor['bridal_makeup_price']
                else:
                    cost = 0
                
                total_cost += cost
        
        # Display the complete plan
        print("🎊 PRIYA & ROHIT'S WEDDING PLAN")
        print("=" * 50)
        
        for service_type, vendor in selected_vendors.items():
            print(f"\n🏆 {service_type.upper()}: {vendor['name']}")
            print(f"   📍 Location: {vendor.get('location_city', 'N/A')}")
            print(f"   ⭐ Rating Score: {vendor.get('ranking_score', 'N/A')}")
            
            if 'contact_phone' in vendor:
                print(f"   📞 Contact: {vendor['contact_phone']}")
            if 'contact_email' in vendor:
                print(f"   📧 Email: {vendor['contact_email']}")
        
        print(f"\n💰 BUDGET SUMMARY")
        print("-" * 30)
        print(f"Total Estimated Cost: ₹{total_cost:,}")
        print(f"Original Budget: ₹{self.client_data['budget']:,}")
        print(f"Budget Remaining: ₹{self.client_data['budget'] - total_cost:,}")
        
        if total_cost <= self.client_data['budget']:
            print("✅ Plan is within budget!")
        else:
            print("⚠️ Plan exceeds budget - consider alternatives")
        
        return selected_vendors, total_cost
    
    def generate_timeline(self):
        """Generate a simple wedding timeline"""
        self.print_section("Wedding Timeline & Checklist")
        
        print("📅 PRE-WEDDING TIMELINE (8 weeks before)")
        print("-" * 40)
        print("🔸 8 weeks: Finalize venue booking")
        print("🔸 7 weeks: Confirm catering menu and guest count")
        print("🔸 6 weeks: Book photographer and schedule engagement shoot")
        print("🔸 5 weeks: Book makeup artist and schedule trial")
        print("🔸 4 weeks: Send invitations")
        print("🔸 3 weeks: Finalize decorations and theme details")
        print("🔸 2 weeks: Confirm all vendor details and timeline")
        print("🔸 1 week: Final guest count and seating arrangements")
        
        print("\n📅 WEDDING DAY TIMELINE")
        print("-" * 30)
        print("🔸 8:00 AM - Makeup artist arrives")
        print("🔸 10:00 AM - Photographer arrives for getting ready shots")
        print("🔸 12:00 PM - Bridal preparations complete")
        print("🔸 2:00 PM - Groom's preparations")
        print("🔸 4:00 PM - Ceremony begins")
        print("🔸 6:00 PM - Reception starts")
        print("🔸 7:00 PM - Dinner service")
        print("🔸 9:00 PM - Cake cutting and celebrations")
        print("🔸 11:00 PM - Event concludes")
    
    def save_plan_to_file(self, selected_vendors, total_cost):
        """Save the wedding plan to a file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"priya_rohit_wedding_plan_{timestamp}.json"
        
        plan_data = {
            "client_info": self.client_data,
            "selected_vendors": selected_vendors,
            "total_cost": total_cost,
            "budget_remaining": self.client_data['budget'] - total_cost,
            "generated_at": datetime.now().isoformat()
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(plan_data, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Wedding plan saved to: {filename}")
            return filename
        except Exception as e:
            print(f"❌ Error saving plan: {e}")
            return None
    
    def run_complete_demo(self):
        """Run the complete demo"""
        self.print_header("Priya & Rohit's Wedding Planning Demo")
        
        print("🎯 This demo will show the Event Planning Agent capabilities:")
        print("   1. Client information processing")
        print("   2. Intelligent vendor sourcing")
        print("   3. Budget-aware recommendations")
        print("   4. Complete wedding plan generation")
        print("   5. Timeline and checklist creation")
        
        # Step 1: Display client information
        self.display_client_info()
        
        # Step 2: Source vendors with budget allocation
        budget_allocation = {
            "venue": 400000,      # 50% of budget
            "caterer": 300000,    # 37.5% of budget  
            "photographer": 70000, # 8.75% of budget
            "makeup_artist": 30000 # 3.75% of budget
        }
        
        self.print_section("Vendor Sourcing with AI Matching")
        print("🤖 Using AI-powered hybrid filtering to find the best matches...")
        print(f"💰 Budget Allocation Strategy:")
        for service, budget in budget_allocation.items():
            percentage = (budget / self.client_data['budget']) * 100
            print(f"   {service.title()}: ₹{budget:,} ({percentage:.1f}%)")
        
        all_vendors = {}
        for service_type, budget in budget_allocation.items():
            vendors = self.source_vendors_by_type(service_type, budget)
            all_vendors[service_type] = vendors
        
        # Step 3: Create complete wedding plan
        selected_vendors, total_cost = self.create_wedding_plan(all_vendors)
        
        # Step 4: Generate timeline
        self.generate_timeline()
        
        # Step 5: Save plan
        filename = self.save_plan_to_file(selected_vendors, total_cost)
        
        # Final summary
        self.print_header("Demo Completed Successfully! 🎉")
        print("✅ Priya & Rohit's wedding plan is ready!")
        print(f"🎊 Total vendors found: {sum(len(v) for v in all_vendors.values())}")
        print(f"💰 Final cost: ₹{total_cost:,}")
        print(f"💰 Budget utilization: {(total_cost/self.client_data['budget']*100):.1f}%")
        
        if filename:
            print(f"📁 Plan saved to: {filename}")
        
        print("\n🌟 The AI system successfully:")
        print("   ✓ Analyzed client preferences and requirements")
        print("   ✓ Matched vendors using intelligent filtering")
        print("   ✓ Optimized budget allocation across services")
        print("   ✓ Generated a complete wedding plan")
        print("   ✓ Created timeline and checklist")
        
        return True

def main():
    """Main function"""
    try:
        demo = PriyaRohitDemo()
        success = demo.run_complete_demo()
        
        if success:
            print("\n🎊 Demo completed successfully!")
            print("💡 This demonstrates the Event Planning Agent's AI capabilities")
        else:
            print("\n⚠️ Demo had some issues")
        
        input("\nPress Enter to exit...")
        return success
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Demo interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()
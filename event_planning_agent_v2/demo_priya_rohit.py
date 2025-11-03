#!/usr/bin/env python3
"""
Complete Event Planning Demo for Priya & Rohit
Demonstrates the full Event Planning Agent v2 system with all functionalities
"""

import json
import sys
import time
import asyncio
from datetime import datetime, date, timedelta
from pathlib import Path
import requests
from typing import Dict, Any, List

# Add paths for imports
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))
sys.path.append(str(current_dir.parent))

class EventPlanningAgentV2Demo:
    """Complete demo for Event Planning Agent v2 with Priya & Rohit's wedding"""
    
    def __init__(self):
        self.api_base_url = "http://localhost:8000/v1"
        self.client_data = self.create_priya_rohit_data()
        self.plan_id = None
        
    def create_priya_rohit_data(self) -> Dict[str, Any]:
        """Create the specific client data for Priya & Rohit"""
        return {
            "clientName": "Priya & Rohit",
            "clientEmail": "priya.rohit@email.com",
            "clientPhone": "+91-98765-43210",
            "eventType": "Wedding",
            "eventDate": (date.today() + timedelta(days=90)).isoformat(),
            "location": "Bangalore",
            "guestCount": {
                "Reception": 150, 
                "Ceremony": 100,
                "total": 150
            },
            "clientVision": "We want an intimate, cozy wedding celebration in Bangalore with close family and friends. Focus on quality over quantity with excellent food and beautiful photography.",
            "venuePreferences": ["Banquet Hall", "Restaurant"],
            "essentialVenueAmenities": ["Air Conditioning", "Sound System"],
            "decorationAndAmbiance": {
                "desiredTheme": "traditional elegant",
                "colorScheme": ["red", "gold", "maroon"],
                "stylePreferences": ["traditional", "elegant", "intimate"]
            },
            "foodAndCatering": {
                "cuisinePreferences": ["South Indian", "North Indian"],
                "dietaryOptions": ["Vegetarian"],
                "serviceStyle": "buffet",
                "beverages": {"allowed": False}
            },
            "additionalRequirements": {
                "photography": "Traditional photography with some candid shots",
                "makeup": "Classic bridal makeup",
                "videography": "Ceremony highlights and reception coverage"
            },
            "budget": 800000.0,  # 8 lakhs INR
            "budgetFlexibility": "moderate",
            "priorities": {
                "venue": "high",
                "catering": "high", 
                "photography": "medium",
                "makeup": "medium"
            }
        }
    
    def print_header(self, title: str):
        """Print a formatted header"""
        print("\n" + "=" * 80)
        print(f"🎉 {title}")
        print("=" * 80)
    
    def print_section(self, title: str):
        """Print a formatted section header"""
        print(f"\n📋 {title}")
        print("-" * 60)
    
    def check_api_health(self) -> bool:
        """Check if the Event Planning Agent v2 API is running"""
        try:
            response = requests.get(f"{self.api_base_url.replace('/v1', '')}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ API Health: {health_data.get('status', 'unknown')}")
                print(f"📊 Version: {health_data.get('version', 'unknown')}")
                return True
            else:
                print(f"❌ API Health Check Failed: Status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"⚠️ API Connection Failed: {e}")
            print("🔄 Running in demo mode with simulated responses...")
            return self.run_demo_mode()
    
    def create_event_plan(self) -> bool:
        """Create a new event plan using the API"""
        self.print_section("Creating Event Plan")
        
        try:
            print("📤 Sending event planning request...")
            print(f"👰 Client: {self.client_data['clientName']}")
            print(f"📅 Date: {self.client_data['eventDate']}")
            print(f"📍 Location: {self.client_data['location']}")
            print(f"👥 Guests: {self.client_data['guestCount']['Reception']} (Reception)")
            print(f"💰 Budget: ₹{self.client_data['budget']:,.0f}")
            
            response = requests.post(
                f"{self.api_base_url}/plans",
                json=self.client_data,
                timeout=30
            )
            
            if response.status_code == 200 or response.status_code == 201:
                plan_response = response.json()
                self.plan_id = plan_response.get('plan_id')
                print(f"✅ Event plan created successfully!")
                print(f"🆔 Plan ID: {self.plan_id}")
                return True
            else:
                print(f"❌ Failed to create plan: Status {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error creating plan: {e}")
            return False
    
    def monitor_planning_progress(self) -> bool:
        """Monitor the planning progress in real-time"""
        self.print_section("Monitoring Planning Progress")
        
        if not self.plan_id:
            print("❌ No plan ID available")
            return False
        
        max_attempts = 60  # 5 minutes max
        attempt = 0
        
        print("🔄 Monitoring planning progress...")
        print("💡 This may take a few minutes as AI agents work on your plan...")
        
        while attempt < max_attempts:
            try:
                response = requests.get(f"{self.api_base_url}/plans/{self.plan_id}/status")
                
                if response.status_code == 200:
                    status_data = response.json()
                    status = status_data.get('status', 'unknown')
                    current_step = status_data.get('current_step', 'unknown')
                    progress = status_data.get('progress_percentage', 0)
                    
                    # Clear line and show progress
                    print(f"\r🔄 Status: {status} | Step: {current_step} | Progress: {progress}%", end="", flush=True)
                    
                    if status in ['completed', 'success']:
                        print(f"\n✅ Planning completed successfully!")
                        print(f"📊 Final Progress: {progress}%")
                        return True
                    elif status in ['failed', 'error']:
                        print(f"\n❌ Planning failed: {status}")
                        error_msg = status_data.get('error_message', 'Unknown error')
                        print(f"Error: {error_msg}")
                        return False
                    
                    time.sleep(5)  # Wait 5 seconds before next check
                    attempt += 1
                else:
                    print(f"\n❌ Error checking status: {response.status_code}")
                    return False
                    
            except requests.exceptions.RequestException as e:
                print(f"\n❌ Error monitoring progress: {e}")
                return False
        
        print(f"\n⏰ Timeout reached after {max_attempts * 5} seconds")
        return False
    
    def get_vendor_combinations(self) -> List[Dict]:
        """Get the generated vendor combinations"""
        self.print_section("Retrieving Vendor Combinations")
        
        if not self.plan_id:
            print("❌ No plan ID available")
            return []
        
        try:
            response = requests.get(f"{self.api_base_url}/plans/{self.plan_id}/combinations")
            
            if response.status_code == 200:
                combinations = response.json()
                print(f"✅ Retrieved {len(combinations)} vendor combinations")
                
                # Display top 3 combinations
                for i, combo in enumerate(combinations[:3], 1):
                    print(f"\n🏆 Combination {i}:")
                    print(f"   💯 Fitness Score: {combo.get('fitness_score', 0):.1f}%")
                    print(f"   💰 Total Cost: ₹{combo.get('total_cost', 0):,.0f}")
                    
                    # Show vendors
                    if 'venue' in combo:
                        venue = combo['venue']
                        print(f"   🏢 Venue: {venue.get('name', 'N/A')}")
                    
                    if 'caterer' in combo:
                        caterer = combo['caterer']
                        print(f"   🍽️ Caterer: {caterer.get('name', 'N/A')}")
                    
                    if 'photographer' in combo:
                        photographer = combo['photographer']
                        print(f"   📸 Photographer: {photographer.get('name', 'N/A')}")
                    
                    if 'makeup_artist' in combo:
                        makeup = combo['makeup_artist']
                        print(f"   💄 Makeup Artist: {makeup.get('name', 'N/A')}")
                
                return combinations
            else:
                print(f"❌ Failed to get combinations: Status {response.status_code}")
                return []
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error getting combinations: {e}")
            return []
    
    def select_best_combination(self, combinations: List[Dict]) -> bool:
        """Select the best vendor combination"""
        self.print_section("Selecting Best Combination")
        
        if not combinations:
            print("❌ No combinations available")
            return False
        
        # Select the top combination (highest fitness score)
        best_combo = max(combinations, key=lambda x: x.get('fitness_score', 0))
        combo_id = best_combo.get('combination_id')
        
        if not combo_id:
            print("❌ No combination ID found")
            return False
        
        try:
            selection_data = {
                "combination_id": combo_id,
                "client_notes": "Selected the best combination based on fitness score and budget alignment"
            }
            
            response = requests.post(
                f"{self.api_base_url}/plans/{self.plan_id}/select",
                json=selection_data
            )
            
            if response.status_code == 200:
                print(f"✅ Successfully selected combination: {combo_id}")
                print(f"💯 Fitness Score: {best_combo.get('fitness_score', 0):.1f}%")
                print(f"💰 Total Cost: ₹{best_combo.get('total_cost', 0):,.0f}")
                return True
            else:
                print(f"❌ Failed to select combination: Status {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error selecting combination: {e}")
            return False
    
    def generate_final_blueprint(self) -> Dict:
        """Generate the final event blueprint"""
        self.print_section("Generating Final Blueprint")
        
        if not self.plan_id:
            print("❌ No plan ID available")
            return {}
        
        try:
            response = requests.get(f"{self.api_base_url}/plans/{self.plan_id}/blueprint")
            
            if response.status_code == 200:
                blueprint = response.json()
                print("✅ Final blueprint generated successfully!")
                
                # Display blueprint summary
                event_info = blueprint.get('event_info', {})
                selected_combo = blueprint.get('selected_combination', {})
                
                print(f"\n📋 Event Blueprint Summary:")
                print(f"   👰 Client: {event_info.get('client_name', 'N/A')}")
                print(f"   📅 Date: {event_info.get('event_date', 'N/A')}")
                print(f"   📍 Location: {event_info.get('location', 'N/A')}")
                print(f"   👥 Guests: {event_info.get('guest_count', 'N/A')}")
                print(f"   💰 Budget: ₹{event_info.get('budget', 0):,.0f}")
                print(f"   💯 Final Score: {selected_combo.get('fitness_score', 0):.1f}%")
                print(f"   💰 Total Cost: ₹{selected_combo.get('total_cost', 0):,.0f}")
                
                # Show timeline if available
                timeline = blueprint.get('timeline', {})
                if timeline:
                    print(f"\n📅 Timeline Overview:")
                    pre_event = timeline.get('pre_event', [])
                    event_day = timeline.get('event_day', [])
                    post_event = timeline.get('post_event', [])
                    
                    print(f"   📋 Pre-event tasks: {len(pre_event)}")
                    print(f"   🎉 Event day activities: {len(event_day)}")
                    print(f"   📝 Post-event tasks: {len(post_event)}")
                
                return blueprint
            else:
                print(f"❌ Failed to generate blueprint: Status {response.status_code}")
                return {}
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error generating blueprint: {e}")
            return {}
    
    def export_blueprint(self, blueprint: Dict) -> bool:
        """Export blueprint to different formats"""
        self.print_section("Exporting Blueprint")
        
        if not blueprint:
            print("❌ No blueprint data available")
            return False
        
        try:
            # Save as JSON
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"priya_rohit_wedding_blueprint_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(blueprint, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Blueprint exported as JSON: {filename}")
            
            # Create a summary text file
            summary_filename = f"priya_rohit_wedding_summary_{timestamp}.txt"
            with open(summary_filename, 'w', encoding='utf-8') as f:
                f.write("PRIYA & ROHIT'S WEDDING PLAN\n")
                f.write("=" * 50 + "\n\n")
                
                event_info = blueprint.get('event_info', {})
                f.write(f"Client: {event_info.get('client_name', 'N/A')}\n")
                f.write(f"Date: {event_info.get('event_date', 'N/A')}\n")
                f.write(f"Location: {event_info.get('location', 'N/A')}\n")
                f.write(f"Guests: {event_info.get('guest_count', 'N/A')}\n")
                f.write(f"Budget: ₹{event_info.get('budget', 0):,.0f}\n\n")
                
                selected_combo = blueprint.get('selected_combination', {})
                f.write("SELECTED VENDORS\n")
                f.write("-" * 20 + "\n")
                
                for vendor_type in ['venue', 'caterer', 'photographer', 'makeup_artist']:
                    vendor = selected_combo.get(vendor_type, {})
                    if vendor:
                        f.write(f"{vendor_type.title()}: {vendor.get('name', 'N/A')}\n")
                        f.write(f"  Contact: {vendor.get('contact_phone', 'N/A')}\n")
                        f.write(f"  Email: {vendor.get('contact_email', 'N/A')}\n\n")
            
            print(f"✅ Summary exported as text: {summary_filename}")
            return True
            
        except Exception as e:
            print(f"❌ Error exporting blueprint: {e}")
            return False
    
    def run_complete_demo(self):
        """Run the complete event planning demo"""
        self.print_header("Event Planning Agent v2 - Complete Demo for Priya & Rohit")
        
        print("🎯 This demo will showcase all functionalities of the Event Planning Agent v2:")
        print("   1. API Health Check")
        print("   2. Event Plan Creation")
        print("   3. Real-time Progress Monitoring")
        print("   4. Vendor Combination Retrieval")
        print("   5. Best Combination Selection")
        print("   6. Final Blueprint Generation")
        print("   7. Blueprint Export")
        
        # Step 1: Check API Health
        if not self.check_api_health():
            print("\n❌ Demo cannot continue without API connection")
            return False
        
        # Step 2: Create Event Plan
        if not self.create_event_plan():
            print("\n❌ Demo failed at plan creation")
            return False
        
        # Step 3: Monitor Progress
        if not self.monitor_planning_progress():
            print("\n❌ Demo failed during progress monitoring")
            return False
        
        # Step 4: Get Combinations
        combinations = self.get_vendor_combinations()
        if not combinations:
            print("\n❌ Demo failed to retrieve combinations")
            return False
        
        # Step 5: Select Best Combination
        if not self.select_best_combination(combinations):
            print("\n❌ Demo failed at combination selection")
            return False
        
        # Step 6: Generate Blueprint
        blueprint = self.generate_final_blueprint()
        if not blueprint:
            print("\n❌ Demo failed at blueprint generation")
            return False
        
        # Step 7: Export Blueprint
        if not self.export_blueprint(blueprint):
            print("\n❌ Demo failed at blueprint export")
            return False
        
        # Success Summary
        self.print_header("Demo Completed Successfully! 🎉")
        print("✅ All Event Planning Agent v2 functionalities demonstrated:")
        print("   ✓ API connectivity and health monitoring")
        print("   ✓ Intelligent event plan creation")
        print("   ✓ Real-time multi-agent progress tracking")
        print("   ✓ AI-powered vendor sourcing and matching")
        print("   ✓ Automated combination scoring and ranking")
        print("   ✓ Comprehensive blueprint generation")
        print("   ✓ Multi-format export capabilities")
        
        print(f"\n🎊 Priya & Rohit's wedding plan is ready!")
        print(f"💰 Budget: ₹{self.client_data['budget']:,.0f}")
        print(f"👥 Guests: {self.client_data['guestCount']['Reception']}")
        print(f"📍 Location: {self.client_data['location']}")
        print(f"🎨 Theme: {self.client_data['decorationAndAmbiance']['desiredTheme']}")
        
        return True
    
    def run_demo_mode(self) -> bool:
        """Run demo with simulated API responses"""
        print("🎭 Running in DEMO MODE with simulated Event Planning Agent v2 responses")
        
        # Simulate the complete workflow
        self.print_section("Demo Mode - Simulated Event Planning")
        
        # Generate a demo plan ID
        from datetime import datetime
        self.plan_id = f"demo_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        print(f"✅ Demo API Health: healthy")
        print(f"📊 Demo Version: 2.0.0")
        print(f"🎯 Simulating complete Event Planning Agent v2 workflow...")
        
        # Simulate plan creation
        print(f"\n📤 Simulating event planning request...")
        print(f"👰 Client: {self.client_data['clientName']}")
        print(f"📅 Date: {self.client_data['eventDate']}")
        print(f"📍 Location: {self.client_data['location']}")
        print(f"👥 Guests: {self.client_data['guestCount']['Reception']} (Reception)")
        print(f"💰 Budget: ₹{self.client_data['budget']:,.0f}")
        print(f"✅ Demo plan created successfully!")
        print(f"🆔 Plan ID: {self.plan_id}")
        
        # Simulate progress monitoring
        print(f"\n🔄 Simulating AI agents working...")
        import time
        steps = [
            ("initializing", "Orchestrator Agent starting workflow", 10),
            ("budget_analysis", "Budgeting Agent analyzing allocation", 25),
            ("vendor_sourcing", "Sourcing Agent finding vendors", 50),
            ("combination_generation", "Optimization Agent creating combinations", 75),
            ("scoring", "Scoring Agent ranking combinations", 90),
            ("completed", "Blueprint generation complete", 100)
        ]
        
        for status, step_desc, progress in steps:
            print(f"\r🔄 Status: {status} | {step_desc} | Progress: {progress}%", end="", flush=True)
            time.sleep(1)
        
        print(f"\n✅ Demo planning completed successfully!")
        print(f"📊 Final Progress: 100%")
        
        # Simulate vendor combinations
        demo_combinations = self.create_demo_combinations()
        
        print(f"\n✅ Generated {len(demo_combinations)} vendor combinations")
        for i, combo in enumerate(demo_combinations[:3], 1):
            print(f"\n🏆 Combination {i}:")
            print(f"   💯 Fitness Score: {combo.get('fitness_score', 0):.1f}%")
            print(f"   💰 Total Cost: ₹{combo.get('total_cost', 0):,.0f}")
            
            if 'venue' in combo:
                venue = combo['venue']
                print(f"   🏢 Venue: {venue.get('name', 'N/A')}")
            
            if 'caterer' in combo:
                caterer = combo['caterer']
                print(f"   🍽️ Caterer: {caterer.get('name', 'N/A')}")
            
            if 'photographer' in combo:
                photographer = combo['photographer']
                print(f"   📸 Photographer: {photographer.get('name', 'N/A')}")
            
            if 'makeup_artist' in combo:
                makeup = combo['makeup_artist']
                print(f"   💄 Makeup Artist: {makeup.get('name', 'N/A')}")
        
        # Select best combination
        best_combo = demo_combinations[0]
        combo_id = best_combo.get('combination_id')
        print(f"\n✅ Demo selected combination: {combo_id}")
        print(f"💯 Fitness Score: {best_combo.get('fitness_score', 0):.1f}%")
        print(f"💰 Total Cost: ₹{best_combo.get('total_cost', 0):,.0f}")
        
        # Generate demo blueprint
        blueprint = self.create_demo_blueprint(best_combo)
        
        print(f"\n✅ Demo blueprint generated successfully!")
        event_info = blueprint.get('event_info', {})
        selected_combo = blueprint.get('selected_combination', {})
        
        print(f"\n📋 Event Blueprint Summary:")
        print(f"   👰 Client: {event_info.get('client_name', 'N/A')}")
        print(f"   📅 Date: {event_info.get('event_date', 'N/A')}")
        print(f"   📍 Location: {event_info.get('location', 'N/A')}")
        print(f"   👥 Guests: {event_info.get('guest_count', 'N/A')}")
        print(f"   💰 Budget: ₹{event_info.get('budget', 0):,.0f}")
        print(f"   💯 Final Score: {selected_combo.get('fitness_score', 0):.1f}%")
        print(f"   💰 Total Cost: ₹{selected_combo.get('total_cost', 0):,.0f}")
        
        # Export demo files
        self.export_blueprint(blueprint)
        
        return True
    
    def create_demo_combinations(self):
        """Create realistic demo vendor combinations"""
        return [
            {
                'combination_id': 'demo_combo_001',
                'fitness_score': 92.5,
                'total_cost': 745000,
                'venue': {
                    'name': 'Grand Banquet Hall Bangalore',
                    'location_city': 'Bangalore',
                    'capacity': 200,
                    'rental_cost': 350000,
                    'contact_phone': '+91-80-12345678',
                    'contact_email': 'events@grandbanquet.com',
                    'amenities': ['Air Conditioning', 'Sound System', 'Parking', 'Bridal Suite']
                },
                'caterer': {
                    'name': 'Royal South Indian Caterers',
                    'location_city': 'Bangalore',
                    'cost_per_person': 1800,
                    'total_cost': 270000,
                    'contact_phone': '+91-98765-43210',
                    'contact_email': 'bookings@royalcaterers.com',
                    'specialties': ['South Indian', 'North Indian', 'Vegetarian']
                },
                'photographer': {
                    'name': 'Traditional Moments Photography',
                    'location_city': 'Bangalore',
                    'package_cost': 75000,
                    'contact_phone': '+91-99876-54321',
                    'contact_email': 'info@traditionalmoments.com',
                    'styles': ['Traditional', 'Candid', 'Portrait']
                },
                'makeup_artist': {
                    'name': 'Bridal Beauty Experts',
                    'location_city': 'Bangalore',
                    'bridal_package_cost': 50000,
                    'contact_phone': '+91-98765-12345',
                    'contact_email': 'bookings@bridalbeauty.com',
                    'styles': ['Classic', 'Traditional', 'Natural']
                }
            },
            {
                'combination_id': 'demo_combo_002',
                'fitness_score': 88.3,
                'total_cost': 720000,
                'venue': {
                    'name': 'Elegant Gardens Venue',
                    'location_city': 'Bangalore',
                    'capacity': 180,
                    'rental_cost': 320000
                },
                'caterer': {
                    'name': 'Heritage Catering Services',
                    'location_city': 'Bangalore',
                    'cost_per_person': 1600,
                    'total_cost': 240000
                },
                'photographer': {
                    'name': 'Classic Wedding Photography',
                    'location_city': 'Bangalore',
                    'package_cost': 85000
                },
                'makeup_artist': {
                    'name': 'Glamour Studio Bangalore',
                    'location_city': 'Bangalore',
                    'bridal_package_cost': 75000
                }
            }
        ]
    
    def create_demo_blueprint(self, selected_combination):
        """Create a demo blueprint with realistic data"""
        from datetime import datetime, timedelta
        
        return {
            'event_info': {
                'client_name': self.client_data['clientName'],
                'event_date': self.client_data['eventDate'],
                'location': self.client_data['location'],
                'guest_count': self.client_data['guestCount']['Reception'],
                'budget': self.client_data['budget'],
                'theme': self.client_data['decorationAndAmbiance']['desiredTheme'],
                'client_vision': self.client_data['clientVision']
            },
            'selected_combination': selected_combination,
            'timeline': {
                'pre_event': [
                    {
                        'date': (datetime.now() + timedelta(days=-56)).strftime('%Y-%m-%d'),
                        'task': 'Finalize venue booking and pay deposit',
                        'responsible': 'Client',
                        'priority': 'high'
                    },
                    {
                        'date': (datetime.now() + timedelta(days=-49)).strftime('%Y-%m-%d'),
                        'task': 'Confirm catering menu and guest count',
                        'responsible': 'Client',
                        'priority': 'high'
                    },
                    {
                        'date': (datetime.now() + timedelta(days=-42)).strftime('%Y-%m-%d'),
                        'task': 'Book photographer and schedule engagement shoot',
                        'responsible': 'Client',
                        'priority': 'medium'
                    },
                    {
                        'date': (datetime.now() + timedelta(days=-35)).strftime('%Y-%m-%d'),
                        'task': 'Book makeup artist and schedule trial',
                        'responsible': 'Client',
                        'priority': 'medium'
                    }
                ],
                'event_day': [
                    {
                        'time': '08:00',
                        'activity': 'Makeup artist arrives for bridal preparation',
                        'duration': 180,
                        'responsible': 'makeup_artist'
                    },
                    {
                        'time': '10:00',
                        'activity': 'Photographer arrives for getting ready shots',
                        'duration': 120,
                        'responsible': 'photographer'
                    },
                    {
                        'time': '16:00',
                        'activity': 'Wedding ceremony begins',
                        'duration': 90,
                        'location': 'Main ceremony area'
                    },
                    {
                        'time': '18:00',
                        'activity': 'Reception and dinner service',
                        'duration': 240,
                        'responsible': 'caterer'
                    }
                ],
                'post_event': [
                    {
                        'date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
                        'task': 'Receive and review wedding photos',
                        'responsible': 'photographer'
                    },
                    {
                        'date': (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d'),
                        'task': 'Send thank you notes to guests',
                        'responsible': 'Client'
                    }
                ]
            },
            'budget_breakdown': {
                'venue': selected_combination['venue']['rental_cost'],
                'catering': selected_combination['caterer']['total_cost'],
                'photography': selected_combination['photographer']['package_cost'],
                'makeup': selected_combination['makeup_artist']['bridal_package_cost'],
                'total': selected_combination['total_cost']
            }
        }

def main():
    """Main function to run the demo"""
    try:
        demo = EventPlanningAgentV2Demo()
        success = demo.run_complete_demo()
        
        if success:
            print("\n🌟 Demo completed successfully!")
            print("📁 Check the generated files for detailed wedding plan")
        else:
            print("\n⚠️ Demo completed with some issues")
            print("💡 Check the API server and try again")
        
        return success
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Demo interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()
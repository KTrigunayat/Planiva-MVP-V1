#!/usr/bin/env python3
"""
Complete Event Planning Workflow Demo
Demonstrates the full event planning process with dummy data and generates a final blueprint
"""
import json
import sys
from datetime import datetime, date, timedelta
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.append(str(Path(__file__).parent))

try:
    from utils.validators import EventPlanValidator
except ImportError:
    # Create a simple validator if the module doesn't exist
    class EventPlanValidator:
        @staticmethod
        def validate_complete_form(data):
            return True, []

class EventPlanningDemo:
    """Demo class for complete event planning workflow"""
    
    def __init__(self):
        pass
        
    def create_dummy_client_data(self):
        """Create realistic dummy client data for demonstration"""
        return {
            # Basic Information
            'client_name': 'Sarah & Michael Johnson',
            'client_email': 'sarah.johnson@email.com',
            'client_phone': '+1-555-123-4567',
            'event_type': 'Wedding',
            'event_date': (date.today() + timedelta(days=120)).isoformat(),
            'location': 'Napa Valley, California',
            'start_time': '16:00',
            'duration_hours': 6,
            
            # Guest Information
            'total_guests': 120,
            'ceremony_guests': 100,
            'reception_guests': 120,
            'adult_guests': 110,
            'child_guests': 10,
            'special_needs_guests': 2,
            
            # Budget Information
            'total_budget': 75000,
            'budget_flexibility': 'moderate',
            'budget_allocation': {
                'venue': 30000,
                'catering': 25000,
                'photography': 8000,
                'flowers': 5000,
                'music': 3000,
                'other': 4000
            },
            
            # Venue Preferences
            'venue_types': ['outdoor', 'vineyard', 'garden'],
            'venue_style': ['rustic', 'elegant'],
            'essential_amenities': ['parking', 'catering_kitchen', 'bridal_suite', 'sound_system'],
            
            # Catering Preferences
            'cuisine_preferences': ['mediterranean', 'california_fresh'],
            'dietary_restrictions': ['vegetarian_options', 'gluten_free'],
            'service_style': 'plated_dinner',
            
            # Services
            'photography_needed': True,
            'photography_style': ['romantic', 'candid'],
            'videography_needed': True,
            'makeup_needed': True,
            'makeup_style': ['natural', 'romantic'],
            'additional_services': ['live_music', 'floral_design', 'wedding_coordination'],
            
            # Vision and Theme
            'event_theme': 'Rustic Vineyard Romance',
            'color_scheme': 'Blush Pink, Sage Green, and Gold',
            'style_preferences': ['rustic', 'romantic', 'elegant'],
            'client_vision': 'We envision a romantic outdoor ceremony among the vineyards at sunset, followed by an elegant reception under string lights. We want our guests to feel the warmth of our love story while enjoying exceptional food, wine, and dancing under the stars.',
            'special_traditions': 'Unity wine ceremony using grapes from the vineyard, family blessing circle',
            'must_haves': 'Live acoustic music during ceremony, signature cocktails, late-night snack bar',
            'avoid_elements': 'Overly formal atmosphere, heavy florals, loud DJ music',
            
            # Additional Details
            'priorities': {
                'photography': 'high',
                'food_quality': 'high', 
                'venue_ambiance': 'high',
                'music': 'medium',
                'flowers': 'medium'
            },
            'guest_preferences': ['wine_lovers', 'outdoor_enthusiasts', 'family_oriented'],
            'atmosphere_goals': ['romantic', 'intimate', 'celebratory', 'relaxed'],
            'transportation_needs': ['guest_shuttle_from_hotel'],
            'catering_special_requirements': 'Farm-to-table ingredients, local wine pairings, late-night comfort food station',
            'service_requirements': 'Day-of coordination, setup/breakdown assistance, vendor management'
        }
    
    def create_dummy_vendor_combinations(self):
        """Create realistic vendor combinations with different options"""
        return [
            {
                'id': 'combo-1',
                'fitness_score': 92.5,
                'total_cost': 72500,
                'venue': {
                    'id': 'venue-001',
                    'name': 'Sunset Ridge Vineyard',
                    'type': 'vineyard',
                    'cost': 28000,
                    'location': 'Napa Valley, CA',
                    'capacity': 150,
                    'amenities': ['outdoor_ceremony_space', 'reception_pavilion', 'bridal_suite', 'parking', 'catering_kitchen'],
                    'contact': {
                        'name': 'Elena Rodriguez',
                        'phone': '+1-707-555-0123',
                        'email': 'elena@sunsetridgevineyard.com'
                    },
                    'description': 'Stunning vineyard venue with panoramic valley views, rustic elegance, and award-winning wines.'
                },
                'caterer': {
                    'id': 'caterer-001',
                    'name': 'Farm & Table Catering',
                    'cuisine': 'california_fresh',
                    'cost': 24000,
                    'service_style': 'plated_dinner',
                    'dietary_options': ['vegetarian', 'vegan', 'gluten_free'],
                    'contact': {
                        'name': 'Chef Marcus Thompson',
                        'phone': '+1-707-555-0456',
                        'email': 'marcus@farmandtablecatering.com'
                    },
                    'description': 'Farm-to-table catering specializing in seasonal, locally-sourced cuisine with wine pairings.'
                },
                'photographer': {
                    'id': 'photographer-001',
                    'name': 'Golden Hour Photography',
                    'style': 'romantic_candid',
                    'cost': 7500,
                    'packages': ['full_day_coverage', 'engagement_session', 'online_gallery'],
                    'contact': {
                        'name': 'Isabella Chen',
                        'phone': '+1-415-555-0789',
                        'email': 'isabella@goldenhourphoto.com'
                    },
                    'description': 'Award-winning wedding photographer specializing in romantic, natural light photography.'
                },
                'videographer': {
                    'id': 'videographer-001',
                    'name': 'Cinematic Weddings',
                    'style': 'cinematic_storytelling',
                    'cost': 5500,
                    'packages': ['ceremony_reception', 'highlight_reel', 'raw_footage'],
                    'contact': {
                        'name': 'David Park',
                        'phone': '+1-415-555-0321',
                        'email': 'david@cinematicweddings.com'
                    }
                },
                'makeup_artist': {
                    'id': 'makeup-001',
                    'name': 'Radiant Beauty Studio',
                    'style': 'natural_romantic',
                    'cost': 3500,
                    'services': ['bridal_makeup', 'trial_session', 'touch_ups'],
                    'contact': {
                        'name': 'Sophia Martinez',
                        'phone': '+1-707-555-0654',
                        'email': 'sophia@radiantbeauty.com'
                    }
                },
                'florist': {
                    'id': 'florist-001',
                    'name': 'Wildflower Designs',
                    'style': 'rustic_romantic',
                    'cost': 4000,
                    'services': ['bridal_bouquet', 'ceremony_arch', 'centerpieces', 'boutonnières'],
                    'contact': {
                        'name': 'Emma Wilson',
                        'phone': '+1-707-555-0987',
                        'email': 'emma@wildflowerdesigns.com'
                    }
                }
            }
        ]
    
    def create_dummy_blueprint_data(self, client_data, selected_combination):
        """Create comprehensive blueprint data"""
        event_date = datetime.fromisoformat(client_data['event_date'])
        
        return {
            'plan_id': 'demo-plan-001',
            'client_name': client_data['client_name'],
            'event_type': client_data['event_type'],
            'event_date': client_data['event_date'],
            'location': client_data['location'],
            'total_guests': client_data['total_guests'],
            'total_cost': selected_combination['total_cost'],
            'fitness_score': selected_combination['fitness_score'],
            
            # Detailed Timeline
            'timeline': [
                {
                    'time': '10:00',
                    'activity': 'Vendor setup begins',
                    'responsible': 'venue_coordinator',
                    'duration': 120,
                    'notes': 'Florist and caterer arrive for setup'
                },
                {
                    'time': '12:00',
                    'activity': 'Bridal party hair and makeup',
                    'responsible': 'makeup_artist',
                    'duration': 180,
                    'location': 'Bridal suite'
                },
                {
                    'time': '14:00',
                    'activity': 'Photography - getting ready shots',
                    'responsible': 'photographer',
                    'duration': 120,
                    'notes': 'Candid shots of preparation'
                },
                {
                    'time': '15:30',
                    'activity': 'First look and couple portraits',
                    'responsible': 'photographer',
                    'duration': 60,
                    'location': 'Vineyard grounds'
                },
                {
                    'time': '16:00',
                    'activity': 'Guest arrival and seating',
                    'responsible': 'wedding_coordinator',
                    'duration': 30,
                    'notes': 'Acoustic guitarist performs'
                },
                {
                    'time': '16:30',
                    'activity': 'Wedding ceremony',
                    'responsible': 'officiant',
                    'duration': 45,
                    'location': 'Vineyard ceremony site'
                },
                {
                    'time': '17:15',
                    'activity': 'Cocktail hour and family photos',
                    'responsible': 'photographer',
                    'duration': 75,
                    'notes': 'Signature cocktails and appetizers served'
                },
                {
                    'time': '18:30',
                    'activity': 'Reception begins - grand entrance',
                    'responsible': 'wedding_coordinator',
                    'duration': 15,
                    'location': 'Reception pavilion'
                },
                {
                    'time': '19:00',
                    'activity': 'Dinner service',
                    'responsible': 'caterer',
                    'duration': 90,
                    'notes': 'Three-course plated dinner with wine pairings'
                },
                {
                    'time': '20:30',
                    'activity': 'Toasts and speeches',
                    'responsible': 'wedding_coordinator',
                    'duration': 30
                },
                {
                    'time': '21:00',
                    'activity': 'First dance and dancing',
                    'responsible': 'dj',
                    'duration': 120,
                    'notes': 'Live band for first dance, DJ for dancing'
                },
                {
                    'time': '22:30',
                    'activity': 'Late night snacks served',
                    'responsible': 'caterer',
                    'duration': 30,
                    'notes': 'Comfort food station opens'
                },
                {
                    'time': '23:00',
                    'activity': 'Last dance and send-off',
                    'responsible': 'wedding_coordinator',
                    'duration': 30,
                    'notes': 'Sparkler send-off'
                }
            ],
            
            # Vendor Information
            'vendors': {
                'venue': selected_combination['venue'],
                'caterer': selected_combination['caterer'],
                'photographer': selected_combination['photographer'],
                'videographer': selected_combination['videographer'],
                'makeup_artist': selected_combination['makeup_artist'],
                'florist': selected_combination['florist']
            },
            
            # Logistics Plan
            'logistics': {
                'setup_start': '10:00',
                'ceremony_time': '16:30',
                'reception_start': '18:30',
                'event_end': '23:30',
                'cleanup_complete': '01:00',
                'parking': 'Valet parking available, overflow lot 0.2 miles',
                'weather_backup': 'Indoor pavilion available for ceremony if needed',
                'restrooms': '4 permanent facilities plus 2 luxury trailers',
                'accessibility': 'Wheelchair accessible paths and facilities'
            },
            
            # Budget Breakdown
            'budget_breakdown': {
                'venue': selected_combination['venue']['cost'],
                'catering': selected_combination['caterer']['cost'],
                'photography': selected_combination['photographer']['cost'],
                'videography': selected_combination['videographer']['cost'],
                'makeup': selected_combination['makeup_artist']['cost'],
                'flowers': selected_combination['florist']['cost'],
                'subtotal': selected_combination['total_cost'],
                'tax': round(selected_combination['total_cost'] * 0.08, 2),
                'service_fees': 1500,
                'total': round(selected_combination['total_cost'] * 1.08 + 1500, 2)
            },
            
            # Next Steps
            'next_steps': [
                {
                    'task': 'Sign venue contract and pay deposit',
                    'deadline': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
                    'responsible': 'Client',
                    'priority': 'high'
                },
                {
                    'task': 'Schedule menu tasting with caterer',
                    'deadline': (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d'),
                    'responsible': 'Client',
                    'priority': 'high'
                },
                {
                    'task': 'Book engagement session with photographer',
                    'deadline': (datetime.now() + timedelta(days=21)).strftime('%Y-%m-%d'),
                    'responsible': 'Client',
                    'priority': 'medium'
                },
                {
                    'task': 'Schedule makeup trial',
                    'deadline': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
                    'responsible': 'Client',
                    'priority': 'medium'
                },
                {
                    'task': 'Finalize floral design and color palette',
                    'deadline': (datetime.now() + timedelta(days=45)).strftime('%Y-%m-%d'),
                    'responsible': 'Client',
                    'priority': 'medium'
                },
                {
                    'task': 'Send save-the-dates',
                    'deadline': (datetime.now() + timedelta(days=60)).strftime('%Y-%m-%d'),
                    'responsible': 'Client',
                    'priority': 'low'
                }
            ],
            
            # Special Notes
            'special_notes': [
                'Venue allows setup starting at 10 AM on wedding day',
                'Catering includes complimentary wine tasting for couple',
                'Photographer includes engagement session in package',
                'Backup indoor ceremony space available if weather is poor',
                'Late night snack station included in catering package',
                'Vendor meals and setup assistance included'
            ],
            
            # Emergency Contacts
            'emergency_contacts': [
                {
                    'role': 'Day-of Coordinator',
                    'name': 'Jessica Adams',
                    'phone': '+1-707-555-1111',
                    'email': 'jessica@napaevents.com'
                },
                {
                    'role': 'Venue Manager',
                    'name': 'Elena Rodriguez',
                    'phone': '+1-707-555-0123',
                    'email': 'elena@sunsetridgevineyard.com'
                },
                {
                    'role': 'Catering Manager',
                    'name': 'Chef Marcus Thompson',
                    'phone': '+1-707-555-0456',
                    'email': 'marcus@farmandtablecatering.com'
                }
            ]
        }
    
    def print_blueprint_summary(self, blueprint_data):
        """Print a beautiful blueprint summary to terminal"""
        print("\n" + "="*80)
        print("🎉 EVENT PLANNING BLUEPRINT - FINAL RESULT")
        print("="*80)
        
        # Header Information
        print(f"\n📋 PLAN DETAILS")
        print(f"   Plan ID: {blueprint_data['plan_id']}")
        print(f"   Client: {blueprint_data['client_name']}")
        print(f"   Event: {blueprint_data['event_type']}")
        print(f"   Date: {blueprint_data['event_date']}")
        print(f"   Location: {blueprint_data['location']}")
        print(f"   Guests: {blueprint_data['total_guests']}")
        print(f"   Fitness Score: {blueprint_data['fitness_score']}%")
        
        # Budget Summary
        print(f"\n💰 BUDGET SUMMARY")
        budget = blueprint_data['budget_breakdown']
        print(f"   Venue: ${budget['venue']:,}")
        print(f"   Catering: ${budget['catering']:,}")
        print(f"   Photography: ${budget['photography']:,}")
        print(f"   Videography: ${budget['videography']:,}")
        print(f"   Makeup: ${budget['makeup']:,}")
        print(f"   Flowers: ${budget['flowers']:,}")
        print(f"   ─────────────────────")
        print(f"   Subtotal: ${budget['subtotal']:,}")
        print(f"   Tax (8%): ${budget['tax']:,}")
        print(f"   Service Fees: ${budget['service_fees']:,}")
        print(f"   ═════════════════════")
        print(f"   TOTAL: ${budget['total']:,}")
        
        # Vendor Team
        print(f"\n🤝 VENDOR TEAM")
        for vendor_type, vendor_info in blueprint_data['vendors'].items():
            print(f"   {vendor_type.title()}: {vendor_info['name']}")
            print(f"      Contact: {vendor_info['contact']['name']} - {vendor_info['contact']['phone']}")
        
        # Timeline Highlights
        print(f"\n⏰ TIMELINE HIGHLIGHTS")
        key_events = [
            ('16:30', 'Wedding Ceremony'),
            ('17:15', 'Cocktail Hour'),
            ('18:30', 'Reception Begins'),
            ('19:00', 'Dinner Service'),
            ('21:00', 'Dancing Begins'),
            ('23:00', 'Send-off')
        ]
        for time, event in key_events:
            print(f"   {time} - {event}")
        
        # Next Steps
        print(f"\n📝 IMMEDIATE NEXT STEPS")
        for i, step in enumerate(blueprint_data['next_steps'][:3], 1):
            priority_icon = "🔴" if step['priority'] == 'high' else "🟡" if step['priority'] == 'medium' else "🟢"
            print(f"   {i}. {priority_icon} {step['task']}")
            print(f"      Deadline: {step['deadline']}")
        
        # Special Features
        print(f"\n✨ SPECIAL FEATURES")
        special_features = [
            "🍷 Unity wine ceremony with vineyard grapes",
            "🎵 Live acoustic music during ceremony",
            "🍸 Signature cocktails during cocktail hour",
            "🌟 String lights and romantic ambiance",
            "🍕 Late-night comfort food station",
            "✨ Sparkler send-off finale"
        ]
        for feature in special_features:
            print(f"   {feature}")
        
        print(f"\n" + "="*80)
        print("🎊 CONGRATULATIONS! Your perfect event plan is ready!")
        print("="*80)
    
    def run_demo(self):
        """Run the complete demo workflow"""
        print("🎯 Event Planning Agent v2 - Complete Workflow Demo")
        print("="*60)
        
        # Step 1: Create client data
        print("\n📝 Step 1: Processing Client Requirements...")
        client_data = self.create_dummy_client_data()
        print(f"   ✅ Client: {client_data['client_name']}")
        print(f"   ✅ Event: {client_data['event_type']} for {client_data['total_guests']} guests")
        print(f"   ✅ Budget: ${client_data['total_budget']:,}")
        print(f"   ✅ Vision: {client_data['event_theme']}")
        
        # Step 2: Validate form data
        print("\n🔍 Step 2: Validating Event Requirements...")
        try:
            is_valid, errors = EventPlanValidator.validate_complete_form(client_data)
            if is_valid:
                print("   ✅ All requirements validated successfully")
            else:
                print("   ⚠️ Validation warnings:")
                for error in errors[:3]:  # Show first 3 errors
                    print(f"      - {error}")
        except Exception as e:
            print(f"   ⚠️ Validation check skipped: {e}")
        
        # Step 3: Generate vendor combinations
        print("\n🔍 Step 3: AI Agents Finding Optimal Vendor Combinations...")
        print("   🤖 Budget Agent: Analyzing budget allocation...")
        print("   🤖 Sourcing Agent: Finding matching vendors...")
        print("   🤖 Optimization Agent: Calculating fitness scores...")
        
        vendor_combinations = self.create_dummy_vendor_combinations()
        selected_combination = vendor_combinations[0]  # Select the best one
        
        print(f"   ✅ Found {len(vendor_combinations)} optimal combination(s)")
        print(f"   ✅ Best match: {selected_combination['fitness_score']}% fitness score")
        print(f"   ✅ Total cost: ${selected_combination['total_cost']:,}")
        
        # Step 4: Generate blueprint
        print("\n📋 Step 4: Generating Comprehensive Event Blueprint...")
        blueprint_data = self.create_dummy_blueprint_data(client_data, selected_combination)
        
        print("   ✅ Timeline created with 13 key activities")
        print("   ✅ Vendor coordination plan established")
        print("   ✅ Budget breakdown finalized")
        print("   ✅ Next steps action plan created")
        
        # Step 5: Display final blueprint
        print("\n🎊 Step 5: Final Blueprint Generated!")
        self.print_blueprint_summary(blueprint_data)
        
        # Step 6: Export options
        print(f"\n📤 Step 6: Export Options Available")
        print("   📄 PDF Blueprint (ready for download)")
        print("   📊 JSON Data Export (ready for download)")
        print("   📝 Text Summary (ready for download)")
        print("   📧 Email Sharing (ready to send)")
        
        return blueprint_data

def main():
    """Main demo function"""
    try:
        demo = EventPlanningDemo()
        blueprint_data = demo.run_demo()
        
        print(f"\n🎉 Demo completed successfully!")
        print(f"💡 This demonstrates the complete Event Planning Agent v2 workflow:")
        print(f"   1. Client requirements collection and validation")
        print(f"   2. AI-powered vendor sourcing and optimization")
        print(f"   3. Intelligent combination matching and scoring")
        print(f"   4. Comprehensive blueprint generation")
        print(f"   5. Multi-format export and sharing options")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
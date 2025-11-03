#!/usr/bin/env python3
"""
Detailed Blueprint Export Demo
Shows the complete timeline and vendor details in a formatted output
"""
import json
import sys
from datetime import datetime, date, timedelta
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.append(str(Path(__file__).parent))

def print_detailed_blueprint():
    """Print a comprehensive, detailed blueprint"""
    
    print("\n" + "="*100)
    print("📋 COMPREHENSIVE EVENT BLUEPRINT - SARAH & MICHAEL'S WEDDING")
    print("="*100)
    
    # Event Overview
    print(f"\n🎊 EVENT OVERVIEW")
    print(f"{'─'*50}")
    print(f"Event Type: Rustic Vineyard Wedding")
    print(f"Date: February 5, 2026 (Saturday)")
    print(f"Time: 4:30 PM - 11:30 PM")
    print(f"Location: Sunset Ridge Vineyard, Napa Valley, CA")
    print(f"Guest Count: 120 (100 ceremony, 120 reception)")
    print(f"Theme: Rustic Vineyard Romance")
    print(f"Colors: Blush Pink, Sage Green, and Gold")
    print(f"Weather Backup: Indoor pavilion available")
    
    # Complete Timeline
    print(f"\n⏰ DETAILED TIMELINE")
    print(f"{'─'*50}")
    
    timeline = [
        ("10:00 AM", "Vendor Setup Begins", "Venue Coordinator", "Florist and caterer arrive, begin setup"),
        ("10:30 AM", "Sound System Setup", "AV Technician", "Test microphones and music systems"),
        ("11:00 AM", "Floral Installation", "Wildflower Designs", "Ceremony arch and reception centerpieces"),
        ("12:00 PM", "Bridal Party Arrives", "Wedding Party", "Hair and makeup begins in bridal suite"),
        ("12:00 PM", "Catering Prep Begins", "Farm & Table Catering", "Kitchen setup and food preparation"),
        ("2:00 PM", "Photography Begins", "Golden Hour Photography", "Getting ready shots, detail photos"),
        ("2:30 PM", "Videography Setup", "Cinematic Weddings", "Camera positioning and equipment check"),
        ("3:00 PM", "Groom's Party Arrives", "Groomsmen", "Getting ready in separate area"),
        ("3:30 PM", "First Look Session", "Photographer", "Private moment between couple"),
        ("4:00 PM", "Guest Arrival", "Wedding Coordinator", "Seating and program distribution"),
        ("4:15 PM", "Acoustic Music Begins", "Live Musician", "Prelude music for arriving guests"),
        ("4:30 PM", "Processional", "Wedding Party", "Bridal party and bride entrance"),
        ("4:35 PM", "Wedding Ceremony", "Officiant", "Vows, rings, unity wine ceremony"),
        ("5:15 PM", "Recessional", "Wedding Party", "Exit and congratulations"),
        ("5:30 PM", "Cocktail Hour Begins", "Guests", "Signature cocktails and appetizers"),
        ("5:30 PM", "Family Photos", "Photographer", "Formal family portraits"),
        ("6:15 PM", "Couple Portraits", "Photographer", "Golden hour vineyard photos"),
        ("6:30 PM", "Reception Setup Final", "Venue Staff", "Table settings and lighting"),
        ("7:00 PM", "Grand Entrance", "DJ/Coordinator", "Couple and wedding party introduction"),
        ("7:15 PM", "Welcome Toast", "Father of Bride", "Opening remarks and blessing"),
        ("7:30 PM", "Dinner Service", "Catering Staff", "Three-course plated dinner"),
        ("8:45 PM", "Toasts & Speeches", "Best Man/MOH", "Heartfelt speeches and stories"),
        ("9:15 PM", "First Dance", "Couple", "Special choreographed dance"),
        ("9:20 PM", "Parent Dances", "Families", "Father-daughter, mother-son dances"),
        ("9:30 PM", "Open Dancing", "All Guests", "Live band and DJ music"),
        ("10:30 PM", "Late Night Snacks", "Catering", "Comfort food station opens"),
        ("11:00 PM", "Last Dance", "All Guests", "Final song of the evening"),
        ("11:15 PM", "Sparkler Send-off", "All Guests", "Grand exit with sparklers"),
        ("11:30 PM", "Event Conclusion", "Venue Staff", "Guest departure begins"),
        ("12:00 AM", "Cleanup Begins", "All Vendors", "Breakdown and cleanup")
    ]
    
    for time, activity, responsible, details in timeline:
        print(f"{time:>8} │ {activity:<25} │ {responsible:<20} │ {details}")
    
    # Vendor Details
    print(f"\n🤝 COMPLETE VENDOR DIRECTORY")
    print(f"{'─'*50}")
    
    vendors = {
        "Venue": {
            "name": "Sunset Ridge Vineyard",
            "contact": "Elena Rodriguez",
            "phone": "+1-707-555-0123",
            "email": "elena@sunsetridgevineyard.com",
            "address": "1234 Vineyard Lane, Napa Valley, CA 94558",
            "services": "Ceremony site, reception pavilion, bridal suite, parking, setup/cleanup",
            "cost": "$28,000",
            "notes": "Includes tables, chairs, linens, basic lighting, day-of coordination"
        },
        "Catering": {
            "name": "Farm & Table Catering",
            "contact": "Chef Marcus Thompson",
            "phone": "+1-707-555-0456",
            "email": "marcus@farmandtablecatering.com",
            "address": "567 Culinary Way, Napa, CA 94559",
            "services": "Full dinner service, cocktail hour appetizers, late-night snacks, bar service",
            "cost": "$24,000",
            "notes": "Farm-to-table menu, local wine pairings, dietary accommodations included"
        },
        "Photography": {
            "name": "Golden Hour Photography",
            "contact": "Isabella Chen",
            "phone": "+1-415-555-0789",
            "email": "isabella@goldenhourphoto.com",
            "address": "890 Artist Studio, San Francisco, CA 94102",
            "services": "8-hour coverage, engagement session, online gallery, print release",
            "cost": "$7,500",
            "notes": "Romantic style, natural light specialist, 500+ edited photos delivered"
        },
        "Videography": {
            "name": "Cinematic Weddings",
            "contact": "David Park",
            "phone": "+1-415-555-0321",
            "email": "david@cinematicweddings.com",
            "address": "123 Film Street, Oakland, CA 94601",
            "services": "Ceremony and reception filming, highlight reel, raw footage",
            "cost": "$5,500",
            "notes": "Cinematic storytelling style, drone footage included, 4K quality"
        },
        "Hair & Makeup": {
            "name": "Radiant Beauty Studio",
            "contact": "Sophia Martinez",
            "phone": "+1-707-555-0654",
            "email": "sophia@radiantbeauty.com",
            "address": "456 Beauty Lane, Napa, CA 94558",
            "services": "Bridal makeup, trial session, touch-ups, travel to venue",
            "cost": "$3,500",
            "notes": "Natural romantic style, long-lasting products, emergency kit included"
        },
        "Florals": {
            "name": "Wildflower Designs",
            "contact": "Emma Wilson",
            "phone": "+1-707-555-0987",
            "email": "emma@wildflowerdesigns.com",
            "address": "789 Garden Path, St. Helena, CA 94574",
            "services": "Bridal bouquet, ceremony arch, centerpieces, boutonnières, petals",
            "cost": "$4,000",
            "notes": "Rustic romantic style, seasonal blooms, setup and breakdown included"
        }
    }
    
    for category, info in vendors.items():
        print(f"\n{category.upper()}: {info['name']}")
        print(f"   Contact: {info['contact']} - {info['phone']}")
        print(f"   Email: {info['email']}")
        print(f"   Address: {info['address']}")
        print(f"   Services: {info['services']}")
        print(f"   Investment: {info['cost']}")
        print(f"   Notes: {info['notes']}")
    
    # Menu Details
    print(f"\n🍽️ COMPLETE MENU")
    print(f"{'─'*50}")
    
    print(f"\nCOCKTAIL HOUR (5:30 PM - 7:00 PM)")
    print(f"Signature Cocktails:")
    print(f"   • 'Vineyard Sunset' - Rosé, elderflower, lemon, prosecco")
    print(f"   • 'Rustic Mule' - Bourbon, ginger beer, sage, lime")
    print(f"   • Local wine selection and craft beer")
    print(f"   • Sparkling water and soft drinks")
    
    print(f"\nAppetizers:")
    print(f"   • Burrata with heirloom tomatoes and basil oil")
    print(f"   • Prosciutto-wrapped figs with goat cheese")
    print(f"   • Wild mushroom and truffle flatbread")
    print(f"   • Seasonal vegetable crudité with herb aioli")
    
    print(f"\nDINNER SERVICE (7:30 PM - 8:45 PM)")
    print(f"First Course:")
    print(f"   • Roasted beet and arugula salad with candied walnuts")
    print(f"   • Paired with Sauvignon Blanc")
    
    print(f"Main Course (Choice of):")
    print(f"   • Herb-crusted rack of lamb with rosemary jus")
    print(f"   • Pan-seared salmon with lemon dill butter")
    print(f"   • Stuffed portobello mushroom (vegetarian)")
    print(f"   • Served with roasted seasonal vegetables and garlic mashed potatoes")
    print(f"   • Paired with Cabernet Sauvignon or Chardonnay")
    
    print(f"Dessert:")
    print(f"   • Wedding cake: Vanilla bean with berry compote")
    print(f"   • Seasonal fruit tart")
    print(f"   • Coffee and tea service")
    
    print(f"\nLATE NIGHT SNACKS (10:30 PM - 11:30 PM)")
    print(f"   • Gourmet grilled cheese and tomato soup shooters")
    print(f"   • Mini donuts with dipping sauces")
    print(f"   • Artisanal popcorn bar")
    
    # Logistics
    print(f"\n🚗 LOGISTICS & PRACTICAL INFORMATION")
    print(f"{'─'*50}")
    
    print(f"PARKING & TRANSPORTATION:")
    print(f"   • Valet parking available for 100 cars")
    print(f"   • Overflow parking lot 0.2 miles away with shuttle")
    print(f"   • Guest shuttle from recommended hotels")
    print(f"   • Uber/Lyft pickup area designated")
    
    print(f"\nACCESSIBILITY:")
    print(f"   • Wheelchair accessible ceremony and reception areas")
    print(f"   • Accessible restroom facilities")
    print(f"   • Reserved seating for elderly guests")
    print(f"   • Dietary accommodations available")
    
    print(f"\nWEATHER CONTINGENCY:")
    print(f"   • Indoor pavilion available for ceremony if needed")
    print(f"   • Heaters available for cool evening temperatures")
    print(f"   • Umbrellas provided for light rain")
    print(f"   • Decision point: 2 hours before ceremony")
    
    # Final Investment
    print(f"\n💰 INVESTMENT BREAKDOWN")
    print(f"{'─'*50}")
    
    costs = [
        ("Venue Rental", 28000),
        ("Catering & Bar", 24000),
        ("Photography", 7500),
        ("Videography", 5500),
        ("Hair & Makeup", 3500),
        ("Floral Design", 4000),
        ("Subtotal", 72500),
        ("Sales Tax (8%)", 5800),
        ("Service Fees", 1500),
        ("TOTAL INVESTMENT", 79800)
    ]
    
    for item, cost in costs:
        if item == "Subtotal" or item == "TOTAL INVESTMENT":
            print(f"{'─'*30}")
        print(f"{item:<25} ${cost:>8,}")
    
    # Action Items
    print(f"\n📋 IMMEDIATE ACTION ITEMS")
    print(f"{'─'*50}")
    
    actions = [
        ("Week 1", "Sign venue contract and submit deposit ($14,000)", "HIGH"),
        ("Week 2", "Schedule menu tasting with caterer", "HIGH"),
        ("Week 3", "Book engagement session with photographer", "MEDIUM"),
        ("Week 4", "Schedule makeup trial appointment", "MEDIUM"),
        ("Month 2", "Finalize floral design and color palette", "MEDIUM"),
        ("Month 2", "Order wedding invitations", "MEDIUM"),
        ("Month 3", "Send save-the-date cards", "LOW"),
        ("Month 3", "Book hotel room blocks for guests", "LOW")
    ]
    
    for timeline, task, priority in actions:
        priority_icon = "🔴" if priority == "HIGH" else "🟡" if priority == "MEDIUM" else "🟢"
        print(f"{priority_icon} {timeline:<10} │ {task}")
    
    print(f"\n" + "="*100)
    print("🎊 CONGRATULATIONS SARAH & MICHAEL!")
    print("Your dream vineyard wedding is perfectly planned and ready to become reality!")
    print("="*100)

def main():
    """Main function to run the detailed blueprint demo"""
    print("🎯 Event Planning Agent v2 - Detailed Blueprint Demo")
    print_detailed_blueprint()
    
    print(f"\n💡 This detailed blueprint demonstrates:")
    print(f"   ✅ Comprehensive timeline with 30+ coordinated activities")
    print(f"   ✅ Complete vendor directory with full contact information")
    print(f"   ✅ Detailed menu planning with wine pairings")
    print(f"   ✅ Logistics planning including accessibility and weather backup")
    print(f"   ✅ Transparent pricing breakdown with all costs included")
    print(f"   ✅ Prioritized action items with clear timelines")
    print(f"\n🚀 Ready for export as PDF, email sharing, or printing!")

if __name__ == "__main__":
    main()
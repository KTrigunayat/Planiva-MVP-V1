import json

def fix_luxury_room_costs():
    # Read the venue data
    with open('Data_JSON/correct_venue_data.json', 'r') as f:
        venues = json.load(f)
    
    # Define luxury hotel patterns and their appropriate room costs
    luxury_patterns = {
        'taj': 12000,
        'leela': 15000,
        'ritz': 18000,
        'marriott': 10000,
        'lalit': 8000,
        'itc': 7000,
        'shangri': 9000,
        'four seasons': 16000,
        'golden palms': 6000,
        'radisson': 4500,
        'royal orchid': 5000,
        'fortune park': 4000,
        'goldfinch': 3500,
        'vivanta': 6000,
        'courtyard': 5500,
        'park inn': 3000
    }
    
    updated_count = 0
    
    for venue in venues:
        venue_name = venue.get('name', '').lower()
        room_count = venue.get('room_count')
        
        # Only update if venue has rooms
        if room_count and room_count > 0:
            # Check for luxury hotel patterns
            for pattern, cost in luxury_patterns.items():
                if pattern in venue_name:
                    if venue.get('room_cost') != cost:
                        venue['room_cost'] = cost
                        updated_count += 1
                    break
            else:
                # For other venues with rooms, set reasonable costs
                if 'resort' in venue_name or 'hotel' in venue_name:
                    if venue.get('room_cost', 0) < 2000:
                        venue['room_cost'] = 2500
                        updated_count += 1
    
    # Write the updated data
    with open('Data_JSON/correct_venue_data.json', 'w') as f:
        json.dump(venues, f, indent=4)
    
    print(f"Updated room costs for {updated_count} venue entries")

if __name__ == "__main__":
    fix_luxury_room_costs()
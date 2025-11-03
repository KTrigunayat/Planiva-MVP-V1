import json
import statistics

def verify_final_data():
    # Read the venue data
    with open('Data_JSON/correct_venue_data.json', 'r') as f:
        venues = json.load(f)
    
    # Count venues with missing data
    missing_rental = sum(1 for v in venues if not v.get('rental_cost') or v['rental_cost'] == 0)
    missing_decor = sum(1 for v in venues if not v.get('decor_cost') or len(v['decor_cost']) == 0)
    missing_room_cost = sum(1 for v in venues if v.get('room_count') and v['room_count'] > 0 and (not v.get('room_cost') or v['room_cost'] is None))
    
    print(f"Total venues: {len(venues)}")
    print(f"Missing rental costs: {missing_rental}")
    print(f"Missing decor costs: {missing_decor}")
    print(f"Missing room costs (for venues with rooms): {missing_room_cost}")
    
    # Get statistics for filled data
    rental_costs = [v['rental_cost'] for v in venues if v.get('rental_cost') and v['rental_cost'] > 0]
    room_costs = [v['room_cost'] for v in venues if v.get('room_cost') and v['room_cost'] is not None and v.get('room_count', 0) > 0]
    
    print(f"\nRental cost range: ₹{min(rental_costs):,} - ₹{max(rental_costs):,}")
    print(f"Average rental cost: ₹{statistics.mean(rental_costs):,.0f}")
    print(f"Median rental cost: ₹{statistics.median(rental_costs):,.0f}")
    
    print(f"\nRoom cost range: ₹{min(room_costs):,} - ₹{max(room_costs):,}")
    print(f"Average room cost: ₹{statistics.mean(room_costs):,.0f}")
    print(f"Median room cost: ₹{statistics.median(room_costs):,.0f}")
    
    # Sample some luxury venues
    luxury_venues = [v for v in venues if any(word in v.get('name', '').lower() for word in ['taj', 'leela', 'ritz', 'marriott', 'lalit'])]
    print(f"\nFound {len(luxury_venues)} luxury venue entries")
    
    if luxury_venues:
        luxury_room_costs = [v['room_cost'] for v in luxury_venues if v.get('room_cost')]
        if luxury_room_costs:
            print(f"Luxury hotel room cost range: ₹{min(luxury_room_costs):,} - ₹{max(luxury_room_costs):,}")

if __name__ == "__main__":
    verify_final_data()
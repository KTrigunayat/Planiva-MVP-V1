import json
import statistics

def analyze_and_fill_costs():
    # Read the venue data
    with open('Data_JSON/correct_venue_data.json', 'r') as f:
        venues = json.load(f)
    
    # Analyze existing data to understand patterns
    rental_costs = []
    room_costs = []
    decor_costs_by_type = {"traditional": [], "modern": [], "minimalist": []}
    
    # Collect existing data for analysis
    for venue in venues:
        if venue.get('rental_cost') and venue['rental_cost'] > 0:
            rental_costs.append(venue['rental_cost'])
        
        if venue.get('room_cost') and venue['room_cost'] is not None:
            room_costs.append(venue['room_cost'])
        
        if venue.get('decor_cost') and len(venue['decor_cost']) > 0:
            for decor in venue['decor_cost']:
                decor_type = decor.get('decor_type')
                cost = decor.get('cost')
                if decor_type in decor_costs_by_type and cost:
                    decor_costs_by_type[decor_type].append(cost)
    
    print(f"Found {len(rental_costs)} venues with rental costs")
    print(f"Found {len(room_costs)} venues with room costs")
    print(f"Found decor costs: Traditional: {len(decor_costs_by_type['traditional'])}, Modern: {len(decor_costs_by_type['modern'])}, Minimalist: {len(decor_costs_by_type['minimalist'])}")
    
    # Calculate statistics for pricing patterns
    if rental_costs:
        rental_stats = {
            'min': min(rental_costs),
            'max': max(rental_costs),
            'median': statistics.median(rental_costs),
            'mean': statistics.mean(rental_costs)
        }
        print(f"Rental cost stats: {rental_stats}")
    
    if room_costs:
        room_stats = {
            'min': min(room_costs),
            'max': max(room_costs),
            'median': statistics.median(room_costs),
            'mean': statistics.mean(room_costs)
        }
        print(f"Room cost stats: {room_stats}")
    
    # Calculate decor cost ratios relative to rental costs
    decor_ratios = {}
    for decor_type in decor_costs_by_type:
        if decor_costs_by_type[decor_type]:
            decor_ratios[decor_type] = {
                'min': min(decor_costs_by_type[decor_type]),
                'max': max(decor_costs_by_type[decor_type]),
                'median': statistics.median(decor_costs_by_type[decor_type]),
                'mean': statistics.mean(decor_costs_by_type[decor_type])
            }
            print(f"{decor_type} decor stats: {decor_ratios[decor_type]}")
    
    # Fill missing values based on patterns
    for venue in venues:
        # Fill rental_cost based on capacity and area type
        if not venue.get('rental_cost') or venue['rental_cost'] == 0:
            capacity = venue.get('ideal_capacity', 0)
            area_type = venue.get('area_type', 'indoor')
            
            # Base cost per person calculation
            if area_type == 'outdoor':
                base_cost_per_person = 600  # Outdoor venues tend to be more expensive
            elif area_type == 'poolside':
                base_cost_per_person = 700  # Poolside premium
            elif area_type == 'indoor & outdoor':
                base_cost_per_person = 650  # Hybrid venues
            else:  # indoor
                base_cost_per_person = 500
            
            # Calculate rental cost with some variation
            estimated_rental = capacity * base_cost_per_person
            
            # Add venue-specific adjustments based on name patterns
            venue_name = venue.get('name', '').lower()
            if any(word in venue_name for word in ['palace', 'taj', 'leela', 'ritz', 'marriott', 'itc']):
                estimated_rental *= 2.5  # Luxury venues
            elif any(word in venue_name for word in ['resort', 'hotel', 'radisson', 'golden']):
                estimated_rental *= 1.8  # Premium venues
            elif any(word in venue_name for word in ['convention', 'banquet']):
                estimated_rental *= 1.2  # Standard venues
            
            venue['rental_cost'] = int(estimated_rental)
        
        # Fill decor_cost based on rental_cost
        if not venue.get('decor_cost') or len(venue['decor_cost']) == 0:
            rental_cost = venue.get('rental_cost', 0)
            if rental_cost > 0:
                # Decor costs are typically 15-25% of rental cost
                traditional_cost = int(rental_cost * 0.15)
                modern_cost = int(rental_cost * 0.20)
                minimalist_cost = int(rental_cost * 0.12)
                
                venue['decor_cost'] = [
                    {"decor_type": "traditional", "cost": traditional_cost},
                    {"decor_type": "modern", "cost": modern_cost},
                    {"decor_type": "minimalist", "cost": minimalist_cost}
                ]
        
        # Fill room_cost based on venue type and location
        if venue.get('room_cost') is None and venue.get('room_count') and venue['room_count'] > 0:
            venue_name = venue.get('name', '').lower()
            
            if any(word in venue_name for word in ['palace', 'taj', 'leela', 'ritz', 'marriott']):
                venue['room_cost'] = 8000  # Luxury hotels
            elif any(word in venue_name for word in ['itc', 'radisson', 'golden', 'shangri']):
                venue['room_cost'] = 5000  # Premium hotels
            elif any(word in venue_name for word in ['resort', 'hotel']):
                venue['room_cost'] = 3000  # Standard hotels/resorts
            else:
                venue['room_cost'] = 1500  # Basic venues with rooms
    
    # Write the updated data
    with open('Data_JSON/correct_venue_data.json', 'w') as f:
        json.dump(venues, f, indent=4)
    
    print(f"Updated {len(venues)} venues with estimated costs")

if __name__ == "__main__":
    analyze_and_fill_costs()
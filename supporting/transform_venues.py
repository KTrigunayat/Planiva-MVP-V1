import json

def transform_venues_data():
    # Read the scraped data
    with open('Data_JSON/scraped_venues_data.json', 'r') as f:
        scraped_data = json.load(f)
    
    transformed_data = []
    
    for venue in scraped_data:
        # Skip venues without capacity data
        if 'capacity' not in venue or not venue['capacity']:
            continue
            
        for area in venue['capacity']:
            # Create a new entry for each area
            transformed_entry = {
                "name": venue['name'],
                "area_name": area['area'],
                "area_type": area['type'],
                "ideal_capacity": area['seating'],
                "max_capacity": area['floating'],
                "rental_cost": area.get('rental_cost', 0),
                "decor_cost": area.get('decor_cost', []),
                "location": venue['location'],
                "policies": venue['policies'],
                "room_count": venue.get('room_count'),
                "room_cost": venue.get('room_cost')
            }
            
            transformed_data.append(transformed_entry)
    
    # Write the transformed data
    with open('Data_JSON/correct_venue_data.json', 'w') as f:
        json.dump(transformed_data, f, indent=4)
    
    print(f"Transformed {len(transformed_data)} venue areas from {len(scraped_data)} venues")

if __name__ == "__main__":
    transform_venues_data()
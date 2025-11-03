import json

def transform_caterers_data():
    # Read the caterers data
    with open('Data_JSON/caterers_data.json', 'r') as f:
        caterers_data = json.load(f)
    
    transformed_data = []
    
    for caterer in caterers_data:
        # Determine if veg only
        pricing = caterer.get('pricing', {})
        veg_price = pricing.get('veg_price_per_plate', 0)
        non_veg_price = pricing.get('starting_plate_non_veg', 0)
        
        # If no non-veg price is specified, assume veg only
        veg_only = non_veg_price == 0 or non_veg_price is None
        
        # Create transformed entry
        transformed_entry = {
            "name": caterer['name'],
            "location": caterer['location'],
            "veg_only": veg_only,
            "per_plate_price_veg": veg_price,
            "per_plate_price_non_veg": non_veg_price if not veg_only else None,
            "cuisines": caterer['details'].get('cuisines', []),
            "about": caterer['details'].get('about', '')
        }
        
        transformed_data.append(transformed_entry)
    
    # Write the transformed data
    with open('Data_JSON/correct_caterers_data.json', 'w') as f:
        json.dump(transformed_data, f, indent=4)
    
    print(f"Transformed {len(transformed_data)} caterers")

if __name__ == "__main__":
    transform_caterers_data()
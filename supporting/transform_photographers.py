import json
import re

def extract_price(price_str):
    """Extract numeric price from string, handling various formats"""
    if not price_str or price_str == "₹Price on Request":
        return 0
    
    # Remove currency symbol and commas
    price_str = price_str.replace('₹', '').replace(',', '').strip()
    
    # Extract numbers from the string
    numbers = re.findall(r'\d+', price_str)
    if numbers:
        return int(numbers[0])
    return 0

def get_max_price(pricing_dict):
    """Get the maximum price from pricing dictionary"""
    max_price = 0
    
    for key, value in pricing_dict.items():
        if key != 'starting_price':  # Handle starting_price separately
            price = extract_price(value)
            max_price = max(max_price, price)
        else:
            # For starting_price, use it as is
            price = extract_price(value)
            max_price = max(max_price, price)
    
    return max_price

def transform_photographers():
    # Read the original data
    with open('Data_JSON/photographers_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    transformed_data = []
    
    for photographer in data:
        # Get maximum price from pricing
        if isinstance(photographer.get('pricing'), dict):
            max_price = get_max_price(photographer['pricing'])
        else:
            max_price = 0
        
        # Get services from details
        services = []
        if 'details' in photographer and 'services_offered' in photographer['details']:
            services = photographer['details']['services_offered']
        
        # Create simplified entry
        simplified_photographer = {
            "name": photographer['name'],
            "location": photographer['location'],
            "price": max_price,
            "services": services,
            "source_url": photographer['source_url']
        }
        
        transformed_data.append(simplified_photographer)
    
    # Write the transformed data
    with open('Data_JSON/photographers_data.json', 'w', encoding='utf-8') as f:
        json.dump(transformed_data, f, indent=2, ensure_ascii=False)
    
    print(f"Transformed {len(transformed_data)} photographers")
    print("Sample entries:")
    for i, photographer in enumerate(transformed_data[:3]):
        print(f"{i+1}. {photographer['name']} - ₹{photographer['price']} - {photographer['location']}")

if __name__ == "__main__":
    transform_photographers()
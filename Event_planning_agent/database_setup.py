import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import uuid

load_dotenv()

def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"), 
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"), 
        host=os.getenv("DB_HOST"), 
        port=os.getenv("DB_PORT")
    )

def create_tables():
    """Create all necessary tables for the event planning system"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Try to enable pgvector extension, but continue without it if not available
    vector_available = False
    try:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        conn.commit()  # Commit the extension creation
        vector_available = True
        print("✅ pgvector extension enabled")
    except Exception as e:
        print(f"⚠️ pgvector extension not available: {e}")
        print("   System will work without vector embeddings (using basic search)")
        conn.rollback()  # Rollback the failed transaction
    
    # Determine embedding column type
    embedding_column = "vector(384)" if vector_available else "TEXT"
    
    # Create venues table
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS venues (
            vendor_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) NOT NULL,
            area_name VARCHAR(255),
            area_type VARCHAR(100),
            location_city VARCHAR(100),
            location_full TEXT,
            ideal_capacity INTEGER,
            max_seating_capacity INTEGER,
            rental_cost INTEGER,
            min_veg_price INTEGER,
            policies JSONB,
            room_count INTEGER,
            room_cost INTEGER,
            decor_options JSONB,
            attributes JSONB,
            embedding {embedding_column}
        );
    """)
    
    # Create caterers table
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS caterers (
            vendor_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) NOT NULL,
            location_city VARCHAR(100),
            location_full TEXT,
            veg_only BOOLEAN,
            min_veg_price INTEGER,
            min_non_veg_price INTEGER,
            max_guest_capacity INTEGER DEFAULT 10000,
            attributes JSONB,
            embedding {embedding_column}
        );
    """)
    
    # Create photographers table
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS photographers (
            vendor_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) NOT NULL,
            location_city VARCHAR(100),
            location_full TEXT,
            photo_package_price INTEGER,
            video_available BOOLEAN DEFAULT true,
            attributes JSONB,
            embedding {embedding_column}
        );
    """)
    
    # Create makeup_artists table
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS makeup_artists (
            vendor_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) NOT NULL,
            location_city VARCHAR(100),
            location_full TEXT,
            bridal_makeup_price INTEGER,
            on_site_service BOOLEAN DEFAULT true,
            attributes JSONB,
            embedding {embedding_column}
        );
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Database tables created successfully!")

def extract_city_from_location(location):
    """Extract city name from location string"""
    if not location:
        return "Bangalore"
    
    # Common patterns for Bangalore locations
    if "Bangalore" in location or "Bengaluru" in location:
        return "Bangalore"
    elif "Kochi" in location:
        return "Kochi"
    elif "Hyderabad" in location:
        return "Hyderabad"
    else:
        # Default to Bangalore if unclear
        return "Bangalore"

def load_venues_data():
    """Load venue data from JSON file"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    with open('../Data_JSON/correct_venue_data.json', 'r', encoding='utf-8') as f:
        venues_data = json.load(f)
    
    for venue in venues_data:
        location_city = extract_city_from_location(venue.get('location', ''))
        
        # Calculate min veg price (using rental cost as base)
        min_veg_price = venue.get('rental_cost', 0) // 100  # Rough estimate
        
        attributes = {
            'about': f"Premium venue in {location_city} with {venue.get('area_type', 'mixed')} space",
            'area_type': venue.get('area_type', 'mixed'),
            'policies': venue.get('policies', {})
        }
        
        cursor.execute("""
            INSERT INTO venues (
                name, area_name, area_type, location_city, location_full,
                ideal_capacity, max_seating_capacity, rental_cost, min_veg_price,
                policies, room_count, room_cost, decor_options, attributes
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            venue['name'], venue.get('area_name'), venue.get('area_type'),
            location_city, venue.get('location'),
            venue.get('ideal_capacity'), venue.get('max_capacity', venue.get('ideal_capacity')),
            venue.get('rental_cost'), min_veg_price,
            json.dumps(venue.get('policies', {})), venue.get('room_count'),
            venue.get('room_cost'), json.dumps(venue.get('decor_cost', [])),
            json.dumps(attributes)
        ))
    
    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Loaded {len(venues_data)} venues")

def load_caterers_data():
    """Load caterer data from JSON file"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    with open('../Data_JSON/correct_caterers_data.json', 'r', encoding='utf-8') as f:
        caterers_data = json.load(f)
    
    for caterer in caterers_data:
        location_city = extract_city_from_location(caterer.get('location', ''))
        
        attributes = {
            'about': caterer.get('about', ''),
            'cuisines': caterer.get('cuisines', [])
        }
        
        cursor.execute("""
            INSERT INTO caterers (
                name, location_city, location_full, veg_only,
                min_veg_price, min_non_veg_price, attributes
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            caterer['name'], location_city, caterer.get('location'),
            caterer.get('veg_only', False),
            caterer.get('per_plate_price_veg', 0),
            caterer.get('per_plate_price_non_veg', 0),
            json.dumps(attributes)
        ))
    
    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Loaded {len(caterers_data)} caterers")

def load_photographers_data():
    """Load photographer data from JSON file"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    with open('../Data_JSON/photographers_data.json', 'r', encoding='utf-8') as f:
        photographers_data = json.load(f)
    
    for photographer in photographers_data:
        location_city = extract_city_from_location(photographer.get('location', ''))
        
        # Check if video services are available
        services = photographer.get('services', [])
        video_available = any('video' in service.lower() or 'cinematography' in service.lower() 
                            for service in services)
        
        attributes = {
            'about': f"Professional photographer in {location_city}",
            'services': services,
            'styles': ['candid', 'traditional']  # Default styles
        }
        
        cursor.execute("""
            INSERT INTO photographers (
                name, location_city, location_full, photo_package_price,
                video_available, attributes
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            photographer['name'], location_city, photographer.get('location'),
            photographer.get('price', 0), video_available,
            json.dumps(attributes)
        ))
    
    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Loaded {len(photographers_data)} photographers")

def load_makeup_artists_data():
    """Load makeup artist data from JSON file"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    with open('../Data_JSON/Makeup_artist.json', 'r', encoding='utf-8') as f:
        makeup_artists_data = json.load(f)
    
    for artist in makeup_artists_data:
        location_city = extract_city_from_location(artist.get('location', ''))
        
        # Check if travels to venue
        services = artist.get('services', [])
        on_site = any('travels' in service.lower() for service in services)
        
        attributes = {
            'about': f"Professional makeup artist in {location_city}",
            'services': services,
            'specialties': ['bridal', 'party']  # Default specialties
        }
        
        cursor.execute("""
            INSERT INTO makeup_artists (
                name, location_city, location_full, bridal_makeup_price,
                on_site_service, attributes
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            artist['name'], location_city, artist.get('location'),
            artist.get('price', 0), on_site,
            json.dumps(attributes)
        ))
    
    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Loaded {len(makeup_artists_data)} makeup artists")

def clean_database():
    """Clean all existing tables and data"""
    print("🧹 Cleaning existing database...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Drop all tables if they exist
    tables = ['venues', 'caterers', 'photographers', 'makeup_artists']
    
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
        print(f"   🗑️ Dropped table: {table}")
    
    # Drop vector extension if exists (will be recreated)
    cursor.execute("DROP EXTENSION IF EXISTS vector CASCADE;")
    print("   🗑️ Dropped vector extension")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("✅ Database cleaned successfully!")

def setup_complete_database(clean_first=True):
    """Complete database setup with all data"""
    print("🚀 Starting complete database setup...")
    
    if clean_first:
        try:
            clean_database()
        except Exception as e:
            print(f"⚠️ Cleaning failed (continuing anyway): {e}")
    
    create_tables()
    load_venues_data()
    load_caterers_data()
    load_photographers_data()
    load_makeup_artists_data()
    
    print("\n✅ Database setup complete! Ready for embeddings and testing.")

if __name__ == "__main__":
    import sys
    
    # Check for command line arguments
    clean_first = True
    if len(sys.argv) > 1:
        if sys.argv[1] == "--no-clean":
            clean_first = False
        elif sys.argv[1] == "--clean-only":
            clean_database()
            sys.exit(0)
        elif sys.argv[1] == "--help":
            print("Usage: python database_setup.py [--clean-only|--no-clean|--help]")
            print("  --clean-only: Only clean the database, don't reload data")
            print("  --no-clean: Don't clean before setup (append to existing data)")
            print("  --help: Show this help message")
            sys.exit(0)
    
    setup_complete_database(clean_first=clean_first)
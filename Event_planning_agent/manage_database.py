#!/usr/bin/env python3
"""
Database Management Script for Planiva Event Planning System
Provides easy commands for database operations
"""

import sys
import os
from database_setup import (
    clean_database, 
    create_tables, 
    load_venues_data, 
    load_caterers_data, 
    load_photographers_data, 
    load_makeup_artists_data,
    get_db_connection
)

def show_database_stats():
    """Show current database statistics"""
    print("📊 Database Statistics")
    print("-" * 30)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        tables = ['venues', 'caterers', 'photographers', 'makeup_artists']
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                count = cursor.fetchone()[0]
                
                # Check for embeddings
                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE embedding IS NOT NULL;")
                embedded_count = cursor.fetchone()[0]
                
                print(f"📋 {table.title()}: {count} records ({embedded_count} with embeddings)")
                
            except Exception as e:
                print(f"❌ {table.title()}: Table doesn't exist")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

def reload_specific_service(service_type):
    """Reload data for a specific service type"""
    print(f"🔄 Reloading {service_type} data...")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Clear existing data for this service type
        if service_type == "venues":
            cursor.execute("DELETE FROM venues;")
            load_venues_data()
        elif service_type == "caterers":
            cursor.execute("DELETE FROM caterers;")
            load_caterers_data()
        elif service_type == "photographers":
            cursor.execute("DELETE FROM photographers;")
            load_photographers_data()
        elif service_type == "makeup_artists":
            cursor.execute("DELETE FROM makeup_artists;")
            load_makeup_artists_data()
        else:
            print(f"❌ Unknown service type: {service_type}")
            return False
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ {service_type} data reloaded successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to reload {service_type}: {e}")
        return False

def clear_embeddings():
    """Clear all embeddings from database"""
    print("🧹 Clearing all embeddings...")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        tables = ['venues', 'caterers', 'photographers', 'makeup_artists']
        
        for table in tables:
            cursor.execute(f"UPDATE {table} SET embedding = NULL;")
            print(f"   🗑️ Cleared embeddings from {table}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ All embeddings cleared!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to clear embeddings: {e}")
        return False

def backup_database():
    """Create a backup of the database"""
    print("💾 Creating database backup...")
    
    try:
        import subprocess
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"planiva_backup_{timestamp}.sql"
        
        # Use pg_dump to create backup
        result = subprocess.run([
            'pg_dump', 
            '-h', os.getenv('DB_HOST', 'localhost'),
            '-p', os.getenv('DB_PORT', '5432'),
            '-U', os.getenv('DB_USER', 'postgres'),
            '-d', os.getenv('DB_NAME', 'planiva_events'),
            '-f', backup_file
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Backup created: {backup_file}")
            return True
        else:
            print(f"❌ Backup failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return False

def show_help():
    """Show help information"""
    print("🛠️ Planiva Database Management")
    print("=" * 40)
    print("Usage: python manage_database.py <command>")
    print()
    print("Commands:")
    print("  stats              Show database statistics")
    print("  clean              Clean all tables and data")
    print("  reload             Reload all data (clean + load)")
    print("  reload-venues      Reload only venues data")
    print("  reload-caterers    Reload only caterers data")
    print("  reload-photographers Reload only photographers data")
    print("  reload-makeup      Reload only makeup artists data")
    print("  clear-embeddings   Clear all vector embeddings")
    print("  backup             Create database backup")
    print("  help               Show this help message")
    print()
    print("Examples:")
    print("  python manage_database.py stats")
    print("  python manage_database.py reload-venues")
    print("  python manage_database.py clean")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "stats":
        show_database_stats()
    
    elif command == "clean":
        clean_database()
    
    elif command == "reload":
        clean_database()
        create_tables()
        load_venues_data()
        load_caterers_data()
        load_photographers_data()
        load_makeup_artists_data()
        print("✅ All data reloaded!")
    
    elif command == "reload-venues":
        reload_specific_service("venues")
    
    elif command == "reload-caterers":
        reload_specific_service("caterers")
    
    elif command == "reload-photographers":
        reload_specific_service("photographers")
    
    elif command == "reload-makeup":
        reload_specific_service("makeup_artists")
    
    elif command == "clear-embeddings":
        clear_embeddings()
    
    elif command == "backup":
        backup_database()
    
    elif command == "help":
        show_help()
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Run 'python manage_database.py help' for available commands")

if __name__ == "__main__":
    main()
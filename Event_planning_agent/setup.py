#!/usr/bin/env python3
"""
Setup script for Planiva Event Planning System
This script helps set up the complete system step by step
"""

import os
import sys
import subprocess
import shutil

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def check_postgresql():
    """Check if PostgreSQL is available"""
    # Try different ways to detect PostgreSQL on Windows
    postgres_commands = ['psql', 'psql.exe']
    postgres_paths = [
        'C:\\Program Files\\PostgreSQL\\*\\bin\\psql.exe',
        'C:\\Program Files (x86)\\PostgreSQL\\*\\bin\\psql.exe'
    ]
    
    # Try direct command first
    for cmd in postgres_commands:
        try:
            result = subprocess.run([cmd, '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ PostgreSQL is available")
                return True
        except FileNotFoundError:
            continue
    
    # Try common installation paths on Windows
    import glob
    for path_pattern in postgres_paths:
        matching_paths = glob.glob(path_pattern)
        if matching_paths:
            try:
                result = subprocess.run([matching_paths[0], '--version'], capture_output=True, text=True)
                if result.returncode == 0:
                    print("✅ PostgreSQL found in installation directory")
                    return True
            except:
                continue
    
    # Try to connect directly using psycopg2 (if PostgreSQL server is running)
    try:
        import psycopg2
        # Try to connect with default credentials
        conn = psycopg2.connect(
            host='localhost',
            port='5432',
            user='postgres',
            password='',  # Try empty password first
            database='postgres'  # Connect to default database
        )
        conn.close()
        print("✅ PostgreSQL server is running and accessible")
        return True
    except:
        pass
    
    print("❌ PostgreSQL not found or not accessible.")
    print("   Options:")
    print("   1. Install PostgreSQL: https://www.postgresql.org/download/windows/")
    print("   2. Use Docker: docker run --name postgres -e POSTGRES_PASSWORD=password -p 5432:5432 -d postgres")
    print("   3. Use cloud PostgreSQL (AWS RDS, Google Cloud SQL, etc.)")
    print("   4. Skip PostgreSQL check with: python setup.py --skip-postgres")
    return False

def check_ollama():
    """Check if Ollama is available"""
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Ollama is available")
            return True
    except FileNotFoundError:
        pass
    
    print("❌ Ollama not found. Please install Ollama first.")
    print("   Download from: https://ollama.ai/")
    return False

def install_requirements():
    """Install Python requirements"""
    print("📦 Installing Python requirements...")
    
    requirements = [
        "psycopg2-binary",
        "python-dotenv", 
        "crewai",
        "langchain-community",
        "langgraph",
        "llama-index",
        "llama-index-vector-stores-postgres",
        "llama-index-embeddings-ollama"
    ]
    
    for req in requirements:
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', req], 
                         check=True, capture_output=True)
            print(f"   ✅ {req}")
        except subprocess.CalledProcessError:
            print(f"   ❌ Failed to install {req}")
            return False
    
    return True

def setup_env_file():
    """Set up environment file"""
    env_file = ".env"
    template_file = ".env.template"
    
    if os.path.exists(env_file):
        print("✅ .env file already exists")
        return True
    
    if os.path.exists(template_file):
        shutil.copy(template_file, env_file)
        print("📝 Created .env file from template")
        print("   ⚠️ Please edit .env file with your database credentials")
        return True
    else:
        # Create basic .env file
        env_content = """# Database Configuration
DB_NAME=planiva_events
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_LLM_MODEL=gemma:2b
"""
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print("📝 Created basic .env file")
        print("   ⚠️ Please edit .env file with your database credentials")
        return True

def pull_ollama_models():
    """Pull required Ollama models"""
    print("🤖 Pulling Ollama models...")
    
    models = ["nomic-embed-text", "gemma:2b"]
    
    for model in models:
        try:
            print(f"   📥 Pulling {model}...")
            subprocess.run(['ollama', 'pull', model], check=True, capture_output=True)
            print(f"   ✅ {model}")
        except subprocess.CalledProcessError:
            print(f"   ❌ Failed to pull {model}")
            return False
    
    return True

def create_database():
    """Create PostgreSQL database"""
    print("🗄️ Setting up database...")
    
    # Try different approaches to create database
    commands_to_try = [
        ['createdb', 'planiva_events'],
        ['createdb.exe', 'planiva_events']
    ]
    
    for cmd in commands_to_try:
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print("   ✅ Database 'planiva_events' created")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    
    # Try to create database using psycopg2 directly
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
        
        # Connect to default postgres database
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'planiva_events'")
        if cursor.fetchone():
            print("   ✅ Database 'planiva_events' already exists")
        else:
            cursor.execute("CREATE DATABASE planiva_events")
            print("   ✅ Database 'planiva_events' created")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"   ⚠️ Could not create database automatically: {e}")
        print("   Please create the database manually:")
        print("   1. Open pgAdmin or psql")
        print("   2. Run: CREATE DATABASE planiva_events;")
        print("   3. Or use: createdb planiva_events")
        return True  # Continue anyway

def clean_database():
    """Clean existing database tables and data"""
    print("🧹 Cleaning existing database...")
    
    try:
        # Import here to avoid circular imports
        import psycopg2
        from dotenv import load_dotenv
        
        load_dotenv()
        
        # Connect to database
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "planiva_events"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432")
        )
        
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
        
        print("   ✅ Database cleaned successfully")
        return True
        
    except Exception as e:
        print(f"   ⚠️ Database cleaning failed (this is OK if database doesn't exist): {e}")
        return True  # Continue even if cleaning fails

def run_database_setup():
    """Run the database setup script"""
    print("📊 Loading data into database...")
    
    try:
        subprocess.run([sys.executable, 'database_setup.py'], check=True)
        print("   ✅ Database setup completed")
        return True
    except subprocess.CalledProcessError:
        print("   ❌ Database setup failed")
        return False

def main():
    """Main setup function"""
    print("🚀 Planiva Event Planning System Setup")
    print("=" * 50)
    
    # Check for command line arguments
    clean_db = True
    skip_postgres = False
    skip_ollama = False
    
    for arg in sys.argv[1:]:
        if arg == "--no-clean":
            clean_db = False
            print("ℹ️ Running setup without cleaning existing database")
        elif arg == "--skip-postgres":
            skip_postgres = True
            print("ℹ️ Skipping PostgreSQL check")
        elif arg == "--skip-ollama":
            skip_ollama = True
            print("ℹ️ Skipping Ollama check")
        elif arg == "--help":
            print("Usage: python setup.py [options]")
            print("Options:")
            print("  --no-clean: Don't clean existing database before setup")
            print("  --skip-postgres: Skip PostgreSQL installation check")
            print("  --skip-ollama: Skip Ollama installation check")
            print("  --help: Show this help message")
            return True
    
    if clean_db:
        print("ℹ️ This will clean and recreate all database tables")
    
    # Check prerequisites
    if not check_python_version():
        return False
    
    if not skip_postgres and not check_postgresql():
        print("\n⚠️ PostgreSQL check failed. You can:")
        print("1. Install PostgreSQL and run setup again")
        print("2. Skip this check with: python setup.py --skip-postgres")
        print("3. Set up PostgreSQL manually and continue")
        
        response = input("\nContinue anyway? (y/N): ").lower().strip()
        if response != 'y':
            return False
    
    if not skip_ollama and not check_ollama():
        print("\n⚠️ Ollama check failed. You can:")
        print("1. Install Ollama and run setup again")
        print("2. Skip this check with: python setup.py --skip-ollama")
        
        response = input("\nContinue anyway? (y/N): ").lower().strip()
        if response != 'y':
            return False
    
    # Install requirements
    if not install_requirements():
        print("❌ Failed to install requirements")
        return False
    
    # Setup environment
    setup_env_file()
    
    # Pull Ollama models
    if not pull_ollama_models():
        print("❌ Failed to pull Ollama models")
        return False
    
    # Create database
    create_database()
    
    # Clean existing database if requested
    if clean_db:
        clean_database()
    
    # Setup database
    if not run_database_setup():
        print("❌ Database setup failed")
        print("   Please check your .env file and database credentials")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Edit .env file with your database credentials if needed")
    print("2. Run: python embed_data.py (to generate embeddings)")
    print("3. Run: python test_complete_system.py (to test everything)")
    print("4. Run: python demo.py (to see it in action)")
    print("\nDatabase Management:")
    print("• Clean only: python database_setup.py --clean-only")
    print("• Reload data: python database_setup.py")
    print("• Add data without cleaning: python database_setup.py --no-clean")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
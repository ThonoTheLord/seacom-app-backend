"""
Script to create management dashboard views in the database.
Run this once to set up all the views needed for the manager dashboard.
"""
import os
import sys

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.database import Database
from app.core.settings import app_settings
from sqlalchemy import text


def create_views():
    """Create the management dashboard views from the SQL file."""
    
    # Connect to database
    url = f"postgresql://{app_settings.DB_USER}:{app_settings.DB_PASSWORD}@{app_settings.DB_HOST}:{app_settings.DB_PORT}/{app_settings.DB_NAME}"
    Database.connect(url)
    
    # Read the SQL file
    sql_file = os.path.join(os.path.dirname(__file__), "01_create_management_dashboard_views.sql")
    
    if not os.path.exists(sql_file):
        print(f"ERROR: SQL file not found at {sql_file}")
        return False
    
    with open(sql_file, "r") as f:
        sql_content = f.read()
    
    # Split by CREATE OR REPLACE VIEW and execute each separately
    # This handles the multi-statement SQL file better
    print("Creating management dashboard views...")
    
    with Database.session() as session:
        try:
            # Execute the entire SQL file as one transaction
            # Split on semicolons but be careful about those inside strings
            session.execute(text(sql_content))
            session.commit()
            print("✅ All views created successfully!")
            
            # Verify views exist
            result = session.execute(text("""
                SELECT table_name FROM information_schema.views 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'v_%'
                ORDER BY table_name
            """))
            views = [row[0] for row in result]
            print(f"\nCreated {len(views)} views:")
            for v in views:
                print(f"  - {v}")
            
            return True
            
        except Exception as e:
            session.rollback()
            print(f"❌ Error creating views: {e}")
            return False


if __name__ == "__main__":
    success = create_views()
    sys.exit(0 if success else 1)

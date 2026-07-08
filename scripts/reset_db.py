import os
import sys
import argparse

# Ensure we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import SQLModel
from app.core.database import engine

# Import all models to ensure they are registered with SQLModel.metadata
from app.models.schema import (
    User, ProjectGroup, ProjectInvite, ProjectParticipant,
    Requirement, ChangeRequest, ChangeApproval, Comment
)

def main():
    parser = argparse.ArgumentParser(description="Reset the database (Development Only)")
    parser.add_argument("--yes", action="store_true", help="Confirm database reset")
    args = parser.parse_args()

    if not args.yes:
        print("Error: You must provide the --yes flag to confirm you want to reset the database.")
        sys.exit(1)

    env = os.environ.get("APP_ENV", os.environ.get("ENV", "development")).lower()
    if env == "production":
        print("Error: Refusing to run in production environment.")
        sys.exit(1)

    print("WARNING: This will drop all tables and recreate them, deleting ALL data.")
    print("Dropping tables...")
    SQLModel.metadata.drop_all(engine)
    print("Recreating tables...")
    SQLModel.metadata.create_all(engine)
    print("Database reset successfully. All tables are now empty.")

if __name__ == "__main__":
    main()

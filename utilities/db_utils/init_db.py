# init_db.py
import os
from pathlib import Path
os.chdir(Path(__file__).resolve().parent.parent.parent)

from sqlalchemy import create_engine
from utilities.db_utils.base import Base
from config.settings_reader import get_db_url, get_update_user

# Import all models to register them with Base
import utilities.db_utils.models

def init_db():
    engine = create_engine(get_db_url())
    Base.metadata.create_all(engine)
    print("✅ All tables created!")

if __name__ == "__main__":
    print("Initializing database...")
    init_db()

    from utilities.db_utils.handler import bulk_add_prompts
    from utilities.db_utils.prompt_list import prompt_list

    print("Loading Intial prompts...")
    bulk_add_prompts(prompt_list, created_by=get_update_user())
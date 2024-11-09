# Database setup
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:1@localhost:5449/temurs_shop")
engine = create_engine(DATABASE_URL)

session = Session(engine)


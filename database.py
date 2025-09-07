# database.py
import logfire
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

logfire.configure()  # Initialize logfire

# Define the database URL for SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./flight.db"

# Create the SQLAlchemy engine
# connect_args is needed only for SQLite to allow multi-threaded access
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
logfire.instrument_sqlalchemy(engine=engine)

# Create a SessionLocal class, which will be the database session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our models to inherit from
Base = declarative_base()

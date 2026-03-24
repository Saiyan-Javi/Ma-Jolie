from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Esto creará un archivo llamado 'ma_jolie.db' en tu carpeta
SQLALCHEMY_DATABASE_URL = "sqlite:///./ma_jolie.db"

# Configuramos el motor de la base de datos
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Creamos una sesión para poder hacer consultas y guardar datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Esta clase 'Base' es la que usarán nuestros modelos
Base = declarative_base()

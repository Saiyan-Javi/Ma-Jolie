from database import engine, Base
# Importamos models para que Python lea los planos antes de crear la base
import models 

print("Construyendo las tablas...")
Base.metadata.create_all(bind=engine)
print("¡Base de datos 'ma_jolie.db' creada con éxito!")
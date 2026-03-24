from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from database import Base # Importamos la base desde nuestro archivo database.py

class Usuario(Base):
    __tablename__ = 'usuarios'
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String)
    correo = Column(String, unique=True, index=True)
    contrasena_hash = Column(String)

class Proyecto(Base):
    __tablename__ = 'proyectos'
    
    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String)
    descripcion = Column(String)
    fecha_limite = Column(DateTime)
    
    id_creador = Column(Integer, ForeignKey('usuarios.id'))
    completado = Column(Boolean, default=False)

class BloqueTrabajo(Base):
    __tablename__ = 'bloques_trabajo'
    
    id = Column(Integer, primary_key=True, index=True)
    id_proyecto = Column(Integer, ForeignKey('proyectos.id'))
    
    fecha_hora_inicio = Column(DateTime)
    fecha_hora_fin = Column(DateTime)
    completado = Column(Boolean, default=False)

class RegistroPersonal(Base):
    __tablename__ = 'registro_personal'
    
    id = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey('usuarios.id'))
    
    inicio_periodo = Column(DateTime, nullable=True)
    fin_periodo = Column(DateTime, nullable=True)
    hubo_relaciones = Column(Boolean, default=False)
    fecha_registro = Column(DateTime)
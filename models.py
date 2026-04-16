from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from database import Base

class Proyecto(Base):
    __tablename__ = "proyectos"
    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, index=True)
    descripcion = Column(String)
    fecha_limite = Column(DateTime)
    id_creador = Column(Integer, default=1) 
    es_compartida = Column(Boolean, default=True)

class BloqueTrabajo(Base):
    __tablename__ = "bloques_trabajo"
    id = Column(Integer, primary_key=True, index=True)
    id_proyecto = Column(Integer, ForeignKey("proyectos.id"))
    fecha_hora_inicio = Column(DateTime)
    fecha_hora_fin = Column(DateTime)
    completado = Column(Boolean, default=False) 

class RegistroPersonal(Base):
    __tablename__ = "registros_personales"
    id = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer)
    fecha_registro = Column(DateTime)
    inicio_periodo = Column(DateTime, nullable=True)
    hubo_relaciones = Column(Boolean, default=False)

class Invitacion(Base):
    __tablename__ = "invitaciones"
    id = Column(Integer, primary_key=True, index=True)
    id_proyecto = Column(Integer, ForeignKey("proyectos.id"))
    id_remitente = Column(Integer) 
    id_destinatario = Column(Integer)
    estado = Column(String, default="pendiente") 

class PerfilUsuario(Base):
    __tablename__ = "perfiles"
    id = Column(Integer, primary_key=True, index=True)
    trigos = Column(Integer, default=0)

# --- NUEVA TABLA: NOTIFICACIONES DE LA TIENDA ---
class NotificacionRecompensa(Base):
    __tablename__ = "notificaciones_recompensas"
    id = Column(Integer, primary_key=True, index=True)
    id_comprador = Column(Integer)
    id_pareja = Column(Integer)
    nombre_premio = Column(String)
    vista = Column(Boolean, default=False)
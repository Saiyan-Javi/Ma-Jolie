from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
from fastapi.middleware.cors import CORSMiddleware

import models
import scheduler
from database import SessionLocal, engine

# Crea las tablas en la base de datos (Neon o local)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Ma Jolie App", description="El motor de productividad")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- FUNCIÓN DE PROGRAMACIÓN DEFENSIVA (RADAR) ---
def verificar_colision(db: Session, inicio: datetime, fin: datetime, id_usuario: int):
    # Buscamos bloques que se crucen con el horario propuesto para el MISMO usuario
    colision = db.query(models.BloqueTrabajo).join(models.Proyecto).filter(
        models.Proyecto.id_creador == id_usuario,
        models.BloqueTrabajo.fecha_hora_inicio < fin,
        models.BloqueTrabajo.fecha_hora_fin > inicio
    ).first()
    return colision

# --- MODELOS DE DATOS (PYDANTIC) ---
class DatosProyecto(BaseModel):
    titulo: str
    descripcion: str
    fecha_limite: datetime
    horas_totales: int
    dias_a_invertir: int
    hora_inicio_pref: int
    hora_fin_pref: int
    creador: str 
    invitar_pareja: bool = False

class DatosTareaDirecta(BaseModel):
    titulo: str
    fecha_limite: datetime
    fecha_inicio: datetime 
    horas: int
    creador: str
    invitar_pareja: bool = False

class DatosRegistroPersonal(BaseModel):
    fecha: datetime
    tipo: str
    creador: str 

class RespuestaInvitacion(BaseModel):
    respuesta: str

class DatosCompra(BaseModel):
    creador: str
    costo: int
    nombre_premio: str

# --- RUTAS DE PROYECTOS Y TAREAS ---

@app.post("/crear-proyecto/")
def crear_proyecto_con_bloques(datos: DatosProyecto, db: Session = Depends(get_db)):
    id_creador_num = 1 if datos.creador == "Javier" else 2
    
    bloques_calculados = scheduler.calcular_bloques_estudio(
        datos.fecha_limite, datos.horas_totales, datos.dias_a_invertir,
        datos.hora_inicio_pref, datos.hora_fin_pref
    )
    
    if isinstance(bloques_calculados, str):
        raise HTTPException(status_code=400, detail=bloques_calculados)
    
    # DEFENSIVA: Verificar colisiones
    for b in bloques_calculados:
        if verificar_colision(db, b['inicio'], b['fin'], id_creador_num):
            fecha_choque = b['inicio'].strftime('%d/%m a las %H:%M')
            raise HTTPException(status_code=400, detail=f"¡Colisión! Ya tienes algo agendado el {fecha_choque}.")

    nuevo_proyecto = models.Proyecto(
        titulo=datos.titulo, 
        descripcion=datos.descripcion, 
        fecha_limite=datos.fecha_limite, 
        id_creador=id_creador_num
    )
    db.add(nuevo_proyecto)
    db.commit()
    db.refresh(nuevo_proyecto)
    
    for bloque in bloques_calculados:
        nuevo_bloque = models.BloqueTrabajo(
            id_proyecto=nuevo_proyecto.id, 
            fecha_hora_inicio=bloque['inicio'], 
            fecha_hora_fin=bloque['fin']
        )
        db.add(nuevo_bloque)
        
    # Enviar invitación si se solicitó
    if datos.invitar_pareja:
        id_destinatario = 2 if id_creador_num == 1 else 1
        invitacion = models.Invitacion(
            id_proyecto=nuevo_proyecto.id, 
            id_remitente=id_creador_num, 
            id_destinatario=id_destinatario
        )
        db.add(invitacion)

    db.commit()
    return {"mensaje": "¡Proyecto guardado con éxito!"}

@app.post("/tarea-directa/")
def crear_tarea_directa(datos: DatosTareaDirecta, db: Session = Depends(get_db)):
    id_creador_num = 1 if datos.creador == "Javier" else 2
    fecha_fin = datos.fecha_inicio + timedelta(hours=datos.horas)
    
    if verificar_colision(db, datos.fecha_inicio, fecha_fin, id_creador_num):
        raise HTTPException(status_code=400, detail="Ya tienes una tarea programada en ese horario.")

    nueva_tarea = models.Proyecto(
        titulo=datos.titulo, 
        descripcion="Tarea Directa", 
        fecha_limite=datos.fecha_limite, 
        id_creador=id_creador_num
    )
    db.add(nueva_tarea)
    db.commit()
    db.refresh(nueva_tarea)
    
    nuevo_bloque = models.BloqueTrabajo(
        id_proyecto=nueva_tarea.id, 
        fecha_hora_inicio=datos.fecha_inicio, 
        fecha_hora_fin=fecha_fin
    )
    db.add(nuevo_bloque)
    
    if datos.invitar_pareja:
        id_destinatario = 2 if id_creador_num == 1 else 1
        invitacion = models.Invitacion(
            id_proyecto=nueva_tarea.id, 
            id_remitente=id_creador_num, 
            id_destinatario=id_destinatario
        )
        db.add(invitacion)

    db.commit()
    return {"mensaje": "¡Tarea directa guardada con éxito!"}

@app.get("/mis-bloques/")
def obtener_bloques(db: Session = Depends(get_db)):
    bloques = db.query(models.BloqueTrabajo).all()
    eventos_calendario = []
    for bloque in bloques:
        proyecto = db.query(models.Proyecto).filter(models.Proyecto.id == bloque.id_proyecto).first()
        if not proyecto: continue
        
        if hasattr(bloque, 'completado') and bloque.completado:
            color_bloque = "#bdc3c7" # Gris si ya se completó
        else:
            color_bloque = "#27ae60" if proyecto.id_creador == 1 else "#f39c12" # Luigi o Daisy
            
        nombre_creador = "Javier" if proyecto.id_creador == 1 else "Joyce"
        
        eventos_calendario.append({
            "id": str(bloque.id), 
            "title": f"{proyecto.titulo} ({nombre_creador})", 
            "title_clean": proyecto.titulo, 
            "start": bloque.fecha_hora_inicio.isoformat(),
            "end": bloque.fecha_hora_fin.isoformat(),
            "color": color_bloque,
            "completado": getattr(bloque, 'completado', False),
            "creador": nombre_creador 
        })
    return eventos_calendario

# --- SISTEMA DE TRIGOS Y COMPLETADO ---

@app.post("/completar-bloque/{bloque_id}")
def completar_bloque(bloque_id: int, db: Session = Depends(get_db)):
    bloque = db.query(models.BloqueTrabajo).filter(models.BloqueTrabajo.id == bloque_id).first()
    if not bloque:
        raise HTTPException(status_code=404, detail="Bloque no encontrado")
    
    proyecto = db.query(models.Proyecto).filter(models.Proyecto.id == bloque.id_proyecto).first()
    
    # Asegurar que el perfil exista
    perfil = db.query(models.PerfilUsuario).filter(models.PerfilUsuario.id == proyecto.id_creador).first()
    if not perfil:
        perfil = models.PerfilUsuario(id=proyecto.id_creador, trigos=0)
        db.add(perfil)
        db.commit()
        db.refresh(perfil)

    bloque.completado = not bloque.completado 
    if bloque.completado:
        perfil.trigos += 10 # Gana 10 trigos 🌾
    else:
        perfil.trigos -= 10 # Pierde 10 trigos si deshace

    db.commit()
    return {"mensaje": "Tarea actualizada", "trigos_actuales": perfil.trigos}

@app.get("/perfil/{creador}")
def obtener_perfil(creador: str, db: Session = Depends(get_db)):
    id_usr = 1 if creador == "Javier" else 2
    perfil = db.query(models.PerfilUsuario).filter(models.PerfilUsuario.id == id_usr).first()
    if not perfil:
        perfil = models.PerfilUsuario(id=id_usr, trigos=0)
        db.add(perfil)
        db.commit()
        db.refresh(perfil)
    return {"trigos": perfil.trigos}

@app.post("/comprar-recompensa/")
def comprar_recompensa(datos: DatosCompra, db: Session = Depends(get_db)):
    id_usr = 1 if datos.creador == "Javier" else 2
    id_pareja = 2 if id_usr == 1 else 1
    perfil = db.query(models.PerfilUsuario).filter(models.PerfilUsuario.id == id_usr).first()
    
    if not perfil or perfil.trigos < datos.costo:
        raise HTTPException(status_code=400, detail="¡Te faltan Trigos 🌾!")
        
    perfil.trigos -= datos.costo
    
    # Notificación para la pareja (Doble Check)
    nueva_notif = models.NotificacionRecompensa(
        id_comprador=id_usr,
        id_pareja=id_pareja,
        nombre_premio=datos.nombre_premio
    )
    db.add(nueva_notif)
    
    db.commit()
    return {"mensaje": "¡Compra exitosa!", "trigos_restantes": perfil.trigos}

@app.get("/mis-notificaciones-tienda/{creador}")
def obtener_notificaciones_tienda(creador: str, db: Session = Depends(get_db)):
    id_usr = 1 if creador == "Javier" else 2
    notificaciones = db.query(models.NotificacionRecompensa).filter(
        models.NotificacionRecompensa.id_pareja == id_usr,
        models.NotificacionRecompensa.vista == False
    ).all()
    
    resultados = []
    for n in notificaciones:
        comprador = "Javier" if n.id_comprador == 1 else "Joyce"
        resultados.append({"id": n.id, "comprador": comprador, "premio": n.nombre_premio})
    return resultados

@app.post("/marcar-notificacion-tienda/{id_notif}")
def marcar_notificacion(id_notif: int, db: Session = Depends(get_db)):
    notif = db.query(models.NotificacionRecompensa).filter(models.NotificacionRecompensa.id == id_notif).first()
    if notif:
        notif.vista = True
        db.commit()
    return {"mensaje": "Notificación vista"}

# --- RUTAS DE INVITACIONES ---

@app.get("/mis-invitaciones/{creador}")
def obtener_invitaciones(creador: str, db: Session = Depends(get_db)):
    id_destinatario = 1 if creador == "Javier" else 2
    invitaciones = db.query(models.Invitacion).filter(
        models.Invitacion.id_destinatario == id_destinatario, 
        models.Invitacion.estado == "pendiente"
    ).all()
    
    resultados = []
    for inv in invitaciones:
        proyecto = db.query(models.Proyecto).filter(models.Proyecto.id == inv.id_proyecto).first()
        if proyecto:
            resultados.append({
                "id_invitacion": inv.id, 
                "titulo": proyecto.titulo, 
                "remitente": "Javier" if inv.id_remitente == 1 else "Joyce"
            })
    return resultados

@app.post("/responder-invitacion/{id_invitacion}")
def responder_invitacion(id_invitacion: int, datos: RespuestaInvitacion, db: Session = Depends(get_db)):
    invitacion = db.query(models.Invitacion).filter(models.Invitacion.id == id_invitacion).first()
    if not invitacion:
        raise HTTPException(status_code=404, detail="Invitación no encontrada")
    
    invitacion.estado = datos.respuesta
    
    if datos.respuesta == "aceptada":
        # Clonar la tarea para quien aceptó
        p_orig = db.query(models.Proyecto).filter(models.Proyecto.id == invitacion.id_proyecto).first()
        p_nuevo = models.Proyecto(
            titulo=p_orig.titulo, 
            descripcion=p_orig.descripcion, 
            fecha_limite=p_orig.fecha_limite, 
            id_creador=invitacion.id_destinatario
        )
        db.add(p_nuevo)
        db.commit()
        db.refresh(p_nuevo)
        
        bloques_orig = db.query(models.BloqueTrabajo).filter(models.BloqueTrabajo.id_proyecto == p_orig.id).all()
        for b in bloques_orig:
            db.add(models.BloqueTrabajo(
                id_proyecto=p_nuevo.id, 
                fecha_hora_inicio=b.fecha_hora_inicio, 
                fecha_hora_fin=b.fecha_hora_fin
            ))
            
    db.commit()
    return {"mensaje": f"Invitación {datos.respuesta}"}

# --- RUTAS PRIVADAS Y SALUD ---

@app.post("/registrar-evento/")
def registrar_evento_personal(datos: DatosRegistroPersonal, db: Session = Depends(get_db)):
    id_usr = 1 if datos.creador == "Javier" else 2
    nuevo_registro = models.RegistroPersonal(id_usuario=id_usr, fecha_registro=datos.fecha)
    
    if datos.tipo == 'inicio_periodo':
        nuevo_registro.inicio_periodo = datos.fecha
    elif datos.tipo == 'relaciones':
        nuevo_registro.hubo_relaciones = True
        
    db.add(nuevo_registro)
    db.commit()
    return {"mensaje": "Registro guardado correctamente"}

@app.get("/prediccion-ciclo/")
def obtener_prediccion(db: Session = Depends(get_db)):
    registros = db.query(models.RegistroPersonal).filter(models.RegistroPersonal.inicio_periodo != None).order_by(models.RegistroPersonal.inicio_periodo.asc()).all()
    fechas = [reg.inicio_periodo for reg in registros]
    fecha_predicha, margen = scheduler.predecir_siguiente_ciclo(fechas)
    
    if not fecha_predicha: 
        return []
        
    eventos = []
    
    # 1. El evento del periodo
    eventos.append({
        "title": "🩸 Posible inicio de ciclo",
        "start": (fecha_predicha - timedelta(days=margen)).date().isoformat(),
        "end": (fecha_predicha + timedelta(days=margen)).date().isoformat(),
        "color": "#e84393", 
        "allDay": True
    })
    
    # 2. La ventana de fertilidad 🌸
    dia_ovulacion = fecha_predicha - timedelta(days=14)
    inicio_fertil = dia_ovulacion - timedelta(days=4)
    fin_fertil = dia_ovulacion + timedelta(days=2) 
    
    eventos.append({
        "title": "🌸 Días Fértiles",
        "start": inicio_fertil.date().isoformat(),
        "end": fin_fertil.date().isoformat(),
        "color": "#a29bfe", 
        "allDay": True
    })
    
    return eventos

@app.get("/datos-privados/")
def obtener_datos_privados(db: Session = Depends(get_db)):
    registros = db.query(models.RegistroPersonal).all()
    eventos = []
    for reg in registros:
        # ID con prefijo para evitar choques en el calendario
        if reg.inicio_periodo:
            eventos.append({
                "id": f"priv_{reg.id}", 
                "title": "🩸 Inicio", 
                "start": reg.inicio_periodo.date().isoformat(), 
                "color": "#c0392b", 
                "allDay": True, 
                "tipo": "periodo"
            })
        if reg.hubo_relaciones:
            eventos.append({
                "id": f"priv_{reg.id}", 
                "title": "❤️", 
                "start": reg.fecha_registro.date().isoformat(), 
                "color": "transparent", 
                "textColor": "#e74c3c", 
                "allDay": True, 
                "tipo": "intimidad"
            })
    return eventos

@app.delete("/eliminar-registro-privado/{registro_id}")
def eliminar_registro_privado(registro_id: int, db: Session = Depends(get_db)):
    registro = db.query(models.RegistroPersonal).filter(models.RegistroPersonal.id == registro_id).first()
    if not registro: 
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    db.delete(registro)
    db.commit()
    return {"mensaje": "Registro eliminado con éxito"}
from datetime import datetime, timedelta
import math
import statistics

def calcular_bloques_estudio(fecha_limite, horas_totales, dias_a_invertir, hora_inicio_pref, hora_fin_pref):
    bloques_generados = []
    
    # REGLA DE ORO: El día de la entrega se deja libre. 
    # El último día para estudiar es un día ANTES de la fecha límite.
    fecha_maxima_estudio = fecha_limite - timedelta(days=1)
    fecha_maxima_estudio = fecha_maxima_estudio.replace(hour=23, minute=59, second=59)

    hoy = datetime.now()

    if hoy > fecha_limite:
        return "Error: La fecha límite ya pasó."
    
    # Calculamos cuántas horas por día tocan
    horas_por_dia = horas_totales / dias_a_invertir
    ventana_diaria = hora_fin_pref - hora_inicio_pref

    if horas_por_dia > ventana_diaria:
        return f"Error: Quieres estudiar {horas_por_dia}h al día, pero tu ventana es de solo {ventana_diaria}h."

    dias_asignados = 0
    dia_iteracion = hoy

    while dias_asignados < dias_a_invertir:
        # Verificamos si nos pasamos del día máximo permitido (día antes de la entrega)
        if dia_iteracion.date() > fecha_maxima_estudio.date():
            return "Error: No hay suficientes días antes de la fecha límite (dejando el día de entrega libre)."
        
        inicio_bloque = dia_iteracion.replace(hour=hora_inicio_pref, minute=0, second=0, microsecond=0)
        
        # Si hoy ya pasó la hora preferida de inicio, saltamos a mañana
        if dia_iteracion.date() == hoy.date() and hoy.hour >= hora_inicio_pref:
            dia_iteracion += timedelta(days=1)
            continue

        # Usamos tu lógica de math.modf para separar horas y minutos exactos
        fraccion_minutos, horas_enteras = math.modf(horas_por_dia)
        fin_bloque = inicio_bloque + timedelta(hours=int(horas_enteras), minutes=int(fraccion_minutos * 60))
        
        bloques_generados.append({
            "inicio": inicio_bloque,
            "fin": fin_bloque
        })
        
        dias_asignados += 1
        dia_iteracion += timedelta(days=1)

    return bloques_generados

def predecir_siguiente_ciclo(fechas_inicio):
    # Si hay menos de 2 registros, no podemos calcular un intervalo. 
    # Asumimos el estándar médico de 28 días y margen de 2 días.
    if len(fechas_inicio) < 2:
        if len(fechas_inicio) == 1:
            return fechas_inicio[0] + timedelta(days=28), 2
        return None, None

    # Calculamos los intervalos en días entre cada periodo
    intervalos = [(fechas_inicio[i] - fechas_inicio[i-1]).days for i in range(1, len(fechas_inicio))]

    # Aplicamos la estadística matemática
    promedio_dias = statistics.mean(intervalos)
    
    # Si solo hay 2 fechas (1 intervalo), la desviación estándar da error, forzamos a 2 días
    desviacion = 2 if len(intervalos) == 1 else statistics.stdev(intervalos)
        
    # Calculamos la fecha del próximo ciclo sumando el promedio al último registro
    fecha_predicha = fechas_inicio[-1] + timedelta(days=int(promedio_dias))
    
    # Redondeamos la desviación para tener un margen en días enteros
    margen_dias = max(1, int(round(desviacion))) 
    

    return fecha_predicha, margen_dias
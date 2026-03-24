from datetime import datetime, timedelta
import math

def calcular_bloques_estudio(fecha_limite, horas_totales, dias_a_invertir, hora_inicio_pref, hora_fin_pref):
    """
    Calcula y distribuye los bloques de trabajo antes de la fecha límite.
    """
    hoy = datetime.now()
    bloques_generados = []
    
    # 1. ¿Cuántos días faltan realmente?
    dias_restantes = (fecha_limite - hoy).days
    
    if dias_restantes < dias_a_invertir:
        return "Error: No hay suficientes días antes de la entrega."

    # 2. Calcular cuántas horas por día (Distribución uniforme para empezar)
    # Por ejemplo: 10 horas totales en 5 días = 2 horas por día
    horas_por_dia = horas_totales / dias_a_invertir
    
    # 3. Restricción: Validar que las horas por día quepan en la ventana preferida
    ventana_disponible = hora_fin_pref - hora_inicio_pref
    if horas_por_dia > ventana_disponible:
        return f"Error: Quieres hacer {horas_por_dia}h diarias, pero tu ventana es de solo {ventana_disponible}h."

    # 4. Generar los bloques (Acomodar los horarios)
    # Seleccionamos los días (por ejemplo, los días inmediatamente anteriores a la entrega)
    for i in range(dias_a_invertir):
        # Retrocedemos desde la fecha límite
        dia_asignado = fecha_limite - timedelta(days=(i + 1))
        
        # Construimos la fecha y hora exacta de inicio y fin para ese día
        inicio_bloque = dia_asignado.replace(hour=hora_inicio_pref, minute=0, second=0)
        
        # Sumamos las horas calculadas (usando math.modf para separar horas y minutos si hay decimales)
        fraccion_minutos, horas_enteras = math.modf(horas_por_dia)
        fin_bloque = inicio_bloque + timedelta(hours=int(horas_enteras), minutes=int(fraccion_minutos * 60))
        
        bloques_generados.append({
            "inicio": inicio_bloque,
            "fin": fin_bloque
        })
        
    # Ordenamos cronológicamente
    bloques_generados.sort(key=lambda x: x["inicio"])
    
    return bloques_generados

# --- PRUEBA DEL ALGORITMO ---
if __name__ == "__main__":
    # Cambiamos la entrega para la próxima semana (ej. 3 de abril) para tener margen de tiempo
    proximo_viernes = datetime(2026, 4, 3, 23, 59) 
    
    print("Calculando horario de estudio...")
    # 10 horas totales, en 4 días, de 19:00 a 22:00 hrs
    mi_horario = calcular_bloques_estudio(proximo_viernes, 10, 4, 19, 22)
    
    # Validamos qué nos devolvió la función antes de imprimir
    if isinstance(mi_horario, str):
        # Si es un texto, significa que devolvió un mensaje de error
        print("⚠️ ALERTA:", mi_horario)
    else:
        # Si no es texto, es nuestra lista de bloques y la imprimimos
        print("✅ ¡Horario generado con éxito!")
        for bloque in mi_horario:
            print(f"Estudiar desde {bloque['inicio'].strftime('%Y-%m-%d %H:%M')} hasta {bloque['fin'].strftime('%Y-%m-%d %H:%M')}")
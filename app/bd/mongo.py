from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId


base = "FocusMeter"


def get_cliente_mongo():
    uri = (
        "mongodb+srv://Adrian_bd:Administrador31.@base.f1r4j33.mongodb.net/"
        "FocusMeter?retryWrites=true&w=majority&appName=Base"
    )
    return MongoClient(uri)


def insertar_registro_atencion(registro):
    cliente = get_cliente_mongo()
    coleccion = cliente[base]["registros_atencion"]
    return coleccion.insert_one(registro)


def get_info_horario_actual(id_aula):
    try:
        cliente = get_cliente_mongo()
        db = cliente[base]

        aulas = db["aulas"]
        horarios = db["horarios"]
        asignaturas = db["asignaturas"]
        docentes = db["docentes"]
        carreras = db["carreras"]

        aula = aulas.find_one({"_id": ObjectId(id_aula)})
        if not aula:
            return None

        ahora = datetime.now()
        hora_actual = ahora.time()

        dias_semana = {
            0: "Lunes",
            1: "Martes",
            2: "Miercoles",
            3: "Jueves",
            4: "Viernes",
            5: "Sabado",
            6: "Domingo"
        }
        dia_actual_es = dias_semana[ahora.weekday()]

        query = {
            "dia": dia_actual_es,
            "id_aula": id_aula
        }

        horarios_dia = horarios.find(query)

        for horario in horarios_dia:
            hora_inicio = datetime.strptime(horario["hora_inicio"], "%H:%M").time()
            hora_fin = datetime.strptime(horario["hora_fin"], "%H:%M").time()

            if hora_inicio <= hora_actual < hora_fin:
                asignatura = asignaturas.find_one(
                    {"_id": ObjectId(horario["id_asignatura"])}
                )
                if not asignatura:
                    continue

                docente = docentes.find_one(
                    {"_id": ObjectId(asignatura["id_docente"])}
                )
                carrera = carreras.find_one(
                    {"_id": ObjectId(asignatura["id_carrera"])}
                )

                return {
                    "aula": aula["nombre_aula"],
                    "docente": docente["nombre"] if docente else "",
                    "materia": asignatura["nombre_asignatura"],
                    "carrera": carrera["nombre_carrera"] if carrera else "",
                    "id_horario": str(horario["_id"]),
                    "hora_inicio": horario["hora_inicio"],
                    "hora_fin": horario["hora_fin"]
                }

        return None

    except Exception:
        return None

    finally:
        try:
            cliente.close()
        except Exception:
            pass

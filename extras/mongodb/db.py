from pymongo import MongoClient
from extras.mongodb.modelo import RegistroAtencion

def get_mongo_client(modo="atlas"):
    if modo == "local":
        uri = "mongodb://localhost:27017"
    elif modo == "atlas":
        uri = (
            "mongodb+srv://Adrian_bd:Administrador31.@base.f1r4j33.mongodb.net/"
            "FocusMeter?retryWrites=true&w=majority&appName=Base"
        )
    else:
        raise ValueError("modo debe ser 'local' o 'atlas'")

    client = MongoClient(uri, serverSelectionTimeoutMS=3000)
    client.admin.command("ping")
    return client


# --------------------------------------- INSERTS ---------------------------------------
def insertar_registro_atencion(registro_atencion: RegistroAtencion):
    documento = {
        "num_estudiantes_detectados": registro_atencion.num_estudiantes_detectados,
        "porcentaje_estimado_atencion": registro_atencion.porcentaje_estimado_atencion,
        "porcentajes_etiquetas": registro_atencion.porcentajes_etiquetas,
        "num_deteccion_etiquetas": registro_atencion.num_deteccion_etiquetas,
        "fecha_deteccion": registro_atencion.fecha_deteccion,
        "hora_detecccion": registro_atencion.hora_detecccion,
        "id_horario": registro_atencion.id_horario
    }

    try:
        client_local = get_mongo_client("local")
        db_local = client_local["FocusMeter"]
        col_local = db_local["registros_atencion"]

        resultado = col_local.insert_one(documento)
        documento["_id"] = resultado.inserted_id


        try:
            client_atlas = get_mongo_client("atlas")
            db_atlas = client_atlas["FocusMeter"]
            db_atlas["registros_atencion"].insert_one(documento)
        except Exception:
            print("Registrado en local, pero no se pudo registrar en MongoDB Atlas")

    except Exception:
        try:
            client_atlas = get_mongo_client("atlas")
            db_atlas = client_atlas["FocusMeter"]
            db_atlas["registros_atencion"].insert_one(documento)
        except Exception:
            print("No se pudo registrar ni en MongoDB local ni en MongoDB Atlas")


# --------------------------------------- CONSULTAS ---------------------------------------
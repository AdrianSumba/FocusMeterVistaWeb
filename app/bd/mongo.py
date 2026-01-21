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
    info_horario = {
        "aula": "",
        "docente": "",
        "materia": "",
        "carrera": "",
        "id_horario": "",
        "hora_inicio": "",
        "hora_fin": ""
    }

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
            "Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miercoles",
            "Thursday": "Jueves", "Friday": "Viernes",
            "Saturday": "Sabado", "Sunday": "Domingo"
        }

        dia_actual_es = dias_semana.get(ahora.strftime("%A"))
        if not dia_actual_es:
            return None

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

                info_horario["aula"] = aula["nombre_aula"]
                info_horario["docente"] = docente["nombre"] if docente else ""
                info_horario["materia"] = asignatura["nombre_asignatura"]
                info_horario["carrera"] = carrera["nombre_carrera"] if carrera else ""
                info_horario["id_horario"] = str(horario["_id"])
                info_horario["hora_inicio"] = horario["hora_inicio"]
                info_horario["hora_fin"] = horario["hora_fin"]

                return info_horario

        return None

    except Exception as e:
        print(f"Ocurrió un error al consultar MongoDB: {e}")
        return None



def _oid(valor):

    if valor is None:
        return None
    if isinstance(valor, ObjectId):
        return valor
    try:
        return ObjectId(str(valor))
    except Exception:
        return None


def _traducir_etiquetas(etiquetas):

    if not isinstance(etiquetas, dict):
        return {}

    mapa = {
        "attentive": "Atento",
        "Attentive": "Atento",
        "distracted": "Distraído",
        "Distracted": "Distraído",
        "sleepy": "Somnoliento",
        "Sleepy": "Somnoliento",
        "bullying": "Acoso escolar",
        "daydreaming": "Soñando despierto",
        "hand_rising": "Mano levantada",
        "human": "Persona",
        "phone_use": "Uso del teléfono",
    }

    traducidas = {}
    for k, v in etiquetas.items():
        nombre = mapa.get(k, mapa.get(str(k).strip(), str(k)))
        try:
            traducidas[nombre] = traducidas.get(nombre, 0) + int(v)
        except Exception:
            continue
    return traducidas


def listar_carreras(periodo_academico=None):

    cliente = get_cliente_mongo()
    db = cliente[base]

    if periodo_academico:
        ids = db["asignaturas"].distinct("id_carrera", {"periodo_academico": periodo_academico})
        carreras = list(
            db["carreras"].find({"_id": {"$in": [_oid(i) for i in ids if _oid(i)]}}, {"nombre_carrera": 1})
        )
    else:
        carreras = list(db["carreras"].find({}, {"nombre_carrera": 1}))

    return [
        {"id": str(c.get("_id")), "nombre": c.get("nombre_carrera", "")}
        for c in sorted(carreras, key=lambda x: x.get("nombre_carrera", ""))
    ]


def obtener_registros_atencion_enriquecidos(
    carrera_id=None,
    periodo_academico=None,
    fecha_desde=None,
    fecha_hasta=None,
    limite=None,
):

    cliente = get_cliente_mongo()
    db = cliente[base]

    match_registros = {}

    if fecha_desde or fecha_hasta:
        fr = {}
        if fecha_desde:
            fr["$gte"] = str(fecha_desde)
        if fecha_hasta:
            fr["$lte"] = str(fecha_hasta)
        match_registros["fecha_deteccion"] = fr

    pipeline = []
    if match_registros:
        pipeline.append({"$match": match_registros})


    pipeline.extend(
        [
            {
                "$addFields": {
                    "_horario_oid": {
                        "$convert": {
                            "input": "$id_horario",
                            "to": "objectId",
                            "onError": None,
                            "onNull": None,
                        }
                    }
                }
            },
            {
                "$lookup": {
                    "from": "horarios",
                    "localField": "_horario_oid",
                    "foreignField": "_id",
                    "as": "horario",
                }
            },
            {"$unwind": {"path": "$horario", "preserveNullAndEmptyArrays": True}},
        ]
    )


    pipeline.extend(
        [
            {
                "$addFields": {
                    "_asignatura_oid": {
                        "$convert": {
                            "input": "$horario.id_asignatura",
                            "to": "objectId",
                            "onError": None,
                            "onNull": None,
                        }
                    }
                }
            },
            {
                "$lookup": {
                    "from": "asignaturas",
                    "localField": "_asignatura_oid",
                    "foreignField": "_id",
                    "as": "asignatura",
                }
            },
            {"$unwind": {"path": "$asignatura", "preserveNullAndEmptyArrays": True}},
        ]
    )

 
    match_post = {}
    if periodo_academico:
        match_post["asignatura.periodo_academico"] = periodo_academico
    if carrera_id:
        carrera_oid = _oid(carrera_id)
        if carrera_oid:

            match_post["asignatura.id_carrera"] = str(carrera_oid)

    if match_post:
        pipeline.append({"$match": match_post})


    pipeline.extend(
        [
            {
                "$addFields": {
                    "_carrera_oid": {
                        "$convert": {
                            "input": "$asignatura.id_carrera",
                            "to": "objectId",
                            "onError": None,
                            "onNull": None,
                        }
                    }
                }
            },
            {
                "$lookup": {
                    "from": "carreras",
                    "localField": "_carrera_oid",
                    "foreignField": "_id",
                    "as": "carrera",
                }
            },
            {"$unwind": {"path": "$carrera", "preserveNullAndEmptyArrays": True}},
        ]
    )

    pipeline.append(
        {
            "$project": {
                "num_estudiantes_detectados": 1,
                "porcentaje_estimado_atencion": 1,
                "num_deteccion_etiquetas": 1,
                "fecha_deteccion": 1,
                "hora_detecccion": 1,
                "id_horario": 1,
                "horario.dia": 1,
                "horario.hora_inicio": 1,
                "horario.hora_fin": 1,
                "asignatura.nombre_asignatura": 1,
                "asignatura.periodo_academico": 1,
                "carrera.nombre_carrera": 1,
                "carrera._id": 1,
            }
        }
    )

    pipeline.append({"$sort": {"fecha_deteccion": -1, "hora_detecccion": -1}})
    if limite:
        pipeline.append({"$limit": int(limite)})

    resultados = list(db["registros_atencion"].aggregate(pipeline, allowDiskUse=True))

    normalizados = []
    for r in resultados:
        etiquetas = _traducir_etiquetas(r.get("num_deteccion_etiquetas", {}))
        normalizados.append(
            {
                "fecha_deteccion": r.get("fecha_deteccion"),
                "hora_detecccion": r.get("hora_detecccion"),
                "dia": (r.get("horario", {}) or {}).get("dia"),
                "hora_inicio": (r.get("horario", {}) or {}).get("hora_inicio"),
                "hora_fin": (r.get("horario", {}) or {}).get("hora_fin"),
                "carrera": (r.get("carrera", {}) or {}).get("nombre_carrera"),
                "carrera_id": str((r.get("carrera", {}) or {}).get("_id"))
                if (r.get("carrera", {}) or {}).get("_id")
                else None,
                "asignatura": (r.get("asignatura", {}) or {}).get("nombre_asignatura"),
                "periodo_academico": (r.get("asignatura", {}) or {}).get("periodo_academico"),
                "num_estudiantes_detectados": r.get("num_estudiantes_detectados", 0),
                "porcentaje_estimado_atencion": r.get("porcentaje_estimado_atencion", 0),
                "etiquetas": etiquetas,
            }
        )

    return normalizados

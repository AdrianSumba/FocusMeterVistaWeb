class Aula:
    def __init__(self,id,nombre_aula):
        self.id=id
        self.nombre_aula=nombre_aula

class Carrera:
    def __init__(self,id,nombre_carrera):
        self.id=id
        self.nombre_carrera=nombre_carrera

class Docente:
    def __init__(self,id,nombre):
        self.id=id
        self.nombre=nombre
        
class Asignatura:
    def __init__(self,id,nombre_asignatura, id_docente, id_carrera, periodo_academico, num_ciclo):
        self.id=id
        self.nombre_asignatura=nombre_asignatura
        self.id_docente=id_docente
        self.id_carrera=id_carrera
        self.periodo_academico=periodo_academico
        self.num_ciclo=num_ciclo
        
class Horario:
    def __init__(self,id,id_asignatura, id_aula, hora_inicio, hora_fin, dia):
        self.id=id
        self.id_asignatura=id_asignatura
        self.id_aula=id_aula
        self.hora_inicio=hora_inicio
        self.hora_fin=hora_fin
        self.dia=dia
        
class RegistroAtencion:
    def __init__(self,id,num_estudiantes_detectados, porcentaje_estimado_atencion, porcentajes_etiquetas,
                    num_detecciones_etiquetas, fecha_deteccion, hora_detecccion, id_horario):
        self.id=id
        self.num_estudiantes_detectados=num_estudiantes_detectados
        self.porcentaje_estimado_atencion=porcentaje_estimado_atencion
        self.porcentajes_etiquetas=porcentajes_etiquetas
        self.num_deteccion_etiquetas=num_detecciones_etiquetas
        self.fecha_deteccion=fecha_deteccion
        self.hora_detecccion=hora_detecccion
        self.id_horario=id_horario
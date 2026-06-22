from .models import Repuesto

class RepuestoRepository:
    @staticmethod
    def obtener_todos():
        return Repuesto.objects.all()

    @staticmethod
    def obtener_por_id(repuesto_id):
        return Repuesto.objects.get(id=repuesto_id)

    @staticmethod
    def crear(datos):
        return Repuesto.objects.create(**datos)

    @staticmethod
    def actualizar(repuesto_id, datos):
        repuesto = Repuesto.objects.filter(id=repuesto_id)
        if repuesto.exists():
            repuesto.update(**datos)
            return repuesto.first()
        return None

    @staticmethod
    def eliminar(repuesto_id):
        repuesto = Repuesto.objects.filter(id=repuesto_id)
        if repuesto.exists():
            repuesto.delete()
            return True
        return False
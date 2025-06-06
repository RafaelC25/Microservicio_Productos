from django.db import models

class Factura(models.Model):
    numero_factura = models.CharField(max_length=50, unique=True)
    fecha_emision = models.DateTimeField(auto_now_add=True)
    cliente = models.JSONField()  # Información del cliente
    items = models.JSONField()    # Lista de productos/servicios
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    impuestos = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=20, default='pendiente')
    metodo_pago = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"Factura {self.numero_factura} - {self.total}"


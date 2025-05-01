import unittest
import os
from src.utils.ticket_utils import generar_ticket_pdf

class TestTicketUtils(unittest.TestCase):
    def test_generar_ticket_venta(self):
        items = [{"nombre": "Producto 1", "cantidad": 2, "precio": 10.0}]
        header_data = {"Fecha": "2025-04-24", "Cliente": "Juan Pérez", "Venta ID": 123}
        filename = "test_ticket_venta.pdf"
        success = generar_ticket_pdf(filename, items, header_data, ticket_type="venta")
        self.assertTrue(success)
        self.assertTrue(os.path.exists(os.path.join("tickets", filename)))
        os.remove(os.path.join("tickets", filename))

    def test_generar_ticket_apartado(self):
        items = [{"nombre": "Producto 2", "cantidad": 1, "precio": 50.0}]
        header_data = {
            "Fecha Creación": "2025-04-24",
            "Fecha Vencimiento": "2025-05-24",
            "Cliente": "Ana López",
            "Apartado ID": 456,
            "Anticipo": 20.0
        }
        filename = "test_ticket_apartado.pdf"
        success = generar_ticket_pdf(filename, items, header_data, ticket_type="apartado")
        self.assertTrue(success)
        self.assertTrue(os.path.exists(os.path.join("tickets", filename)))
        os.remove(os.path.join("tickets", filename))

if __name__ == '__main__':
    unittest.main()

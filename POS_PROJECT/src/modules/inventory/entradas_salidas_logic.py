import logging
from datetime import datetime
from src.core.config.db_manager import DatabaseManager
from src.core.config.config import CONFIG
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os

logger = logging.getLogger(__name__)

class EntradasSalidasLogic:
    def __init__(self, db_manager=None, store_id=1):
        self.db_manager = db_manager or DatabaseManager()
        self.store_id = store_id
        logger.info(f"Inicializando EntradasSalidasLogic para tienda {self.store_id}")

    def _validate_sku(self, sku):
        """Valida si un SKU existe en la base de datos."""
        try:
            cursor = self.db_manager.get_cursor()
            cursor.execute("SELECT 1 FROM productos WHERE sku = ? AND store_id = ?", (sku, self.store_id))
            return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Error al validar SKU {sku} en tienda {self.store_id}: {str(e)}")
            return False

    def _validate_stock_for_salida(self, sku, cantidad):
        """Valida si hay suficiente stock para una salida."""
        try:
            cursor = self.db_manager.get_cursor()
            cursor.execute("SELECT inventario FROM productos WHERE sku = ? AND store_id = ?", (sku, self.store_id))
            result = cursor.fetchone()
            if not result:
                return False
            inventario = result['inventario']
            return inventario >= cantidad
        except Exception as e:
            logger.error(f"Error al validar stock para SKU {sku} en tienda {self.store_id}: {str(e)}")
            return False

    def _exportar_pdf(self, data, headers, x_positions, title, folio, output_dir):
        """Método auxiliar para exportar datos a PDF."""
        try:
            pdf_path = os.path.join(output_dir, f"{folio}.pdf")
            c = canvas.Canvas(pdf_path, pagesize=letter)
            width, height = letter

            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, height - 50, f"{title} - Folio: {folio}")
            c.setFont("Helvetica", 12)
            c.drawString(50, height - 70, f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            c.drawString(50, height - 90, f"Tienda ID: {self.store_id}")

            y = height - 120
            c.setFont("Helvetica-Bold", 10)
            for i, header in enumerate(headers):
                c.drawString(x_positions[i], y, header)
            y -= 20

            c.setFont("Helvetica", 10)
            for item in data:
                if y < 50:
                    c.showPage()
                    y = height - 50
                    c.setFont("Helvetica-Bold", 10)
                    for i, header in enumerate(headers):
                        c.drawString(x_positions[i], y, header)
                    y -= 20
                    c.setFont("Helvetica", 10)
                
                values = [str(item.get(header.lower(), '')) for header in headers]
                for i, value in enumerate(values):
                    c.drawString(x_positions[i], y, value)
                y -= 15

            c.save()
            logger.info(f"Historial exportado a PDF: {pdf_path} para tienda {self.store_id}")
            return pdf_path
        except Exception as e:
            logger.error(f"Error al exportar historial a PDF para tienda {self.store_id}: {str(e)}", exc_info=True)
            return None

    def registrar_movimiento(self, tipo, motivo, sku, cantidad, sucursal_origen=None, sucursal_destino=None):
        try:
            if cantidad <= 0:
                logger.error(f"Intento de registrar movimiento con cantidad inválida: {cantidad} en tienda {self.store_id}")
                return {
                    "success": False,
                    "message": "La cantidad debe ser mayor a 0",
                    "folio": None
                }

            if not self._validate_sku(sku):
                logger.error(f"SKU {sku} no existe en tienda {self.store_id}")
                return {
                    "success": False,
                    "message": f"El SKU {sku} no existe.",
                    "folio": None
                }

            if tipo == "salida" and not self._validate_stock_for_salida(sku, cantidad):
                logger.error(f"Stock insuficiente para salida de SKU {sku} (cantidad solicitada: {cantidad}) en tienda {self.store_id}")
                return {
                    "success": False,
                    "message": f"Stock insuficiente para el SKU {sku}.",
                    "folio": None
                }

            cursor = self.db_manager.get_cursor()
            folio = f"MOV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute("""
                INSERT INTO movimientos (tipo, motivo, sku, cantidad, fecha, folio, sucursal_origen, sucursal_destino, store_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (tipo, motivo, sku, cantidad, fecha, folio, sucursal_origen, sucursal_destino, self.store_id))

            if tipo == "entrada":
                cursor.execute("UPDATE productos SET inventario = inventario + ? WHERE sku = ? AND store_id = ?", (cantidad, sku, self.store_id))
            else:
                cursor.execute("UPDATE productos SET inventario = inventario - ? WHERE sku = ? AND store_id = ?", (cantidad, sku, self.store_id))

            self.db_manager.conn.commit()
            logger.info(f"Movimiento registrado: {tipo}, SKU: {sku}, Folio: {folio} para tienda {self.store_id}")
            return {
                "success": True,
                "message": "Movimiento registrado exitosamente",
                "folio": folio
            }
        except Exception as e:
            logger.error(f"Error al registrar movimiento para tienda {self.store_id}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": f"Error al registrar movimiento: {str(e)}",
                "folio": None
            }

    def registrar_nuevo_producto(self, sku, nombre, cantidad, precio):
        try:
            if cantidad <= 0:
                logger.error(f"Intento de registrar nuevo producto con cantidad inválida: {cantidad} en tienda {self.store_id}")
                return {
                    "success": False,
                    "message": "La cantidad debe ser mayor a 0",
                    "folio": None
                }

            if precio < 0:
                logger.error(f"Intento de registrar nuevo producto con precio inválido: {precio} en tienda {self.store_id}")
                return {
                    "success": False,
                    "message": "El precio no puede ser negativo",
                    "folio": None
                }

            cursor = self.db_manager.get_cursor()
            cursor.execute("SELECT 1 FROM productos WHERE sku = ? AND store_id = ?", (sku, self.store_id))
            if cursor.fetchone():
                logger.error(f"SKU {sku} ya existe en tienda {self.store_id}")
                return {
                    "success": False,
                    "message": f"El SKU {sku} ya existe.",
                    "folio": None
                }

            cursor.execute("""
                INSERT INTO productos (sku, nombre, inventario, precio, ventas, store_id)
                VALUES (?, ?, ?, ?, 0, ?)
            """, (sku, nombre, cantidad, precio, self.store_id))
            self.db_manager.conn.commit()

            result = self.registrar_movimiento("entrada", "nueva_mercancia", sku, cantidad)
            if not result["success"]:
                logger.error(f"Fallo al registrar movimiento de entrada para nuevo producto SKU {sku} en tienda {self.store_id}: {result['message']}")
                return {
                    "success": False,
                    "message": f"No se pudo registrar el movimiento de entrada: {result['message']}",
                    "folio": None
                }

            logger.info(f"Nuevo producto registrado: SKU {sku}, Nombre: {nombre} para tienda {self.store_id}")
            return {
                "success": True,
                "message": "Producto registrado exitosamente",
                "folio": result["folio"]
            }
        except Exception as e:
            logger.error(f"Error al registrar nuevo producto para tienda {self.store_id}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": f"Error al registrar nuevo producto: {str(e)}",
                "folio": None
            }

    def buscar_producto(self, sku):
        try:
            cursor = self.db_manager.get_cursor()
            cursor.execute("SELECT sku, nombre, inventario, precio FROM productos WHERE sku = ? AND store_id = ?", (sku, self.store_id))
            result = cursor.fetchone()
            product = dict(result) if result else None
            logger.info(f"Producto buscado: SKU {sku}, Encontrado: {bool(product)} para tienda {self.store_id}")
            return {
                "success": True,
                "message": "Producto buscado exitosamente",
                "product": product
            }
        except Exception as e:
            logger.error(f"Error al buscar producto para tienda {self.store_id}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": f"Error al buscar producto: {str(e)}",
                "product": None
            }

    def obtener_historial(self, tipo_filtro="Todos", limit=100):
        try:
            cursor = self.db_manager.get_cursor()
            query = "SELECT tipo, motivo, sku, cantidad, fecha, folio, sucursal_origen, sucursal_destino FROM movimientos WHERE store_id = ?"
            params = [self.store_id]
            if tipo_filtro != "Todos":
                query += " AND tipo = ?"
                params.append(tipo_filtro.lower())
            query += " ORDER BY fecha DESC LIMIT ?"
            params.append(limit)
            cursor.execute(query, params)
            historial = [dict(row) for row in cursor.fetchall()]
            logger.info(f"Historial obtenido: {len(historial)} movimientos para tienda {self.store_id}")
            return {
                "success": True,
                "message": "Historial obtenido exitosamente",
                "historial": historial
            }
        except Exception as e:
            logger.error(f"Error al obtener historial para tienda {self.store_id}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": f"Error al obtener historial: {str(e)}",
                "historial": []
            }

    def exportar_historial_pdf(self, movimientos, tipo_filtro, folio):
        headers = ["Tipo", "Motivo", "SKU", "Cantidad", "Fecha", "Folio", "Sucursal Origen", "Sucursal Destino"]
        x_positions = [50, 90, 150, 220, 260, 370, 450, 520]
        data = [
            {
                'tipo': movimiento['tipo'].capitalize(),
                'motivo': movimiento['motivo'].replace('_', ' ').capitalize(),
                'sku': movimiento['sku'],
                'cantidad': movimiento['cantidad'],
                'fecha': movimiento['fecha'],
                'folio': movimiento['folio'],
                'sucursal origen': movimiento['sucursal_origen'] or "N/A",
                'sucursal destino': movimiento['sucursal_destino'] or "N/A"
            } for movimiento in movimientos
        ]
        pdf_path = self._exportar_pdf(data, headers, x_positions, f"Reporte de Historial de Movimientos (Filtro: {tipo_filtro})", folio, "reportes/historial_movimientos")
        if pdf_path:
            return {
                "success": True,
                "message": "Historial exportado a PDF exitosamente",
                "pdf_path": pdf_path
            }
        else:
            return {
                "success": False,
                "message": "Error al exportar historial a PDF",
                "pdf_path": None
            }
import logging
from datetime import datetime
from src.core.config.db_manager import DatabaseManager
import json
import os
import csv
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import matplotlib.pyplot as plt
import numpy as np

logger = logging.getLogger(__name__)

class ReportesLogic:
    def __init__(self, db_manager=None, store_id=1):
        self.db_manager = db_manager or DatabaseManager()
        self.store_id = store_id
        logger.info(f"Inicializando ReportesLogic para tienda {self.store_id}")

    def _execute_query(self, query, params, fetch_all=True):
        """Método auxiliar para ejecutar consultas SQL y manejar errores."""
        try:
            cursor = self.db_manager.get_cursor()
            cursor.execute(query, params)
            if fetch_all:
                result = [dict(row) for row in cursor.fetchall()]
            else:
                result = cursor.fetchone()[0]
            return result
        except Exception as e:
            logger.error(f"Error al ejecutar consulta en tienda {self.store_id}: {str(e)}")
            raise

    def obtener_ventas(self, fecha_desde, fecha_hasta, metodo_pago, cliente=None, offset=0, limit=20):
        query = """
            SELECT v.id, v.user_id, v.metodo_pago, v.fecha, v.total, c.nombre_completo
            FROM ventas v
            LEFT JOIN clientes c ON v.id_cliente = c.id
            WHERE v.fecha BETWEEN ? AND ? AND v.store_id = ?
        """
        params = [fecha_desde, fecha_hasta, self.store_id]
        if metodo_pago != "Todos":
            query += " AND v.metodo_pago = ?"
            params.append(metodo_pago)
        if cliente:
            query += " AND c.nombre_completo LIKE ?"
            params.append(f"%{cliente}%")
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        result = self._execute_query(query, params)
        logger.info(f"Ventas obtenidas para tienda {self.store_id}: {len(result)} registros")
        return result

    def contar_ventas(self, fecha_desde, fecha_hasta, metodo_pago, cliente=None):
        query = """
            SELECT COUNT(*)
            FROM ventas v
            LEFT JOIN clientes c ON v.id_cliente = c.id
            WHERE v.fecha BETWEEN ? AND ? AND v.store_id = ?
        """
        params = [fecha_desde, fecha_hasta, self.store_id]
        if metodo_pago != "Todos":
            query += " AND v.metodo_pago = ?"
            params.append(metodo_pago)
        if cliente:
            query += " AND c.nombre_completo LIKE ?"
            params.append(f"%{cliente}%")
        count = self._execute_query(query, params, fetch_all=False)
        logger.info(f"Total de ventas contadas para tienda {self.store_id}: {count}")
        return count

    def obtener_inventario(self, stock_bajo=False, offset=0, limit=20):
        query = "SELECT sku, nombre, inventario, ventas FROM productos WHERE store_id = ?"
        params = [self.store_id]
        if stock_bajo:
            query += " AND inventario < 5"
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        result = self._execute_query(query, params)
        logger.info(f"Inventario obtenido para tienda {self.store_id}: {len(result)} productos")
        return result

    def contar_inventario(self, stock_bajo=False):
        query = "SELECT COUNT(*) FROM productos WHERE store_id = ?"
        params = [self.store_id]
        if stock_bajo:
            query += " AND inventario < 5"
        count = self._execute_query(query, params, fetch_all=False)
        logger.info(f"Total de productos contados para tienda {self.store_id}: {count}")
        return count

    def obtener_apartados(self, estado, cliente=None, fecha_desde=None, fecha_hasta=None, offset=0, limit=20):
        query = """
            SELECT a.id, c.nombre_completo, a.productos, a.anticipo, a.fecha_creacion, a.fecha_vencimiento, a.estado
            FROM apartados a
            LEFT JOIN clientes c ON a.id_cliente = c.id
            WHERE a.estado = ? AND a.store_id = ?
        """
        params = [estado, self.store_id]
        if cliente:
            query += " AND c.nombre_completo LIKE ?"
            params.append(f"%{cliente}%")
        if fecha_desde and fecha_hasta:
            query += " AND a.fecha_creacion BETWEEN ? AND ?"
            params.extend([fecha_desde, fecha_hasta])
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        result = self._execute_query(query, params)
        logger.info(f"Apartados obtenidos para tienda {self.store_id}: {len(result)} registros")
        return result

    def contar_apartados(self, estado, cliente=None, fecha_desde=None, fecha_hasta=None):
        query = """
            SELECT COUNT(*)
            FROM apartados a
            LEFT JOIN clientes c ON a.id_cliente = c.id
            WHERE a.estado = ? AND a.store_id = ?
        """
        params = [estado, self.store_id]
        if cliente:
            query += " AND c.nombre_completo LIKE ?"
            params.append(f"%{cliente}%")
        if fecha_desde and fecha_hasta:
            query += " AND a.fecha_creacion BETWEEN ? AND ?"
            params.extend([fecha_desde, fecha_hasta])
        count = self._execute_query(query, params, fetch_all=False)
        logger.info(f"Total de apartados contados para tienda {self.store_id}: {count}")
        return count

    def obtener_clientes_frecuentes(self, offset=0, limit=20):
        query = """
            SELECT c.nombre_completo, COUNT(v.id) as total_compras, SUM(v.total) as total_gastado
            FROM ventas v
            LEFT JOIN clientes c ON v.id_cliente = c.id
            WHERE c.nombre_completo IS NOT NULL AND v.store_id = ?
            GROUP BY c.id, c.nombre_completo
            ORDER BY total_compras DESC
            LIMIT ? OFFSET ?
        """
        result = self._execute_query(query, (self.store_id, limit, offset))
        logger.info(f"Clientes frecuentes obtenidos para tienda {self.store_id}: {len(result)} registros")
        return result

    def contar_clientes_frecuentes(self):
        query = """
            SELECT COUNT(DISTINCT c.id)
            FROM ventas v
            LEFT JOIN clientes c ON v.id_cliente = c.id
            WHERE c.nombre_completo IS NOT NULL AND v.store_id = ?
        """
        count = self._execute_query(query, (self.store_id,), fetch_all=False)
        logger.info(f"Total de clientes frecuentes contados para tienda {self.store_id}: {count}")
        return count

    def obtener_productos_mas_vendidos(self, offset=0, limit=20):
        query = """
            SELECT p.sku, p.nombre, p.ventas, p.inventario
            FROM productos p
            WHERE p.store_id = ?
            ORDER BY p.ventas DESC
            LIMIT ? OFFSET ?
        """
        result = self._execute_query(query, (self.store_id, limit, offset))
        logger.info(f"Productos más vendidos obtenidos para tienda {self.store_id}: {len(result)} registros")
        return result

    def contar_productos_mas_vendidos(self):
        query = "SELECT COUNT(*) FROM productos WHERE store_id = ?"
        count = self._execute_query(query, (self.store_id,), fetch_all=False)
        logger.info(f"Total de productos contados para tienda {self.store_id}: {count}")
        return count

    def obtener_ventas_por_dia(self, fecha_desde, fecha_hasta):
        query = """
            SELECT DATE(v.fecha) as fecha, COUNT(v.id) as total_ventas, SUM(v.total) as total_gastado
            FROM ventas v
            WHERE v.fecha BETWEEN ? AND ? AND v.store_id = ?
            GROUP BY DATE(v.fecha)
            ORDER BY DATE(v.fecha)
        """
        result = self._execute_query(query, (fecha_desde, fecha_hasta, self.store_id))
        logger.info(f"Ventas por día obtenidas para tienda {self.store_id}: {len(result)} registros")
        return result

    def generar_grafico_ventas_por_dia(self, ventas_por_dia, fecha_desde, fecha_hasta, folio):
        try:
            output_dir = os.path.join("reportes", "analisis", "graficos")
            os.makedirs(output_dir, exist_ok=True)
            png_path = os.path.join(output_dir, f"{folio}_ventas_por_dia.png")

            fechas = [venta['fecha'] for venta in ventas_por_dia]
            totales = [float(venta['total_gastado']) for venta in ventas_por_dia]

            plt.figure(figsize=(8, 6))
            plt.plot(fechas, totales, marker='o', color='b', label='Total Gastado')
            plt.title(f"Ventas por Día ({fecha_desde} a {fecha_hasta}) - Tienda {self.store_id}")
            plt.xlabel('Fecha')
            plt.ylabel('Total Gastado ($)')
            plt.xticks(rotation=45)
            plt.grid(True)
            plt.legend()
            plt.tight_layout()
            plt.savefig(png_path)
            plt.close()  # Cerrar explícitamente el gráfico
            logger.info(f"Gráfico de ventas por día generado para tienda {self.store_id}: {png_path}")
            return png_path
        except Exception as e:
            logger.error(f"Error al generar gráfico de ventas por día para tienda {self.store_id}: {str(e)}")
            raise

    def generar_grafico_productos_vendidos(self, productos, folio):
        try:
            output_dir = os.path.join("reportes", "analisis", "graficos")
            os.makedirs(output_dir, exist_ok=True)
            png_path = os.path.join(output_dir, f"{folio}_productos_vendidos.png")

            nombres = [producto['nombre'] for producto in productos]
            ventas = [producto['ventas'] for producto in productos]

            plt.figure(figsize=(8, 6))
            plt.bar(nombres, ventas, color='g')
            plt.title(f"Productos Más Vendidos - Tienda {self.store_id}")
            plt.xlabel('Producto')
            plt.ylabel('Ventas')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.savefig(png_path)
            plt.close()  # Cerrar explícitamente el gráfico
            logger.info(f"Gráfico de productos más vendidos generado para tienda {self.store_id}: {png_path}")
            return png_path
        except Exception as e:
            logger.error(f"Error al generar gráfico de productos más vendidos para tienda {self.store_id}: {str(e)}")
            raise

    def _exportar_pdf(self, data, headers, x_positions, title, folio, output_dir, filename_prefix):
        """Método auxiliar para exportar datos a PDF."""
        pdf_path = os.path.join(output_dir, f"{folio}.pdf")
        c = canvas.Canvas(pdf_path, pagesize=letter)
        width, height = letter

        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, f"{title} - Folio: {folio} - Tienda {self.store_id}")
        c.setFont("Helvetica", 12)
        c.drawString(50, height - 70, f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        y = height - 100
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
        logger.info(f"Reporte exportado a PDF para tienda {self.store_id}: {pdf_path}")
        return pdf_path

    def _exportar_csv(self, data, headers, output_dir, filename_prefix, folio):
        """Método auxiliar para exportar datos a CSV."""
        csv_path = os.path.join(output_dir, f"{folio}.csv")
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            for item in data:
                writer.writerow({header: item.get(header.lower(), '') for header in headers})
        logger.info(f"Reporte exportado a CSV para tienda {self.store_id}: {csv_path}")
        return csv_path

    def exportar_ventas_pdf(self, ventas, fecha_desde, fecha_hasta, folio):
        headers = ["ID", "Usuario", "Cliente", "Método Pago", "Fecha", "Total"]
        x_positions = [50, 90, 140, 240, 320, 420]
        data = [
            {
                'id': venta['id'],
                'usuario': venta['user_id'],
                'cliente': venta['nombre_completo'] if venta['nombre_completo'] else "Sin cliente",
                'método pago': venta['metodo_pago'],
                'fecha': venta['fecha'],
                'total': f"${venta['total']:.2f}"
            } for venta in ventas
        ]
        return self._exportar_pdf(data, headers, x_positions, f"Reporte de Ventas ({fecha_desde} a {fecha_hasta})", folio, "reportes/ventas", "ventas")

    def exportar_ventas_csv(self, ventas, fecha_desde, fecha_hasta, folio):
        headers = ['ID', 'Usuario', 'Cliente', 'Método Pago', 'Fecha', 'Total']
        data = [
            {
                'id': venta['id'],
                'usuario': venta['user_id'],
                'cliente': venta['nombre_completo'] if venta['nombre_completo'] else "Sin cliente",
                'método pago': venta['metodo_pago'],
                'fecha': venta['fecha'],
                'total': f"${venta['total']:.2f}"
            } for venta in ventas
        ]
        return self._exportar_csv(data, headers, "reportes/ventas", "ventas", folio)

    def exportar_inventario_pdf(self, productos, folio):
        headers = ["SKU", "Nombre", "Inventario", "Ventas"]
        x_positions = [50, 100, 300, 350]
        data = [
            {
                'sku': producto['sku'],
                'nombre': producto['nombre'],
                'inventario': producto['inventario'],
                'ventas': producto['ventas']
            } for producto in productos
        ]
        return self._exportar_pdf(data, headers, x_positions, "Reporte de Inventario", folio, "reportes/inventario", "inventario")

    def exportar_inventario_csv(self, productos, folio):
        headers = ['SKU', 'Nombre', 'Inventario', 'Ventas']
        data = [
            {
                'sku': producto['sku'],
                'nombre': producto['nombre'],
                'inventario': producto['inventario'],
                'ventas': producto['ventas']
            } for producto in productos
        ]
        return self._exportar_csv(data, headers, "reportes/inventario", "inventario", folio)

    def exportar_apartados_pdf(self, apartados, estado, folio):
        headers = ["ID", "Cliente", "Productos", "Anticipo", "Fecha Creación", "Fecha Vencimiento", "Estado"]
        x_positions = [50, 90, 150, 300, 350, 450, 500]
        data = [
            {
                'id': apartado['id'],
                'cliente': apartado['nombre_completo'],
                'productos': ", ".join([f"{item['sku']} (x{item['cantidad']})" for item in json.loads(apartado['productos'])]),
                'anticipo': f"${apartado['anticipo']:.2f}",
                'fecha creación': apartado['fecha_creacion'],
                'fecha vencimiento': apartado['fecha_vencimiento'],
                'estado': apartado['estado']
            } for apartado in apartados
        ]
        return self._exportar_pdf(data, headers, x_positions, f"Reporte de Apartados (Estado: {estado.capitalize()})", folio, "reportes/apartados", "apartados")

    def exportar_apartados_csv(self, apartados, estado, folio):
        headers = ['ID', 'Cliente', 'Productos', 'Anticipo', 'Fecha Creación', 'Fecha Vencimiento', 'Estado']
        data = [
            {
                'id': apartado['id'],
                'cliente': apartado['nombre_completo'],
                'productos': ", ".join([f"{item['sku']} (x{item['cantidad']})" for item in json.loads(apartado['productos'])]),
                'anticipo': apartado['anticipo'],
                'fecha creación': apartado['fecha_creacion'],
                'fecha vencimiento': apartado['fecha_vencimiento'],
                'estado': apartado['estado']
            } for apartado in apartados
        ]
        return self._exportar_csv(data, headers, "reportes/apartados", "apartados", folio)

    def exportar_clientes_frecuentes_pdf(self, clientes, folio):
        headers = ["Cliente", "Total Compras", "Total Gastado"]
        x_positions = [50, 200, 300]
        data = [
            {
                'cliente': cliente['nombre_completo'],
                'total compras': cliente['total_compras'],
                'total gastado': f"${cliente['total_gastado']:.2f}"
            } for cliente in clientes
        ]
        return self._exportar_pdf(data, headers, x_positions, "Reporte de Clientes Frecuentes", folio, "reportes/analisis", "clientes_frecuentes")

    def exportar_productos_vendidos_pdf(self, productos, folio):
        headers = ["SKU", "Nombre", "Ventas", "Inventario"]
        x_positions = [50, 100, 300, 350]
        data = [
            {
                'sku': producto['sku'],
                'nombre': producto['nombre'],
                'ventas': producto['ventas'],
                'inventario': producto['inventario']
            } for producto in productos
        ]
        return self._exportar_pdf(data, headers, x_positions, "Reporte de Productos Más Vendidos", folio, "reportes/analisis", "productos_vendidos")

    def exportar_analisis_csv(self, clientes, productos, folio):
        try:
            output_dir = os.path.join("reportes", "analisis")
            os.makedirs(output_dir, exist_ok=True)
            csv_path = os.path.join(output_dir, f"{folio}.csv")
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                if clientes:
                    writer.writerow([f"Reporte de Clientes Frecuentes - Tienda {self.store_id}"])
                    writer.writerow(["Cliente", "Total Compras", "Total Gastado"])
                    for cliente in clientes:
                        writer.writerow([
                            cliente['nombre_completo'],
                            cliente['total_compras'],
                            f"${cliente['total_gastado']:.2f}"
                        ])
                if clientes and productos:
                    writer.writerow([])
                if productos:
                    writer.writerow([f"Reporte de Productos Más Vendidos - Tienda {self.store_id}"])
                    writer.writerow(["SKU", "Nombre", "Ventas", "Inventario"])
                    for producto in productos:
                        writer.writerow([
                            producto['sku'],
                            producto['nombre'],
                            producto['ventas'],
                            producto['inventario']
                        ])
            logger.info(f"Reporte de análisis exportado a CSV para tienda {self.store_id}: {csv_path}")
            return csv_path
        except Exception as e:
            logger.error(f"Error al exportar análisis a CSV para tienda {self.store_id}: {str(e)}")
            raise

    def generar_reporte_analisis_datos(self, fecha_desde, fecha_hasta, folio):
        try:
            output_dir = os.path.join("reportes", "analisis")
            os.makedirs(output_dir, exist_ok=True)
            md_path = os.path.join(output_dir, f"{folio}_reporte_datos.md")

            # Recolectar datos
            ventas = self.obtener_ventas(fecha_desde, fecha_hasta, "Todos", None, offset=0, limit=None)
            clientes_frecuentes = self.obtener_clientes_frecuentes(limit=5)
            productos_vendidos = self.obtener_productos_mas_vendidos(limit=5)
            apartados_activos = self.contar_apartados("activo", fecha_desde=fecha_desde, fecha_hasta=fecha_hasta)
            apartados_vencidos = self.contar_apartados("vencido", fecha_desde=fecha_desde, fecha_hasta=fecha_hasta)
            apartados_completados = self.contar_apartados("completado", fecha_desde=fecha_desde, fecha_hasta=fecha_hasta)
            apartados_cancelados = self.contar_apartados("cancelado", fecha_desde=fecha_desde, fecha_hasta=fecha_hasta)

            # Calcular métricas de ventas
            total_ventas = len(ventas)
            total_gastado = sum(float(venta['total']) for venta in ventas)
            dias = (datetime.strptime(fecha_hasta, "%Y-%m-%d") - datetime.strptime(fecha_desde, "%Y-%m-%d")).days + 1
            promedio_diario = total_gastado / dias if dias > 0 else 0
            metodos_pago = {}
            for venta in ventas:
                metodo = venta['metodo_pago']
                metodos_pago[metodo] = metodos_pago.get(metodo, 0) + 1
            metodo_mas_usado = max(metodos_pago.items(), key=lambda x: x[1], default=("Ninguno", 0))[0]

            # Generar contenido del archivo Markdown con comillas simples para evitar problemas
            contenido = f"""
# Reporte de Análisis de Datos - Proyecto POS - Tienda {self.store_id}

**Fecha de Generación:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Rango de Datos Analizados:** {fecha_desde} a {fecha_hasta}

**Folio:** {folio}

## Resumen de Ventas

- **Total de Ventas:** {total_ventas}
- **Total Gastado:** ${total_gastado:.2f}
- **Promedio Diario:** ${promedio_diario:.2f} (en {dias} días)
- **Método de Pago Más Usado:** {metodo_mas_usado}

## Clientes Frecuentes (Top 5)

| Cliente | Total Compras | Total Gastado |
|---------|---------------|---------------|
"""
            for cliente in clientes_frecuentes:
                contenido += f"| {cliente['nombre_completo']} | {cliente['total_compras']} | ${cliente['total_gastado']:.2f} |\n"

            contenido += """
## Productos Más Vendidos (Top 5)

| SKU | Nombre | Ventas | Inventario Actual |
|-----|--------|--------|-------------------|
"""
            for producto in productos_vendidos:
                contenido += f"| {producto['sku']} | {producto['nombre']} | {producto['ventas']} | {producto['inventario']} |\n"

            contenido += f"""
## Apartados

- **Activos:** {apartados_activos}
- **Vencidos:** {apartados_vencidos}
- **Completados:** {apartados_completados}
- **Cancelados:** {apartados_cancelados}

## Metas y Mejoras Futuras

- **Ventas:** ¿Podemos aumentar las ventas identificando patrones en los métodos de pago más usados?
- **Clientes:** ¿Cómo podemos fidelizar más a estos clientes frecuentes?
- **Productos:** ¿Necesitamos reabastecer alguno de estos productos más vendidos? ¿Hay productos con bajas ventas que necesiten promoción?
- **Apartados:** ¿Podemos optimizar el manejo de apartados vencidos o cancelados?

---

**Notas para Análisis Futuro:**  
Este archivo contiene métricas clave del sistema POS para analizar tendencias y planificar mejoras. Por favor, agrega cualquier comentario o dato adicional antes de que lo revisemos juntos.
"""

            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(contenido)
            logger.info(f"Reporte de análisis de datos generado para tienda {self.store_id}: {md_path}")
            return md_path
        except Exception as e:
            logger.error(f"Error al generar reporte de análisis de datos para tienda {self.store_id}: {str(e)}")
            raise
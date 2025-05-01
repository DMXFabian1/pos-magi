from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import os
from datetime import datetime

def generar_ticket_pdf(filename, items, header_data, ticket_type="venta", output_dir="tickets"):
    """
    Genera un ticket en formato PDF para ventas o apartados.

    Args:
        filename (str): Nombre del archivo PDF (sin ruta).
        items (list): Lista de ítems con formato [{"nombre": str, "cantidad": int, "precio": float}].
        header_data (dict): Datos del encabezado (e.g., {"Fecha": str, "Cliente": str, "Apartado ID": int}).
        ticket_type (str): Tipo de ticket ("venta" o "apartado"). Por defecto: "venta".
        output_dir (str): Directorio donde se guardará el PDF. Por defecto: "tickets".

    Returns:
        bool: True si el PDF se generó correctamente, False en caso de error.
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
        styles = getSampleStyleSheet()
        style_normal = styles["Normal"]
        style_heading = styles["Heading1"]
        style_title = styles["Title"]
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        story = []
        story.append(Paragraph("Ticket de Venta" if ticket_type == "venta" else "Ticket de Apartado", style_title))
        story.append(Spacer(1, 12))
        for key, value in header_data.items():
            story.append(Paragraph(f"{key}: {value}", style_normal))
        story.append(Spacer(1, 12))
        story.append(Paragraph("-" * 40, style_normal))
        story.append(Spacer(1, 12))
        total = 0
        for item in items:
            nombre = item.get("nombre", "Producto desconocido")
            cantidad = item.get("cantidad", 0)
            precio = item.get("precio", 0)
            subtotal = cantidad * precio
            total += subtotal
            story.append(Paragraph(f"{nombre} x{cantidad} - ${subtotal:.2f}", style_normal))
            story.append(Spacer(1, 6))
        story.append(Paragraph("-" * 40, style_normal))
        story.append(Paragraph(f"Total: ${total:.2f}", style_heading))
        story.append(Spacer(1, 12))
        if ticket_type == "apartado":
            anticipo = header_data.get("Anticipo", 0)
            story.append(Paragraph(f"Anticipo pagado: ${anticipo:.2f}", style_normal))
            story.append(Paragraph(f"Saldo pendiente: ${(total - anticipo):.2f}", style_normal))
        doc.build(story)
        return True
    except Exception as e:
        print(f"Error al generar ticket PDF: {e}")
        return False
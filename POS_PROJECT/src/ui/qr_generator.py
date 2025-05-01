# qr_generator.py
import qrcode
import logging
import os
from PIL import Image, ImageDraw, ImageFont, ImageTk
from src.core.utils.utils import sanitize_filename
from datetime import datetime
import shutil
import io
import win32clipboard
import tkinter as tk
from tkinter import messagebox
import win32print
import win32ui
from PIL import ImageWin

logger = logging.getLogger(__name__)

def validate_string(arg, name, allow_empty=False):
    if not isinstance(arg, str):
        raise ValueError(f"El argumento '{name}' debe ser una cadena.")
    if not allow_empty and not arg:
        raise ValueError(f"El argumento '{name}' no puede estar vacío.")

def adjust_font_size(draw, text, font_path, initial_size, max_width):
    font_size = initial_size
    while font_size > 10:
        try:
            font = ImageFont.truetype(font_path, font_size)
        except IOError:
            font = ImageFont.load_default()
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        if text_width <= max_width:
            return font
        font_size -= 2
    try:
        return ImageFont.truetype(font_path, 10)
    except IOError:
        return ImageFont.load_default()

def generar_qr(data, output_path):
    try:
        validate_string(data, "data")
        validate_string(output_path, "output_path")
        if os.path.exists(output_path):
            os.remove(output_path)
            logger.debug(f"Archivo existente eliminado: {output_path}")
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=6,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(output_path)
        logger.info(f"QR generado y guardado exitosamente en: {output_path}")
        return True
    except ValueError as ve:
        logger.error(f"Error de validación en generar_qr: {str(ve)}")
        raise
    except IOError as ioe:
        logger.error(f"Error de E/S al generar o guardar QR en {output_path}: {str(ioe)}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado al generar o guardar QR en {output_path}: {str(e)}")
        raise

def generar_etiqueta(sku, escuela, nivel_educativo, nombre, talla, genero, qr_path, output_path):
    try:
        validate_string(sku, "sku")
        validate_string(escuela, "escuela", allow_empty=True)
        validate_string(nivel_educativo, "nivel_educativo", allow_empty=True)
        validate_string(nombre, "nombre")
        validate_string(talla, "talla", allow_empty=True)
        validate_string(genero, "genero", allow_empty=True)
        validate_string(qr_path, "qr_path")
        validate_string(output_path, "output_path")
        if not os.path.exists(qr_path):
            raise IOError(f"El archivo QR no existe en la ruta especificada: {qr_path}")
        label_width = 992
        label_height = 271
        label_image = Image.new("1", (label_width, label_height), 1)
        draw = ImageDraw.Draw(label_image)
        qr_image = Image.open(qr_path)
        qr_size = 231
        qr_image = qr_image.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
        qr_image = qr_image.convert("1")
        qr_x = label_width - qr_size - 20
        qr_y = (label_height - qr_size) // 2
        label_image.paste(qr_image, (qr_x, qr_y))
        font_path = "arial.ttf"
        initial_font_size = 30
        text_x = 20
        line_spacing = 10
        max_text_width = qr_x - 40
        fields = []
        if escuela:
            if nivel_educativo:
                fields.append(f"{nivel_educativo} - {escuela}")
            else:
                fields.append(escuela)
        fields.append(nombre if nombre else "Sin Nombre")
        fields.append(f"Talla: {talla}" if talla else "Sin Talla")
        if genero:
            fields.append(genero)
        fields.append(sku)
        line_height = 40
        text_height = len(fields) * line_height + (len(fields) - 1) * line_spacing
        text_y = (label_height - text_height) // 2
        for field in fields:
            font = adjust_font_size(draw, field, font_path, initial_font_size, max_text_width)
            draw.text((text_x, text_y), field, font=font, fill=0)
            text_y += line_height + line_spacing
        label_image.save(output_path, "PNG")
        logger.info(f"Etiqueta generada y guardada exitosamente en: {output_path}")
        return True
    except ValueError as ve:
        logger.error(f"Error de validación en generar_etiqueta: {str(ve)}")
        raise
    except IOError as ioe:
        logger.error(f"Error de E/S al generar o guardar la etiqueta en {output_path}: {str(ioe)}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado al generar o guardar la etiqueta en {output_path}: {str(e)}")
        raise

def generate_product_labels(sku, escuela, nivel_educativo, nombre, talla, genero, base_dir, tipo_prenda, tipo_pieza):
    """Genera códigos QR y etiquetas para un producto, manejando la creación de directorios y nombres de archivo."""
    folder_name = f"{nombre}_{tipo_prenda}_{tipo_pieza}"
    folder_path = os.path.join(base_dir, folder_name.replace("/", "_").replace("\\", "_"))
    os.makedirs(folder_path, exist_ok=True)
    sanitized_talla = sanitize_filename(talla) if talla else "SinTalla"
    talla_folder = os.path.join(folder_path, sanitized_talla)
    os.makedirs(talla_folder, exist_ok=True)
    qr_filename = f"{sku}_{nombre}_{sanitized_talla}_qr.png"
    label_filename = f"{sku}_{nombre}_{sanitized_talla}_label.png"
    qr_path_absolute = os.path.join(talla_folder, qr_filename)
    label_path_absolute = os.path.join(talla_folder, label_filename)
    qr_path_relative = os.path.join("Mis codigos", folder_name.replace("/", "_").replace("\\", "_"), sanitized_talla, qr_filename)
    label_path_relative = os.path.join("Mis codigos", folder_name.replace("/", "_").replace("\\", "_"), sanitized_talla, label_filename)
    generar_qr(sku, qr_path_absolute)
    generar_etiqueta(sku, escuela, nivel_educativo, nombre, talla, genero, qr_path_absolute, label_path_absolute)
    return qr_path_relative, label_path_relative

class QRGenerator:
    def __init__(self, root_folder, db_manager, manager, store_id=1):
        self.root_folder = root_folder
        self.db_manager = db_manager
        self.manager = manager
        self.store_id = store_id
        self.current_label_path = None
        logger.info(f"Inicializando QRGenerator para tienda {self.store_id}")

    def copiar_qr(self):
        """Copia el código QR de los productos seleccionados al portapapeles."""
        selected_items = self.manager.ui.tree.selection()
        if not selected_items:
            messagebox.showwarning("Advertencia", "Selecciona al menos un producto.")
            return
        try:
            with self.db_manager as db:
                cursor = db.get_cursor()
                for item in selected_items:
                    sku = self.manager.ui.tree.item(item)["values"][1].upper()
                    cursor.execute("SELECT qr_path FROM productos WHERE sku = ? AND store_id = ?", (sku, self.store_id))
                    result = cursor.fetchone()
                    if result:
                        qr_path = os.path.join(self.root_folder, result[0])
                        if os.path.exists(qr_path):
                            img = Image.open(qr_path)
                            output = io.BytesIO()
                            img.convert("RGB").save(output, format="BMP")
                            data = output.getvalue()[14:]
                            output.close()
                            win32clipboard.OpenClipboard()
                            win32clipboard.EmptyClipboard()
                            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
                            win32clipboard.CloseClipboard()
                            logger.info(f"Etiqueta de {sku} copiada al portapapeles en tienda {self.store_id}.")
                            messagebox.showinfo("Éxito", f"Etiqueta de {sku} copiada al portapapeles.")
                        else:
                            logger.error(f"No se encontró la etiqueta para {sku} en {qr_path} en tienda {self.store_id}.")
                            messagebox.showerror("Error", f"No se encontró la etiqueta para {sku}.")
                    else:
                        logger.error(f"No se encontró el producto con SKU {sku} en tienda {self.store_id}.")
                        messagebox.showerror("Error", f"No se encontró el producto con SKU {sku}.")
        except Exception as e:
            logger.error(f"Error al copiar la etiqueta en tienda {self.store_id}: {str(e)}")
            messagebox.showerror("Error", f"No se pudo copiar la etiqueta: {str(e)}")

    def regenerate_label(self, sku, entries, qr_label):
        """Regenera la etiqueta QR para un producto."""
        try:
            nombre = entries["nombre"].get().strip()
            escuela = entries["escuela"].get().strip()
            nivel_educativo = entries["nivel_educativo"].get().strip()
            talla = entries["talla"].get().strip()
            genero = entries["genero"].get().strip()
            tipo_prenda = entries["tipo_prenda"].get().strip()
            tipo_pieza = entries["tipo_pieza"].get().strip()

            if not nombre:
                messagebox.showerror("Error", "El campo Nombre es requerido para generar la etiqueta.")
                return

            qr_path_relative, label_path_relative = generate_product_labels(
                sku, escuela, nivel_educativo, nombre, talla, genero, 
                os.path.join(self.root_folder, "Mis codigos"), tipo_prenda, tipo_pieza
            )

            with self.db_manager as db:
                cursor = db.get_cursor()
                cursor.execute("UPDATE productos SET qr_path = ? WHERE sku = ? AND store_id = ?", (label_path_relative, sku, self.store_id))
                self.db_manager.commit()

            label_path_absolute = os.path.join(self.root_folder, label_path_relative)
            img = Image.open(label_path_absolute)
            img.thumbnail((150, 150), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            qr_label.configure(image=photo, text="")
            qr_label.image = photo
            self.current_label_path = label_path_absolute
            logger.info(f"Etiqueta regenerada para SKU {sku} en tienda {self.store_id}: {label_path_absolute}")
            messagebox.showinfo("Éxito", "Etiqueta regenerada correctamente.")

        except Exception as e:
            logger.error(f"Error al regenerar la etiqueta para SKU {sku} en tienda {self.store_id}: {str(e)}")
            messagebox.showerror("Error", f"No se pudo regenerar la etiqueta: {str(e)}")

    def copy_image_to_clipboard(self):
        """Copia la imagen de la etiqueta al portapapeles."""
        try:
            if not self.current_label_path or not os.path.exists(self.current_label_path):
                logger.error(f"No hay imagen de etiqueta para copiar en tienda {self.store_id}.")
                messagebox.showerror("Error", "No hay imagen para copiar.")
                return
            img = Image.open(self.current_label_path)
            output = io.BytesIO()
            img.convert("RGB").save(output, format="BMP")
            data = output.getvalue()[14:]
            output.close()
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            win32clipboard.CloseClipboard()
            logger.info(f"Imagen de etiqueta copiada al portapapeles en tienda {self.store_id}: {self.current_label_path}")
            messagebox.showinfo("Éxito", "Imagen copiada al portapapeles.\nPuedes pegarla en P-touch Editor.")
        except Exception as e:
            logger.error(f"Error al copiar la imagen de la etiqueta en tienda {self.store_id}: {str(e)}")
            messagebox.showerror("Error", f"No se pudo copiar la imagen: {str(e)}")

    def print_labels(self):
        """Imprime etiquetas para un producto seleccionado."""
        selected_items = self.manager.ui.tree.selection()
        if not selected_items:
            messagebox.showwarning("Advertencia", "Selecciona un producto para imprimir etiquetas.")
            return
        if len(selected_items) > 1:
            messagebox.showwarning("Advertencia", "Selecciona solo un producto para imprimir etiquetas.")
            return

        sku = self.manager.ui.tree.item(selected_items[0])["values"][1].upper()
        with self.db_manager as db:
            cursor = db.get_cursor()
            cursor.execute("SELECT qr_path FROM productos WHERE sku = ? AND store_id = ?", (sku, self.store_id))
            result = cursor.fetchone()
            if not result or not result[0]:
                logger.error(f"No se encontró la etiqueta para el producto con SKU {sku} en tienda {self.store_id}.")
                messagebox.showerror("Error", f"No se encontró la etiqueta para el producto con SKU {sku}.")
                return

            qr_path = os.path.join(self.root_folder, result[0])
            if not os.path.exists(qr_path):
                logger.error(f"La etiqueta para el producto con SKU {sku} no existe en el sistema de archivos: {qr_path} en tienda {self.store_id}.")
                messagebox.showerror("Error", f"La etiqueta para el producto con SKU {sku} no existe en el sistema de archivos.")
                return

        quantity = tk.simpledialog.askinteger("Cantidad de Etiquetas", "Ingresa la cantidad de etiquetas a imprimir:", 
                                             parent=self.manager.ui.window, minvalue=1, maxvalue=100)
        if quantity is None:
            return

        try:
            printer_name = "Brother QL-800"
            hprinter = win32print.OpenPrinter(printer_name)
            try:
                printer_info = win32print.GetPrinter(hprinter, 2)
                hdc = win32ui.CreateDC()
                hdc.CreatePrinterDC(printer_name)

                image = Image.open(qr_path)
                image = image.convert("L")
                image = image.point(lambda x: 0 if x < 128 else 255, "1")

                label_width = image.width
                label_height = image.height

                hdc.StartDoc("Label Print Job")
                for _ in range(quantity):
                    hdc.StartPage()
                    dib = ImageWin.Dib(image)
                    dib.draw(hdc.GetHandleOutput(), (0, 0, label_width, label_height))
                    hdc.EndPage()

                hdc.EndDoc()
                hdc.DeleteDC()
                logger.info(f"Se imprimieron {quantity} etiquetas para el SKU {sku} en la impresora Brother QL-800 en tienda {self.store_id}.")
                messagebox.showinfo("Éxito", f"Se imprimieron {quantity} etiquetas para el producto con SKU {sku}.")
            finally:
                win32print.ClosePrinter(hprinter)
        except ImportError:
            logger.error("No se encontró la librería pywin32.")
            messagebox.showerror("Error", "No se encontró la librería pywin32. Instálala con 'pip install pywin32'.")
        except Exception as e:
            logger.error(f"Error al imprimir etiquetas en tienda {self.store_id}: {str(e)}")
            messagebox.showerror("Error", f"No se pudo imprimir la etiqueta: {str(e)}\nAsegúrate de que la impresora Brother QL-800 esté conectada y configurada correctamente.")
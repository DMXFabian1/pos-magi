import customtkinter as ctk
from tkinter import ttk, messagebox
import tkinter as tk
from src.modules.sales.apartados.apartados_creation_window import ApartadoCreationWindow
from src.core.config.db_manager import DatabaseManager
from src.core.config.config import CONFIG
import logging
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from PIL import Image, ImageTk
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class PosVentas:
    def __init__(self, user_id, parent_frame, root, db_manager=None):
        required_config_keys = ['DB_NAME', 'METODOS_PAGO', 'VENTAS_CONFIG', 'POS_TITLE', 'THEME_MODE', 'THEME_COLOR', 'NIVELES_EDUCATIVOS', 'ROOT_FOLDER', 'SALES_REPORTS_DIR']
        for key in required_config_keys:
            if key not in CONFIG:
                logger.error(f"Clave requerida '{key}' no encontrada en CONFIG.")
                raise KeyError(f"Clave requerida '{key}' no encontrada en CONFIG.")

        try:
            self.db_manager = db_manager or DatabaseManager()
            self.user_id = user_id
            cursor = self.db_manager.get_cursor()
            cursor.execute("SELECT role FROM users WHERE id = ?", (self.user_id,))
            self.role = cursor.fetchone()['role']
        except Exception as e:
            logger.error(f"Error al inicializar PosVentas: {str(e)}")
            messagebox.showerror("Error", f"No se pudo iniciar Ventas: {str(e)}")
            raise

        self.items = []
        self.id_cliente = None
        self.descuento_total = 0
        self.parent_frame = parent_frame
        self.root = root
        self.empty_image = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        self.empty_image_photo = ImageTk.PhotoImage(self.empty_image)

        self.main_frame = ctk.CTkFrame(self.parent_frame)

        self.search_frame = ctk.CTkFrame(self.main_frame, fg_color="#f0f0f0", corner_radius=10)
        self.search_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(self.search_frame, text="Producto (SKU/Nombre):", font=("Arial", 12, "bold")).pack(side="left", padx=5)
        self.entry_busqueda = ctk.CTkEntry(self.search_frame, width=250, height=30)
        self.entry_busqueda.pack(side="left", padx=5)
        self.entry_busqueda.bind("<Return>", lambda event: self.buscar_y_agregar())

        ctk.CTkLabel(self.search_frame, text="Cantidad:", font=("Arial", 12, "bold")).pack(side="left", padx=5)
        self.entry_cantidad = ctk.CTkEntry(self.search_frame, width=60, height=30)
        self.entry_cantidad.pack(side="left", padx=5)
        self.entry_cantidad.insert(0, "1")

        ctk.CTkLabel(self.search_frame, text="Descuento ($):", font=("Arial", 12, "bold")).pack(side="left", padx=5)
        self.entry_descuento = ctk.CTkEntry(self.search_frame, width=60, height=30)
        self.entry_descuento.pack(side="left", padx=5)
        self.entry_descuento.insert(0, "0")

        ctk.CTkButton(self.search_frame, text="Agregar", command=self.buscar_y_agregar, fg_color="#4CAF50", hover_color="#45A049").pack(side="left", padx=5)

        self.cliente_frame = ctk.CTkFrame(self.main_frame, fg_color="#f0f0f0", corner_radius=10)
        self.cliente_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(self.cliente_frame, text="Cliente (Nombre/Teléfono):", font=("Arial", 12, "bold")).pack(side="left", padx=5)
        self.entry_cliente = ctk.CTkEntry(self.cliente_frame, width=250, height=30)
        self.entry_cliente.pack(side="left", padx=5)
        self.entry_cliente.bind("<Return>", lambda event: self.buscar_cliente())
        ctk.CTkButton(self.cliente_frame, text="Buscar Cliente", command=self.buscar_cliente, fg_color="#2196F3", hover_color="#1976D2").pack(side="left", padx=5)
        ctk.CTkButton(self.cliente_frame, text="Agregar Cliente", command=self.agregar_cliente, fg_color="#4CAF50", hover_color="#45A049").pack(side="left", padx=5)
        ctk.CTkButton(self.cliente_frame, text="Gestionar Clientes", command=self.open_client_management, fg_color="#FF9800", hover_color="#F57C00").pack(side="left", padx=5)
        ctk.CTkButton(self.cliente_frame, text="Omitir Cliente", command=self.omitir_cliente, fg_color="#9E9E9E", hover_color="#757575").pack(side="left", padx=5)

        self.content_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.tree_frame = ctk.CTkFrame(self.content_frame, fg_color="#ffffff", corner_radius=10)
        self.tree_frame.pack(side="left", fill="both", expand=True)
        style = ttk.Style()
        style.configure("Treeview", rowheight=25)
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"))
        style.map("Treeview", background=[('selected', '#2196F3')])
        self.tree = ttk.Treeview(
            self.tree_frame,
            columns=("SKU", "Nombre", "Cantidad", "Precio", "Descuento", "Subtotal"),
            show="headings",
            style="Treeview"
        )
        self.tree.heading("SKU", text="SKU")
        self.tree.heading("Nombre", text="Nombre")
        self.tree.heading("Cantidad", text="Cantidad")
        self.tree.heading("Precio", text="Precio")
        self.tree.heading("Descuento", text="Descuento")
        self.tree.heading("Subtotal", text="Subtotal")
        self.tree.column("SKU", width=100)
        self.tree.column("Nombre", width=250)
        self.tree.column("Cantidad", width=80)
        self.tree.column("Precio", width=80)
        self.tree.column("Descuento", width=80)
        self.tree.column("Subtotal", width=100)
        self.tree.pack(fill="both", expand=True)

        self.tree.tag_configure('oddrow', background='#E8F0FE')
        self.tree.tag_configure('evenrow', background='#FFFFFF')

        self.button_remove = ctk.CTkButton(self.tree_frame, text="Eliminar Seleccionado", command=self.eliminar_item, fg_color="#F44336", hover_color="#D32F2F")
        self.button_remove.pack(side="right", padx=5, pady=5)

        self.detail_frame = ctk.CTkFrame(self.content_frame, fg_color="#FFFFFF", corner_radius=10, border_width=2, border_color="#D3D3D3", width=288)
        self.detail_frame.pack(side="right", fill="y", padx=(5, 0))
        self.detail_frame.pack_propagate(False)
        self.detail_frame.grid_rowconfigure(0, weight=0)
        self.detail_frame.grid_rowconfigure(1, weight=0)
        self.detail_frame.grid_rowconfigure(2, weight=1)
        self.detail_frame.grid_columnconfigure(0, weight=1)

        title_frame = ctk.CTkFrame(self.detail_frame, fg_color="#1A2E5A", corner_radius=0)
        title_frame.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(title_frame, text="Detalles del Producto", font=("Helvetica", 16, "bold"), text_color="#FFFFFF").grid(row=0, column=0, pady=5, padx=10, sticky="w")

        image_frame = ctk.CTkFrame(self.detail_frame, fg_color="#F5F5F5", corner_radius=8, width=288)
        image_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=(5, 2))
        image_frame.grid_propagate(False)
        image_frame.grid_columnconfigure(0, weight=1)
        image_frame.grid_rowconfigure(0, weight=0)
        image_frame.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(image_frame, text="Imagen del Producto:", font=("Helvetica", 10, "bold"), text_color="#1A2E5A").grid(row=0, column=0, pady=(2, 1), sticky="n")
        self.image_container = tk.Frame(image_frame, width=90, height=90, bg="#F5F5F5")
        self.image_container.grid(row=1, column=0, pady=(0, 2), sticky="n")
        self.image_container.grid_propagate(False)
        self.image_label = tk.Label(self.image_container, text="Sin imagen", width=90, height=90, bg="#F5F5F5")
        self.image_label.pack()

        details_content = ctk.CTkFrame(self.detail_frame, fg_color="#FFFFFF", corner_radius=5, width=288)
        details_content.grid(row=2, column=0, sticky="nsew", padx=5, pady=(2, 5))
        details_content.grid_propagate(False)
        details_content.grid_columnconfigure(0, weight=0)
        details_content.grid_columnconfigure(1, weight=1)
        details_content.grid_columnconfigure(2, weight=0)
        details_content.grid_columnconfigure(3, weight=1)

        self.detail_labels = {}
        fields = ["sku", "nombre", "nivel_educativo", "escuela", "color", "tipo_prenda", "tipo_pieza", "genero", "atributo", "ubicacion", "escudo", "marca", "talla", "inventario", "ventas", "precio"]

        for i, field in enumerate(fields):
            if i < 8:
                col_label = 0
                col_value = 1
                row = i
            else:
                col_label = 2
                col_value = 3
                row = i - 8
            ctk.CTkLabel(details_content, text=f"{field.capitalize()}:", font=("Helvetica", 12, "bold"), text_color="#1A2E5A").grid(row=row, column=col_label, padx=(0, 3), pady=0, sticky="e")
            self.detail_labels[field] = ctk.CTkLabel(details_content, text="", font=("Helvetica", 11), text_color="#333333", wraplength=100, anchor="w", justify="left")
            self.detail_labels[field].grid(row=row, column=col_value, padx=(3, 5), pady=0, sticky="w")

        self.tree.bind("<<TreeviewSelect>>", self.mostrar_detalle)

        self.total_frame = ctk.CTkFrame(self.main_frame, fg_color="#f0f0f0", corner_radius=10)
        self.total_frame.pack(fill="x", padx=10, pady=5)
        self.label_subtotal = ctk.CTkLabel(self.total_frame, text="Subtotal: $0.00", font=("Arial", 14, "bold"))
        self.label_subtotal.pack(side="left", padx=10)
        self.label_descuento = ctk.CTkLabel(self.total_frame, text="Descuento Productos: $0.00", font=("Arial", 14, "bold"))
        self.label_descuento.pack(side="left", padx=10)
        self.label_descuento_total = ctk.CTkLabel(self.total_frame, text="Descuento Total (0%): $0.00", font=("Arial", 14, "bold"))
        self.label_descuento_total.pack(side="left", padx=10)
        ctk.CTkButton(self.total_frame, text="Gestionar Descuento Total", command=self.gestionar_descuento_total, fg_color="#FF5722", hover_color="#E64A19").pack(side="left", padx=5)
        self.label_total = ctk.CTkLabel(self.total_frame, text="Total: $0.00", font=("Arial", 14, "bold"))
        self.label_total.pack(side="left", padx=10)

        self.pago_frame = ctk.CTkFrame(self.main_frame, fg_color="#f0f0f0", corner_radius=10)
        self.pago_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(self.pago_frame, text="Método de pago:", font=("Arial", 12, "bold")).pack(side="left", padx=5)
        self.combo_pago = ctk.CTkComboBox(self.pago_frame, values=CONFIG['METODOS_PAGO'], state="readonly", width=150)
        self.combo_pago.pack(side="left", padx=5)
        self.combo_pago.set(CONFIG['METODOS_PAGO'][0])

        self.button_frame = ctk.CTkFrame(self.main_frame, fg_color="#f0f0f0", corner_radius=10)
        self.button_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(self.button_frame, text="Finalizar Venta (F10)", command=self.finalizar_venta, fg_color="#4CAF50", hover_color="#45A049", width=150).pack(side="left", padx=5)
        ctk.CTkButton(self.button_frame, text="Cancelar (ESC)", command=self.cancelar_venta, fg_color="#F44336", hover_color="#D32F2F", width=150).pack(side="left", padx=5)
        ctk.CTkButton(self.button_frame, text="Crear Apartado", command=self.abrir_ventana_apartado, fg_color="#FF9800", hover_color="#F57C00", width=150).pack(side="left", padx=5)
        ctk.CTkButton(self.button_frame, text="Imprimir Ticket", command=self.imprimir_ticket, fg_color="#2196F3", hover_color="#1976D2", width=150).pack(side="left", padx=5)

        self.root.bind("<F10>", lambda event: self.finalizar_venta())
        self.root.bind("<Escape>", lambda event: self.cancelar_venta())

        self.entry_busqueda.focus_set()
        logger.info(f"Interfaz de POS inicializada para usuario con ID '{self.user_id}'.")

    def abrir_ventana_apartado(self):
        if not self.items:
            messagebox.showerror("Error", "No hay productos para crear un apartado.")
            return
        ApartadoCreationWindow(self.root, self.user_id, self.items, self.descuento_total, self.db_manager, self)

    def agregar_cliente(self):
        try:
            nav_manager = self.root.nav_manager
            if not nav_manager.clientes_instance:
                from src.modules.clients.client_manager import ClientManager
                nav_manager.clientes_instance = ClientManager(
                    user_id=self.user_id,
                    parent_frame=nav_manager.content_frame,
                    root=self.root,
                    db_manager=self.db_manager
                )
            nav_manager.clientes_instance.abrir_ventana_crear_cliente(callback=self.cliente_creado)
        except AttributeError:
            messagebox.showerror("Error", "No se pudo abrir la gestión de clientes.")
            logger.error("ClientManager no encontrado.")

    def cliente_creado(self, id_cliente, nombre_completo):
        self.id_cliente = id_cliente
        self.entry_cliente.delete(0, "end")
        self.entry_cliente.insert(0, nombre_completo)
        logger.info(f"Cliente creado y seleccionado: {nombre_completo} (ID: {id_cliente}).")

    def open_client_management(self):
        try:
            self.root.nav_manager.open_client_management()
            logger.info("Redirigiendo a la gestión de clientes desde PosVentas.")
        except AttributeError:
            messagebox.showerror("Error", "No se pudo abrir la gestión de clientes.")
            logger.error("NavigationManager no encontrado en root.nav_manager.")

    def crear_apartado(self, id_cliente, anticipo):
        try:
            nav_manager = self.root.nav_manager
            if not nav_manager.apartados_instance:
                from src.modules.sales.apartados.apartados_manager import ApartadosManager
                nav_manager.apartados_instance = ApartadosManager(
                    user_id=self.user_id,
                    parent_frame=nav_manager.content_frame,
                    root=self.root,
                    db_manager=self.db_manager
                )

            fecha_creacion = datetime.now().strftime('%Y-%m-%d')
            fecha_vencimiento = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')

            apartado_id = nav_manager.apartados_instance.registrar_apartado(
                user_id=self.user_id,
                items=self.items,
                id_cliente=id_cliente,
                descuento_total=self.descuento_total,
                fecha_vencimiento=fecha_vencimiento,
                anticipo=anticipo
            )

            for item in self.items:
                self.db_manager.actualizar_inventario(item['sku'], -item['cantidad'])

            self.imprimir_ticket_apartado(apartado_id, id_cliente, fecha_creacion, fecha_vencimiento, anticipo)

            self.cancelar_venta()

            messagebox.showinfo("Éxito", f"Apartado registrado con ID: {apartado_id}")
            logger.info(f"Apartado registrado: {apartado_id}")
        except AttributeError:
            messagebox.showerror("Error", "No se pudo acceder a la gestión de apartados.")
            logger.error("NavigationManager o ApartadosManager no encontrados.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo registrar el apartado: {str(e)}")
            logger.error(f"Error al registrar apartado: {str(e)}")

    def imprimir_ticket_apartado(self, apartado_id, id_cliente, fecha_creacion, fecha_vencimiento, anticipo):
        try:
            ticket_path = os.path.join(CONFIG['ROOT_FOLDER'], CONFIG['SALES_REPORTS_DIR'], f"apartado_{self.user_id}_{apartado_id}.pdf")
            doc = SimpleDocTemplate(ticket_path, pagesize=letter)
            elements = []
            styles = getSampleStyleSheet()
            elements.append(Paragraph("Comprobante de Apartado - Boutique", styles['Heading1']))
            elements.append(Paragraph(f"ID Apartado: {apartado_id}", styles['Normal']))
            elements.append(Paragraph(f"Usuario: {self.user_id}", styles['Normal']))
            cliente = self.db_manager.get_cliente(id_cliente)
            elements.append(Paragraph(f"Cliente: {cliente['nombre_completo']} (ID: {id_cliente})", styles['Normal']))
            elements.append(Paragraph(f"Fecha de Creación: {fecha_creacion}", styles['Normal']))
            elements.append(Paragraph(f"Fecha de Vencimiento: {fecha_vencimiento}", styles['Normal']))
            elements.append(Spacer(1, 12))
            elements.append(Paragraph("Detalles del apartado:", styles['Heading2']))
            for item in self.items:
                subtotal_item = item['cantidad'] * item['precio']
                elements.append(Paragraph(f"{item['nombre']} (SKU: {item['sku']}) - Cantidad: {item['cantidad']} - Precio: ${item['precio']:.2f} - Descuento: ${item['descuento']:.2f} - Subtotal: ${subtotal_item - item['descuento']:.2f}", styles['Normal']))
            subtotal = sum(item['cantidad'] * item['precio'] for item in self.items)
            total_descuento_items = sum(item['descuento'] for item in self.items)
            subtotal_despues_descuentos = subtotal - total_descuento_items
            descuento_total = (subtotal_despues_descuentos * self.descuento_total) / 100
            total = subtotal_despues_descuentos - descuento_total
            monto_restante = total - anticipo
            elements.append(Spacer(1, 12))
            elements.append(Paragraph(f"Subtotal: ${subtotal:.2f}", styles['Normal']))
            elements.append(Paragraph(f"Descuento Productos: ${total_descuento_items:.2f}", styles['Normal']))
            elements.append(Paragraph(f"Descuento Total ({self.descuento_total}%): ${descuento_total:.2f}", styles['Normal']))
            elements.append(Paragraph(f"Total: ${total:.2f}", styles['Normal']))
            elements.append(Paragraph(f"Anticipo: ${anticipo:.2f}", styles['Normal']))
            elements.append(Paragraph(f"Monto Restante para Liquidar: ${monto_restante:.2f}", styles['Normal']))
            doc.build(elements)
            messagebox.showinfo("Éxito", f"Comprobante de apartado guardado en: {ticket_path}")
            logger.info(f"Comprobante de apartado generado y guardado en {ticket_path}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el comprobante: {str(e)}")
            logger.error(f"Error al generar comprobante de apartado: {str(e)}")

    def mostrar_detalle(self, event):
        selected_items = self.tree.selection()
        logger.debug(f"Elementos seleccionados: {selected_items}")
        if not selected_items:
            logger.debug("No hay elementos seleccionados para mostrar detalles.")
            for field, label in self.detail_labels.items():
                label.configure(text="")
            self.image_label.configure(image=self.empty_image_photo, text="Sin imagen")
            self.image_label.image = self.empty_image_photo
            return

        item = selected_items[0]
        index = int(self.tree.index(item))
        producto = self.items[index]
        sku = producto['sku']
        logger.debug(f"Mostrando detalles para SKU: {sku}")

        try:
            with self.db_manager as db:
                cursor = db.get_cursor()
                cursor.execute('SELECT * FROM productos WHERE sku = ?', (sku,))
                producto_db = cursor.fetchone()
                if not producto_db:
                    logger.error(f"Producto no encontrado con SKU {sku}.")
                    messagebox.showerror("Error", "Producto no encontrado.")
                    return

                logger.debug(f"Datos del producto SKU {sku}: {producto_db}")

                fields_mapping = {
                    "sku": producto_db[0],
                    "nombre": producto_db[1],
                    "nivel_educativo": producto_db[2],
                    "escuela": producto_db[3],
                    "color": producto_db[4],
                    "tipo_prenda": producto_db[5],
                    "tipo_pieza": producto_db[6],
                    "genero": producto_db[7],
                    "marca": producto_db[8],
                    "talla": producto_db[9],
                    "atributo": producto_db[10],
                    "ubicacion": producto_db[11],
                    "escudo": producto_db[12],
                    "inventario": producto_db[14],
                    "ventas": producto_db[15],
                    "precio": producto_db[16],
                }

                for field, value in fields_mapping.items():
                    display_value = str(value if value is not None else "")
                    if field == "precio" and value:
                        try:
                            display_value = f"{float(value):.2f}"
                        except ValueError:
                            pass
                    if field == "escuela" and display_value:
                        nivel_educativo = fields_mapping.get("nivel_educativo", "")
                        if nivel_educativo:
                            display_value = f"{display_value} ({nivel_educativo})"
                    if field == "genero" and display_value:
                        if display_value == "Mujer":
                            symbol = "♀"
                            color = "#800080"
                        elif display_value == "Hombre":
                            symbol = "♂"
                            color = "#008000"
                        elif display_value == "Unisex":
                            symbol = "⚥"
                            color = "#808080"
                        else:
                            symbol = ""
                            color = "#333333"
                        display_value = f"{symbol} {display_value}" if symbol else display_value
                        logger.debug(f"Actualizando {field} con valor: {display_value}, color: {color}")
                        self.detail_labels[field].configure(text=display_value, text_color=color)
                        continue
                    if field == "ubicacion":
                        display_value = display_value if display_value else ""
                    logger.debug(f"Actualizando {field} con valor: {display_value}")
                    self.detail_labels[field].configure(text=display_value, text_color="#4B5EAA")

                image_path = producto_db[17]
                logger.debug(f"Intentando cargar imagen desde: {image_path}")
                if image_path:
                    image_path_absolute = os.path.join(CONFIG['ROOT_FOLDER'], image_path)
                    logger.debug(f"Ruta absoluta de la imagen: {image_path_absolute}")
                    if os.path.exists(image_path_absolute):
                        img = Image.open(image_path_absolute)
                        img.thumbnail((90, 90), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(img)
                        self.image_label.configure(image=photo, text="")
                        self.image_label.image = photo
                        logger.debug("Imagen del producto cargada exitosamente.")
                    else:
                        logger.warning(f"Archivo de imagen no encontrado: {image_path_absolute}")
                        self.image_label.configure(image=self.empty_image_photo, text="Archivo de imagen no encontrado")
                        self.image_label.image = self.empty_image_photo
                else:
                    logger.debug("El producto no tiene imagen asociada.")
                    self.image_label.configure(image=self.empty_image_photo, text="Sin imagen")
                    self.image_label.image = self.empty_image_photo
        except Exception as e:
            logger.error(f"Error al mostrar detalles para SKU {sku}: {str(e)}")
            messagebox.showerror("Error", f"Error al mostrar detalles: {str(e)}")

    def buscar_y_agregar(self):
        query = self.entry_busqueda.get().strip()
        logging.debug(f"Buscando producto con query: '{query}'")
        try:
            cantidad = int(self.entry_cantidad.get())
            descuento = float(self.entry_descuento.get())
            if cantidad <= 0:
                messagebox.showerror("Error", "La cantidad debe ser mayor a 0.")
                return
            if descuento < 0:
                messagebox.showerror("Error", "El descuento no puede ser negativo.")
                return

            productos = self.db_manager.buscar_productos(query=query, limit=1)
            if not productos:
                messagebox.showinfo("No encontrado", "No se encontró el producto.")
                return

            sku, nombre, precio, inventario = productos[0]['sku'], productos[0]['nombre'], productos[0]['precio'], productos[0]['inventario']
            if not self.db_manager.validar_stock(sku, cantidad):
                messagebox.showerror("Error", f"Stock insuficiente para '{nombre}' (disponible: {inventario}).")
                return

            item = {
                "sku": sku,
                "nombre": nombre,
                "cantidad": cantidad,
                "precio": precio,
                "descuento": descuento
            }
            self.items.append(item)
            self.actualizar_tabla()
            self.entry_busqueda.delete(0, "end")
            self.entry_cantidad.delete(0, "end")
            self.entry_cantidad.insert(0, "1")
            self.entry_descuento.delete(0, "end")
            self.entry_descuento.insert(0, "0")
            self.entry_busqueda.focus_set()
            logger.info(f"Producto '{nombre}' añadido (SKU: {sku}, Cantidad: {cantidad}, Descuento: ${descuento}).")
        except ValueError:
            messagebox.showerror("Error", "Cantidad o descuento inválidos.")
            logger.error(f"Entrada inválida: cantidad={self.entry_cantidad.get()}, descuento={self.entry_descuento.get()}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al añadir producto: {str(e)}")
            logger.error(f"Error al añadir producto: {str(e)}")

    def eliminar_item(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Selección", "Seleccione un producto para eliminar.")
            return
        if len(selected) > 1:
            messagebox.showinfo("Selección", "Seleccione solo un producto para eliminar.")
            return

        index = int(self.tree.index(selected[0]))
        item = self.items.pop(index)
        self.actualizar_tabla()
        logger.info(f"Producto eliminado de la venta: {item['nombre']} (SKU: {item['sku']}).")

    def buscar_cliente(self):
        query = self.entry_cliente.get().strip()
        try:
            clientes = self.db_manager.buscar_clientes(query=query, limit=1)
            if not clientes:
                messagebox.showinfo("No encontrado", "No se encontró el cliente.")
                return
            id_cliente, nombre = clientes[0]['id'], clientes[0]['nombre_completo']
            self.id_cliente = id_cliente
            self.entry_cliente.delete(0, "end")
            self.entry_cliente.insert(0, nombre)
            logger.info(f"Cliente seleccionado: {nombre} (ID: {id_cliente}).")
        except Exception as e:
            messagebox.showerror("Error", f"Error al buscar cliente: {str(e)}")
            logger.error(f"Error al buscar cliente: {str(e)}")

    def omitir_cliente(self):
        self.id_cliente = None
        self.entry_cliente.delete(0, "end")
        self.entry_cliente.insert(0, "Cliente omitido")
        self.entry_cliente.configure(state="disabled")
        logger.info("Cliente omitido para la venta.")

    def gestionar_descuento_total(self):
        def aplicar_descuento(porcentaje):
            try:
                self.descuento_total = float(porcentaje)
                self.actualizar_tabla()
                dialog.destroy()
                logger.info(f"Descuento total aplicado: {self.descuento_total}%")
            except ValueError:
                messagebox.showerror("Error", "Porcentaje inválido. Ingrese un número válido.")
                logger.error(f"Porcentaje inválido ingresado: {porcentaje}")

        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Gestionar Descuento Total")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Seleccionar Descuento Total", font=("Arial", 14)).pack(pady=10)

        ctk.CTkButton(dialog, text="5%", command=lambda: aplicar_descuento(5), fg_color="#FF5722", hover_color="#E64A19").pack(pady=5)
        ctk.CTkButton(dialog, text="10%", command=lambda: aplicar_descuento(10), fg_color="#FF5722", hover_color="#E64A19").pack(pady=5)
        ctk.CTkButton(dialog, text="15%", command=lambda: aplicar_descuento(15), fg_color="#FF5722", hover_color="#E64A19").pack(pady=5)

        ctk.CTkLabel(dialog, text="Porcentaje Personalizado (%):", font=("Arial", 12, "bold")).pack(pady=5)
        entry_descuento = ctk.CTkEntry(dialog, width=100)
        entry_descuento.pack(pady=5)
        entry_descuento.bind("<Return>", lambda event: aplicar_descuento(entry_descuento.get()))
        ctk.CTkButton(dialog, text="Aplicar", command=lambda: aplicar_descuento(entry_descuento.get()), fg_color="#4CAF50", hover_color="#45A049").pack(pady=10)

        ctk.CTkButton(dialog, text="Eliminar Descuento", command=lambda: aplicar_descuento(0), fg_color="#F44336", hover_color="#D32F2F").pack(pady=5)

        entry_descuento.focus_set()

    def actualizar_tabla(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        subtotal = 0
        total_descuento_items = 0
        total_subtotal_ajustado = 0

        for item in self.items:
            subtotal_item = item['cantidad'] * item['precio']
            subtotal += subtotal_item
            total_descuento_items += item['descuento']

        subtotal_despues_descuentos = subtotal - total_descuento_items
        descuento_total = (subtotal_despues_descuentos * self.descuento_total) / 100

        if subtotal > 0 and self.items:
            for idx, item in enumerate(self.items):
                subtotal_item = item['cantidad'] * item['precio']
                proporcion = subtotal_item / subtotal
                descuento_proporcional = (descuento_total * proporcion)
                descuento_combinado = item['descuento'] + descuento_proporcional
                subtotal_ajustado = subtotal_item - descuento_combinado
                total_subtotal_ajustado += subtotal_ajustado

                tag = 'oddrow' if idx % 2 == 0 else 'evenrow'
                self.tree.insert("", "end", values=(
                    item['sku'],
                    item['nombre'],
                    item['cantidad'],
                    f"${item['precio']:.2f}",
                    f"${descuento_combinado:.2f}",
                    f"${subtotal_ajustado:.2f}"
                ), tags=(tag,))

        total = total_subtotal_ajustado

        self.label_subtotal.configure(text=f"Subtotal: ${subtotal:.2f}")
        self.label_descuento.configure(text=f"Descuento Productos: ${total_descuento_items:.2f}")
        self.label_descuento_total.configure(text=f"Descuento Total ({self.descuento_total}%): ${descuento_total:.2f}")
        self.label_total.configure(text=f"Total: ${total:.2f}")

    def imprimir_ticket(self):
        if not self.items:
            messagebox.showerror("Error", "No hay productos para imprimir un ticket.")
            return
        try:
            ticket_path = os.path.join(CONFIG['ROOT_FOLDER'], CONFIG['SALES_REPORTS_DIR'], f"ticket_{self.user_id}_{len(os.listdir(os.path.join(CONFIG['ROOT_FOLDER'], CONFIG['SALES_REPORTS_DIR']))) + 1}.pdf")
            doc = SimpleDocTemplate(ticket_path, pagesize=letter)
            elements = []
            styles = getSampleStyleSheet()
            elements.append(Paragraph("Ticket de Venta - Boutique", styles['Heading1']))
            elements.append(Paragraph(f"ID Venta: {self.db_manager.get_last_sale_id()}", styles['Normal']))
            elements.append(Paragraph(f"Usuario: {self.user_id}", styles['Normal']))
            if self.id_cliente:
                cliente = self.db_manager.get_cliente(self.id_cliente)
                elements.append(Paragraph(f"Cliente: {cliente['nombre_completo']} (ID: {self.id_cliente})", styles['Normal']))
            else:
                elements.append(Paragraph("Cliente: No especificado", styles['Normal']))
            elements.append(Paragraph(f"Método de pago: {self.combo_pago.get()}", styles['Normal']))
            elements.append(Spacer(1, 12))
            elements.append(Paragraph("Detalles de la venta:", styles['Heading2']))
            for item in self.items:
                subtotal_item = item['cantidad'] * item['precio']
                elements.append(Paragraph(f"{item['nombre']} (SKU: {item['sku']}) - Cantidad: {item['cantidad']} - Precio: ${item['precio']:.2f} - Descuento: ${item['descuento']:.2f} - Subtotal: ${subtotal_item - item['descuento']:.2f}", styles['Normal']))
            subtotal = sum(item['cantidad'] * item['precio'] for item in self.items)
            total_descuento_items = sum(item['descuento'] for item in self.items)
            subtotal_despues_descuentos = subtotal - total_descuento_items
            descuento_total = (subtotal_despues_descuentos * self.descuento_total) / 100
            total = subtotal_despues_descuentos - descuento_total
            elements.append(Spacer(1, 12))
            elements.append(Paragraph(f"Subtotal: ${subtotal:.2f}", styles['Normal']))
            elements.append(Paragraph(f"Descuento Productos: ${total_descuento_items:.2f}", styles['Normal']))
            elements.append(Paragraph(f"Descuento Total ({self.descuento_total}%): ${descuento_total:.2f}", styles['Normal']))
            elements.append(Paragraph(f"Total: ${total:.2f}", styles['Normal']))
            from datetime import datetime
            elements.append(Paragraph(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
            doc.build(elements)
            messagebox.showinfo("Éxito", f"Ticket guardado en: {ticket_path}")
            logger.info(f"Ticket generado y guardado en {ticket_path}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el ticket: {str(e)}")
            logger.error(f"Error al generar ticket: {str(e)}")

    def finalizar_venta(self):
        if not self.items:
            messagebox.showerror("Error", "No hay productos en la venta.")
            return
        try:
            metodo_pago = self.combo_pago.get()
            id_venta = self.db_manager.registrar_venta(
                user_id=self.user_id,
                items=self.items,
                metodo_pago=metodo_pago,
                id_cliente=self.id_cliente,
                tasa_iva=0
            )
            for item in self.items:
                self.db_manager.actualizar_inventario(item['sku'], -item['cantidad'])
            self.imprimir_ticket()
            messagebox.showinfo("Éxito", f"Venta registrada con ID: {id_venta}")
            self.cancelar_venta()
            logger.info(f"Venta finalizada: {id_venta}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo registrar la venta: {str(e)}")
            logger.error(f"Error al finalizar venta: {str(e)}")

    def cancelar_venta(self):
        self.items = []
        self.id_cliente = None
        self.descuento_total = 0
        self.entry_cliente.delete(0, "end")
        self.entry_cliente.configure(state="normal")
        self.entry_busqueda.delete(0, "end")
        self.entry_cantidad.delete(0, "end")
        self.entry_cantidad.insert(0, "1")
        self.entry_descuento.delete(0, "end")
        self.entry_descuento.insert(0, "0")
        self.actualizar_tabla()
        self.entry_busqueda.focus_set()
        logger.info("Venta cancelada.")
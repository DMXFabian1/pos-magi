import customtkinter as ctk
from tkinter import ttk, messagebox
from src.utils.ticket_utils import generar_ticket_pdf
from src.modules.sales.apartados.apartados_creation_window import ApartadoCreationWindow
from src.core.config.db_manager import DatabaseManager
from src.core.config.config import CONFIG
import logging
import os
from datetime import datetime, timedelta
from src.utils.client_utils import buscar_clientes_reutilizable
from PIL import Image, ImageTk

logger = logging.getLogger(__name__)

class PosVentas:
    def __init__(self, user_id, parent_frame, root, db_manager=None, store_id=1):
        required_config_keys = ['DB_NAME', 'METODOS_PAGO', 'VENTAS_CONFIG', 'POS_TITLE', 'THEME_MODE', 'THEME_COLOR', 'NIVELES_EDUCATIVOS', 'ROOT_FOLDER', 'SALES_REPORTS_DIR']
        for key in required_config_keys:
            if key not in CONFIG:
                logger.error(f"Clave requerida '{key}' no encontrada en CONFIG para tienda {store_id}.")
                raise KeyError(f"Clave requerida '{key}' no encontrada en CONFIG.")

        try:
            self.db_manager = db_manager or DatabaseManager()
            self.user_id = user_id
            self.store_id = store_id
            cursor = self.db_manager.get_cursor()
            cursor.execute("SELECT role FROM users WHERE id = ? AND store_id = ?", (user_id, store_id))
            result = cursor.fetchone()
            if not result:
                raise ValueError(f"Usuario con ID {user_id} no encontrado en tienda {store_id}.")
            self.role = result['role']
        except Exception as e:
            logger.error(f"Error al inicializar PosVentas para usuario {user_id} en tienda {store_id}: {str(e)}")
            messagebox.showerror("Error", f"No se pudo iniciar Ventas: {str(e)}")
            raise

        self.items = []
        self.id_cliente = None
        self.descuento_total = 0
        self.parent_frame = parent_frame
        self.root = root
        self.cliente_nombre = None
        self.product_cache = {}  # Cache for product searches

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
        self.image_container = ctk.CTkFrame(image_frame, width=90, height=90, fg_color="#F5F5F5")
        self.image_container.grid(row=1, column=0, pady=(0, 2), sticky="n")
        self.image_container.grid_propagate(False)
        self.image_label = ctk.CTkLabel(self.image_container, text="Sin imagen", width=90, height=90)
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
        logger.info(f"Interfaz de POS inicializada para usuario con ID '{self.user_id}' en tienda {self.store_id}.")

    def agregar_o_actualizar_item(self, sku, nombre, cantidad, precio, descuento):
        """
        Agrega un nuevo item o actualiza uno existente con el mismo SKU.
        """
        for item in self.items:
            if item['sku'] == sku:
                item['cantidad'] += cantidad
                item['descuento'] += descuento  # Acumular descuento por producto
                logger.debug(f"Producto actualizado: {nombre} (SKU: {sku}, Nueva cantidad: {item['cantidad']}, Descuento acumulado: ${item['descuento']}) en tienda {self.store_id}")
                return True
        # Si no existe, añadir nuevo item
        self.items.append({
            "sku": sku,
            "nombre": nombre,
            "cantidad": cantidad,
            "precio": precio,
            "descuento": descuento
        })
        logger.debug(f"Producto añadido: {nombre} (SKU: {sku}, Cantidad: {cantidad}, Descuento: ${descuento}) en tienda {self.store_id}")
        return False

    def abrir_ventana_apartado(self):
        if not self.items:
            messagebox.showerror("Error", "No hay productos para crear un apartado.")
            logger.warning(f"Intento de crear apartado sin productos en tienda {self.store_id}")
            return
        ApartadoCreationWindow(self.root, self.user_id, self.items, self.descuento_total, self.db_manager, self, store_id=self.store_id)

    def agregar_cliente(self):
        try:
            nav_manager = self.root.nav_manager
            if not nav_manager.clientes_instance:
                from src.modules.clients.client_manager import ClientManager
                nav_manager.clientes_instance = ClientManager(
                    user_id=self.user_id,
                    parent_frame=nav_manager.content_frame,
                    root=self.root,
                    db_manager=self.db_manager,
                    store_id=self.store_id
                )
            nav_manager.clientes_instance.abrir_ventana_crear_cliente(callback=self.cliente_creado)
            logger.debug(f"Ventana de creación de cliente abierta desde PosVentas para tienda {self.store_id}")
        except AttributeError:
            messagebox.showerror("Error", "No se pudo abrir la gestión de clientes.")
            logger.error(f"ClientManager no encontrado para tienda {self.store_id}")

    def cliente_creado(self, id_cliente, nombre_completo):
        self.id_cliente = id_cliente
        self.cliente_nombre = nombre_completo
        self.entry_cliente.delete(0, "end")
        self.entry_cliente.insert(0, nombre_completo)
        logger.info(f"Cliente creado y seleccionado: {nombre_completo} (ID: {id_cliente}) en tienda {self.store_id}")

    def open_client_management(self):
        try:
            self.root.nav_manager.open_client_management()
            logger.info(f"Redirigiendo a la gestión de clientes desde PosVentas para tienda {self.store_id}")
        except AttributeError:
            messagebox.showerror("Error", "No se pudo abrir la gestión de clientes.")
            logger.error(f"NavigationManager no encontrado en root.nav_manager para tienda {self.store_id}")

    def mostrar_ventana_seleccion_clientes(self, clientes):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Seleccionar Cliente")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()

        self.clientes_originales = clientes.copy()

        search_frame = ctk.CTkFrame(dialog)
        search_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(search_frame, text="Filtrar (Nombre/Teléfono):", font=("Arial", 12, "bold")).pack(side="left", padx=5)
        entry_busqueda = ctk.CTkEntry(search_frame, width=250)
        entry_busqueda.pack(side="left", padx=5)

        tree_frame = ctk.CTkFrame(dialog)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)

        tree = ttk.Treeview(
            tree_frame,
            columns=("ID", "Nombre", "Teléfono"),
            show="headings",
            height=10
        )
        tree.heading("ID", text="ID")
        tree.heading("Nombre", text="Nombre Completo")
        tree.heading("Teléfono", text="Teléfono")
        tree.column("ID", width=50)
        tree.column("Nombre", width=250)
        tree.column("Teléfono", width=150)
        tree.pack(fill="both", expand=True)

        def filtrar_clientes(event=None):
            query = entry_busqueda.get().strip().lower()
            tree.delete(*tree.get_children())
            clientes_filtrados = [
                cliente for cliente in self.clientes_originales
                if (query in cliente['nombre_completo'].lower() or
                    (cliente['numero'] and query in cliente['numero'].lower()))
            ]
            for cliente in clientes_filtrados:
                tree.insert("", "end", values=(
                    cliente['id'],
                    cliente['nombre_completo'],
                    cliente['numero'] if cliente['numero'] else "N/A"
                ))

        entry_busqueda.bind("<KeyRelease>", filtrar_clientes)

        for cliente in clientes:
            tree.insert("", "end", values=(
                cliente['id'],
                cliente['nombre_completo'],
                cliente['numero'] if cliente['numero'] else "N/A"
            ))

        button_frame = ctk.CTkFrame(dialog)
        button_frame.pack(fill="x", padx=10, pady=5)

        def seleccionar_cliente():
            selected = tree.selection()
            if not selected:
                messagebox.showinfo("Selección", "Seleccione un cliente para continuar.")
                logger.warning(f"Intento de seleccionar cliente sin selección en tienda {self.store_id}")
                return
            item = tree.item(selected[0])
            cliente_id = item['values'][0]
            cliente_nombre = item['values'][1]
            self.id_cliente = cliente_id
            self.cliente_nombre = cliente_nombre
            self.entry_cliente.delete(0, "end")
            self.entry_cliente.insert(0, cliente_nombre)
            logger.info(f"Cliente seleccionado: {cliente_nombre} (ID: {cliente_id}) en tienda {self.store_id}")
            dialog.destroy()

        ctk.CTkButton(button_frame, text="Seleccionar", command=seleccionar_cliente, fg_color="#4CAF50", hover_color="#45A049").pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Cancelar", command=dialog.destroy, fg_color="#F44336", hover_color="#D32F2F").pack(side="left", padx=5)

        entry_busqueda.focus_set()

    def buscar_cliente(self):
        query = self.entry_cliente.get().strip()
        clientes = buscar_clientes_reutilizable(
            db_manager=self.db_manager,
            query=query,
            limit=50,
            show_messages=False,
            store_id=self.store_id
        )
        if not clientes:
            messagebox.showinfo("No encontrado", f"No se encontraron clientes para la búsqueda: '{query}' en tienda {self.store_id}")
            return
        self.mostrar_ventana_seleccion_clientes(clientes)

    def crear_apartado(self, id_cliente, anticipo):
        try:
            logger.debug(f"Creando apartado para cliente {id_cliente} con anticipo {anticipo} en tienda {self.store_id}")
            from src.modules.sales.apartados.apartados_logic import ApartadosLogic
            apartados_logic = ApartadosLogic(self.db_manager, self.user_id, self.store_id)

            if not id_cliente:
                logger.error(f"Intento de crear apartado sin cliente en tienda {self.store_id}")
                return {
                    "success": False,
                    "message": "Debe seleccionar un cliente para el apartado."
                }

            cursor = self.db_manager.get_cursor()
            cursor.execute("SELECT 1 FROM clientes WHERE id = ? AND store_id = ?", (id_cliente, self.store_id))
            if not cursor.fetchone():
                logger.error(f"Cliente con ID {id_cliente} no existe en tienda {self.store_id}")
                return {
                    "success": False,
                    "message": "El cliente seleccionado no existe."
                }

            if anticipo < 0:
                logger.error(f"Intento de crear apartado con anticipo negativo: {anticipo} en tienda {self.store_id}")
                return {
                    "success": False,
                    "message": "El anticipo no puede ser negativo."
                }

            for item in self.items:
                if not self.db_manager.validar_stock(item['sku'], item['cantidad'], self.store_id):
                    logger.error(f"Stock insuficiente para {item['nombre']} (SKU: {item['sku']}) en tienda {self.store_id}")
                    return {
                        "success": False,
                        "message": f"Stock insuficiente para '{item['nombre']}' (SKU: {item['sku']})."
                    }

            productos = [
                {
                    "sku": item["sku"],
                    "nombre": item["nombre"],
                    "cantidad": item["cantidad"],
                    "precio": item["precio"],
                    "descuento": item["descuento"]
                }
                for item in self.items
            ]

            result = apartados_logic.crear_apartado(
                id_cliente=id_cliente,
                user_id=self.user_id,
                productos=productos,
                anticipo=anticipo,
                store_id=self.store_id
            )

            if not result["success"]:
                logger.error(f"Fallo al crear apartado en tienda {self.store_id}: {result['message']}")
                return {
                    "success": False,
                    "message": result["message"]
                }

            apartado_id = result["apartado_id"]
            receipt_path = result["receipt_path"]

            # Actualizar inventario solo si el apartado se creó exitosamente
            with self.db_manager as db:
                cursor = db.get_cursor()
                for item in self.items:
                    cursor.execute(
                        "UPDATE productos SET inventario = inventario - ? WHERE sku = ? AND store_id = ?",
                        (item['cantidad'], item['sku'], self.store_id)
                    )
                db.connection.commit()

            fecha_creacion = datetime.now().strftime('%Y-%m-%d')
            fecha_vencimiento = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            pdf_path = self.imprimir_ticket_apartado(apartado_id, id_cliente, fecha_creacion, fecha_vencimiento, anticipo)

            # Limpiar estado solo si todo salió bien
            self.cancelar_venta()

            logger.info(f"Apartado registrado: {apartado_id}, Comprobante: {receipt_path}, Ticket PDF: {pdf_path} en tienda {self.store_id}")
            return {
                "success": True,
                "message": "Apartado registrado exitosamente",
                "apartado_id": apartado_id,
                "receipt_path": receipt_path,
                "pdf_path": pdf_path
            }

        except Exception as e:
            logger.error(f"Error al registrar apartado para cliente {id_cliente} en tienda {self.store_id}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": f"No se pudo registrar el apartado: {str(e)}"
            }

    def imprimir_ticket_apartado(self, apartado_id, id_cliente, fecha_creacion, fecha_vencimiento, anticipo):
        try:
            cliente = self.db_manager.get_cliente(id_cliente, store_id=self.store_id)
            cliente_nombre = cliente["nombre_completo"] if cliente else "Sin cliente"
            items = [
                {
                    "nombre": item["nombre"],
                    "cantidad": item["cantidad"],
                    "precio": item["precio"]
                }
                for item in self.items
            ]
            header_data = {
                "Fecha Creación": fecha_creacion,
                "Fecha Vencimiento": fecha_vencimiento,
                "Cliente": cliente_nombre,
                "Apartado ID": apartado_id,
                "Anticipo": anticipo
            }
            filename = f"ticket_apartado_{apartado_id}.pdf"
            output_dir = os.path.join(CONFIG['ROOT_FOLDER'], CONFIG['SALES_REPORTS_DIR'])
            success = generar_ticket_pdf(filename, items, header_data, ticket_type="apartado", output_dir=output_dir)
            if success:
                pdf_path = os.path.join(output_dir, filename)
                logger.info(f"Ticket de apartado {filename} generado correctamente en {pdf_path} para tienda {self.store_id}")
                return pdf_path
            else:
                logger.error(f"Error al generar el ticket de apartado {filename} en tienda {self.store_id}")
                return None
        except Exception as e:
            logger.error(f"Error al generar comprobante de apartado {apartado_id} en tienda {self.store_id}: {str(e)}")
            return None

    def mostrar_detalle(self, event):
        selected_items = self.tree.selection()
        logger.debug(f"Elementos seleccionados: {selected_items} en tienda {self.store_id}")
        if not selected_items:
            logger.debug(f"No hay elementos seleccionados para mostrar detalles en tienda {self.store_id}")
            for field, label in self.detail_labels.items():
                label.configure(text="")
            self.image_label.configure(text="Sin imagen")
            return

        item = selected_items[0]
        index = int(self.tree.index(item))
        producto = self.items[index]
        sku = producto['sku']
        logger.debug(f"Mostrando detalles para SKU: {sku} en tienda {self.store_id}")

        try:
            with self.db_manager as db:
                cursor = db.get_cursor()
                cursor.execute('SELECT * FROM productos WHERE sku = ? AND store_id = ?', (sku, self.store_id))
                producto_db = cursor.fetchone()
                if not producto_db:
                    logger.error(f"Producto no encontrado con SKU {sku} en tienda {self.store_id}")
                    messagebox.showerror("Error", "Producto no encontrado.")
                    return

                logger.debug(f"Datos del producto SKU {sku}: {producto_db} en tienda {self.store_id}")

                fields_mapping = {
                    "sku": producto_db['sku'],
                    "nombre": producto_db['nombre'],
                    "nivel_educativo": producto_db['nivel_educativo'],
                    "escuela": producto_db['escuela'],
                    "color": producto_db['color'],
                    "tipo_prenda": producto_db['tipo_prenda'],
                    "tipo_pieza": producto_db['tipo_pieza'],
                    "genero": producto_db['genero'],
                    "atributo": producto_db['atributo'],
                    "ubicacion": producto_db['ubicacion'],
                    "escudo": producto_db['escudo'],
                    "marca": producto_db['marca'],
                    "talla": producto_db['talla'],
                    "inventario": producto_db['inventario'],
                    "ventas": producto_db['ventas'],
                    "precio": producto_db['precio'],
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
                        logger.debug(f"Actualizando {field} con valor: {display_value}, color: {color} en tienda {self.store_id}")
                        self.detail_labels[field].configure(text=display_value, text_color=color)
                        continue
                    if field == "ubicacion":
                        display_value = display_value if display_value else ""
                    logger.debug(f"Actualizando {field} con valor: {display_value} en tienda {self.store_id}")
                    self.detail_labels[field].configure(text=display_value, text_color="#4B5EAA")

                image_path = producto_db['image_path']
                logger.debug(f"Intentando cargar imagen desde: {image_path} en tienda {self.store_id}")
                if image_path:
                    image_path_absolute = os.path.join(CONFIG['ROOT_FOLDER'], image_path)
                    logger.debug(f"Ruta absoluta de la imagen: {image_path_absolute} en tienda {self.store_id}")
                    if os.path.exists(image_path_absolute):
                        img = Image.open(image_path_absolute)
                        img.thumbnail((90, 90), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(img)
                        self.image_label.configure(image=photo, text="")
                        self.image_label.image = photo
                        logger.debug(f"Imagen del producto cargada exitosamente en tienda {self.store_id}")
                    else:
                        logger.warning(f"Archivo de imagen no encontrado: {image_path_absolute} en tienda {self.store_id}")
                        self.image_label.configure(text="Archivo de imagen no encontrado")
                    self.image_label.image = None
                else:
                    logger.debug(f"El producto no tiene imagen asociada en tienda {self.store_id}")
                    self.image_label.configure(text="Sin imagen")
                    self.image_label.image = None
        except Exception as e:
            logger.error(f"Error al mostrar detalles para SKU {sku} en tienda {self.store_id}: {str(e)}")
            messagebox.showerror("Error", f"Error al mostrar detalles: {str(e)}")

    def buscar_y_agregar(self):
        query = self.entry_busqueda.get().strip()
        logger.debug(f"Buscando producto con query: '{query}' en tienda {self.store_id}")
        try:
            cantidad = int(self.entry_cantidad.get())
            descuento = float(self.entry_descuento.get())
            if cantidad <= 0:
                messagebox.showerror("Error", "La cantidad debe ser mayor a 0.")
                logger.warning(f"Intento de agregar producto con cantidad inválida: {cantidad} en tienda {self.store_id}")
                return
            if descuento < 0:
                messagebox.showerror("Error", "El descuento no puede ser negativo.")
                logger.warning(f"Intento de agregar producto con descuento negativo: {descuento} en tienda {self.store_id}")
                return

            # Check cache first
            if query in self.product_cache:
                productos = self.product_cache[query]
            else:
                productos = self.db_manager.buscar_productos(query=query, store_id=self.store_id, limit=1)
                self.product_cache[query] = productos

            if not productos:
                messagebox.showinfo("No encontrado", "No se encontró el producto.")
                logger.info(f"Producto no encontrado para query: '{query}' en tienda {self.store_id}")
                return

            sku, nombre, precio, inventario = productos[0]['sku'], productos[0]['nombre'], productos[0]['precio'], productos[0]['inventario']
            
            # Calcular cantidad total para este SKU (existente + nueva)
            cantidad_total = cantidad
            for item in self.items:
                if item['sku'] == sku:
                    cantidad_total += item['cantidad']
            
            if not self.db_manager.validar_stock(sku, cantidad_total, self.store_id):
                messagebox.showerror("Error", f"Stock insuficiente para '{nombre}' (disponible: {inventario}, requerido: {cantidad_total}).")
                logger.warning(f"Stock insuficiente para '{nombre}' (SKU: {sku}, disponible: {inventario}, requerido: {cantidad_total}) en tienda {self.store_id}")
                return

            # Agregar o actualizar el item
            self.agregar_o_actualizar_item(sku, nombre, cantidad, precio, descuento)
            self.actualizar_tabla()
            self.entry_busqueda.delete(0, "end")
            self.entry_cantidad.delete(0, "end")
            self.entry_cantidad.insert(0, "1")
            self.entry_descuento.delete(0, "end")
            self.entry_descuento.insert(0, "0")
            self.entry_busqueda.focus_set()
            logger.info(f"Producto '{nombre}' procesado (SKU: {sku}, Cantidad añadida: {cantidad}, Descuento: ${descuento}) en tienda {self.store_id}")
        except ValueError:
            messagebox.showerror("Error", "Por favor, ingrese una cantidad y descuento válidos (números).")
            logger.error(f"Entrada inválida: cantidad={self.entry_cantidad.get()}, descuento={self.entry_descuento.get()} en tienda {self.store_id}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al añadir producto: {str(e)}. Verifique el SKU o contacte al soporte.")
            logger.error(f"Error al añadir producto en tienda {self.store_id}: {str(e)}")

    def eliminar_item(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Selección", "Seleccione un producto para eliminar.")
            logger.warning(f"Intento de eliminar producto sin selección en tienda {self.store_id}")
            return
        if len(selected) > 1:
            messagebox.showinfo("Selección", "Seleccione solo un producto para eliminar.")
            logger.warning(f"Intento de eliminar múltiples productos en tienda {self.store_id}")
            return

        index = int(self.tree.index(selected[0]))
        item = self.items[index]
        
        # Reducir cantidad en 1
        item['cantidad'] -= 1
        if item['cantidad'] <= 0:
            self.items.pop(index)
            logger.info(f"Producto eliminado completamente: {item['nombre']} (SKU: {item['sku']}) en tienda {self.store_id}")
        else:
            # Ajustar descuento proporcionalmente
            item['descuento'] = (item['descuento'] / (item['cantidad'] + 1)) * item['cantidad']
            logger.info(f"Cantidad reducida: {item['nombre']} (SKU: {item['sku']}, Nueva cantidad: {item['cantidad']}) en tienda {self.store_id}")
        
        self.actualizar_tabla()

    def omitir_cliente(self):
        self.id_cliente = None
        self.cliente_nombre = None
        self.entry_cliente.delete(0, "end")
        self.entry_cliente.insert(0, "Cliente omitido")
        self.entry_cliente.configure(state="disabled")
        logger.info(f"Cliente omitido para la venta en tienda {self.store_id}")

    def gestionar_descuento_total(self):
        def aplicar_descuento(porcentaje):
            try:
                self.descuento_total = float(porcentaje)
                self.actualizar_tabla()
                dialog.destroy()
                logger.info(f"Descuento total aplicado: {self.descuento_total}% en tienda {self.store_id}")
            except ValueError:
                messagebox.showerror("Error", "Porcentaje inválido. Ingrese un número válido.")
                logger.error(f"Porcentaje inválido ingresado: {porcentaje} en tienda {self.store_id}")

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
                proporcion = subtotal_item / subtotal if subtotal > 0 else 0
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

    def imprimir_ticket(self, cantidad_recibida=None, cambio=None):
        if not self.items:
            messagebox.showerror("Error", "No hay productos para imprimir un ticket.")
            logger.warning(f"Intento de imprimir ticket sin productos en tienda {self.store_id}")
            return
        try:
            sale_id = self.db_manager.get_last_sale_id(self.store_id)
            items = [
                {
                    "nombre": item["nombre"],
                    "cantidad": item["cantidad"],
                    "precio": item["precio"]
                }
                for item in self.items
            ]
            header_data = {
                "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Cliente": self.cliente_nombre or "Sin cliente",
                "Venta ID": sale_id,
                "Método de pago": self.combo_pago.get(),
                "Descuento Total (%)": f"{self.descuento_total:.2f}",
                "Cantidad Recibida": f"${cantidad_recibida:.2f}" if cantidad_recibida is not None else "N/A",
                "Cambio": f"${cambio:.2f}" if cambio is not None else "N/A"
            }
            filename = f"ticket_venta_{sale_id}.pdf"
            output_dir = os.path.join(CONFIG['ROOT_FOLDER'], CONFIG['SALES_REPORTS_DIR'])
            success = generar_ticket_pdf(filename, items, header_data, ticket_type="venta", output_dir=output_dir)
            if success:
                pdf_path = os.path.join(output_dir, filename)
                messagebox.showinfo("Éxito", f"Ticket guardado en: {pdf_path}")
                logger.info(f"Ticket de venta {filename} generado correctamente en tienda {self.store_id}")
                return pdf_path
            else:
                messagebox.showerror("Error", "No se pudo generar el ticket de venta.")
                logger.error(f"Error al generar el ticket de venta {filename} en tienda {self.store_id}")
                return None
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el ticket: {str(e)}")
            logger.error(f"Error al generar ticket en tienda {self.store_id}: {str(e)}")
            return None

    def mostrar_ventana_descuento_y_pago(self, callback):
        # Calcular total actual para mostrar en la ventana
        subtotal = sum(item['cantidad'] * item['precio'] for item in self.items)
        total_descuento_items = sum(item['descuento'] for item in self.items)
        subtotal_despues_descuentos = subtotal - total_descuento_items

        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Finalizar Venta")
        dialog.geometry("400x400")
        dialog.transient(self.root)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="¿Venta con descuento?", font=("Arial", 14, "bold")).pack(pady=10)

        def aplicar_descuento(porcentaje):
            self.descuento_total = porcentaje
            self.actualizar_tabla()
            total = float(self.label_total.cget("text").replace("Total: $", ""))
            mostrar_ventana_pago(total)

        def mostrar_ventana_pago(total):
            dialog_pago = ctk.CTkToplevel(self.root)
            dialog_pago.title("Ingresar Pago")
            dialog_pago.geometry("400x300")
            dialog_pago.transient(self.root)
            dialog_pago.grab_set()

            ctk.CTkLabel(dialog_pago, text=f"Total a pagar: ${total:.2f}", font=("Arial", 14, "bold")).pack(pady=10)

            ctk.CTkLabel(dialog_pago, text="Cantidad recibida ($):", font=("Arial", 12, "bold")).pack(pady=5)
            entry_recibido = ctk.CTkEntry(dialog_pago, width=100)
            entry_recibido.pack(pady=5)
            entry_recibido.focus_set()

            label_cambio = ctk.CTkLabel(dialog_pago, text="Cambio: $0.00", font=("Arial", 12, "bold"))
            label_cambio.pack(pady=10)

            def calcular_cambio(event=None):
                try:
                    recibido = float(entry_recibido.get())
                    if recibido < total:
                        messagebox.showerror("Error", "La cantidad recibida es menor al total.")
                        return
                    cambio = recibido - total
                    label_cambio.configure(text=f"Cambio: ${cambio:.2f}")
                except ValueError:
                    label_cambio.configure(text="Cambio: $0.00")

            def confirmar_pago():
                try:
                    recibido = float(entry_recibido.get())
                    if recibido < total:
                        messagebox.showerror("Error", "La cantidad recibida es menor al total.")
                        return
                    cambio = recibido - total
                    dialog_pago.destroy()
                    dialog.destroy()
                    callback(recibido, cambio)
                except ValueError:
                    messagebox.showerror("Error", "Por favor, ingrese una cantidad válida.")

            entry_recibido.bind("<KeyRelease>", calcular_cambio)
            entry_recibido.bind("<Return>", lambda event: confirmar_pago())

            ctk.CTkButton(dialog_pago, text="Confirmar Pago", command=confirmar_pago, fg_color="#4CAF50", hover_color="#45A049").pack(pady=10)
            ctk.CTkButton(dialog_pago, text="Cancelar", command=lambda: [dialog_pago.destroy(), dialog.destroy()], fg_color="#F44336", hover_color="#D32F2F").pack(pady=5)

        ctk.CTkButton(dialog, text="Precio Normal (0%)", command=lambda: aplicar_descuento(0), fg_color="#2196F3", hover_color="#1976D2").pack(pady=5)
        ctk.CTkButton(dialog, text="5% Descuento", command=lambda: aplicar_descuento(5), fg_color="#FF5722", hover_color="#E64A19").pack(pady=5)
        ctk.CTkButton(dialog, text="10% Descuento", command=lambda: aplicar_descuento(10), fg_color="#FF5722", hover_color="#E64A19").pack(pady=5)

        ctk.CTkButton(dialog, text="Cancelar", command=dialog.destroy, fg_color="#F44336", hover_color="#D32F2F").pack(pady=10)

        # Atajos de teclado para selección rápida
        dialog.bind("1", lambda event: aplicar_descuento(0))
        dialog.bind("2", lambda event: aplicar_descuento(5))
        dialog.bind("3", lambda event: aplicar_descuento(10))

    def finalizar_venta(self):
        if not self.items:
            messagebox.showerror("Error", "No hay productos en la venta.")
            logger.warning(f"Intento de finalizar venta sin productos en tienda {self.store_id}")
            return

        def procesar_venta(cantidad_recibida, cambio):
            try:
                metodo_pago = self.combo_pago.get()
                id_venta = self.db_manager.registrar_venta(
                    user_id=self.user_id,
                    items=self.items,
                    metodo_pago=metodo_pago,
                    id_cliente=self.id_cliente,
                    tasa_iva=0,
                    store_id=self.store_id
                )
                with self.db_manager as db:
                    cursor = db.get_cursor()
                    for item in self.items:
                        cursor.execute(
                            "UPDATE productos SET inventario = inventario - ? WHERE sku = ? AND store_id = ?",
                            (item['cantidad'], item['sku'], self.store_id)
                        )
                    db.connection.commit()
                pdf_path = self.imprimir_ticket(cantidad_recibida, cambio)
                messagebox.showinfo("Éxito", f"Venta registrada con ID: {id_venta}\nCantidad recibida: ${cantidad_recibida:.2f}\nCambio: ${cambio:.2f}\nTicket: {pdf_path}")
                self.cancelar_venta()
                logger.info(f"Venta finalizada: {id_venta}, Cantidad recibida: ${cantidad_recibida:.2f}, Cambio: ${cambio:.2f} en tienda {self.store_id}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo registrar la venta: {str(e)}")
                logger.error(f"Error al finalizar venta en tienda {self.store_id}: {str(e)}")

        self.mostrar_ventana_descuento_y_pago(procesar_venta)

    def cancelar_venta(self):
        self.items = []
        self.id_cliente = None
        self.cliente_nombre = None
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
        logger.info(f"Venta cancelada en tienda {self.store_id}")
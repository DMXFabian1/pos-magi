import customtkinter as ctk
from tkinter import ttk, messagebox
from src.core.config.db_manager import DatabaseManager
import logging
from datetime import datetime
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from src.core.config.config import CONFIG

logger = logging.getLogger(__name__)

class PresupuestosManager:
    def __init__(self, user_id, parent_frame, root, db_manager=None, store_id=1):
        logging.debug("Iniciando PresupuestosManager")
        self.user_id = user_id
        self.parent_frame = parent_frame
        self.root = root
        self.db_manager = db_manager or DatabaseManager()
        self.store_id = store_id
        logging.debug("DatabaseManager creado")

        self.pdf_dir = os.path.join(CONFIG['ROOT_FOLDER'], CONFIG['SALES_REPORTS_DIR'], "presupuestos")
        os.makedirs(self.pdf_dir, exist_ok=True)

        self.main_frame = ctk.CTkFrame(self.parent_frame)
        logging.debug("main_frame creado")

        ctk.CTkLabel(self.main_frame, text="Presupuestos", font=("Arial", 20)).pack(pady=20)
        ctk.CTkButton(self.main_frame, text="Hacer Presupuesto", command=self.iniciar_proceso, width=200, height=50, font=("Arial", 16)).pack(pady=20)
        logging.debug("Pantalla inicial configurada")

        logger.info(f"Interfaz de gestión de presupuestos inicializada para usuario con ID '{self.user_id}' en tienda {self.store_id}.")

    def iniciar_proceso(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self.main_frame, text="Seleccione la Ubicación", font=("Arial", 20)).pack(pady=20)
        ubicacion_var = ctk.StringVar()

        def seleccionar_ubicacion(ubicacion):
            ubicacion_var.set(ubicacion)
            self.seleccionar_cliente(ubicacion_var)

        ctk.CTkButton(self.main_frame, text="Comunidad", command=lambda: seleccionar_ubicacion("Comunidad"), width=150, height=50, font=("Arial", 16)).pack(pady=10)
        ctk.CTkButton(self.main_frame, text="San Felipe", command=lambda: seleccionar_ubicacion("San Felipe"), width=150, height=50, font=("Arial", 16)).pack(pady=10)

    def seleccionar_cliente(self, ubicacion_var):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        cliente_id_var = ctk.StringVar()
        cliente_nombre_var = ctk.StringVar()

        ctk.CTkLabel(self.main_frame, text="Seleccionar Cliente", font=("Arial", 20)).pack(pady=20)
        cliente_label = ctk.CTkLabel(self.main_frame, textvariable=cliente_nombre_var, text="No seleccionado")
        cliente_label.pack(pady=10)

        def abrir_seleccion_cliente():
            clientes_dialog = ctk.CTkToplevel(self.root)
            clientes_dialog.title("Seleccionar Cliente")
            clientes_dialog.geometry("600x400")
            clientes_dialog.transient(self.main_frame)
            clientes_dialog.grab_set()

            tree_frame = ctk.CTkFrame(clientes_dialog)
            tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
            tree = ttk.Treeview(
                tree_frame,
                columns=("ID", "Nombre Completo", "Teléfono"),
                show="headings"
            )
            tree.heading("ID", text="ID")
            tree.heading("Nombre Completo", text="Nombre Completo")
            tree.heading("Teléfono", text="Teléfono")
            tree.column("ID", width=50)
            tree.column("Nombre Completo", width=250)
            tree.column("Teléfono", width=150)
            tree.pack(side="left", fill="both", expand=True)

            clientes = self.db_manager.buscar_clientes(query="", limit=None)
            for cliente in clientes:
                tree.insert("", "end", values=(
                    cliente['id'],
                    cliente['nombre_completo'],
                    cliente['numero']
                ))

            def confirmar_seleccion():
                selected = tree.selection()
                if not selected:
                    messagebox.showinfo("Selección", "Seleccione un cliente.")
                    return
                item = tree.item(selected[0])
                cliente_id_var.set(item['values'][0])
                cliente_nombre_var.set(item['values'][1])
                clientes_dialog.destroy()
                self.agregar_productos(ubicacion_var, cliente_id_var, cliente_nombre_var)

            ctk.CTkButton(clientes_dialog, text="Seleccionar", command=confirmar_seleccion).pack(pady=10)

        ctk.CTkButton(self.main_frame, text="Seleccionar Cliente", command=abrir_seleccion_cliente, width=150, height=50, font=("Arial", 16)).pack(pady=10)

    def agregar_productos(self, ubicacion_var, cliente_id_var, cliente_nombre_var):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        productos_list = []
        subtotal_var = ctk.DoubleVar(value=0.0)

        ctk.CTkLabel(self.main_frame, text="Agregar Productos", font=("Arial", 20)).pack(pady=20)
        ctk.CTkLabel(self.main_frame, text=f"Cliente: {cliente_nombre_var.get()}", font=("Arial", 14)).pack(pady=5)

        productos_frame = ctk.CTkFrame(self.main_frame)
        productos_frame.pack(fill="both", expand=True, padx=10, pady=5)
        productos_container = ctk.CTkFrame(productos_frame)
        productos_container.pack(fill="both", expand=True, padx=5, pady=5)
        productos_entries = []

        def agregar_producto():
            frame = ctk.CTkFrame(productos_container)
            frame.pack(fill="x", pady=2)
            ctk.CTkLabel(frame, text="SKU:").pack(side="left", padx=5)
            entry_sku = ctk.CTkEntry(frame, width=100)
            entry_sku.pack(side="left", padx=5)

            ctk.CTkLabel(frame, text="Nombre:").pack(side="left", padx=5)
            label_nombre = ctk.CTkLabel(frame, text="N/A", width=150)
            label_nombre.pack(side="left", padx=5)

            ctk.CTkLabel(frame, text="Precio:").pack(side="left", padx=5)
            label_precio = ctk.CTkLabel(frame, text="0.0", width=50)
            label_precio.pack(side="left", padx=5)

            ctk.CTkLabel(frame, text="Cantidad:").pack(side="left", padx=5)
            entry_cantidad = ctk.CTkEntry(frame, width=50)
            entry_cantidad.pack(side="left", padx=5)

            def actualizar_info_producto(*args):
                sku = entry_sku.get().strip()
                if sku:
                    producto = self.db_manager.buscar_productos(sku, limit=1, store_id=self.store_id)
                    if producto:
                        label_nombre.configure(text=producto[0]['nombre'])
                        label_precio.configure(text=str(producto[0]['precio']))
                        try:
                            cantidad = int(entry_cantidad.get()) if entry_cantidad.get() else 0
                            if cantidad > 0 and not self.db_manager.validar_stock(sku, cantidad, store_id=self.store_id):
                                messagebox.showwarning("Advertencia", f"No hay suficiente inventario para el producto {sku}.")
                        except ValueError:
                            pass
                    else:
                        label_nombre.configure(text="Producto no encontrado")
                        label_precio.configure(text="0.0")
                actualizar_resumen()

            def actualizar_resumen(*args):
                productos_temp = []
                for entry_sku, _, label_precio, entry_cantidad, _ in productos_entries:
                    try:
                        sku = entry_sku.get().strip()
                        cantidad = int(entry_cantidad.get()) if entry_cantidad.get() else 0
                        precio = float(label_precio.cget("text"))
                        if sku and cantidad > 0:
                            productos_temp.append({
                                "sku": sku,
                                "cantidad": cantidad,
                                "precio": precio,
                                "descuento": 0
                            })
                    except ValueError:
                        continue
                productos_list.clear()
                productos_list.extend(productos_temp)
                subtotal = sum(item['cantidad'] * item['precio'] for item in productos_list)
                subtotal_var.set(subtotal)

            entry_sku.bind("<KeyRelease>", actualizar_info_producto)
            entry_cantidad.bind("<KeyRelease>", actualizar_resumen)

            def eliminar_producto():
                frame.destroy()
                productos_entries.remove((entry_sku, label_nombre, label_precio, entry_cantidad, frame))
                actualizar_resumen()

            ctk.CTkButton(frame, text="Eliminar", command=eliminar_producto, fg_color="red").pack(side="left", padx=5)
            productos_entries.append((entry_sku, label_nombre, label_precio, entry_cantidad, frame))
            actualizar_resumen()

        ctk.CTkButton(productos_frame, text="Agregar Producto", command=agregar_producto).pack(anchor="w", padx=5, pady=5)
        agregar_producto()

        resumen_frame = ctk.CTkFrame(self.main_frame)
        resumen_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(resumen_frame, text="Subtotal:").pack(anchor="w", padx=5)
        ctk.CTkLabel(resumen_frame, textvariable=subtotal_var).pack(anchor="w", padx=20)

        def generar_presupuesto():
            if not cliente_id_var.get():
                messagebox.showerror("Error", "Seleccione un cliente.")
                return
            
            productos = []
            for entry_sku, _, label_precio, entry_cantidad, _ in productos_entries:
                sku = entry_sku.get().strip()
                cantidad = entry_cantidad.get().strip()
                if not sku or not cantidad:
                    messagebox.showerror("Error", "Complete todos los campos de los productos.")
                    return
                try:
                    cantidad = int(cantidad)
                    if cantidad <= 0:
                        raise ValueError
                except ValueError:
                    messagebox.showerror("Error", f"La cantidad debe ser un número entero positivo.")
                    return
                producto = self.db_manager.buscar_productos(sku, limit=1, store_id=self.store_id)
                if not producto:
                    messagebox.showerror("Error", f"No se encontró el producto con SKU {sku}.")
                    return
                productos.append({
                    "sku": sku,
                    "nombre": producto[0]['nombre'],
                    "cantidad": cantidad,
                    "precio": producto[0]['precio'],
                    "descuento": 0
                })
            
            if not productos:
                messagebox.showerror("Error", "Debe agregar al menos un producto.")
                return
            
            try:
                cliente_id = int(cliente_id_var.get())
                cliente = self.db_manager.get_cliente(cliente_id)
                if not cliente:
                    raise ValueError("Cliente no encontrado")
                
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                folio = f"PRES-{timestamp}-{cliente_id}"
                
                pdf_path = os.path.join(self.pdf_dir, f"presupuesto_{folio}.pdf")
                c = canvas.Canvas(pdf_path, pagesize=letter)
                width, height = letter
                
                c.setFont("Helvetica-Bold", 16)
                c.drawString(100, height - 50, "ClothesApp - Presupuesto")
                c.setFont("Helvetica", 12)
                c.drawString(100, height - 70, f"Folio: {folio}")
                c.drawString(100, height - 90, f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                c.drawString(100, height - 110, f"Ubicación: {ubicacion_var.get()}")
                
                c.setFont("Helvetica-Bold", 14)
                c.drawString(100, height - 150, "Cliente")
                c.setFont("Helvetica", 12)
                c.drawString(100, height - 170, f"Nombre: {cliente['nombre_completo']}")
                c.drawString(100, height - 190, f"Teléfono: {cliente['numero']}")
                
                c.setFont("Helvetica-Bold", 14)
                c.drawString(100, height - 230, "Productos")
                y = height - 250
                c.setFont("Helvetica", 12)
                c.drawString(100, y, "SKU")
                c.drawString(150, y, "Nombre")
                c.drawString(300, y, "Cantidad")
                c.drawString(350, y, "Precio Unitario")
                c.drawString(450, y, "Subtotal")
                y -= 20
                
                total = 0
                for producto in productos:
                    subtotal = producto['cantidad'] * producto['precio']
                    total += subtotal
                    c.drawString(100, y, producto['sku'])
                    c.drawString(150, y, producto['nombre'])
                    c.drawString(300, y, str(producto['cantidad']))
                    c.drawString(350, y, f"${producto['precio']:.2f}")
                    c.drawString(450, y, f"${subtotal:.2f}")
                    y -= 20
                
                y -= 20
                c.setFont("Helvetica-Bold", 14)
                c.drawString(100, y, f"Total: ${total:.2f}")
                
                y -= 40
                c.setFont("Helvetica", 10)
                c.drawString(100, y, "Nota: Este presupuesto es válido por 7 días a partir de la fecha de emisión.")
                
                c.showPage()
                c.save()
                
                messagebox.showinfo("Éxito", f"Presupuesto generado: {pdf_path}")
                self.main_frame.destroy()
                self.__init__(self.user_id, self.parent_frame, self.root, self.db_manager, self.store_id)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo generar el presupuesto: {str(e)}")
                logger.error(f"Error al generar presupuesto en tienda {self.store_id}: {str(e)}")

        ctk.CTkButton(self.main_frame, text="Generar Presupuesto", command=generar_presupuesto, width=150, height=50, font=("Arial", 16)).pack(pady=20)

    def pack(self, **kwargs):
        self.main_frame.pack(**kwargs)
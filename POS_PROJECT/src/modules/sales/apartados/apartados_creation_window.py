import customtkinter as ctk
from tkinter import ttk, messagebox
import logging
import os
import webbrowser
from src.utils.ui_utils import mostrar_ventana_seleccion

logger = logging.getLogger(__name__)

class ApartadoCreationWindow:
    def __init__(self, root, user_id, items, descuento_total, db_manager, pos_ventas, store_id=1):
        self.root = root
        self.user_id = user_id
        self.items = items  # Lista de ítems que se puede modificar
        self.descuento_total = descuento_total
        self.db_manager = db_manager
        self.pos_ventas = pos_ventas
        self.store_id = store_id  # Añadir store_id
        self.id_cliente = None

        self.window = ctk.CTkToplevel(self.root)
        self.window.title("Crear Apartado")
        self.window.geometry("900x700")
        self.window.transient(self.root)
        self.window.grab_set()
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)  # Manejar cierre de ventana
        logger.debug(f"Ventana de creación de apartado inicializada para tienda {self.store_id}")

        # Usar un CTkScrollableFrame para permitir desplazamiento
        self.scrollable_frame = ctk.CTkScrollableFrame(self.window, fg_color="#f0f0f0")
        self.scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.product_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="#f0f0f0", corner_radius=10)
        self.product_frame.pack(fill="x", padx=0, pady=5)
        ctk.CTkLabel(self.product_frame, text="Productos Seleccionados", font=("Arial", 14, "bold")).pack(pady=5)
        logger.debug("product_frame empaquetado")

        self.tree_container = ctk.CTkFrame(self.product_frame)
        self.tree_container.pack(fill="both", expand=True, padx=5, pady=5)

        self.tree = ttk.Treeview(
            self.tree_container,
            columns=("SKU", "Nombre", "Cantidad", "Precio", "Descuento", "Subtotal"),
            show="headings",
            height=min(len(self.items), 15)
        )
        self.tree.heading("SKU", text="SKU")
        self.tree.heading("Nombre", text="Nombre")
        self.tree.heading("Cantidad", text="Cantidad")
        self.tree.heading("Precio", text="Precio")
        self.tree.heading("Descuento", text="Descuento")
        self.tree.heading("Subtotal", text="Subtotal")
        self.tree.column("SKU", width=115)
        self.tree.column("Nombre", width=200)
        self.tree.column("Cantidad", width=90)
        self.tree.column("Precio", width=90)
        self.tree.column("Descuento", width=90)
        self.tree.column("Subtotal", width=115)

        scrollbar = ttk.Scrollbar(self.tree_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        logger.debug("tree creado y empaquetado")

        # Botón para eliminar producto
        self.button_remove = ctk.CTkButton(
            self.product_frame,
            text="Eliminar Producto",
            command=self.eliminar_producto,
            fg_color="#F44336",
            hover_color="#D32F2F"
        )
        self.button_remove.pack(side="right", padx=5, pady=5)
        logger.debug("button_remove empaquetado")

        self.total_label = ctk.CTkLabel(self.product_frame, text="Total: $0.00", font=("Arial", 12, "bold"))
        self.total_label.pack(pady=5)

        self.anticipo_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="#f0f0f0", corner_radius=10)
        self.anticipo_frame.pack(fill="x", padx=0, pady=5)
        ctk.CTkLabel(self.anticipo_frame, text="Anticipo ($):", font=("Arial", 12, "bold")).pack(side="left", padx=5)
        self.entry_anticipo = ctk.CTkEntry(self.anticipo_frame, width=150, height=30)
        self.entry_anticipo.pack(side="left", padx=5)
        self.entry_anticipo.insert(0, "0.00")
        self.anticipo_error_label = ctk.CTkLabel(self.anticipo_frame, text="", text_color="red", font=("Arial", 10))
        self.anticipo_error_label.pack(side="left", padx=5)
        self.total_pendiente_label = ctk.CTkLabel(self.anticipo_frame, text="Total Pendiente: $0.00", font=("Arial", 12, "bold"))
        self.total_pendiente_label.pack(side="left", padx=10)
        logger.debug("anticipo_frame empaquetado")

        self.entry_anticipo.bind("<KeyRelease>", self.validar_anticipo)

        self.actualizar_tabla_productos()

        self.cliente_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="#f0f0f0", corner_radius=10)
        self.cliente_frame.pack(fill="x", padx=0, pady=5)
        ctk.CTkLabel(self.cliente_frame, text="Cliente (Nombre/Teléfono):", font=("Arial", 12, "bold")).pack(side="left", padx=5)
        self.entry_cliente = ctk.CTkEntry(self.cliente_frame, width=250, height=30)
        self.entry_cliente.pack(side="left", padx=5)
        self.entry_cliente.bind("<Return>", lambda event: self.buscar_cliente())
        ctk.CTkButton(self.cliente_frame, text="Buscar Cliente", command=self.buscar_cliente, fg_color="#2196F3", hover_color="#1976D2").pack(side="left", padx=5)
        ctk.CTkButton(self.cliente_frame, text="Agregar Cliente", command=self.agregar_cliente, fg_color="#4CAF50", hover_color="#45A049").pack(side="left", padx=5)
        ctk.CTkButton(self.cliente_frame, text="Limpiar Cliente", command=self.limpiar_cliente, fg_color="#9E9E9E", hover_color="#757575").pack(side="left", padx=5)
        logger.debug("cliente_frame empaquetado")

        self.action_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="#f0f0f0", corner_radius=10)
        self.action_frame.pack(fill="x", padx=0, pady=5)
        ctk.CTkButton(self.action_frame, text="Confirmar Apartado (F10)", command=self.confirmar_apartado, fg_color="#FF9800", hover_color="#F57C00").pack(side="left", padx=5)
        ctk.CTkButton(self.action_frame, text="Cancelar (Esc)", command=self.on_closing, fg_color="#F44336", hover_color="#D32F2F").pack(side="left", padx=5)
        logger.debug("action_frame empaquetado")

        self.window.bind("<F10>", lambda event: self.confirmar_apartado())
        self.window.bind("<Escape>", lambda event: self.on_closing())
        self.window.bind("<Control-f>", lambda event: self.entry_cliente.focus_set() if self.window.winfo_exists() else None)
        self.window.bind("<F3>", lambda event: self.entry_cliente.focus_set() if self.window.winfo_exists() else None)

    def on_closing(self):
        """Maneja el cierre de la ventana, desvinculando eventos para evitar errores."""
        # Desvincular eventos de teclas para evitar interacciones después del cierre
        self.window.unbind("<F10>")
        self.window.unbind("<Escape>")
        self.window.unbind("<Control-f>")
        self.window.unbind("<F3>")
        logger.debug(f"Ventana de creación de apartado cerrada para tienda {self.store_id}")
        self.window.destroy()

    def combinar_productos(self):
        """Combina productos con el mismo SKU en self.items, sumando sus cantidades."""
        combined_items = []
        sku_dict = {}

        for item in self.items:
            sku = item['sku']
            if sku in sku_dict:
                sku_dict[sku]['cantidad'] += item['cantidad']
            else:
                sku_dict[sku] = item.copy()

        combined_items = list(sku_dict.values())
        self.items.clear()
        self.items.extend(combined_items)

    def actualizar_tabla_productos(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.combinar_productos()

        # Filtrar productos con cantidad cero
        self.items = [item for item in self.items if item['cantidad'] > 0]
        if len(self.items) != len(self.items):
            logger.info("Productos con cantidad cero fueron eliminados de la lista.")

        subtotal = 0
        total_descuento_items = 0
        for idx, item in enumerate(self.items):
            subtotal_item = item['cantidad'] * item['precio'] - item['descuento']
            self.tree.insert("", "end", values=(
                item['sku'],
                item['nombre'],
                item['cantidad'],
                f"${item['precio']:.2f}",
                f"${item['descuento']:.2f}",
                f"${subtotal_item:.2f}"
            ))
            subtotal += item['cantidad'] * item['precio']
            total_descuento_items += item['descuento']

        subtotal_despues_descuentos = subtotal - total_descuento_items
        descuento_total = (subtotal_despues_descuentos * self.descuento_total) / 100
        total = subtotal_despues_descuentos - descuento_total
        self.total_label.configure(text=f"Total: ${total:.2f}")
        logger.debug(f"Tabla de productos actualizada, total: ${total:.2f} para tienda {self.store_id}")

        self.tree.configure(height=min(len(self.items), 15))
        self.validar_anticipo()

        if not self.items:
            self.button_remove.configure(state="disabled")
        else:
            self.button_remove.configure(state="normal")

    def restar_producto(self, index):
        if 0 <= index < len(self.items):
            self.items[index]['cantidad'] -= 1
            if self.items[index]['cantidad'] <= 0:
                self.items.pop(index)
                logger.info(f"Producto en índice {index} eliminado por cantidad cero para tienda {self.store_id}.")
            self.actualizar_tabla_productos()
            logger.info(f"Producto restado en índice {index}, nueva cantidad: {self.items[index]['cantidad'] if index < len(self.items) else 'eliminado'} para tienda {self.store_id}")

    def eliminar_producto(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Selección", "Seleccione un producto para eliminar")
            logger.warning(f"Intento de eliminar producto sin selección para tienda {self.store_id}")
            return
        if len(selected) > 1:
            messagebox.showinfo("Selección", "Seleccione solo un producto para eliminar")
            logger.warning(f"Intento de eliminar múltiples productos para tienda {self.store_id}")
            return

        index = int(self.tree.index(selected[0]))
        item = self.items.pop(index)
        self.actualizar_tabla_productos()
        logger.info(f"Producto eliminado del apartado: {item['nombre']} (SKU: {item['sku']}) para tienda {self.store_id}")

    def validar_anticipo(self, event=None):
        try:
            anticipo = float(self.entry_anticipo.get())
            subtotal = sum(item['cantidad'] * item['precio'] for item in self.items)
            total_descuento_items = sum(item['descuento'] for item in self.items)
            subtotal_despues_descuentos = subtotal - total_descuento_items
            descuento_total = (subtotal_despues_descuentos * self.descuento_total) / 100
            total = subtotal_despues_descuentos - descuento_total

            total_pendiente = total - anticipo
            self.total_pendiente_label.configure(text=f"Total Pendiente: ${total_pendiente:.2f}")

            if anticipo <= 0:
                self.entry_anticipo.configure(border_color="red")
                self.anticipo_error_label.configure(text="El anticipo debe ser mayor a 0")
                return False
            elif anticipo > total:
                self.entry_anticipo.configure(border_color="red")
                self.anticipo_error_label.configure(text=f"El anticipo no puede ser mayor a ${total:.2f}")
                return False
            else:
                self.entry_anticipo.configure(border_color="green")
                self.anticipo_error_label.configure(text="")
                return True
        except ValueError:
            self.entry_anticipo.configure(border_color="red")
            self.anticipo_error_label.configure(text="El anticipo debe ser un número válido")
            subtotal = sum(item['cantidad'] * item['precio'] for item in self.items)
            total_descuento_items = sum(item['descuento'] for item in self.items)
            subtotal_despues_descuentos = subtotal - total_descuento_items
            descuento_total = (subtotal_despues_descuentos * self.descuento_total) / 100
            total = subtotal_despues_descuentos - descuento_total
            self.total_pendiente_label.configure(text=f"Total Pendiente: ${total:.2f}")
            return False

    def limpiar_cliente(self):
        self.id_cliente = None
        self.entry_cliente.delete(0, "end")
        logger.info(f"Cliente deseleccionado para tienda {self.store_id}")

    def mostrar_ventana_seleccion_clientes(self, clientes):
        columns = ["ID", "Nombre Completo", "Teléfono"]
        column_widths = {"ID": 50, "Nombre Completo": 250, "Teléfono": 150}
        formatted_clientes = [
            {
                "ID": cliente['id'],
                "Nombre Completo": cliente['nombre_completo'],
                "Teléfono": cliente['numero'] if cliente['numero'] else "N/A"
            }
            for cliente in clientes
        ]

        def on_select(cliente):
            self.id_cliente = cliente['ID']
            self.entry_cliente.delete(0, "end")
            self.entry_cliente.insert(0, cliente['Nombre Completo'])
            logger.info(f"Cliente seleccionado: {cliente['Nombre Completo']} (ID: {cliente['ID']}) para tienda {self.store_id}")

        mostrar_ventana_seleccion(
            parent=self.window,
            title="Seleccionar Cliente",
            items=formatted_clientes,
            columns=columns,
            column_widths=column_widths,
            on_select_callback=on_select
        )

    def buscar_cliente(self):
        query = self.entry_cliente.get().strip()
        try:
            clientes = self.db_manager.buscar_clientes(query=query, store_id=self.store_id, limit=50)
            if not clientes:
                messagebox.showinfo("No encontrado", f"No se encontraron clientes para la búsqueda: '{query}'")
                return
            self.mostrar_ventana_seleccion_clientes(clientes)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo buscar clientes: {str(e)}")
            logger.error(f"Error al buscar clientes para tienda {self.store_id}: {str(e)}")

    def agregar_cliente(self):
        try:
            from src.modules.clients.client_manager import ClientManager
            client_manager = ClientManager(
                user_id=self.user_id,
                parent_frame=self.window,
                root=self.root,
                db_manager=self.db_manager,
                store_id=self.store_id
            )
            client_manager.añadir_cliente(callback=self.cliente_creado)
            logger.debug(f"Ventana de creación de cliente abierta para tienda {self.store_id}")
        except ImportError:
            logger.error(f"No se pudo importar ClientManager para tienda {self.store_id}")
            messagebox.showerror("Error", "No se pudo cargar el módulo de gestión de clientes")
        except Exception as e:
            logger.error(f"Error al añadir cliente para tienda {self.store_id}: {str(e)}")
            messagebox.showerror("Error", f"No se pudo añadir el cliente: {str(e)}")

    def cliente_creado(self, id_cliente, nombre_completo):
        if id_cliente and nombre_completo:
            self.id_cliente = id_cliente
            self.entry_cliente.delete(0, "end")
            self.entry_cliente.insert(0, nombre_completo)
            messagebox.showinfo("Éxito", f"Cliente '{nombre_completo}' creado y seleccionado")
            logger.info(f"Cliente creado y seleccionado: {nombre_completo} (ID: {id_cliente}) para tienda {self.store_id}")
        else:
            logger.debug(f"Cliente no creado, no se seleccionará para tienda {self.store_id}")

    def mostrar_resumen_apartado(self, anticipo, total, total_pendiente):
        dialog = ctk.CTkToplevel(self.window)
        dialog.title("Confirmar Apartado")
        dialog.geometry("500x400")
        dialog.transient(self.window)
        dialog.grab_set()

        text_frame = ctk.CTkFrame(dialog)
        text_frame.pack(fill="both", expand=True, padx=10, pady=10)

        resumen = "Resumen del Apartado\n\n"
        resumen += f"Cliente: {self.entry_cliente.get()}\n\n"
        resumen += "Productos:\n"
        for item in self.items:
            subtotal_item = item['cantidad'] * item['precio'] - item['descuento']
            resumen += f"- {item['sku']} ({item['nombre']}): {item['cantidad']} x ${item['precio']:.2f} (Desc: ${item['descuento']:.2f}) = ${subtotal_item:.2f}\n"
        resumen += f"\nTotal: ${total:.2f}\n"
        resumen += f"Anticipo: ${anticipo:.2f}\n"
        resumen += f"Total Pendiente: ${total_pendiente:.2f}\n\n"
        resumen += "¿Desea confirmar el apartado?"

        textbox = ctk.CTkTextbox(text_frame, wrap="word", height=300, width=450)
        textbox.pack(side="left", fill="both", expand=True)
        textbox.insert("1.0", resumen)
        textbox.configure(state="disabled")

        scrollbar = ctk.CTkScrollbar(text_frame, command=textbox.yview)
        scrollbar.pack(side="right", fill="y")
        textbox.configure(yscrollcommand=scrollbar.set)

        button_frame = ctk.CTkFrame(dialog)
        button_frame.pack(fill="x", padx=10, pady=5)

        def confirmar():
            dialog.destroy()
            try:
                logger.debug(f"Intentando crear apartado para cliente {self.id_cliente} con anticipo {anticipo} en tienda {self.store_id}")
                # Llamar a pos_ventas.crear_apartado
                result = self.pos_ventas.crear_apartado(id_cliente=self.id_cliente, anticipo=anticipo)

                if result["success"]:
                    logger.info(f"Apartado creado exitosamente: ID {result['apartado_id']} para tienda {self.store_id}")
                    # Mostrar diálogo de éxito con opción para abrir comprobantes
                    success_dialog = ctk.CTkToplevel(self.window)
                    success_dialog.title("Apartado Creado")
                    success_dialog.geometry("400x250")
                    success_dialog.transient(self.window)
                    success_dialog.grab_set()

                    msg = f"Apartado ID {result['apartado_id']} creado exitosamente.\n"
                    msg += "Se generaron un comprobante y un ticket PDF."
                    ctk.CTkLabel(success_dialog, text=msg, wraplength=350).pack(pady=10)

                    receipt_path = result.get("receipt_path")
                    if receipt_path:
                        ctk.CTkButton(
                            success_dialog,
                            text="Abrir Comprobante",
                            command=lambda: webbrowser.open(f"file://{os.path.abspath(receipt_path)}")
                        ).pack(pady=5)

                    pdf_path = result.get("pdf_path")
                    if pdf_path:
                        ctk.CTkButton(
                            success_dialog,
                            text="Abrir Ticket PDF",
                            command=lambda: webbrowser.open(f"file://{os.path.abspath(pdf_path)}")
                        ).pack(pady=5)

                    ctk.CTkButton(success_dialog, text="Cerrar", command=success_dialog.destroy).pack(pady=10)

                    self.on_closing()  # Usar on_closing para cerrar la ventana de manera segura
                    logger.info(f"Apartado creado: ID {result['apartado_id']}, Comprobante: {receipt_path}, Ticket PDF: {pdf_path} para tienda {self.store_id}")
                else:
                    logger.error(f"Error al crear apartado para tienda {self.store_id}: {result['message']}")
                    messagebox.showerror("Error", result["message"])

            except Exception as e:
                logger.error(f"Excepción al crear apartado para cliente {self.id_cliente} en tienda {self.store_id}: {str(e)}", exc_info=True)
                messagebox.showerror("Error", f"No se pudo crear el apartado: {str(e)}")

        ctk.CTkButton(button_frame, text="Confirmar", command=confirmar, fg_color="#4CAF50", hover_color="#45A049").pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Cancelar", command=dialog.destroy, fg_color="#F44336", hover_color="#D32F2F").pack(side="left", padx=5)

    def confirmar_apartado(self):
        if not self.items:
            messagebox.showerror("Error", "Debe haber al menos un producto en el apartado")
            logger.warning(f"Intento de confirmar apartado sin productos para tienda {self.store_id}")
            return

        # Validar que no haya productos con cantidad cero
        for item in self.items:
            if item['cantidad'] <= 0:
                messagebox.showerror("Error", f"El producto {item['nombre']} (SKU: {item['sku']}) tiene cantidad cero. Por favor, elimine o ajuste la cantidad.")
                logger.warning(f"Intento de confirmar apartado con producto en cantidad cero: {item['nombre']} (SKU: {item['sku']}) para tienda {self.store_id}")
                return

        if not self.id_cliente:
            messagebox.showerror("Error", "Debe seleccionar un cliente para el apartado")
            logger.warning(f"Intento de confirmar apartado sin cliente seleccionado para tienda {self.store_id}")
            return

        if not self.validar_anticipo():
            messagebox.showerror("Error", "Por favor, corrija el valor del anticipo antes de continuar.")
            return

        try:
            anticipo = float(self.entry_anticipo.get())
            subtotal = sum(item['cantidad'] * item['precio'] for item in self.items)
            total_descuento_items = sum(item['descuento'] for item in self.items)
            subtotal_despues_descuentos = subtotal - total_descuento_items
            descuento_total = (subtotal_despues_descuentos * self.descuento_total) / 100
            total = subtotal_despues_descuentos - descuento_total
            total_pendiente = total - anticipo

            self.mostrar_resumen_apartado(anticipo, total, total_pendiente)

        except ValueError:
            logger.error(f"Entrada inválida para anticipo: {self.entry_anticipo.get()} para tienda {self.store_id}")
            messagebox.showerror("Error", "El anticipo debe ser un número válido")
        except Exception as e:
            logger.error(f"Error inesperado al confirmar apartado para cliente {self.id_cliente} en tienda {self.store_id}: {str(e)}", exc_info=True)
            messagebox.showerror("Error", f"No se pudo confirmar el apartado: {str(e)}")
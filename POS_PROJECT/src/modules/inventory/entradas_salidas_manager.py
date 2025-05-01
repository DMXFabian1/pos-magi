import customtkinter as ctk
from tkinter import ttk, messagebox
import logging
from datetime import datetime
from src.modules.inventory.entradas_salidas_logic import EntradasSalidasLogic
from src.core.config.config import CONFIG

logger = logging.getLogger(__name__)

class EntradasSalidasManager:
    def __init__(self, user_id, parent_frame, root, db_manager=None, store_id=1):
        self.user_id = user_id
        self.parent_frame = parent_frame
        self.root = root
        self.store_id = store_id
        self.logic = EntradasSalidasLogic(db_manager, store_id=self.store_id)
        self.main_frame = ctk.CTkFrame(self.parent_frame)
        self.current_products = []
        self.setup_ui()
        logger.info(f"Inicializando EntradasSalidasManager para usuario con ID '{self.user_id}' en tienda {self.store_id}")

    def setup_ui(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self.main_frame, text="Entradas y Salidas", font=("Arial", 24, "bold")).pack(pady=(20, 10))

        buttons_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkButton(
            buttons_frame,
            text="Entradas",
            command=self.mostrar_entradas,
            width=200,
            height=60,
            font=("Arial", 16),
            corner_radius=8
        ).pack(side="left", padx=20)
        ctk.CTkButton(
            buttons_frame,
            text="Salidas",
            command=self.mostrar_salidas,
            width=200,
            height=60,
            font=("Arial", 16),
            corner_radius=8
        ).pack(side="left", padx=20)

    def mostrar_entradas(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self.main_frame, text="Registrar Entradas", font=("Arial", 20)).pack(pady=10)

        tipo_frame = ctk.CTkFrame(self.main_frame)
        tipo_frame.pack(fill="x", padx=20, pady=5)
        buttons = [
            ("Nueva Mercancía", lambda: self.mostrar_formulario("entrada", "nueva_mercancia")),
            ("Resurtido", lambda: self.mostrar_formulario("entrada", "resurtido")),
            ("Cambio", lambda: self.mostrar_formulario("entrada", "cambio_entrada")),
            ("Transferencia", lambda: self.mostrar_formulario("entrada", "transferencia_entrada"))
        ]
        for idx, (text, command) in enumerate(buttons):
            ctk.CTkButton(
                tipo_frame,
                text=text,
                command=command,
                width=150,
                height=40,
                font=("Arial", 14)
            ).grid(row=0, column=idx, padx=5, pady=5)

        self.setup_treeview()

    def mostrar_salidas(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self.main_frame, text="Registrar Salidas", font=("Arial", 20)).pack(pady=10)

        tipo_frame = ctk.CTkFrame(self.main_frame)
        tipo_frame.pack(fill="x", padx=20, pady=5)
        buttons = [
            ("Cambio", lambda: self.mostrar_formulario("salida", "cambio_salida")),
            ("Transferencia", lambda: self.mostrar_formulario("salida", "transferencia_salida"))
        ]
        for idx, (text, command) in enumerate(buttons):
            ctk.CTkButton(
                tipo_frame,
                text=text,
                command=command,
                width=150,
                height=40,
                font=("Arial", 14)
            ).grid(row=0, column=idx, padx=5, pady=5)

        self.setup_treeview()

    def setup_treeview(self):
        tree_frame = ctk.CTkFrame(self.main_frame)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.tree = ttk.Treeview(
            tree_frame,
            columns=("SKU", "Nombre", "Cantidad", "Motivo"),
            show="headings"
        )
        self.tree.heading("SKU", text="SKU")
        self.tree.heading("Nombre", text="Nombre")
        self.tree.heading("Cantidad", text="Cantidad")
        self.tree.heading("Motivo", text="Motivo")
        self.tree.column("SKU", width=100)
        self.tree.column("Nombre", width=200)
        self.tree.column("Cantidad", width=100)
        self.tree.column("Motivo", width=150)
        self.tree.pack(fill="both", expand=True)

        self.actualizar_treeview()

        action_frame = ctk.CTkFrame(self.main_frame)
        action_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(
            action_frame,
            text="Confirmar",
            command=self.confirmar_movimientos,
            width=150,
            height=40
        ).pack(side="left", padx=5)
        ctk.CTkButton(
            action_frame,
            text="Cancelar",
            command=self.setup_ui,
            width=150,
            height=40
        ).pack(side="left", padx=5)

    def actualizar_treeview(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for prod in self.current_products:
            self.tree.insert("", "end", values=(
                prod["sku"],
                prod["nombre"],
                prod["cantidad"],
                prod["motivo"]
            ))

    def mostrar_formulario(self, tipo, motivo):
        form_window = ctk.CTkToplevel(self.root)
        form_window.title(f"Registrar {tipo.capitalize()} - {motivo.replace('_', ' ').capitalize()}")
        form_window.geometry("400x400")

        ctk.CTkLabel(form_window, text="SKU:").pack(pady=5)
        sku_var = ctk.StringVar()
        ctk.CTkEntry(form_window, textvariable=sku_var).pack(pady=5)

        ctk.CTkLabel(form_window, text="Cantidad:").pack(pady=5)
        cantidad_var = ctk.StringVar()
        ctk.CTkEntry(form_window, textvariable=cantidad_var).pack(pady=5)

        if motivo in ["nueva_mercancia", "transferencia_entrada"]:
            ctk.CTkLabel(form_window, text="Nombre:").pack(pady=5)
            nombre_var = ctk.StringVar()
            ctk.CTkEntry(form_window, textvariable=nombre_var).pack(pady=5)
            ctk.CTkLabel(form_window, text="Precio:").pack(pady=5)
            precio_var = ctk.StringVar()
            ctk.CTkEntry(form_window, textvariable=precio_var).pack(pady=5)
        else:
            nombre_var = precio_var = None

        if motivo in ["transferencia_entrada", "transferencia_salida"]:
            ctk.CTkLabel(form_window, text="Sucursal Origen:").pack(pady=5)
            sucursal_origen_var = ctk.StringVar()
            ctk.CTkEntry(form_window, textvariable=sucursal_origen_var).pack(pady=5)
            ctk.CTkLabel(form_window, text="Sucursal Destino:").pack(pady=5)
            sucursal_destino_var = ctk.StringVar()
            ctk.CTkEntry(form_window, textvariable=sucursal_destino_var).pack(pady=5)
        else:
            sucursal_origen_var = sucursal_destino_var = None

        def agregar():
            try:
                sku = sku_var.get().strip()
                cantidad = int(cantidad_var.get())
                producto = self.logic.buscar_producto(sku)
                
                if motivo in ["nueva_mercancia", "transferencia_entrada"] and not producto:
                    nombre = nombre_var.get().strip()
                    precio = float(precio_var.get())
                    if not nombre or precio <= 0:
                        raise ValueError("Nombre y precio son obligatorios")
                    producto = {"sku": sku, "nombre": nombre, "precio": precio}
                elif not producto:
                    raise ValueError("Producto no encontrado")

                self.current_products.append({
                    "tipo": tipo,
                    "motivo": motivo,
                    "sku": sku,
                    "nombre": producto["nombre"],
                    "cantidad": cantidad,
                    "sucursal_origen": sucursal_origen_var.get().strip() if sucursal_origen_var else None,
                    "sucursal_destino": sucursal_destino_var.get().strip() if sucursal_destino_var else None
                })
                self.actualizar_treeview()
                form_window.destroy()
                logger.info(f"Producto agregado a la sesión: SKU {sku}, tipo: {tipo}, motivo: {motivo} en tienda {self.store_id}")
            except ValueError as e:
                messagebox.showerror("Error", str(e))
                logger.error(f"Error al agregar producto en tienda {self.store_id}: {str(e)}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo agregar: {str(e)}")
                logger.error(f"Error inesperado al agregar producto en tienda {self.store_id}: {str(e)}")

        ctk.CTkButton(form_window, text="Agregar", command=agregar).pack(pady=20)

    def confirmar_movimientos(self):
        try:
            for prod in self.current_products:
                self.logic.registrar_movimiento(
                    prod["tipo"],
                    prod["motivo"],
                    prod["sku"],
                    prod["cantidad"],
                    prod["sucursal_origen"],
                    prod["sucursal_destino"]
                )
            messagebox.showinfo("Éxito", "Movimientos registrados")
            logger.info(f"Movimientos confirmados para {len(self.current_products)} productos en tienda {self.store_id}")
            self.current_products = []
            self.setup_ui()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron confirmar los movimientos: {str(e)}")
            logger.error(f"Error al confirmar movimientos en tienda {self.store_id}: {str(e)}")

    def pack(self, **kwargs):
        self.main_frame.pack(**kwargs)
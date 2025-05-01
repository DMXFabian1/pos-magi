# inventory_manager.py
from src.core.config.db_manager import DatabaseManager
import sqlite3
import logging
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from src.core.utils.tooltips import ToolTip
from src.modules.products.product_manager_logic import ProductManagerLogic

logger = logging.getLogger(__name__)

class InventoryManager:
    def __init__(self, root_folder, db_manager, manager, store_id=1):
        self.root_folder = root_folder
        self.db_manager = db_manager
        self.manager = manager
        self.store_id = store_id
        logger.info(f"Inicializando InventoryManager para tienda {self.store_id}")

    def validate_numeric_entry(self, entry, field_name):
        """Valida entradas numéricas."""
        value = entry.get().strip()
        try:
            if value:
                float(value)
                if float(value) < 0:
                    raise ValueError("El valor no puede ser negativo.")
            entry.configure(fg_color="#FFFFFF", border_color="#A3BFFA")
            return True
        except ValueError:
            entry.configure(fg_color="#FFE6E6", border_color="#FF5555")
            messagebox.showwarning("Advertencia", f"El campo {field_name} debe ser un número válido y no negativo.")
            return False

    def open_price_modification_window(self):
        """Abre una ventana para modificar los precios de los productos seleccionados."""
        selected_items = self.manager.ui.tree.selection()
        if not selected_items:
            messagebox.showwarning("Advertencia", "Selecciona al menos un producto para modificar el precio.")
            return

        selected_skus = [self.manager.ui.tree.item(item)["values"][1].upper() for item in selected_items]
        price_window = ctk.CTkToplevel(self.manager.ui.window)
        price_window.title("Modificar Precios")
        price_window.geometry("400x300")
        price_window.configure(fg_color="#F5F7FA")
        price_window.transient(self.manager.root)
        price_window.grab_set()

        ctk.CTkLabel(price_window, text="Modificar Precios", font=("Helvetica", 16, "bold"), text_color="#1A2E5A").pack(pady=10)

        mode_frame = ctk.CTkFrame(price_window, fg_color="transparent")
        mode_frame.pack(fill="x", padx=20, pady=5)
        mode_var = tk.StringVar(value="set")
        ctk.CTkRadioButton(mode_frame, text="Establecer Precio", variable=mode_var, value="set", font=("Helvetica", 12)).pack(side="left", padx=10)
        ctk.CTkRadioButton(mode_frame, text="Aumentar/Disminuir", variable=mode_var, value="adjust", font=("Helvetica", 12)).pack(side="left", padx=10)

        value_frame = ctk.CTkFrame(price_window, fg_color="transparent")
        value_frame.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(value_frame, text="Valor:", font=("Helvetica", 12)).pack(side="left", padx=5)
        value_entry = ctk.CTkEntry(value_frame, placeholder_text="Ej: 100.00 o -10.00", width=150)
        value_entry.pack(side="left", padx=5)
        value_entry.bind("<KeyRelease>", lambda e: self.validate_numeric_entry(value_entry, "Valor"))

        button_frame = ctk.CTkFrame(price_window, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=20)
        ctk.CTkButton(button_frame, text="Aplicar", command=lambda: self.update_selected_prices(value_entry.get(), selected_skus, mode_var.get()), 
                      fg_color="#4A90E2", hover_color="#2A6EBB", corner_radius=8, font=("Helvetica", 12), width=120).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Cancelar", command=price_window.destroy, 
                      fg_color="#FF6F61", hover_color="#E55B50", corner_radius=8, font=("Helvetica", 12), width=120).pack(side="left", padx=10)

    def update_selected_prices(self, value, selected_skus, mode="set"):
        """Actualiza los precios de los productos seleccionados."""
        try:
            value = float(value)
            if mode == "set" and value < 0:
                messagebox.showwarning("Advertencia", "El precio no puede ser negativo.")
                return

            with self.db_manager as db:
                cursor = db.get_cursor()
                for sku in selected_skus:
                    cursor.execute("SELECT precio FROM productos WHERE sku = ? AND store_id = ?", (sku, self.store_id))
                    result = cursor.fetchone()
                    if not result:
                        logger.warning(f"No se encontró el producto con SKU {sku} en tienda {self.store_id}.")
                        continue
                    current_price = result[0] or 0.0
                    new_price = value if mode == "set" else current_price + value
                    if new_price < 0:
                        new_price = 0
                    cursor.execute("UPDATE productos SET precio = ? WHERE sku = ? AND store_id = ?", (new_price, sku, self.store_id))
                    logger.info(f"Precio actualizado para SKU {sku}: {current_price} -> {new_price} en tienda {self.store_id}")

            self.manager.cargar_productos()
            messagebox.showinfo("Éxito", f"Precios actualizados para {len(selected_skus)} producto(s).")
        except ValueError:
            messagebox.showerror("Error", "Por favor, ingresa un valor numérico válido.")
        except sqlite3.Error as e:
            logger.error(f"Error al actualizar precios: {str(e)}")
            messagebox.showerror("Error", f"No se pudo actualizar los precios: {str(e)}")

    def update_mass_prices(self, increment):
        """Actualiza los precios de todos los productos aplicando un incremento."""
        try:
            with self.db_manager as db:
                cursor = db.get_cursor()
                cursor.execute("UPDATE productos SET precio = CASE WHEN precio + ? < 0 THEN 0 ELSE precio + ? END WHERE store_id = ?", (increment, increment, self.store_id))
                logger.info(f"Precios ajustados masivamente: incremento de {increment} en tienda {self.store_id}")

            self.manager.cargar_productos()
            messagebox.showinfo("Éxito", "Precios ajustados masivamente.")
        except sqlite3.Error as e:
            logger.error(f"Error al ajustar precios masivamente: {str(e)}")
            messagebox.showerror("Error", f"No se pudo ajustar los precios masivamente: {str(e)}")
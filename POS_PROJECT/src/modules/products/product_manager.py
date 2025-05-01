import customtkinter as ctk
from src.modules.products.product_manager_ui import ProductManagerUI
from src.modules.products.product_manager_logic import ProductManagerLogic
from src.modules.inventory.inventory_manager import InventoryManager
from src.ui.qr_generator import QRGenerator
from src.core.config.config import CONFIG
from tkinter import messagebox
import logging

logger = logging.getLogger(__name__)

class ProductManagerWindow:
    def __init__(self, app, root, icons):
        self.app = app
        self.root = root  # Ahora root se pasa explícitamente
        self.icons = icons  # Recibimos los iconos
        self.root_folder = app.root_folder if hasattr(app, 'root_folder') else CONFIG['ROOT_FOLDER']
        self.tallas_personalizadas = getattr(app, 'tallas_personalizadas', [])
        self.setup_window()
        self.initialize_state()
        self.db_manager = app.db_manager
        self.inventory_manager = InventoryManager(self.root_folder, self.db_manager, self)
        self.label_manager = QRGenerator(self.root_folder, self.db_manager, self)
        self.product_manager = ProductManagerLogic(self)
        self.ui = ProductManagerUI(self)  # Pasamos self, que ahora incluye los iconos
        self.setup_keybindings()
        self.setup_buttons()  # Nuevo método para configurar botones
        self.load_initial_data()

    def setup_window(self):
        self.window = ctk.CTkToplevel(self.root)
        self.window.title("Gestión de Productos")
        self.window.geometry("1200x700")
        self.window.state('zoomed')  # Maximizar la ventana al abrirse
        self.window.configure(fg_color="#E6F0FA")
        self.window.transient(self.root)
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

    def initialize_state(self):
        self.selection_state = {}
        self.first_selected_item = None
        self.selection_anchor = None
        self.last_selected_sku = None
        self.current_page = 0
        self.page_size = 30
        self.total_pages = 0
        self.current_filters = {}
        self.sort_column = None
        self.sort_direction = "asc"
        self.columns = [
            "sku", "nombre", "nivel_educativo", "escuela", "color", "tipo_prenda", "tipo_pieza",
            "genero", "atributo", "ubicacion", "escudo", "marca", "talla", "inventario", "ventas", "precio"
        ]
        self.visible_columns = [
            "sku", "nombre", "escuela", "color", "tipo_prenda", "tipo_pieza", "genero", "talla", "inventario", "ventas", "precio"
        ]
        self.is_deleting = False
        self.current_label_path = None

    def setup_keybindings(self):
        self.window.bind("<Control-a>", lambda event: self.select_all())
        self.window.bind("<Control-c>", lambda event: self.product_manager.copy_sku())
        self.window.bind("<Control-p>", lambda event: self.ui.open_print_preview())
        self.window.bind("<Delete>", lambda event: self.product_manager.eliminar_seleccion())

    def setup_buttons(self):
        # Crear un frame para los botones adicionales
        button_frame = ctk.CTkFrame(self.window)
        button_frame.pack(fill="x", padx=10, pady=5)

        # Botón para ajustar inventario
        ctk.CTkButton(
            button_frame,
            text="Ajustar Inventario",
            command=self.ajustar_inventario,
            width=150,
            height=40,
            font=("Arial", 14)
        ).pack(side="left", padx=5)

    def load_initial_data(self):
        self.product_manager.cargar_productos()

    def on_closing(self):
        self.window.destroy()

    def select_all(self):
        for item in self.ui.tree.get_children():
            self.ui.tree.selection_add(item)
            self.ui.update_selection_count()

    def copy_sku(self):
        self.product_manager.copy_sku()

    def ajustar_inventario(self):
        selected_items = self.ui.tree.selection()
        if not selected_items:
            messagebox.showinfo("Selección", "Seleccione al menos un producto para ajustar el inventario.")
            return

        def guardar_ajuste():
            try:
                cantidad = int(entry_cantidad.get())
                for item in selected_items:
                    values = self.ui.tree.item(item)['values']
                    sku = values[0]  # SKU está en la primera columna
                    self.db_manager.actualizar_inventario(sku, cantidad)
                    logger.info(f"Inventario ajustado para SKU {sku} por usuario {self.user_id}: {cantidad}")
                dialog_ajuste.destroy()
                messagebox.showinfo("Éxito", "Inventario ajustado para los productos seleccionados.")
                self.product_manager.cargar_productos()
            except ValueError:
                messagebox.showerror("Error", "La cantidad debe ser un número entero.")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo ajustar el inventario: {str(e)}")
                logger.error(f"Error al ajustar inventario: {str(e)}")

        dialog_ajuste = ctk.CTkToplevel(self.window)
        dialog_ajuste.title("Ajustar Inventario")
        dialog_ajuste.geometry("300x200")
        dialog_ajuste.transient(self.window)
        dialog_ajuste.grab_set()

        ctk.CTkLabel(dialog_ajuste, text=f"Productos seleccionados: {len(selected_items)}", font=("Arial", 14)).pack(pady=10)
        ctk.CTkLabel(dialog_ajuste, text="Cantidad a agregar (positiva o negativa):").pack(pady=5)
        entry_cantidad = ctk.CTkEntry(dialog_ajuste, width=100)
        entry_cantidad.pack(pady=5)
        ctk.CTkButton(dialog_ajuste, text="Guardar", command=guardar_ajuste).pack(pady=10)

    def lock_interface(self, lock=True):
        state = "disabled" if lock else "normal"
        self.ui.prev_button.configure(state=state)
        self.ui.next_button.configure(state=state)
        self.ui.delete_button.configure(state=state)
        self.ui.edit_button.configure(state=state)
        self.ui.copy_button.configure(state=state)
        self.ui.copy_label_button.configure(state=state)
        self.ui.print_button.configure(state=state)

    def update_selection_count(self):
        selected_count = sum(1 for selected in self.selection_state.values() if selected)
        total_count = len(self.selection_state)
        self.ui.selection_count_label.configure(text=f"Seleccionados: {selected_count}/{total_count}")

    def update_pagination_text(self, total_items, current_page, total_pages):
        self.ui.update_pagination_text(total_items, current_page, total_pages)

    def on_treeview_click(self, event):
        self.ui.on_treeview_click(event)

    def on_shift_click(self, event):
        self.ui.on_shift_click(event)

    def get_unique_values(self, column):
        return self.product_manager.get_unique_values(column)

    def prev_page(self):
        self.product_manager.prev_page()

    def next_page(self):
        self.product_manager.next_page()

    def sort_by_column(self, column):
        self.product_manager.sort_by_column(column)

    def apply_quick_search(self, event=None):
        self.product_manager.apply_quick_search(event)

    def clear_filters(self):
        self.product_manager.clear_filters()

    def cargar_productos(self):
        self.product_manager.cargar_productos()

    def apply_filters(self, event=None):
        self.product_manager.apply_filters(event)

    def eliminar_seleccion(self):
        self.product_manager.eliminar_seleccion()

    def duplicar_producto(self):
        self.product_manager.duplicar_producto()

    def edit_product(self):
        self.product_manager.edit_product()

    def validate_numeric_entry(self, entry, field_name):
        self.product_manager.validate_numeric_entry(entry, field_name)

    def select_new_image(self):
        self.product_manager.select_new_image()

    def save_edited_product(self, sku, entries, edit_window):
        self.product_manager.save_edited_product(sku, entries, edit_window)

    def copy_image_to_clipboard(self):
        self.label_manager.copy_image_to_clipboard()

    def print_labels(self, copies=1):
        if self.current_label_path:
            for _ in range(copies):
                self.label_manager.print_labels([self.current_label_path])

    def open_price_modification_window(self):
        self.inventory_manager.open_price_modification_window()

    def update_selected_prices(self, value, selected_skus, mode="set"):
        self.inventory_manager.update_selected_prices(value, selected_skus, mode)

    def update_mass_prices(self, increment):
        self.inventory_manager.update_mass_prices(increment)

    def mostrar_detalle(self, event):
        self.ui.mostrar_detalle(event)

def abrir_gestion_productos(app):
    """Abre la ventana de gestión de productos."""
    root = app.parent if hasattr(app, 'parent') else app.root
    icons = app.icons
    ProductManagerWindow(app, root, icons)
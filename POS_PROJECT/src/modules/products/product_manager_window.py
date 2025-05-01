import customtkinter as ctk
from src.modules.products.product_manager_ui import ProductManagerUI
from src.modules.products.product_manager_logic import ProductManagerLogic
from src.modules.inventory.inventory_manager import InventoryManager
from src.ui.qr_generator import QRGenerator
from src.core.config.config import CONFIG
from tkinter import messagebox
import logging
import os
from PIL import Image, ImageWin
import win32print
import win32ui

logger = logging.getLogger(__name__)

class ProductManagerWindow:
    def __init__(self, app, parent_frame, root, icons, store_id=1):
        self.app = app
        self.parent_frame = parent_frame
        self.root = root
        self.icons = icons
        self.store_id = store_id

        if not hasattr(app, 'db_manager') or app.db_manager is None:
            logger.error("db_manager no está definido en app")
            raise ValueError("db_manager no está definido en app")
        if not root:
            logger.error("root no está definido")
            raise ValueError("root no está definido")
        if not icons:
            logger.warning("icons no están definidos, inicializando con diccionario vacío")
            self.icons = {}

        self.user_id = app.user_id if hasattr(app, 'user_id') else "unknown_user"
        self.role = app.role if hasattr(app, 'role') else "unknown_role"
        self.root_folder = app.root_folder if hasattr(app, 'root_folder') else CONFIG['ROOT_FOLDER']
        self.tallas_personalizadas = getattr(app, 'tallas_personalizadas', [])
        self.db_manager = app.db_manager
        logger.info(f"Inicializando ProductManagerWindow para usuario {self.user_id} con rol {self.role} en tienda {self.store_id}")

        self.setup_window()
        self.initialize_state()
        self.inventory_manager = InventoryManager(self.root_folder, self.db_manager, self, store_id=self.store_id)
        self.label_manager = QRGenerator(self.root_folder, self.db_manager, self, store_id=self.store_id)
        self.product_manager = ProductManagerLogic(self, store_id=self.store_id)
        self.ui = ProductManagerUI(self, store_id=self.store_id)
        self.setup_keybindings()
        self.setup_buttons()
        self.load_initial_data()
        logging.debug(f"Iconos recibidos en ProductManagerWindow: {list(self.icons.keys())}")

    def setup_window(self):
        self.main_frame = ctk.CTkFrame(self.parent_frame)
        self.main_frame.configure(fg_color="#E6F0FA")
        self.main_frame.pack(fill="both", expand=True)
        logger.debug("Ventana de ProductManagerWindow configurada")

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
        logger.debug("Estado inicializado")

    def setup_keybindings(self):
        self.ui.tree.bind("<Control-a>", self._handle_select_all)
        self.ui.tree.bind("<Control-c>", self._handle_copy_sku)
        self.ui.tree.bind("<Control-p>", self._handle_print_preview)
        self.ui.tree.bind("<Delete>", self._handle_delete_selection)
        logger.debug("Keybindings configurados en el Treeview")

    def _handle_select_all(self, event):
        try:
            self.select_all()
        except Exception as e:
            logger.error(f"Error al manejar select_all: {str(e)}")

    def _handle_copy_sku(self, event):
        try:
            if hasattr(self.product_manager, 'copy_sku'):
                self.product_manager.copy_sku()
            else:
                logger.error("copy_sku no está definido en product_manager")
        except Exception as e:
            logger.error(f"Error al manejar copy_sku: {str(e)}")

    def _handle_print_preview(self, event):
        try:
            if hasattr(self.ui, 'open_print_preview'):
                self.ui.open_print_preview()
            else:
                logger.error("open_print_preview no está definido en ui")
        except Exception as e:
            logger.error(f"Error al manejar print_preview: {str(e)}")

    def _handle_delete_selection(self, event):
        try:
            if hasattr(self.product_manager, 'eliminar_seleccion'):
                self.product_manager.eliminar_seleccion()
            else:
                logger.error("eliminar_seleccion no está definido en product_manager")
        except Exception as e:
            logger.error(f"Error al manejar delete_selection: {str(e)}")

    def setup_buttons(self):
        pass

    def load_initial_data(self):
        try:
            self.product_manager.cargar_productos()
            logger.debug("Datos iniciales cargados")
        except Exception as e:
            logger.error(f"Error al cargar datos iniciales: {str(e)}")
            messagebox.showerror("Error", "No se pudieron cargar los datos iniciales.")

    def on_closing(self):
        try:
            self.ui.tree.unbind("<Control-a>")
            self.ui.tree.unbind("<Control-c>")
            self.ui.tree.unbind("<Control-p>")
            self.ui.tree.unbind("<Delete>")
            self.main_frame.pack_forget()
            self.main_frame.destroy()
            self.ui = None
            self.product_manager = None
            self.inventory_manager = None
            self.label_manager = None
            logger.debug("ProductManagerWindow cerrado y recursos limpiados")
        except Exception as e:
            logger.error(f"Error al cerrar ProductManagerWindow: {str(e)}")

    def select_all(self):
        for item in self.ui.tree.get_children():
            self.ui.tree.selection_add(item)
            self.ui.update_selection_count()

    def copy_sku(self):
        self.product_manager.copy_sku()

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
        """Imprime etiquetas para el producto seleccionado enviando la imagen directamente a la impresora."""
        selected_items = self.ui.tree.selection()
        if not selected_items:
            messagebox.showwarning("Advertencia", "Selecciona un producto para imprimir etiquetas.")
            return
        if len(selected_items) > 1:
            messagebox.showwarning("Advertencia", "Selecciona solo un producto para imprimir etiquetas.")
            return

        sku = self.ui.tree.item(selected_items[0])["values"][1].upper()
        cursor = self.db_manager.get_cursor()
        cursor.execute("SELECT qr_path FROM productos WHERE sku = ? AND store_id = ?", (sku, self.store_id))
        result = cursor.fetchone()
        if not result or not result[0]:
            messagebox.showerror("Error", f"No se encontró la etiqueta para el producto con SKU {sku} en tienda {self.store_id}.")
            return

        qr_path = os.path.join(self.root_folder, result[0])
        if not os.path.exists(qr_path):
            messagebox.showerror("Error", f"La etiqueta para el producto con SKU {sku} no existe en el sistema de archivos.")
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
                for _ in range(copies):
                    hdc.StartPage()
                    dib = ImageWin.Dib(image)
                    dib.draw(hdc.GetHandleOutput(), (0, 0, label_width, label_height))
                    hdc.EndPage()

                hdc.EndDoc()
                hdc.DeleteDC()
                logger.info(f"Se imprimieron {copies} etiquetas para el producto con SKU {sku} en tienda {self.store_id}.")
            finally:
                win32print.ClosePrinter(hprinter)
        except ImportError:
            logger.error("Librería pywin32 no encontrada")
            messagebox.showerror("Error", "No se encontró la librería pywin32. Instálala con 'pip install pywin32'.")
        except Exception as e:
            logger.error(f"Error al imprimir la etiqueta para SKU {sku}: {str(e)}")
            messagebox.showerror("Error", f"No se pudo imprimir la etiqueta: {str(e)}\nAsegúrate de que la impresora Brother QL-800 esté conectada y configurada correctamente.")

    def open_price_modification_window(self):
        self.inventory_manager.open_price_modification_window()

    def update_selected_prices(self, value, selected_skus, mode="set"):
        self.inventory_manager.update_selected_prices(value, selected_skus, mode)

    def update_mass_prices(self, increment):
        self.inventory_manager.update_mass_prices(increment)

    def mostrar_detalle(self, event):
        self.ui.mostrar_detalle(event)

def abrir_gestion_productos(app, parent_frame, store_id=1):
    """Crea y devuelve una instancia de ProductManagerWindow para ser incrustada en el content_frame."""
    root = app.root
    icons = app.icons
    return ProductManagerWindow(app, parent_frame, root, icons, store_id=store_id)
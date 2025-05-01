import sqlite3
import os
import io
import win32clipboard
import shutil
from PIL import Image, ImageTk
from src.core.config.db_manager import DatabaseManager
from src.core.config.config import CONFIG, exportar_configuraciones
from src.core.utils.utils import sanitize_filename
import logging
import subprocess
import tkinter as tk
import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog, simpledialog
from src.ui.ui_components import create_labeled_entry, create_labeled_combobox
from src.core.utils.tooltips import ToolTip
from datetime import datetime

logger = logging.getLogger(__name__)

class ProductManagerLogic:
    def __init__(self, manager, store_id=1):
        logger.debug("Iniciando inicialización de ProductManagerLogic")
        self.manager = manager
        self.store_id = store_id
        self.root_folder = CONFIG['ROOT_FOLDER']
        self.db_manager = DatabaseManager()
        self.selection_state = manager.selection_state
        self.first_selected_item = manager.first_selected_item
        self.selection_anchor = manager.selection_anchor
        self.last_selected_sku = manager.last_selected_sku
        self.current_page = manager.current_page
        self.page_size = manager.page_size
        self.total_pages = manager.total_pages
        self.current_filters = manager.current_filters
        self.sort_column = manager.sort_column
        self.sort_direction = manager.sort_direction
        self.columns = manager.columns
        self.visible_columns = manager.visible_columns
        self.is_deleting = manager.is_deleting
        self.current_label_path = manager.current_label_path
        self.search_after_id = None
        self.empty_image = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        self.empty_image_photo = ImageTk.PhotoImage(self.empty_image)
        self.omit_vars = {}
        self.edit_image_path = None
        self.edit_qr_path = None
        self.edit_image_label = None
        self.edit_qr_label = None
        self.image_references = []
        self.cached_total_items = None
        self.cached_total_pages = None
        self.cached_filters = None
        logger.info(f"ProductManagerLogic inicializado para tienda {self.store_id}")

    def get_unique_values(self, column):
        try:
            with self.db_manager as db:
                cursor = db.get_cursor()
                escaped_column = f'"{column}"'
                query = f"""
                    SELECT DISTINCT {escaped_column}
                    FROM productos
                    WHERE {escaped_column} IS NOT NULL
                    AND TRIM({escaped_column}) != ''
                    AND LENGTH(TRIM({escaped_column})) > 0
                    AND store_id = ?
                """
                logger.debug(f"Ejecutando consulta para valores únicos: {query}")
                cursor.execute(query, (self.store_id,))
                values = [row[0] for row in cursor.fetchall()]
                values = [str(v).strip() for v in values if v and str(v).strip() and len(str(v).strip()) > 0]
                logger.debug(f"Valores únicos obtenidos para {column}: {values}")

                if column == "talla":
                    custom_tallas = getattr(self.manager, 'tallas_personalizadas', [])
                    values.extend(talla for talla in custom_tallas if talla and talla.strip() and len(talla.strip()) > 0 and talla not in values)
                    
                    tallas_ordenadas = [
                        "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "16", "18", "20",
                        "28", "32", "34", "36", "38", "40", "42", "44", "46", "48",
                        "XS", "S", "M", "L", "XL", "XXL", "XXXL", "XXXXL",
                        "CH", "MD", "GD", "EXG",
                        "Uni", "ESP", "NT",
                        "0-0", "0-2", "3-5", "6-8", "9-12", "13-18", "CH-MD", "GD-EXG", "Dama"
                    ]
                    
                    def parse_size(size):
                        size = str(size).strip()
                        if size in tallas_ordenadas:
                            return (0, tallas_ordenadas.index(size))
                        return (1, size.lower())
                    
                    values.sort(key=parse_size)
                    values = [str(value) for value in values]
                else:
                    numeric_columns = ["inventario", "ventas", "precio"]
                    if column in numeric_columns:
                        def to_float(value):
                            try:
                                return float(value)
                            except (ValueError, TypeError):
                                return float('inf')
                        values.sort(key=to_float)
                        values = [str(value) for value in values]
                    else:
                        values.sort()

                return values
        except sqlite3.Error as e:
            logger.error(f"Error al obtener valores únicos para {column} en tienda {self.store_id}: {str(e)}")
            messagebox.showerror("Error", f"No se pudo cargar los valores de {column}: {str(e)}")
            return []

    def update_filters(self):
        self.current_filters = {
            "search": self.manager.ui.search_entry.get().strip().upper(),
            "escuela": self.manager.ui.combo_escuela.get().strip() if self.manager.ui.combo_escuela.get() else None,
            "nivel_educativo": self.manager.ui.combo_nivel.get().strip() if self.manager.ui.combo_nivel.get() else None,
            "color": self.manager.ui.combo_color.get().strip() if self.manager.ui.combo_color.get() else None,
            "tipo_prenda": self.manager.ui.combo_tipo_prenda.get().strip() if self.manager.ui.combo_tipo_prenda.get() else None,
            "tipo_pieza": self.manager.ui.combo_tipo_pieza.get().strip() if self.manager.ui.combo_tipo_pieza.get() else None,
            "genero": self.manager.ui.combo_genero.get().strip() if self.manager.ui.combo_genero.get() else None,
            "atributo": self.manager.ui.combo_atributo.get().strip() if self.manager.ui.combo_atributo.get() else None,
            "marca": self.manager.ui.combo_marca.get().strip() if self.manager.ui.combo_marca.get() else None,
            "talla": self.manager.ui.combo_talla.get().strip().upper() if self.manager.ui.combo_talla.get() else None
        }

    def apply_quick_search(self, event=None):
        if self.search_after_id is not None:
            self.manager.root.after_cancel(self.search_after_id)
        self.search_after_id = self.manager.root.after(300, self._perform_quick_search)

    def _perform_quick_search(self):
        self.current_page = 0
        self.selection_anchor = None
        self.update_filters()
        search_text = self.current_filters.get("search", "").strip()
        if len(search_text) >= 6:
            with self.db_manager as db:
                cursor = db.get_cursor()
                cursor.execute('SELECT sku FROM productos WHERE UPPER(sku) = ? AND store_id = ?', (search_text.upper(), self.store_id))
                result = cursor.fetchone()
                if result:
                    logger.debug(f"Búsqueda exacta de SKU exitosa: {search_text}")
                    self.current_filters["search"] = search_text
                    self.current_filters["exact_sku"] = search_text
                    self.cargar_productos()
                    for item in self.manager.ui.tree.get_children():
                        if self.manager.ui.tree.item(item)["values"][1].upper() == search_text.upper():
                            self.manager.ui.tree.selection_set(item)
                            self.manager.ui.tree.focus(item)
                            self.manager.ui.tree.see(item)
                            self.manager.ui.mostrar_detalle(None)
                            break
                    return
        logger.debug(f"Búsqueda normal para: {search_text}")
        self.cargar_productos()

    def apply_filters(self, event=None):
        self.current_page = 0
        self.current_filters.pop("exact_sku", None)
        self.update_filters()
        self.selection_anchor = None
        self.cargar_productos()

    def clear_filters(self):
        self.current_page = 0
        self.current_filters = {}
        self.sort_column = None
        self.sort_direction = "asc"
        self.selection_anchor = None
        self.cached_total_items = None
        self.cached_total_pages = None
        self.cached_filters = None
        self.cargar_productos()

    def cancel_pending_search(self):
        if self.search_after_id is not None:
            self.manager.root.after_cancel(self.search_after_id)
            self.search_after_id = None
            logger.debug("Búsqueda rápida pendiente cancelada.")

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.selection_anchor = None
            self.cargar_productos()
            logger.debug(f"Navegando a página anterior: {self.current_page}")

    def next_page(self):
        if self.total_pages > 0 and self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.selection_anchor = None
            self.cargar_productos()
            logger.debug(f"Navegando a página siguiente: {self.current_page}")

    def sort_by_column(self, column):
        if self.sort_column == column:
            self.sort_direction = "desc" if self.sort_direction == "asc" else "asc"
        else:
            self.sort_column = column
            self.sort_direction = "asc"
        self.selection_anchor = None
        self.cargar_productos()

    def update_selection(self, event=None):
        selected_items = self.manager.ui.tree.selection()
        visible_skus = [self.manager.ui.tree.item(item)["values"][1] for item in self.manager.ui.tree.get_children()]
        for sku in visible_skus:
            self.selection_state[sku] = False
        for item in selected_items:
            sku = self.manager.ui.tree.item(item)["values"][1]
            self.selection_state[sku] = True
        self.manager.update_selection_count()
        self.manager.ui.mostrar_detalle(event)

    def cargar_productos(self):
        try:
            self.manager.ui.lock_interface(True)
            selected_skus = [sku for sku, selected in self.selection_state.items() if selected]
            logger.debug(f"SKUs seleccionados antes de recargar: {selected_skus}")

            for item in self.manager.ui.tree.get_children():
                self.manager.ui.tree.delete(item)

            try:
                self.db_manager.ensure_tables()
            except sqlite3.Error as e:
                logger.error(f"Error al verificar las tablas de la base de datos: {str(e)}")
                messagebox.showerror("Error", f"No se pudo verificar las tablas de la base de datos: {str(e)}")
                return

            conditions = ["store_id = ?"]
            params = [self.store_id]

            if self.current_filters.get("exact_sku"):
                conditions.append('UPPER(sku) = ?')
                params.append(self.current_filters["exact_sku"].upper())
            else:
                if self.current_filters.get("search"):
                    conditions.append('(UPPER(sku) LIKE ? OR UPPER(nombre) LIKE ?)')
                    params.extend([f"%{self.current_filters['search']}%", f"%{self.current_filters['search']}%"])
                if self.current_filters.get("escuela"):
                    conditions.append('escuela = ?')
                    params.append(self.current_filters["escuela"])
                if self.current_filters.get("nivel_educativo"):
                    conditions.append('"nivel_educativo" = ?')
                    params.append(self.current_filters["nivel_educativo"])
                if self.current_filters.get("color"):
                    conditions.append('color = ?')
                    params.append(self.current_filters["color"])
                if self.current_filters.get("tipo_prenda"):
                    conditions.append('"tipo_prenda" = ?')
                    params.append(self.current_filters["tipo_prenda"])
                if self.current_filters.get("tipo_pieza"):
                    conditions.append('"tipo_pieza" = ?')
                    params.append(self.current_filters["tipo_pieza"])
                if self.current_filters.get("genero"):
                    conditions.append('genero = ?')
                    params.append(self.current_filters["genero"])
                if self.current_filters.get("atributo"):
                    conditions.append('atributo = ?')
                    params.append(self.current_filters["atributo"])
                if self.current_filters.get("marca"):
                    conditions.append('marca = ?')
                    params.append(self.current_filters["marca"])
                if self.current_filters.get("talla"):
                    conditions.append('UPPER(talla) = ?')
                    params.append(self.current_filters["talla"].upper())

            where_clause = "WHERE " + " AND ".join(conditions)

            if self.cached_filters == self.current_filters and self.cached_total_items is not None:
                total_items = self.cached_total_items
                self.total_pages = self.cached_total_pages
                logger.debug(f"Usando total_items y total_pages desde cache: {total_items}, {self.total_pages}")
            else:
                try:
                    with self.db_manager as db:
                        cursor = db.get_cursor()
                        count_query = f"SELECT COUNT(*) FROM productos {where_clause}"
                        cursor.execute(count_query, params)
                        total_items = cursor.fetchone()[0]
                        logger.debug(f"Total elementos calculados: {total_items}")
                        self.cached_total_items = total_items
                        self.cached_filters = self.current_filters.copy()
                except sqlite3.Error as e:
                    logger.error(f"Error al contar productos: {str(e)}")
                    messagebox.showerror("Error", f"No se pudo contar los productos: {str(e)}")
                    return

            if total_items == 0:
                self.manager.ui.tree.insert("", "end", values=[""] * len(self.manager.ui.tree["columns"]), text="No se encontraron productos")
                self.total_pages = 0
                self.current_page = 0
                self.manager.update_pagination_text(total_items, self.current_page, self.total_pages)
                self.manager.ui.prev_button.configure(state="disabled")
                self.manager.ui.next_button.configure(state="disabled")
                self.manager.ui.lock_interface(False)
                return

            self.page_size = 30
            self.total_pages = max(1, (total_items + self.page_size - 1) // self.page_size)
            self.current_page = min(max(0, self.current_page), self.total_pages - 1)
            self.cached_total_pages = self.total_pages
            self.manager.update_pagination_text(total_items, self.current_page, self.total_pages)
            self.manager.ui.prev_button.configure(state="disabled" if self.current_page == 0 else "normal")
            self.manager.ui.next_button.configure(state="disabled" if self.current_page >= self.total_pages - 1 else "normal")

            offset = self.current_page * self.page_size
            query = f"""
                SELECT sku, nombre, "nivel_educativo", escuela, color, "tipo_prenda", "tipo_pieza", 
                    genero, atributo, ubicacion, escudo, marca, talla, inventario, ventas, precio 
                FROM productos 
                {where_clause}
                ORDER BY "{self.sort_column or 'sku'}" {self.sort_direction.upper()} 
                LIMIT ? OFFSET ?
            """
            params.extend([self.page_size, offset])
            productos = []
            try:
                with self.db_manager as db:
                    cursor = db.get_cursor()
                    cursor.execute(query, params)
                    productos = cursor.fetchall()
                    logger.debug(f"Productos cargados desde la base de datos: {len(productos)}")
            except sqlite3.Error as e:
                logger.error(f"Error al cargar productos: {str(e)}")
                messagebox.showerror("Error", f"No se pudo cargar los productos: {str(e)}")
                return

            if not productos:
                self.manager.ui.tree.insert("", "end", values=[""] * len(self.manager.ui.tree["columns"]), text="No hay productos para mostrar")
            else:
                items_to_insert = []
                for idx, producto in enumerate(productos):
                    sku = producto[0]
                    values = [
                        "☑" if self.selection_state.get(sku, False) else "☐",
                        producto[0], producto[1], producto[2], producto[3], producto[4],
                        producto[5], producto[6], producto[7], producto[8], producto[9],
                        producto[10], producto[11], producto[12], producto[13], producto[14],
                        f"{producto[15]:.2f}" if producto[15] is not None else "0.00"
                    ]
                    filtered_values = [values[0]] + [values[self.columns.index(col) + 1] for col in self.visible_columns]
                    tag = "evenrow" if idx % 2 == 0 else "oddrow"
                    items_to_insert.append((filtered_values, sku, tag))
                    if sku not in self.selection_state:
                        self.selection_state[sku] = False

                item_map = {}
                for values, sku, tag in items_to_insert:
                    item = self.manager.ui.tree.insert("", "end", values=values, tags=(tag,))
                    item_map[sku] = item
                    if sku in selected_skus:
                        self.manager.ui.tree.selection_add(item)
                        self.selection_state[sku] = True

                if selected_skus:
                    first_selected_sku = selected_skus[0]
                    if first_selected_sku in item_map:
                        self.manager.ui.tree.see(item_map[first_selected_sku])
                        self.manager.ui.tree.focus(item_map[first_selected_sku])

            self.manager.update_selection_count()
            self.manager.ui.update_filter_comboboxes()

            self.manager.ui.tree.update_idletasks()
            logger.debug("Treeview actualizado visualmente")

        except Exception as e:
            logger.error(f"Error inesperado al cargar productos: {str(e)}")
            messagebox.showerror("Error", f"Error inesperado al cargar productos: {str(e)}")
        finally:
            self.manager.ui.lock_interface(False)

    def copy_sku(self):
        selected_items = self.manager.ui.tree.selection()
        if not selected_items:
            messagebox.showwarning("Advertencia", "Selecciona al menos un producto.")
            return
        skus = [self.manager.ui.tree.item(item)["values"][1].upper() for item in selected_items]
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(", ".join(skus))
        win32clipboard.CloseClipboard()
        logger.info(f"SKUs copiados al portapapeles: {', '.join(skus)}")
        messagebox.showinfo("Éxito", "SKU(s) copiados al portapapeles.")

    def eliminar_seleccion(self):
        if self.is_deleting:
            return
        self.is_deleting = True

        skus = [sku for sku, selected in self.selection_state.items() if selected]
        if not skus:
            messagebox.showwarning("Advertencia", "Selecciona al menos un producto para eliminar.")
            self.is_deleting = False
            return
        if not messagebox.askyesno("Confirmar", f"¿Estás seguro de que deseas eliminar {len(skus)} producto(s)?"):
            self.is_deleting = False
            return

        try:
            self.manager.ui.delete_button.configure(state="disabled")
            self.manager.ui.tree.unbind("<<TreeviewSelect>>")
            self.manager.ui.tree.unbind("<Button-1>")
            self.manager.ui.tree.unbind("<Shift-Button-1>")

            with self.db_manager as db:
                cursor = db.get_cursor()
                talla_folders_to_delete = set()
                base_folders = set()

                for sku in skus:
                    cursor.execute("SELECT qr_path, talla FROM productos WHERE sku = ? AND store_id = ?", (sku, self.store_id))
                    result = cursor.fetchone()
                    if result:
                        qr_path = result[0]
                        talla = result[1]
                        if qr_path:
                            talla_folder_relative = os.path.dirname(qr_path)
                            base_folder_relative = os.path.dirname(talla_folder_relative)
                            talla_folder_absolute = os.path.join(self.root_folder, talla_folder_relative)
                            base_folder_absolute = os.path.join(self.root_folder, base_folder_relative)
                            talla_folders_to_delete.add(talla_folder_absolute)
                            base_folders.add(base_folder_absolute)

                for sku in skus:
                    cursor.execute("DELETE FROM productos WHERE sku = ? AND store_id = ?", (sku, self.store_id))
                    logger.info(f"Producto eliminado: SKU {sku} en tienda {self.store_id}")
                    self.selection_state.pop(sku, None)

                for talla_folder_absolute in talla_folders_to_delete:
                    if os.path.exists(talla_folder_absolute):
                        shutil.rmtree(talla_folder_absolute, ignore_errors=True)
                        logger.info(f"Subcarpeta de talla eliminada: {talla_folder_absolute}")
                    else:
                        logger.warning(f"Subcarpeta de talla no encontrada para eliminar: {talla_folder_absolute}")

                for base_folder_absolute in base_folders:
                    if os.path.exists(base_folder_absolute):
                        remaining_items = os.listdir(base_folder_absolute)
                        if not remaining_items:
                            shutil.rmtree(base_folder_absolute, ignore_errors=True)
                            logger.info(f"Carpeta base vacía eliminada: {base_folder_absolute}")

            self.selection_anchor = None
            self.manager.cargar_productos()
            messagebox.showinfo("Éxito", f"{len(skus)} producto(s) eliminado(s).")
        except sqlite3.Error as e:
            logger.error(f"Error al eliminar productos: {str(e)}")
            messagebox.showerror("Error", f"No se pudo eliminar los productos: {str(e)}")
        except OSError as e:
            logger.error(f"Error al eliminar archivos: {str(e)}")
            messagebox.showerror("Error", f"Error al eliminar archivos: {str(e)}")
        finally:
            self.manager.ui.delete_button.configure(state="normal")
            self.manager.ui.tree.bind("<<TreeviewSelect>>", self.manager.mostrar_detalle)
            self.manager.ui.tree.bind("<Button-1>", self.manager.on_treeview_click)
            self.manager.ui.tree.bind("<Shift-Button-1>", self.manager.on_shift_click)
            self.is_deleting = False

    def duplicar_producto(self):
        selected_items = self.manager.ui.tree.selection()
        if not selected_items:
            messagebox.showwarning("Advertencia", "Selecciona un producto para duplicar.")
            return
        if len(selected_items) > 1:
            messagebox.showwarning("Advertencia", "Selecciona solo un producto para duplicar.")
            return

        item = selected_items[0]
        values = self.manager.ui.tree.item(item, "values")
        sku = values[1]

        try:
            with self.db_manager as db:
                cursor = db.get_cursor()
                cursor.execute("SELECT * FROM productos WHERE sku = ? AND store_id = ?", (sku, self.store_id))
                producto = cursor.fetchone()
                if not producto:
                    logger.error(f"No se encontró el producto con SKU {sku} en tienda {self.store_id}.")
                    messagebox.showerror("Error", f"No se encontró el producto con SKU {sku}.")
                    return

                _, nombre, nivel_educativo, escuela, color, tipo_prenda, tipo_pieza, genero, atributo, ubicacion, escudo, marca, talla, _, _, _, _, _ = producto
                cursor.execute("""
                    SELECT COUNT(*) FROM productos 
                    WHERE UPPER(nombre) = UPPER(?) 
                    AND UPPER(COALESCE("nivel_educativo", '')) = UPPER(COALESCE(?, ''))
                    AND UPPER(COALESCE(escuela, '')) = UPPER(COALESCE(?, ''))
                    AND UPPER(COALESCE("tipo_prenda", '')) = UPPER(COALESCE(?, ''))
                    AND UPPER(COALESCE("tipo_pieza", '')) = UPPER(COALESCE(?, ''))
                    AND UPPER(COALESCE(genero, '')) = UPPER(COALESCE(?, ''))
                    AND UPPER(COALESCE(talla, '')) = UPPER(COALESCE(?, ''))
                    AND UPPER(COALESCE(color, '')) = UPPER(COALESCE(?, ''))
                    AND UPPER(COALESCE(escudo, '')) = UPPER(COALESCE(?, ''))
                    AND UPPER(COALESCE(marca, '')) = UPPER(COALESCE(?, ''))
                    AND sku != ?
                    AND store_id = ?
                """, (nombre, nivel_educativo, escuela, tipo_prenda, tipo_pieza, genero, talla, color, escudo, marca, sku, self.store_id))
                count = cursor.fetchone()[0]

                if count > 0:
                    if not messagebox.askyesno("Confirmar Duplicado", f"Ya existe un producto con las mismas características. ¿Deseas sobrescribir el producto existente?"):
                        return
                    cursor.execute("""
                        DELETE FROM productos 
                        WHERE UPPER(nombre) = UPPER(?) 
                        AND UPPER(COALESCE("nivel_educativo", '')) = UPPER(COALESCE(?, ''))
                        AND UPPER(COALESCE(escuela, '')) = UPPER(COALESCE(?, ''))
                        AND UPPER(COALESCE("tipo_prenda", '')) = UPPER(COALESCE(?, ''))
                        AND UPPER(COALESCE("tipo_pieza", '')) = UPPER(COALESCE(?, ''))
                        AND UPPER(COALESCE(genero, '')) = UPPER(COALESCE(?, ''))
                        AND UPPER(COALESCE(talla, '')) = UPPER(COALESCE(?, ''))
                        AND UPPER(COALESCE(color, '')) = UPPER(COALESCE(?, ''))
                        AND UPPER(COALESCE(escudo, '')) = UPPER(COALESCE(?, ''))
                        AND UPPER(COALESCE(marca, '')) = UPPER(COALESCE(?, ''))
                        AND sku != ?
                        AND store_id = ?
                    """, (nombre, nivel_educativo, escuela, tipo_prenda, tipo_pieza, genero, talla, color, escudo, marca, sku, self.store_id))

                if not messagebox.askyesno("Confirmar", f"¿Estás seguro de que deseas duplicar el producto con SKU {sku}?"):
                    return

                cursor.execute("SELECT ultimo_sku FROM contador_sku WHERE id = 1")
                result = cursor.fetchone()
                if not result:
                    logger.error("No se encontró el contador de SKU en la base de datos.")
                    messagebox.showerror("Error", "No se encontró el contador de SKU.")
                    return
                ultimo_sku = result[0]
                try:
                    ultimo_numero = int(ultimo_sku)
                except ValueError:
                    logger.error(f"Formato inválido de ultimo_sku: {ultimo_sku}")
                    messagebox.showerror("Error", "Formato inválido del contador de SKU.")
                    return

                nuevo_numero = ultimo_numero + 1
                new_sku = f"{nuevo_numero:06d}"
                cursor.execute("UPDATE contador_sku SET ultimo_sku = ? WHERE id = 1", (new_sku,))

                cursor.execute("""
                    INSERT INTO productos (
                        sku, nombre, "nivel_educativo", escuela, color, "tipo_prenda", "tipo_pieza", 
                        genero, marca, talla, atributo, ubicacion, escudo, qr_path, 
                        inventario, ventas, precio, image_path, store_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (new_sku, producto[1], producto[2], producto[3], producto[4], producto[5], producto[6], 
                      producto[7], producto[8], producto[9], producto[10], producto[11], producto[12], 
                      producto[13], producto[14], producto[15], producto[16], producto[17], self.store_id))

            self.selection_anchor = None
            self.manager.cargar_productos()
            logger.info(f"Producto duplicado con nuevo SKU: {new_sku} en tienda {self.store_id}")
            messagebox.showinfo("Éxito", f"Producto duplicado con nuevo SKU: {new_sku}")

        except sqlite3.Error as e:
            logger.error(f"Error al duplicar el producto con SKU {sku}: {str(e)}")
            messagebox.showerror("Error", f"No se pudo duplicar el producto: {str(e)}")
        except Exception as e:
            logger.error(f"Error inesperado al duplicar el producto con SKU {sku}: {str(e)}")
            messagebox.showerror("Error", f"Error inesperado: {str(e)}")

    def edit_product(self):
        selected_items = self.manager.ui.tree.selection()
        if not selected_items:
            messagebox.showwarning("Advertencia", "Selecciona un producto para editar.")
            return
        if len(selected_items) > 1:
            messagebox.showwarning("Advertencia", "Selecciona solo un producto para editar.")
            return

        sku = self.manager.ui.tree.item(selected_items[0])["values"][1].upper()
        with self.db_manager as db:
            cursor = db.get_cursor()
            cursor.execute('SELECT * FROM productos WHERE sku = ? AND store_id = ?', (sku, self.store_id))
            producto = cursor.fetchone()
            if not producto:
                logger.error(f"Producto no encontrado con SKU {sku} en tienda {self.store_id}.")
                messagebox.showerror("Error", "Producto no encontrado.")
                return

        edit_window = ctk.CTkToplevel(self.manager.root)
        edit_window.title(f"Editar Producto - SKU: {sku}")
        edit_window.geometry("800x600")
        edit_window.configure(fg_color="#F5F7FA")
        edit_window.transient(self.manager.root)
        edit_window.grab_set()

        def on_window_close():
            self.image_references = []
            edit_window.destroy()

        edit_window.protocol("WM_DELETE_WINDOW", on_window_close)

        canvas = tk.Canvas(edit_window, bg="#F5F7FA", highlightthickness=0)
        scrollbar = ctk.CTkScrollbar(edit_window, orientation="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")

        content_frame = ctk.CTkFrame(canvas, fg_color="#FFFFFF", corner_radius=10, border_width=1, border_color="#A3BFFA")
        canvas.create_window((0, 0), window=content_frame, anchor="nw")

        general_frame = ctk.CTkFrame(content_frame, fg_color="#E6F0FA", corner_radius=5)
        general_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew", columnspan=2)
        ctk.CTkLabel(general_frame, text="Información General", font=("Helvetica", 14, "bold"), text_color="#1A2E5A").grid(row=0, column=0, columnspan=4, padx=10, pady=5, sticky="w")

        fields_general = [
            ("nombre", "Nombre", True, 1, True),
            ("escuela", "Escuela", True, 3, False),
            ("nivel_educativo", "Nivel Educativo", False, 2, False),
        ]
        entries = {}
        self.omit_vars = {}
        for i, (field, label, is_entry, index, required) in enumerate(fields_general):
            col = 0 if i < 2 else 2
            row = (i % 2) + 1
            self.omit_vars[field] = tk.BooleanVar(value=False)
            if is_entry:
                entry_field = create_labeled_entry(general_frame, f"{label}:", placeholder_text=f"Ej: {label}", width=200, 
                                                   row=row, column=col, sticky="w", 
                                                   omit_var=self.omit_vars[field], toggle_callback=self.toggle_field,
                                                   tooltip=f"Ingresa el {label.lower()} del producto{' (requerido)' if required else ''}")
                entries[field] = entry_field["entry"]
                value = str(producto[index] or "")
                entries[field].insert(0, value)
                if value.strip() == "" or producto[index] is None:
                    self.omit_vars[field].set(True)
                    entries[field].configure(state="disabled")
                    logger.debug(f"Campo {field} marcado como omitido para SKU {sku} (valor: {value})")
            else:
                values = sorted(CONFIG.get("NIVELES_EDUCATIVOS", []))
                values = [""] + values
                combobox_field = create_labeled_combobox(general_frame, f"{label}:", values=values, width=200, 
                                                         row=row, column=col, sticky="w", 
                                                         omit_var=self.omit_vars[field], toggle_callback=self.toggle_field,
                                                         tooltip=f"Selecciona el {label.lower()} del producto")
                entries[field] = combobox_field["combobox"]
                value = str(producto[index] or "").strip()
                if value in values:
                    entries[field].set(value)
                else:
                    entries[field].set("")
                    logger.warning(f"Valor inválido para {field} en SKU {sku}: {value}")
                if value.strip() == "" or producto[index] is None:
                    self.omit_vars[field].set(True)
                    entries[field].configure(state="disabled")
                    logger.debug(f"Campo {field} marcado como omitido para SKU {sku} (valor: {value})")

        characteristics_frame = ctk.CTkFrame(content_frame, fg_color="#E6F0FA", corner_radius=5)
        characteristics_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew", columnspan=2)
        ctk.CTkLabel(characteristics_frame, text="Características del Producto", font=("Helvetica", 14, "bold"), text_color="#1A2E5A").grid(row=0, column=0, columnspan=4, padx=10, pady=5, sticky="w")

        fields_characteristics = [
            ("color", "Color", False, 4, False),
            ("tipo_prenda", "Tipo Prenda", False, 5, False),
            ("tipo_pieza", "Tipo Pieza", False, 6, False),
            ("genero", "Género", False, 7, False),
            ("atributo", "Atributo", False, 10, False),
            ("marca", "Marca", False, 8, False),
            ("talla", "Talla", False, 9, False),
            ("ubicacion", "Ubicación", False, 11, False),
            ("escudo", "Escudo", False, 12, False),
        ]
        config_mappings = {
            "color": "COLORES",
            "tipo_prenda": "TIPOS_PRENDA",
            "tipo_pieza": "TIPOS_PIEZA",
            "genero": "GENEROS",
            "atributo": "ATRIBUTOS",
            "marca": "MARCAS",
            "talla": "TALLAS",
            "ubicacion": "UBICACIONES",
            "escudo": "ESCUDOS",
        }
        for i, (field, label, is_entry, index, required) in enumerate(fields_characteristics):
            col = 0 if i % 2 == 0 else 2
            row = (i // 2) + 1
            self.omit_vars[field] = tk.BooleanVar(value=False)
            if is_entry:
                entry_field = create_labeled_entry(characteristics_frame, f"{label}:", placeholder_text=f"Ej: {label}", width=200, 
                                                   row=row, column=col, sticky="w", 
                                                   omit_var=self.omit_vars[field], toggle_callback=self.toggle_field,
                                                   tooltip=f"Ingresa el {label.lower()} del producto{' (requerido)' if required else ''}")
                entries[field] = entry_field["entry"]
                value = str(producto[index] or "").strip()
                entries[field].insert(0, value)
                if value == "" or producto[index] is None:
                    self.omit_vars[field].set(True)
                    entries[field].configure(state="disabled")
                    logger.debug(f"Campo {field} marcado como omitido para SKU {sku} (valor: {value})")
            else:
                config_key = config_mappings.get(field, "")
                values = sorted(CONFIG.get(config_key, []))
                values = [""] + values
                combobox_field = create_labeled_combobox(characteristics_frame, f"{label}:", values=values, width=200, 
                                                         row=row, column=col, sticky="w", 
                                                         omit_var=self.omit_vars[field], toggle_callback=self.toggle_field,
                                                         tooltip=f"Selecciona el {label.lower()} del producto")
                entries[field] = combobox_field["combobox"]
                value = str(producto[index] or "").strip()
                if value in values:
                    entries[field].set(value)
                else:
                    entries[field].set("")
                    logger.debug(f"Valor inválido para {field} en SKU {sku}: {value}")
                if value.strip() == "" or producto[index] is None:
                    self.omit_vars[field].set(True)
                    entries[field].configure(state="disabled")
                    logger.debug(f"Campo {field} marcado como omitido para SKU {sku} (valor: {value})")

        inventory_frame = ctk.CTkFrame(content_frame, fg_color="#E6F0FA", corner_radius=5)
        inventory_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew", columnspan=2)
        ctk.CTkLabel(inventory_frame, text="Inventario y Precio", font=("Helvetica", 14, "bold"), text_color="#1A2E5A").grid(row=0, column=0, columnspan=4, padx=10, pady=5, sticky="w")

        fields_inventory = [
            ("precio", "Precio", True, 16, True),
            ("inventario", "Inventario", True, 14, True),
            ("ventas", "Ventas", True, 15, True),
        ]
        for i, (field, label, is_entry, index, required) in enumerate(fields_inventory):
            col = 0 if i < 2 else 2
            row = (i % 2) + 1
            if field in ["inventario", "ventas"]:
                entry_field = create_labeled_entry(inventory_frame, f"{label}:", placeholder_text=f"Ej: {label}", width=200, 
                                                   row=row, column=col, sticky="w", 
                                                   tooltip=f"Ingresa el {label.lower()} del producto (requerido)")
                entries[field] = entry_field["entry"]
            else:
                self.omit_vars[field] = tk.BooleanVar(value=False)
                entry_field = create_labeled_entry(inventory_frame, f"{label}:", placeholder_text=f"Ej: {label}", width=200, 
                                                   row=row, column=col, sticky="w", 
                                                   omit_var=self.omit_vars[field], toggle_callback=self.toggle_field,
                                                   tooltip=f"Ingresa el {label.lower()} del producto (requerido)")
                entries[field] = entry_field["entry"]
            
            try:
                value = float(producto[index]) if producto[index] is not None else 0.0
                if field == "precio":
                    entries[field].insert(0, f"{value:.2f}")
                else:
                    entries[field].insert(0, str(int(value)))
                if field == "precio" and value == 0:
                    self.omit_vars[field].set(True)
                    entries[field].configure(state="disabled")
            except (ValueError, TypeError) as e:
                logger.warning(f"Valor inválido en la base de datos para {field}: {producto[index]} (error: {str(e)})")
                entries[field].insert(0, "0")
            entries[field].bind("<KeyRelease>", lambda e, f=field: self.validate_numeric_entry(entries[f], label))

        media_frame = ctk.CTkFrame(content_frame, fg_color="#F5F5F5", corner_radius=8)
        media_frame.grid(row=3, column=0, padx=10, pady=5, sticky="ew", columnspan=2)
        media_frame.grid_columnconfigure(0, weight=1)
        media_frame.grid_columnconfigure(1, weight=1)

        image_subframe = ctk.CTkFrame(media_frame, fg_color="#F5F5F5", corner_radius=8)
        image_subframe.grid(row=0, column=0, padx=5, pady=5, sticky="n")
        ctk.CTkLabel(image_subframe, text="Imagen del Producto", font=("Helvetica", 12, "bold"), text_color="#1A2E5A").grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="w")

        self.edit_image_label = ctk.CTkLabel(image_subframe, text="Sin imagen", width=150, height=150)
        self.edit_image_label.grid(row=1, column=0, padx=5, pady=5)
        self.edit_image_path = producto[17]
        if self.edit_image_path:
            image_path_absolute = os.path.join(self.root_folder, self.edit_image_path)
            try:
                img = Image.open(image_path_absolute)
                img.thumbnail((150, 150), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.edit_image_label.configure(image=photo, text="")
                self.edit_image_label.image = photo
                self.image_references.append(photo)
            except Exception as e:
                logger.error(f"Error al cargar la imagen para edición: {str(e)}")
                self.edit_image_label.configure(image=self.empty_image_photo, text="No se pudo cargar la imagen")
                self.edit_image_label.image = self.empty_image_photo
        select_image_button = ctk.CTkButton(image_subframe, text="Seleccionar Imagen", command=self.select_new_image, 
                                            fg_color="#4A90E2", hover_color="#2A6EBB", corner_radius=8, font=("Helvetica", 12), width=120)
        select_image_button.grid(row=1, column=1, padx=5, pady=5)
        ToolTip(select_image_button, "Seleccionar una nueva imagen para el producto")

        qr_subframe = ctk.CTkFrame(media_frame, fg_color="#F5F5F5", corner_radius=8)
        qr_subframe.grid(row=0, column=1, padx=5, pady=5, sticky="n")
        ctk.CTkLabel(qr_subframe, text="Etiqueta del Producto", font=("Helvetica", 12, "bold"), text_color="#1A2E5A").grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="w")

        self.edit_qr_label = ctk.CTkLabel(qr_subframe, text="Sin etiqueta", width=150, height=150)
        self.edit_qr_label.grid(row=1, column=0, padx=5, pady=5)
        self.edit_qr_path = producto[13]
        if self.edit_qr_path:
            qr_path_absolute = os.path.join(self.root_folder, self.edit_qr_path)
            if os.path.exists(qr_path_absolute):
                try:
                    img = Image.open(qr_path_absolute)
                    img.thumbnail((150, 150), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    self.edit_qr_label.configure(image=photo, text="")
                    self.edit_qr_label.image = photo
                    self.image_references.append(photo)
                except Exception as e:
                    logger.error(f"Error al cargar la etiqueta para edición: {str(e)}")
                    self.edit_qr_label.configure(image=self.empty_image_photo, text="No se pudo cargar la etiqueta")
                    self.edit_qr_label.image = self.empty_image_photo

        regenerate_qr_button = ctk.CTkButton(qr_subframe, text="Regenerar Etiqueta", 
                                             command=lambda: self.manager.label_manager.regenerate_label(sku, entries, self.edit_qr_label), 
                                             fg_color="#4A90E2", hover_color="#2A6EBB", corner_radius=8, 
                                             font=("Helvetica", 12), width=120)
        regenerate_qr_button.grid(row=1, column=1, padx=5, pady=5)
        ToolTip(regenerate_qr_button, "Regenerar la etiqueta (QR) del producto")

        button_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)
        save_button = ctk.CTkButton(button_frame, text="Guardar", command=lambda: self.save_edited_product(sku, entries, edit_window), 
                                    fg_color="#4A90E2", hover_color="#2A6EBB", corner_radius=8, font=("Helvetica", 12), width=120)
        save_button.pack(side="left", padx=10)
        ToolTip(save_button, "Guardar los cambios realizados")
        cancel_button = ctk.CTkButton(button_frame, text="Cancelar", command=on_window_close, 
                                      fg_color="#FF6F61", hover_color="#E55B50", corner_radius=8, font=("Helvetica", 12), width=120)
        cancel_button.pack(side="left", padx=10)
        ToolTip(cancel_button, "Cancelar y cerrar la ventana")

        content_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

        def on_mouse_scroll(event):
            if canvas.winfo_exists() and canvas.winfo_containing(event.x_root, event.y_root) == canvas:
                canvas.yview_scroll(int(-event.delta / 120), "units")

        canvas.bind_all("<MouseWheel>", on_mouse_scroll)

    def toggle_field(self, omit_var, widget):
        state = "disabled" if omit_var.get() else "normal"
        widget.configure(state=state)

    def validate_numeric_entry(self, entry, field_name):
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

    def select_new_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")])
        if file_path:
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_extension = os.path.splitext(file_path)[1]
                new_filename = f"product_image_{timestamp}{file_extension}"
                new_file_path = os.path.join(self.root_folder, "ProductImages", new_filename)
                os.makedirs(os.path.dirname(new_file_path), exist_ok=True)
                shutil.copy(file_path, new_file_path)
                self.edit_image_path = os.path.join("ProductImages", new_filename)
                img = Image.open(new_file_path)
                img.thumbnail((150, 150), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.edit_image_label.configure(image=photo, text="")
                self.edit_image_label.image = photo
                self.image_references.append(photo)
                logger.info(f"Nueva imagen seleccionada para edición: {self.edit_image_path}")
            except PermissionError as e:
                logger.error(f"Error de permisos al copiar la imagen: {str(e)}")
                messagebox.showerror("Error", "No se tienen los permisos necesarios para copiar la imagen.")
                self.edit_image_path = None
                self.edit_image_label.configure(image=self.empty_image_photo, text="No se pudo cargar la imagen")
                self.edit_image_label.image = self.empty_image_photo
            except Exception as e:
                logger.error(f"Error al cargar la imagen para edición: {str(e)}")
                messagebox.showerror("Error", f"No se pudo cargar la imagen: {str(e)}")
                self.edit_image_path = None
                self.edit_image_label.configure(image=self.empty_image_photo, text="No se pudo cargar la imagen")
                self.edit_image_label.image = self.empty_image_photo

    def save_edited_product(self, sku, entries, edit_window):
        try:
            nombre = entries["nombre"].get().strip()
            if not nombre:
                messagebox.showerror("Error", "El campo Nombre no puede estar vacío.")
                return

            numeric_fields = [("precio", "Precio"), ("inventario", "Inventario"), ("ventas", "Ventas")]
            for field, label in numeric_fields:
                if not self.validate_numeric_entry(entries[field], label):
                    return

            precio = float(entries["precio"].get().strip() or 0.0)
            inventario = int(entries["inventario"].get().strip() or 0)
            ventas = int(entries["ventas"].get().strip() or 0)

            ubicacion = entries["ubicacion"].get().strip()
            if ubicacion and ubicacion.isdigit():
                messagebox.showerror("Error", "El campo Ubicación no puede ser un número.")
                return

            talla = entries["talla"].get().strip().upper()
            if talla:
                tallas_permitidas = CONFIG.get("TALLAS", []) + getattr(self.manager, 'tallas_personalizadas', [])
                if tallas_permitidas and talla not in tallas_permitidas:
                    messagebox.showerror("Error", f"La talla '{talla}' no está en la lista de tallas permitidas.")
                    return

            with self.db_manager as db:
                cursor = db.get_cursor()
                cursor.execute("""
                    UPDATE productos SET 
                        nombre = ?, "nivel_educativo" = ?, escuela = ?, color = ?, "tipo_prenda" = ?, "tipo_pieza" = ?, 
                        genero = ?, atributo = ?, ubicacion = ?, escudo = ?, marca = ?, talla = ?, 
                        inventario = ?, ventas = ?, precio = ?, qr_path = ?, image_path = ?
                    WHERE sku = ? AND store_id = ?
                """, (
                    nombre,
                    None if self.omit_vars["nivel_educativo"].get() else entries["nivel_educativo"].get().strip(),
                    None if self.omit_vars["escuela"].get() else entries["escuela"].get().strip(),
                    None if self.omit_vars["color"].get() else entries["color"].get().strip(),
                    None if self.omit_vars["tipo_prenda"].get() else entries["tipo_prenda"].get().strip(),
                    None if self.omit_vars["tipo_pieza"].get() else entries["tipo_pieza"].get().strip(),
                    None if self.omit_vars["genero"].get() else entries["genero"].get().strip(),
                    None if self.omit_vars["atributo"].get() else entries["atributo"].get().strip(),
                    None if self.omit_vars["ubicacion"].get() else entries["ubicacion"].get().strip(),
                    None if self.omit_vars["escudo"].get() else entries["escudo"].get().strip(),
                    None if self.omit_vars["marca"].get() else entries["marca"].get().strip(),
                    None if self.omit_vars["talla"].get() else talla,
                    inventario,
                    ventas,
                    0.0 if self.omit_vars.get("precio", tk.BooleanVar(value=False)).get() else precio,
                    self.edit_qr_path if hasattr(self, 'edit_qr_path') else None,
                    self.edit_image_path,
                    sku,
                    self.store_id
                ))
                self.db_manager.commit()
                logger.info(f"Producto actualizado en la base de datos: SKU {sku} en tienda {self.store_id}")

            self.selection_anchor = None
            self.manager.cargar_productos()
            logger.info(f"Producto actualizado: SKU {sku} en tienda {self.store_id}")
            messagebox.showinfo("Éxito", f"Producto {sku} actualizado correctamente.")
            edit_window.destroy()

        except sqlite3.Error as e:
            logger.error(f"Error al actualizar el producto con SKU {sku}: {str(e)}")
            messagebox.showerror("Error", f"No se pudo actualizar el producto: {str(e)}")
        except ValueError as e:
            logger.error(f"Valores inválidos al actualizar el producto con SKU {sku}: {str(e)}")
            messagebox.showerror("Error", f"Valores inválidos: {str(e)}")
        finally:
            edit_window.destroy()
            logger.debug("Ventana de edición cerrada")
import tkinter as tk
import customtkinter as ctk
from tkinter import ttk, messagebox
from src.core.utils.tooltips import ToolTip
from PIL import Image, ImageTk
import logging
import sqlite3
from src.core.utils.utils import sanitize_filename
from src.ui.qr_generator import generar_qr, generar_etiqueta
import os

logger = logging.getLogger(__name__)

class PrintPreviewWindow(ctk.CTkToplevel):
    def __init__(self, parent, label_path, print_callback):
        super().__init__(parent)
        self.title("Vista Previa e Impresión")
        self.geometry("600x700")
        self.configure(fg_color="#E6F0FA")
        self.transient(parent)
        self.grab_set()
        self.label_path = label_path
        self.print_callback = print_callback
        self.setup_ui()

    def setup_ui(self):
        main_frame = ctk.CTkFrame(self, fg_color="#F5F7FA", corner_radius=10, border_width=1, border_color="#A3BFFA")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        main_frame.grid_rowconfigure(0, weight=0)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_rowconfigure(2, weight=0)
        main_frame.grid_rowconfigure(3, weight=0)
        main_frame.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(main_frame, text="Vista Previa de la Etiqueta", font=("Helvetica", 16, "bold"), text_color="#1A2E5A", wraplength=500)
        title_label.grid(row=0, column=0, pady=(10, 20))

        label_frame = ctk.CTkFrame(main_frame, fg_color="#F5F5F5", corner_radius=8, width=400, height=400)
        label_frame.grid(row=1, column=0, pady=10)
        label_frame.grid_propagate(False)

        if self.label_path and os.path.exists(self.label_path):
            img = Image.open(self.label_path)
            img_width, img_height = img.size
            max_size = 400
            if img_width > img_height:
                new_width = max_size
                new_height = int(max_size * img_height / img_width)
            else:
                new_height = max_size
                new_width = int(max_size * img_width / img_height)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.label_image = tk.Label(label_frame, image=photo, bg="#F5F5F5")
            self.label_image.image = photo
            self.label_image.place(relx=0.5, rely=0.5, anchor="center")
        else:
            error_label = ctk.CTkLabel(label_frame, text="No se pudo cargar la etiqueta", font=("Helvetica", 12), text_color="#FF5555")
            error_label.place(relx=0.5, rely=0.5, anchor="center")

        copies_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        copies_frame.grid(row=2, column=0, pady=10)
        ctk.CTkLabel(copies_frame, text="Número de copias:", font=("Helvetica", 12, "bold"), text_color="#1A2E5A").pack(side="left", padx=5)
        self.copies_entry = ctk.CTkEntry(copies_frame, width=60, border_color="#A3BFFA", fg_color="#FFFFFF")
        self.copies_entry.pack(side="left", padx=5)
        self.copies_entry.insert(0, "1")
        ToolTip(self.copies_entry, "Especifica cuántas copias de la etiqueta deseas imprimir")

        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.grid(row=3, column=0, pady=20)
        ctk.CTkButton(buttons_frame, text="Imprimir", command=self.print_labels, fg_color="#4A90E2", hover_color="#2A6EBB", corner_radius=8, width=150, font=("Helvetica", 12)).pack(side="left", padx=15)
        ctk.CTkButton(buttons_frame, text="Cancelar", command=self.destroy, fg_color="#A9A9A9", hover_color="#8B8B8B", corner_radius=8, width=150, font=("Helvetica", 12)).pack(side="left", padx=15)

    def print_labels(self):
        try:
            copies = int(self.copies_entry.get().strip())
            if copies <= 0:
                messagebox.showwarning("Advertencia", "El número de copias debe ser mayor que 0.")
                return
            self.print_callback(copies)
            messagebox.showinfo("Éxito", f"Se enviaron {copies} etiquetas a la impresora.")
            self.destroy()
        except ValueError:
            messagebox.showwarning("Advertencia", "Por favor, ingresa un número válido de copias.")

class ProductManagerUI:
    def __init__(self, manager, store_id=1):
        self.manager = manager
        self.root = manager.root
        self.store_id = store_id
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
        self.empty_image = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        self.empty_image_photo = ImageTk.PhotoImage(self.empty_image)
        logger.info(f"Inicializando ProductManagerUI para tienda {self.store_id}")
        logger.debug(f"Iconos disponibles: {list(self.manager.icons.keys())}")
        print("Iniciando ProductManagerUI")
        self.setup_ui()
        print("setup_ui completado")

    def setup_ui(self):
        print("Iniciando setup_ui")
        self.manager.main_frame.grid_rowconfigure(0, weight=1)
        self.manager.main_frame.grid_columnconfigure(0, weight=1)

        self.main_frame = ctk.CTkFrame(self.manager.main_frame, fg_color="#FFFFFF", corner_radius=10, border_width=2, border_color="#D3D3D3")
        self.main_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=0)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        print("main_frame configurado")

        top_bar = ctk.CTkFrame(self.main_frame, fg_color="#F5F7FA", corner_radius=0)
        top_bar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        top_bar.grid_columnconfigure(0, weight=0)
        top_bar.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(top_bar, text="Gestión de Productos", font=("Helvetica", 18, "bold"), text_color="#1A2E5A").grid(row=0, column=0, padx=15, pady=10, sticky="w")

        search_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        search_frame.grid(row=0, column=1, padx=15, sticky="e")
        ctk.CTkLabel(search_frame, text="🔍 Buscar:", font=("Helvetica", 12)).grid(row=0, column=0, padx=5, sticky="w")
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Buscar por SKU o Nombre", width=200)
        self.search_entry.grid(row=0, column=1, padx=5, sticky="w")
        self.search_entry.bind("<KeyRelease>", self.manager.apply_quick_search)
        self.search_entry.bind("<Return>", self.manager.apply_quick_search)

        content_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        content_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=4, minsize=500)
        content_frame.grid_columnconfigure(1, weight=1, minsize=250)
        print(f"content_frame configurado: {content_frame.winfo_width()}x{content_frame.winfo_height()}")

        left_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        left_frame.grid_rowconfigure(0, weight=0)
        left_frame.grid_rowconfigure(1, weight=0)
        left_frame.grid_rowconfigure(2, weight=1)
        left_frame.grid_rowconfigure(3, weight=0)
        left_frame.grid_columnconfigure(0, weight=1)

        filter_frame = ctk.CTkFrame(left_frame, fg_color="#F5F7FA", corner_radius=5)
        filter_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))

        product_filter_frame = ctk.CTkFrame(filter_frame, fg_color="#E6F0FA", corner_radius=5)
        product_filter_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=2)
        product_filter_frame.grid_columnconfigure(0, weight=0)
        product_filter_frame.grid_columnconfigure(1, weight=0)
        product_filter_frame.grid_columnconfigure(2, weight=0)
        product_filter_frame.grid_columnconfigure(3, weight=0)
        product_filter_frame.grid_columnconfigure(4, weight=1)
        ctk.CTkLabel(product_filter_frame, text="Características del Producto", font=("Helvetica", 14, "bold"), text_color="#1A2E5A").grid(row=0, column=0, columnspan=5, padx=10, sticky="w")
        self.combo_color = ctk.CTkComboBox(product_filter_frame, values=[""], width=150, font=("Helvetica", 12))
        self.combo_color.grid(row=1, column=0, padx=10, sticky="w")
        self.combo_tipo_prenda = ctk.CTkComboBox(product_filter_frame, values=[""], width=150, font=("Helvetica", 12))
        self.combo_tipo_prenda.grid(row=1, column=1, padx=10, sticky="w")
        self.combo_tipo_pieza = ctk.CTkComboBox(product_filter_frame, values=[""], width=150, font=("Helvetica", 12))
        self.combo_tipo_pieza.grid(row=1, column=2, padx=10, sticky="w")
        self.combo_atributo = ctk.CTkComboBox(product_filter_frame, values=[""], width=150, font=("Helvetica", 12))
        self.combo_atributo.grid(row=1, column=3, padx=10, sticky="w")

        other_filter_frame = ctk.CTkFrame(filter_frame, fg_color="#E6F0FA", corner_radius=5)
        other_filter_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=2)
        other_filter_frame.grid_columnconfigure(0, weight=0)
        other_filter_frame.grid_columnconfigure(1, weight=0)
        other_filter_frame.grid_columnconfigure(2, weight=0)
        other_filter_frame.grid_columnconfigure(3, weight=0)
        other_filter_frame.grid_columnconfigure(4, weight=0)
        other_filter_frame.grid_columnconfigure(5, weight=1)
        ctk.CTkLabel(other_filter_frame, text="Otros Filtros", font=("Helvetica", 14, "bold"), text_color="#1A2E5A").grid(row=0, column=0, columnspan=5, padx=10, sticky="w")
        self.combo_escuela = ctk.CTkComboBox(other_filter_frame, values=[""], width=150, font=("Helvetica", 12))
        self.combo_escuela.grid(row=1, column=0, padx=10, sticky="w")
        self.combo_nivel = ctk.CTkComboBox(other_filter_frame, values=[""], width=150, font=("Helvetica", 12))
        self.combo_nivel.grid(row=1, column=1, padx=10, sticky="w")
        self.combo_genero = ctk.CTkComboBox(other_filter_frame, values=[""], width=150, font=("Helvetica", 12))
        self.combo_genero.grid(row=1, column=2, padx=10, sticky="w")
        self.combo_marca = ctk.CTkComboBox(other_filter_frame, values=[""], width=150, font=("Helvetica", 12))
        self.combo_marca.grid(row=1, column=3, padx=10, sticky="w")
        self.combo_talla = ctk.CTkComboBox(other_filter_frame, values=[""], width=150, font=("Helvetica", 12))
        self.combo_talla.grid(row=1, column=4, padx=10, sticky="w")

        control_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        control_frame.grid(row=1, column=0, sticky="ew", pady=5)
        control_frame.grid_columnconfigure(0, weight=0)
        control_frame.grid_columnconfigure(1, weight=0)
        control_frame.grid_columnconfigure(2, weight=0)
        control_frame.grid_columnconfigure(3, weight=1)
        self.filter_button = ctk.CTkButton(control_frame, text="Aplicar Filtros", command=self.manager.apply_filters, fg_color="#4A90E2", hover_color="#2A6EBB", width=120, corner_radius=8, font=("Helvetica", 12))
        self.filter_button.grid(row=0, column=0, padx=5, sticky="w")
        ctk.CTkButton(control_frame, text="🗑 Limpiar Filtros", command=self.manager.clear_filters, fg_color="#FF6F61", hover_color="#E55B50", width=120, corner_radius=8, font=("Helvetica", 12)).grid(row=0, column=1, padx=5, sticky="w")
        ctk.CTkButton(control_frame, text="🔄 Refrescar", command=self.manager.cargar_productos, fg_color="#4A90E2", hover_color="#2A6EBB", width=120, corner_radius=8, font=("Helvetica", 12)).grid(row=0, column=2, padx=5, sticky="w")
        self.selection_count_label = ctk.CTkLabel(control_frame, text="Productos seleccionados: 0", font=("Helvetica", 12))
        self.selection_count_label.grid(row=0, column=3, padx=10, sticky="w")

        tree_and_pagination_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        tree_and_pagination_frame.grid(row=2, column=0, sticky="nsew")
        tree_and_pagination_frame.grid_rowconfigure(0, weight=1)
        tree_and_pagination_frame.grid_rowconfigure(1, weight=0)
        tree_and_pagination_frame.grid_columnconfigure(0, weight=1)

        tree_frame = ctk.CTkFrame(tree_and_pagination_frame, fg_color="transparent")
        tree_frame.grid(row=0, column=0, sticky="nsew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(1, weight=0)
        columns_to_show = ["Select"] + self.visible_columns
        self.tree = ttk.Treeview(tree_frame, columns=columns_to_show, show="headings", height=10)
        self.tree.grid(row=0, column=0, sticky="nsew")

        style = ttk.Style()
        style.configure("Treeview", rowheight=22, font=("Helvetica", 11), highlightthickness=1, highlightcolor="#808080", highlightbackground="#808080")
        style.map("Treeview", background=[('selected', '#ADD8E6'), ('!selected', 'white')], foreground=[('!selected', 'black')])
        style.configure("Treeview.Heading", font=("Helvetica", 12))
        self.tree.tag_configure("selected", background="#ADD8E6")

        scrollbar_y = ctk.CTkScrollbar(tree_frame, command=self.tree.yview)
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar_y.set)

        self.tree.heading("Select", text="✔")
        self.tree.column("Select", width=40, anchor="center", stretch=False)
        column_widths = {
            "sku": 100, "nombre": 200, "escuela": 90, "nivel_educativo": 70, "marca": 70,
            "color": 60, "tipo_prenda": 80, "tipo_pieza": 80, "ubicacion": 80, "escudo": 80,
            "talla": 50, "inventario": 50, "ventas": 50, "precio": 55
        }
        for col in self.visible_columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.manager.sort_by_column(c))
            self.tree.column(col, width=column_widths.get(col, 100), anchor="center")

        self.tree.bind("<Button-1>", self.on_treeview_click)
        self.tree.bind("<Double-1>", self.on_treeview_double_click)
        self.tree.bind("<Shift-Button-1>", self.on_shift_click)
        self.tree.bind("<<TreeviewSelect>>", self.manager.mostrar_detalle)
        self.root.bind("<Control-a>", lambda event: self.select_all_with_shortcut(event))
        self.root.bind("<Control-Shift-A>", lambda event: self.deselect_all_with_shortcut(event))
        self.tree.bind("<Control-Shift-Down>", self.on_ctrl_shift_down)
        self.tree.bind("<Control-Shift-Up>", self.on_ctrl_shift_up)
        self.tree.bind("<Shift-Up>", lambda event: "break")
        self.tree.bind("<Shift-Down>", lambda event: "break")

        self.root.bind("<Escape>", lambda event: self.clear_window())

        pagination_frame = ctk.CTkFrame(tree_and_pagination_frame, fg_color="transparent")
        pagination_frame.grid(row=1, column=0, sticky="ew", pady=5)
        pagination_frame.grid_columnconfigure(0, weight=0)
        pagination_frame.grid_columnconfigure(1, weight=0)
        pagination_frame.grid_columnconfigure(2, weight=0)
        pagination_frame.grid_columnconfigure(3, weight=1)
        pagination_frame.grid_columnconfigure(4, weight=0)
        pagination_frame.grid_columnconfigure(5, weight=0)
        self.prev_button = ctk.CTkButton(pagination_frame, text="◄", command=self.manager.prev_page, fg_color="#4A90E2", hover_color="#2A6EBB", corner_radius=8, font=("Helvetica", 12), width=40)
        self.prev_button.grid(row=0, column=0, padx=5, sticky="w")
        self.page_label = ctk.CTkLabel(pagination_frame, text="Página 1 de 1", font=("Helvetica", 12))
        self.page_label.grid(row=0, column=1, padx=5, sticky="w")
        self.next_button = ctk.CTkButton(pagination_frame, text="►", command=self.manager.next_page, fg_color="#4A90E2", hover_color="#2A6EBB", corner_radius=8, font=("Helvetica", 12), width=40)
        self.next_button.grid(row=0, column=2, padx=5, sticky="w")
        self.select_all_button = ctk.CTkButton(pagination_frame, text="✓ Todo", command=self.select_all, fg_color="#4A90E2", hover_color="#2A6EBB", corner_radius=8, font=("Helvetica", 12))
        self.select_all_button.grid(row=0, column=4, padx=5, sticky="e")
        self.deselect_all_button = ctk.CTkButton(pagination_frame, text="✗ Ninguno", command=self.deselect_all, fg_color="#FF6F61", hover_color="#E55B50", corner_radius=8, font=("Helvetica", 12))
        self.deselect_all_button.grid(row=0, column=5, padx=5, sticky="e")

        detail_frame = ctk.CTkFrame(content_frame, fg_color="#FFFFFF", corner_radius=10, border_width=2, border_color="#D3D3D3", width=250)
        detail_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        detail_frame.grid_propagate(False)
        detail_frame.grid_rowconfigure(0, weight=0)
        detail_frame.grid_rowconfigure(1, weight=0)
        detail_frame.grid_rowconfigure(2, weight=1)
        detail_frame.grid_rowconfigure(3, weight=0)
        detail_frame.grid_rowconfigure(4, weight=0)
        detail_frame.grid_columnconfigure(0, weight=1)
        print(f"detail_frame colocado en grid: row=0, column=1, dimensions={detail_frame.winfo_width()}x{detail_frame.winfo_height()}")

        title_frame = ctk.CTkFrame(detail_frame, fg_color="#1A2E5A", corner_radius=0)
        title_frame.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(title_frame, text="Detalles del Producto", font=("Helvetica", 16, "bold"), text_color="#FFFFFF").grid(row=0, column=0, pady=5, padx=10, sticky="w")
        print("title_frame creado y colocado")

        details_content = ctk.CTkFrame(detail_frame, fg_color="#FFFFFF", corner_radius=5, width=250)
        details_content.grid(row=1, column=0, sticky="nsew", padx=5, pady=(5, 5))
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
            self.detail_labels[field] = ctk.CTkLabel(details_content, text="", font=("Helvetica", 11), text_color="#333333", wraplength=80, anchor="w", justify="left")
            self.detail_labels[field].grid(row=row, column=col_value, padx=(3, 5), pady=0, sticky="w")
        print("details_content creado y colocado, detail_labels inicializado")

        media_frame = ctk.CTkFrame(detail_frame, fg_color="transparent", width=250)
        media_frame.grid(row=3, column=0, sticky="ew", padx=5, pady=(2, 2))
        media_frame.grid_propagate(False)
        media_frame.grid_columnconfigure(0, weight=1)
        media_frame.grid_columnconfigure(1, weight=1)

        image_frame = ctk.CTkFrame(media_frame, fg_color="#F5F5F5", corner_radius=8, width=100)
        image_frame.grid(row=0, column=0, sticky="ew", padx=(0, 3))
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
        print("image_frame creado y colocado, image_label inicializado")

        qr_frame = ctk.CTkFrame(media_frame, fg_color="#F5F5F5", corner_radius=8, width=100)
        qr_frame.grid(row=0, column=1, sticky="ew", padx=(3, 0))
        qr_frame.grid_propagate(False)
        qr_frame.grid_columnconfigure(0, weight=1)
        qr_frame.grid_rowconfigure(0, weight=0)
        qr_frame.grid_rowconfigure(1, weight=1)
        qr_frame.grid_rowconfigure(2, weight=0)
        ctk.CTkLabel(qr_frame, text="Etiqueta del Producto:", font=("Helvetica", 10, "bold"), text_color="#1A2E5A").grid(row=0, column=0, pady=(2, 1), sticky="n")
        self.qr_container = tk.Frame(qr_frame, width=90, height=90, bg="#F5F5F5")
        self.qr_container.grid(row=1, column=0, pady=(0, 2), sticky="n")
        self.qr_container.grid_propagate(False)
        self.qr_label = tk.Label(self.qr_container, text="Selecciona un producto", width=90, height=90, bg="#F5F5F5")
        self.qr_label.pack()
        self.copy_label_button = ctk.CTkButton(qr_frame, text="Copiar Etiqueta", command=self.manager.copy_image_to_clipboard, 
                                               fg_color="#4A90E2", hover_color="#2A6EBB", corner_radius=8, font=("Helvetica", 10), width=80)
        self.copy_label_button.grid(row=2, column=0, pady=2)
        ToolTip(self.copy_label_button, "Copiar la etiqueta (QR) al portapapeles (Ctrl+Q)")
        print("qr_frame creado y colocado, qr_label inicializado")

        self.create_action_buttons(detail_frame)
        print("action_buttons_frame creado y colocado")

        self.manager.main_frame.bind("<Configure>", self.on_resize)

        self.manager.main_frame.update()
        print(f"Main frame actualizado: {self.manager.main_frame.winfo_width()}x{self.manager.main_frame.winfo_height()}")
        print(f"content_frame dimensions después de update: {content_frame.winfo_width()}x{content_frame.winfo_height()}")
        print(f"left_frame dimensions después de update: {left_frame.winfo_width()}x{left_frame.winfo_height()}")
        print(f"detail_frame dimensions después de update: {detail_frame.winfo_width()}x{detail_frame.winfo_height()}")

    def create_action_buttons(self, parent_frame):
        action_buttons_frame = ctk.CTkFrame(parent_frame, fg_color="transparent", width=250)
        action_buttons_frame.grid(row=4, column=0, sticky="s", padx=5, pady=(0, 5))
        action_buttons_frame.grid_propagate(False)
        for i in range(6):
            action_buttons_frame.grid_columnconfigure(i, weight=1, minsize=40)
        action_buttons_frame.grid_rowconfigure(0, weight=0)

        buttons = [
            ("edit", self.manager.edit_product, "Editar el producto seleccionado", 0),
            ("copy", self.manager.copy_sku, "Copiar el SKU del producto seleccionado", 1),
            ("delete", self.manager.eliminar_seleccion, "Eliminar los productos seleccionados", 2),
            ("duplicate", self.manager.duplicar_producto, "Duplicar el producto seleccionado", 3),
            ("price", self.manager.open_price_modification_window, "Modificar precios de productos", 4),
            ("print", self.open_print_preview, "Vista previa e impresión de etiquetas (Ctrl+P)", 5),
        ]

        for icon_key, command, tooltip, column in buttons:
            icon = self.manager.icons.get(icon_key)
            if icon is None:
                logger.warning(f"Icono '{icon_key}' no encontrado")
            button = ctk.CTkButton(action_buttons_frame, image=icon, text="", command=command,
                                   fg_color="#4A90E2" if icon_key != "delete" else "#FF5555",
                                   hover_color="#2A6EBB" if icon_key != "delete" else "#CC4444",
                                   corner_radius=8, width=32, height=32)
            button.grid(row=0, column=column, padx=2, pady=2)
            ToolTip(button, tooltip)
            setattr(self, f"{icon_key}_button", button)

        return action_buttons_frame

    def on_resize(self, event):
        total_width = self.manager.main_frame.winfo_width()
        if total_width < 800:
            minsize_right = 200
        elif total_width < 1200:
            minsize_right = 230
        else:
            minsize_right = 260
        
        content_frame = self.main_frame.winfo_children()[1]
        content_frame.grid_columnconfigure(1, minsize=minsize_right)
        detail_frame = content_frame.winfo_children()[1]
        detail_frame.configure(width=minsize_right)

    def open_print_preview(self):
        logger.debug(f"Abriendo vista previa de impresión con label_path: {self.current_label_path}")
        if not self.current_label_path:
            messagebox.showwarning("Advertencia", "Por favor, selecciona un producto con una etiqueta para imprimir.")
            return
        PrintPreviewWindow(self.root, self.current_label_path, self.manager.print_labels)

    def split_text(self, text, max_length=10):
        text = str(text)
        if len(text) <= max_length:
            return text
        words = text.split()
        if len(words) <= 1:
            mid = len(text) // 2
            return f"{text[:mid]}\n{text[mid:]}"
        mid = len(words) // 2
        part1 = " ".join(words[:mid])
        part2 = " ".join(words[mid:])
        if len(part1) > max_length:
            mid = len(part1) // 2
            part1 = f"{part1[:mid]}\n{part1[mid:]}"
        if len(part2) > max_length:
            mid = len(part2) // 2
            part2 = f"{part2[:mid]}\n{part2[mid:]}"
        return f"{part1}\n{part2}"

    def clear_window(self):
        self.clear_filters()
        self.deselect_all()
        for field, label in self.detail_labels.items():
            logger.debug(f"Limpiando campo {field}")
            label.configure(text="")
        self.image_label.configure(image=self.empty_image_photo, text="Sin imagen")
        self.image_label.image = self.empty_image_photo
        logger.debug("Imagen limpiada")
        self.qr_label.configure(image=self.empty_image_photo, text="Selecciona un producto")
        self.qr_label.image = self.empty_image_photo
        logger.debug("QR limpiado")
        self.current_label_path = None
        self.last_selected_sku = None
        logger.debug("Ventana limpiada con éxito")

    def on_closing(self):
        logger.debug("Cerrando ProductManagerUI")
        if hasattr(self, 'tree') and self.tree.winfo_exists():
            self.tree.unbind("<<TreeviewSelect>>")
            self.tree.unbind("<Button-1>")
            self.tree.unbind("<Double-1>")
            self.tree.unbind("<Shift-Button-1>")
            self.tree.unbind("<Control-Shift-Up>")
            self.tree.unbind("<Control-Shift-Down>")
            self.tree.unbind("<Shift-Up>")
            self.tree.unbind("<Shift-Down>")
        self.manager.main_frame.pack_forget()

    def mostrar_detalle(self, event):
        selected_items = self.tree.selection()
        logger.debug(f"Elementos seleccionados: {selected_items}")
        if not selected_items:
            logger.debug("No hay elementos seleccionados para mostrar detalles.")
            for field, label in self.detail_labels.items():
                logger.debug(f"Limpiando campo {field}")
                label.configure(text="")
            self.image_label.configure(image=self.empty_image_photo, text="Sin imagen")
            self.image_label.image = self.empty_image_photo
            logger.debug("Imagen limpiada")
            self.qr_label.configure(image=self.empty_image_photo, text="Selecciona un producto")
            self.qr_label.image = self.empty_image_photo
            logger.debug("QR limpiado")
            self.current_label_path = None
            return

        item = selected_items[0]
        values = self.tree.item(item, "values")
        logger.debug(f"Valores del item seleccionado: {values}")
        sku = values[1].upper()
        logger.debug(f"Mostrando detalles para SKU: {sku}")
        if sku == self.last_selected_sku:
            logger.debug("SKU ya mostrado, omitiendo actualización")
            return

        self.last_selected_sku = sku
        try:
            with self.manager.db_manager as db:
                cursor = db.get_cursor()
                cursor.execute('SELECT * FROM productos WHERE sku = ? AND store_id = ?', (sku, self.store_id))
                producto = cursor.fetchone()
                if not producto:
                    logger.error(f"Producto no encontrado con SKU {sku} en tienda {self.store_id}.")
                    messagebox.showerror("Error", "Producto no encontrado.")
                    return

                logger.debug(f"Datos del producto SKU {sku}: {producto}")

                fields_mapping = {
                    "sku": producto[0],
                    "nombre": producto[1],
                    "nivel_educativo": producto[2],
                    "escuela": producto[3],
                    "color": producto[4],
                    "tipo_prenda": producto[5],
                    "tipo_pieza": producto[6],
                    "genero": producto[7],
                    "marca": producto[8],
                    "talla": producto[9],
                    "atributo": producto[10],
                    "ubicacion": producto[11],
                    "escudo": producto[12],
                    "inventario": producto[14],
                    "ventas": producto[15],
                    "precio": producto[16],
                }

                for field, value in fields_mapping.items():
                    display_value = str(value if value is not None else "")
                    display_value = self.split_text(display_value, max_length=10)
                    if field == "precio" and value:
                        try:
                            display_value = f"{float(value):.2f}"
                        except ValueError:
                            pass
                    if field == "escuela" and display_value:
                        nivel_educativo = fields_mapping.get("nivel_educativo", "")
                        if nivel_educativo:
                            display_value = self.split_text(f"{display_value} ({nivel_educativo})", max_length=10)
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
                        display_value = self.split_text(f"{symbol} {display_value}" if symbol else display_value, max_length=10)
                        logger.debug(f"Actualizando {field} con valor: {display_value}, color: {color}")
                        self.detail_labels[field].configure(text=display_value, text_color=color)
                        continue
                    if field == "ubicacion":
                        display_value = display_value if display_value else ""
                    logger.debug(f"Actualizando {field} con valor: {display_value}")
                    self.detail_labels[field].configure(text=display_value, text_color="#4B5EAA")

                image_path = producto[17]
                logger.debug(f"Intentando cargar imagen desde: {image_path}")
                if image_path:
                    image_path_absolute = os.path.join(self.manager.root_folder, image_path)
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

                qr_path = producto[13]
                nombre = producto[1]
                nivel_educativo = producto[2]
                escuela = producto[3]
                talla = producto[9]
                genero = producto[7]

                logger.debug(f"Intentando cargar o generar etiqueta QR para SKU {sku}, qr_path: {qr_path}")
                nombre_base = nombre.rsplit(" ", 1)[0] if " " in nombre else nombre
                folder_name = f"{nombre_base}_{producto[5]}_{producto[6]}"
                folder_path = os.path.join(self.manager.root_folder, "Mis codigos", folder_name.replace("/", "_").replace("\\", "_"))
                talla_folder = os.path.join(folder_path, sanitize_filename(talla) if talla else "SinTalla")
                os.makedirs(talla_folder, exist_ok=True)

                qr_file_path = os.path.join(talla_folder, f"{sku}_{nombre_base}_{sanitize_filename(talla) if talla else 'SinTalla'}_qr.png")
                label_file_path = os.path.join(talla_folder, f"{sku}_{nombre_base}_{sanitize_filename(talla) if talla else 'SinTalla'}_label.png")

                if qr_path and "Mis codigos" in qr_path:
                    old_folder = os.path.dirname(os.path.dirname(qr_path))
                    if old_folder != os.path.join("Mis codigos", folder_name.replace("/", "_").replace("\\", "_")):
                        qr_path = None
                        logger.debug("Ruta de QR desactualizada, será regenerada.")

                if not os.path.exists(qr_file_path):
                    generar_qr(sku, qr_file_path)
                    logger.debug(f"QR generado en: {qr_file_path}")

                if not qr_path or qr_path == "" or not os.path.exists(label_file_path) or qr_path != os.path.relpath(label_file_path, self.manager.root_folder):
                    generar_etiqueta(sku, escuela, nivel_educativo, nombre_base, talla, genero, qr_file_path, label_file_path)
                    cursor.execute("UPDATE productos SET qr_path = ? WHERE sku = ? AND store_id = ?", (os.path.relpath(label_file_path, self.manager.root_folder), sku, self.store_id))
                    self.manager.db_manager.commit()
                    qr_path = os.path.relpath(label_file_path, self.manager.root_folder)
                    logger.debug(f"Etiqueta generada y guardada en: {label_file_path}")

                if qr_path:
                    qr_path_absolute = os.path.join(self.manager.root_folder, qr_path)
                    logger.debug(f"Ruta absoluta de la etiqueta QR: {qr_path_absolute}")
                    if os.path.exists(qr_path_absolute):
                        img = Image.open(qr_path_absolute)
                        img.thumbnail((90, 90), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(img)
                        self.qr_label.configure(image=photo, text="")
                        self.qr_label.image = photo
                        self.current_label_path = qr_path_absolute
                        logger.debug("Etiqueta QR cargada exitosamente.")
                    else:
                        logger.error(f"Archivo de QR no encontrado: {qr_path_absolute}")
                        self.qr_label.configure(image=self.empty_image_photo, text="No se pudo generar la etiqueta")
                        self.qr_label.image = self.empty_image_photo
                        self.current_label_path = None
                else:
                    logger.error(f"No se pudo generar QR para SKU: {sku}")
                    self.qr_label.configure(image=self.empty_image_photo, text="No se pudo generar la etiqueta")
                    self.qr_label.image = self.empty_image_photo
                    self.current_label_path = None
        except sqlite3.Error as e:
            logger.error(f"Error al actualizar la etiqueta para SKU {sku}: {str(e)}")
            messagebox.showerror("Error", f"No se pudo actualizar la etiqueta: {str(e)}")
        except OSError as e:
            logger.error(f"Error al manejar archivos para SKU {sku}: {str(e)}")
            messagebox.showerror("Error", f"Error al manejar archivos: {str(e)}")
        except Exception as e:
            logger.error(f"Error inesperado al mostrar detalles para SKU {sku}: {str(e)}")
            messagebox.showerror("Error", f"Error inesperado: {str(e)}")
            self.qr_label.configure(image=self.empty_image_photo, text="No se pudo generar la etiqueta")
            self.qr_label.image = self.empty_image_photo
            self.current_label_path = None

    def initialize_comboboxes(self):
        print("Inicializando comboboxes")
        self.combo_color.configure(values=self.manager.get_unique_values("color"))
        self.combo_tipo_prenda.configure(values=self.manager.get_unique_values("tipo_prenda"))
        self.combo_tipo_pieza.configure(values=self.manager.get_unique_values("tipo_pieza"))
        self.combo_atributo.configure(values=self.manager.get_unique_values("atributo"))
        self.combo_escuela.configure(values=self.manager.get_unique_values("escuela"))
        self.combo_nivel.configure(values=self.manager.get_unique_values("nivel_educativo"))
        self.combo_genero.configure(values=self.manager.get_unique_values("genero"))
        self.combo_marca.configure(values=self.manager.get_unique_values("marca"))
        self.combo_talla.configure(values=self.manager.get_unique_values("talla"))

    def update_filter_comboboxes(self):
        try:
            self.combo_color.configure(values=[""] + sorted(self.manager.get_unique_values("color")))
            self.combo_tipo_prenda.configure(values=[""] + sorted(self.manager.get_unique_values("tipo_prenda")))
            self.combo_tipo_pieza.configure(values=[""] + sorted(self.manager.get_unique_values("tipo_pieza")))
            self.combo_atributo.configure(values=[""] + sorted(self.manager.get_unique_values("atributo")))
            self.combo_escuela.configure(values=[""] + sorted(self.manager.get_unique_values("escuela")))
            self.combo_nivel.configure(values=[""] + sorted(self.manager.get_unique_values("nivel_educativo")))
            self.combo_genero.configure(values=[""] + sorted(self.manager.get_unique_values("genero")))
            self.combo_marca.configure(values=[""] + sorted(self.manager.get_unique_values("marca")))
            self.combo_talla.configure(values=[""] + sorted(self.manager.get_unique_values("talla")))
            print("Comboboxes de filtros actualizados correctamente.")
        except Exception as e:
            print(f"Error al actualizar comboboxes de filtros: {str(e)}")
            raise

    def update_pagination_text(self, total_items, current_page, total_pages):
        if total_items == 0:
            self.page_label.configure(text="No hay productos")
        else:
            self.page_label.configure(text=f"Página {current_page + 1} de {total_pages}")

    def adjust_column_widths(self):
        available_width = self.manager.main_frame.winfo_width() - 650
        total_width = sum([40, 90, 180, 90, 70, 70, 60, 80, 80, 80, 80, 50, 50, 50, 55])
        if available_width > total_width:
            stretch_factor = available_width / total_width
            column_widths = {
                "Select": 40, "sku": 90, "nombre": 180, "escuela": 90, "nivel_educativo": 70, "marca": 70,
                "color": 60, "tipo_prenda": 80, "tipo_pieza": 80, "ubicacion": 80, "escudo": 80, "talla": 50, "inventario": 50, "ventas": 50, "precio": 55
            }
            for col in self.tree["columns"]:
                new_width = int(column_widths.get(col, 70) * stretch_factor)
                self.tree.column(col, width=new_width)

    def lock_interface(self, lock=True):
        state = "disabled" if lock else "normal"
        logger.debug(f"Lock interface called with lock={lock}, tree exists={hasattr(self, 'tree') and self.tree.winfo_exists()}")

        try:
            if hasattr(self, 'prev_button') and self.prev_button.winfo_exists():
                self.prev_button.configure(state=state)
            if hasattr(self, 'next_button') and self.next_button.winfo_exists():
                self.next_button.configure(state=state)
            if hasattr(self, 'combo_escuela') and self.combo_escuela.winfo_exists():
                self.combo_escuela.configure(state=state)
            if hasattr(self, 'combo_nivel') and self.combo_nivel.winfo_exists():
                self.combo_nivel.configure(state=state)
            if hasattr(self, 'combo_color') and self.combo_color.winfo_exists():
                self.combo_color.configure(state=state)
            if hasattr(self, 'combo_tipo_prenda') and self.combo_tipo_prenda.winfo_exists():
                self.combo_tipo_prenda.configure(state=state)
            if hasattr(self, 'combo_tipo_pieza') and self.combo_tipo_pieza.winfo_exists():
                self.combo_tipo_pieza.configure(state=state)
            if hasattr(self, 'combo_genero') and self.combo_genero.winfo_exists():
                self.combo_genero.configure(state=state)
            if hasattr(self, 'combo_atributo') and self.combo_atributo.winfo_exists():
                self.combo_atributo.configure(state=state)
            if hasattr(self, 'combo_marca') and self.combo_marca.winfo_exists():
                self.combo_marca.configure(state=state)
            if hasattr(self, 'combo_talla') and self.combo_talla.winfo_exists():
                self.combo_talla.configure(state=state)
            if hasattr(self, 'search_entry') and self.search_entry.winfo_exists():
                self.search_entry.configure(state=state)
            if hasattr(self, 'filter_button') and self.filter_button.winfo_exists():
                self.filter_button.configure(state=state)
            if hasattr(self, 'select_all_button') and self.select_all_button.winfo_exists():
                self.select_all_button.configure(state=state)
            if hasattr(self, 'deselect_all_button') and self.deselect_all_button.winfo_exists():
                self.deselect_all_button.configure(state=state)
            if hasattr(self, 'edit_button') and self.edit_button.winfo_exists():
                self.edit_button.configure(state=state)
            if hasattr(self, 'copy_button') and self.copy_button.winfo_exists():
                self.copy_button.configure(state=state)
            if hasattr(self, 'delete_button') and self.delete_button.winfo_exists():
                self.delete_button.configure(state=state)
            if hasattr(self, 'duplicate_button') and self.duplicate_button.winfo_exists():
                self.duplicate_button.configure(state=state)
            if hasattr(self, 'price_button') and self.price_button.winfo_exists():
                self.price_button.configure(state=state)
            if hasattr(self, 'print_button') and self.print_button.winfo_exists():
                self.print_button.configure(state=state)
            if hasattr(self, 'copy_label_button') and self.copy_label_button.winfo_exists():
                self.copy_label_button.configure(state=state)

            if hasattr(self, 'tree') and self.tree.winfo_exists():
                if lock:
                    self.tree.unbind("<Button-1>")
                    self.tree.unbind("<Double-1>")
                    self.tree.unbind("<Shift-Button-1>")
                    self.tree.unbind("<Control-Shift-Up>")
                    self.tree.unbind("<Control-Shift-Down>")
                    self.tree.unbind("<Shift-Up>")
                    self.tree.unbind("<Shift-Down>")
                    self.tree.unbind("<<TreeviewSelect>>")
                else:
                    self.tree.bind("<Button-1>", self.on_treeview_click)
                    self.tree.bind("<Double-1>", self.on_treeview_double_click)
                    self.tree.bind("<Shift-Button-1>", self.on_shift_click)
                    self.tree.bind("<Control-Shift-Up>", self.on_ctrl_shift_up)
                    self.tree.bind("<Control-Shift-Down>", self.on_ctrl_shift_down)
                    self.tree.bind("<Shift-Up>", lambda event: "break")
                    self.tree.bind("<Shift-Down>", lambda event: "break")
                    self.tree.bind("<<TreeviewSelect>>", self.manager.mostrar_detalle)
            else:
                logger.warning("El widget self.tree no existe o ha sido destruido. No se pueden vincular/desvincular eventos.")
        except tk.TclError as e:
            logger.warning(f"Error al configurar widgets en lock_interface: {str(e)}")

    def update_selection_count(self):
        selected_count = sum(1 for value in self.selection_state.values() if value)
        self.selection_count_label.configure(text=f"Productos seleccionados: {selected_count}")

    def on_treeview_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            return
        column = self.tree.identify_column(event.x)
        if column != "#1":
            return
        item = self.tree.identify_row(event.y)
        if item:
            sku = self.tree.item(item, "values")[1]
            current_value = self.tree.item(item, "values")[0]
            new_value = "☑" if current_value == "☐" else "☐"
            values = list(self.tree.item(item, "values"))
            values[0] = new_value
            self.tree.item(item, values=values)
            self.selection_state[sku] = (new_value == "☑")
            if new_value == "☑":
                self.tree.item(item, tags=("selected",))
            else:
                self.tree.item(item, tags=())
            self.update_selection_count()

    def on_treeview_double_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        sku = self.tree.item(item, "values")[1]
        current_value = self.tree.item(item, "values")[0]
        new_value = "☑" if current_value == "☐" else "☐"
        values = list(self.tree.item(item, "values"))
        values[0] = new_value
        self.tree.item(item, values=values)
        self.selection_state[sku] = (new_value == "☑")
        if new_value == "☑":
            self.tree.item(item, tags=("selected",))
        else:
            self.tree.item(item, tags=())
        self.update_selection_count()

    def on_shift_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        sku = self.tree.item(item, "values")[1]
        if not self.first_selected_item:
            self.first_selected_item = item
            current_value = self.tree.item(item, "values")[0]
            new_value = "☑" if current_value == "☐" else "☐"
            values = list(self.tree.item(item, "values"))
            values[0] = new_value
            self.tree.item(item, values=values)
            self.selection_state[sku] = (new_value == "☑")
            if new_value == "☑":
                self.tree.item(item, tags=("selected",))
            else:
                self.tree.item(item, tags=())
        else:
            items = list(self.tree.get_children())
            start_idx = items.index(self.first_selected_item)
            end_idx = items.index(item)
            start, end = min(start_idx, end_idx), max(start_idx, end_idx)
            for idx in range(start, end + 1):
                current_item = items[idx]
                current_sku = self.tree.item(current_item, "values")[1]
                values = list(self.tree.item(current_item, "values"))
                values[0] = "☑"
                self.tree.item(current_item, values=values)
                self.selection_state[current_sku] = True
                self.tree.item(current_item, tags=("selected",))
            self.first_selected_item = None
        self.update_selection_count()

    def on_ctrl_shift_down(self, event):
        items = list(self.tree.get_children())
        if not items:
            return

        current_focus = self.tree.focus()
        if not current_focus:
            self.selection_anchor = items[0]
            self.tree.focus(self.selection_anchor)
            self.tree.selection_set(self.selection_anchor)
        else:
            if self.selection_anchor is None:
                self.selection_anchor = current_focus

        current_focus = self.tree.focus()
        next_item = self.tree.next(current_focus)
        if not next_item:
            return

        self.clear_previous_selections()
        self.tree.focus(next_item)
        self.update_selection_range()

        return "break"

    def on_ctrl_shift_up(self, event):
        items = list(self.tree.get_children())
        if not items:
            return

        current_focus = self.tree.focus()
        if not current_focus:
            self.selection_anchor = items[0]
            self.tree.focus(self.selection_anchor)
            self.tree.selection_set(self.selection_anchor)
        else:
            if self.selection_anchor is None:
                self.selection_anchor = current_focus

        current_focus = self.tree.focus()
        prev_item = self.tree.prev(current_focus)
        if not prev_item:
            return

        self.clear_previous_selections()
        self.tree.focus(prev_item)
        self.update_selection_range()

        return "break"

    def clear_previous_selections(self):
        items = list(self.tree.get_children())
        for item in items:
            sku = self.tree.item(item, "values")[1]
            if self.selection_state.get(sku, False):
                values = list(self.tree.item(item, "values"))
                values[0] = "☐"
                self.tree.item(item, values=values)
                self.selection_state[sku] = False
                self.tree.item(item, tags=())
        self.update_selection_count()

    def update_selection_range(self):
        items = list(self.tree.get_children())
        if not items:
            return

        anchor_idx = items.index(self.selection_anchor) if self.selection_anchor in items else 0
        current_focus = self.tree.focus()
        current_idx = items.index(current_focus) if current_focus in items else 0

        start_idx, end_idx = min(anchor_idx, current_idx), max(anchor_idx, current_idx)

        for idx in range(start_idx, end_idx + 1):
            item = items[idx]
            sku = self.tree.item(item, "values")[1]
            values = list(self.tree.item(item, "values"))
            values[0] = "☑"
            self.tree.item(item, values=values)
            self.selection_state[sku] = True
            self.tree.item(item, tags=("selected",))
            self.tree.selection_add(item)

        for idx in range(len(items)):
            if idx < start_idx or idx > end_idx:
                item = items[idx]
                sku = self.tree.item(item, "values")[1]
                if self.selection_state.get(sku, False):
                    values = list(self.tree.item(item, "values"))
                    values[0] = "☐"
                    self.tree.item(item, values=values)
                    self.selection_state[sku] = False
                    self.tree.item(item, tags=())
                    self.tree.selection_remove(item)

        self.update_selection_count()

    def select_all(self):
        for item in self.tree.get_children():
            sku = self.tree.item(item, "values")[1]
            values = list(self.tree.item(item, "values"))
            values[0] = "☑"
            self.tree.item(item, values=values)
            self.selection_state[sku] = True
            self.tree.item(item, tags=("selected",))
        self.update_selection_count()

    def deselect_all(self):
        for item in self.tree.get_children():
            sku = self.tree.item(item, "values")[1]
            values = list(self.tree.item(item, "values"))
            values[0] = "☐"
            self.tree.item(item, values=values)
            self.selection_state[sku] = False
            self.tree.item(item, tags=())
            self.tree.selection_remove(item)
            self.tree.focus("")
        self.clear_filters()
        self.update_selection_count()

    def select_all_with_shortcut(self, event):
        self.select_all()
        return "break"

    def deselect_all_with_shortcut(self, event):
        self.deselect_all()
        return "break"

    def clear_filters(self):
        self.search_entry.delete(0, tk.END)
        self.combo_escuela.set("")
        self.combo_nivel.set("")
        self.combo_color.set("")
        self.combo_tipo_prenda.set("")
        self.combo_tipo_pieza.set("")
        self.combo_genero.set("")
        self.combo_atributo.set("")
        self.combo_marca.set("")
        self.combo_talla.set("")
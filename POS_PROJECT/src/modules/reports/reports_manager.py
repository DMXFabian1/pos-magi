import customtkinter as ctk
from tkinter import ttk, messagebox, Canvas, PhotoImage, Toplevel
import logging
from datetime import datetime
import json
from src.modules.reports.reports_logic import ReportesLogic
from src.core.config.config import CONFIG
from tkcalendar import Calendar

logger = logging.getLogger(__name__)

THEME_COLOR_MAP = {
    "dark-blue": "#1f6aa5",
    "blue": "#1a73e8",
    "green": "#2cc985",
}

class ReportesManager:
    def __init__(self, user_id, parent_frame, root, db_manager=None, store_id=1):
        logging.debug("Iniciando ReportesManager")
        self.user_id = user_id
        self.parent_frame = parent_frame
        self.root = root
        self.store_id = store_id
        self.reportes_logic = ReportesLogic(db_manager, store_id=self.store_id)
        logging.debug("ReportesLogic inicializado")

        self.main_frame = ctk.CTkFrame(self.parent_frame)
        logging.debug("main_frame creado")
        self.setup_ui()
        logger.info(f"Interfaz de gestión de reportes inicializada para usuario con ID '{self.user_id}' en tienda {self.store_id}.")

    def setup_ui(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self.main_frame, text="Reportes", font=("Arial", 24, "bold")).pack(pady=(20, 10))

        tab_control = ctk.CTkTabview(self.main_frame)
        tab_control.pack(fill="both", expand=True, padx=10, pady=5)

        ventas_tab = tab_control.add("Ventas")
        self.setup_ventas_tab(ventas_tab)

        inventario_tab = tab_control.add("Inventario")
        self.setup_inventario_tab(inventario_tab)

        apartados_tab = tab_control.add("Apartados")
        self.setup_apartados_tab(apartados_tab)

        analisis_tab = tab_control.add("Análisis")
        self.setup_analisis_tab(analisis_tab)

    def setup_ventas_tab(self, tab):
        filtros_frame = ctk.CTkFrame(tab)
        filtros_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(filtros_frame, text="Rango de Fechas", font=("Arial", 14)).pack(side="left", padx=5)

        # Desde
        ctk.CTkLabel(filtros_frame, text="Desde:").pack(side="left", padx=5)
        fecha_desde_var = ctk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        fecha_desde_label = ctk.CTkLabel(filtros_frame, textvariable=fecha_desde_var, width=100)
        fecha_desde_label.pack(side="left", padx=5)

        def seleccionar_fecha_desde():
            top = Toplevel(self.root)
            top.title("Seleccionar Fecha Desde")
            cal = Calendar(top, selectmode="day", date_pattern="yyyy-mm-dd")
            cal.pack(pady=10)
            def set_date():
                fecha_desde_var.set(cal.get_date())
                top.destroy()
            ctk.CTkButton(top, text="Seleccionar", command=set_date).pack(pady=5)

        ctk.CTkButton(filtros_frame, text="📅", command=seleccionar_fecha_desde, width=30).pack(side="left", padx=5)

        # Hasta
        ctk.CTkLabel(filtros_frame, text="Hasta:").pack(side="left", padx=5)
        fecha_hasta_var = ctk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        fecha_hasta_label = ctk.CTkLabel(filtros_frame, textvariable=fecha_hasta_var, width=100)
        fecha_hasta_label.pack(side="left", padx=5)

        def seleccionar_fecha_hasta():
            top = Toplevel(self.root)
            top.title("Seleccionar Fecha Hasta")
            cal = Calendar(top, selectmode="day", date_pattern="yyyy-mm-dd")
            cal.pack(pady=10)
            def set_date():
                fecha_hasta_var.set(cal.get_date())
                top.destroy()
            ctk.CTkButton(top, text="Seleccionar", command=set_date).pack(pady=5)

        ctk.CTkButton(filtros_frame, text="📅", command=seleccionar_fecha_hasta, width=30).pack(side="left", padx=5)

        ctk.CTkLabel(filtros_frame, text="Método de Pago:").pack(side="left", padx=5)
        metodo_pago_var = ctk.StringVar(value="Todos")
        valores_metodos = ["Todos"] + CONFIG["METODOS_PAGO"]
        ctk.CTkOptionMenu(filtros_frame, values=valores_metodos, variable=metodo_pago_var).pack(side="left", padx=5)

        ctk.CTkLabel(filtros_frame, text="Cliente:").pack(side="left", padx=5)
        cliente_var = ctk.StringVar()
        ctk.CTkEntry(filtros_frame, textvariable=cliente_var, width=150).pack(side="left", padx=5)

        tree_frame = ctk.CTkFrame(tab)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.ventas_tree = ttk.Treeview(
            tree_frame,
            columns=("ID", "Usuario", "Cliente", "Método Pago", "Fecha", "Total"),
            show="headings"
        )
        self.ventas_tree.heading("ID", text="ID")
        self.ventas_tree.heading("Usuario", text="Usuario")
        self.ventas_tree.heading("Cliente", text="Cliente")
        self.ventas_tree.heading("Método Pago", text="Método Pago")
        self.ventas_tree.heading("Fecha", text="Fecha")
        self.ventas_tree.heading("Total", text="Total")
        self.ventas_tree.column("ID", width=50)
        self.ventas_tree.column("Usuario", width=100)
        self.ventas_tree.column("Cliente", width=150)
        self.ventas_tree.column("Método Pago", width=100)
        self.ventas_tree.column("Fecha", width=150)
        self.ventas_tree.column("Total", width=100)
        self.ventas_tree.pack(fill="both", expand=True)

        self.ventas_current_page = 0
        self.ventas_page_size = 20
        self.ventas_total_records = 0

        pagination_frame = ctk.CTkFrame(tab)
        pagination_frame.pack(fill="x", padx=10, pady=5)
        self.ventas_page_label = ctk.CTkLabel(pagination_frame, text="Página 1")
        self.ventas_page_label.pack(side="left", padx=5)
        ctk.CTkButton(pagination_frame, text="Anterior", command=lambda: self.change_ventas_page(-1, fecha_desde_var, fecha_hasta_var, metodo_pago_var, cliente_var)).pack(side="left", padx=5)
        ctk.CTkButton(pagination_frame, text="Siguiente", command=lambda: self.change_ventas_page(1, fecha_desde_var, fecha_hasta_var, metodo_pago_var, cliente_var)).pack(side="left", padx=5)

        def cargar_ventas():
            try:
                fecha_desde = fecha_desde_var.get()
                fecha_hasta = fecha_hasta_var.get()
                metodo_pago = metodo_pago_var.get()
                cliente = cliente_var.get().strip() if cliente_var.get() else None
                datetime.strptime(fecha_desde, "%Y-%m-%d")
                datetime.strptime(fecha_hasta, "%Y-%m-%d")
                total_records = self.reportes_logic.contar_ventas(fecha_desde, fecha_hasta, metodo_pago, cliente)
                if total_records == 0:
                    messagebox.showinfo("Información", "No se encontraron ventas en el rango de fechas seleccionado.")
                    return
                self.ventas_current_page = 0
                self.ventas_total_records = total_records
                self.update_ventas_page(fecha_desde, fecha_hasta, metodo_pago, cliente)
            except ValueError:
                messagebox.showerror("Error", "Formato de fecha inválido. Use YYYY-MM-DD.")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo cargar el reporte: {str(e)}")
                logger.error(f"Error al cargar reporte de ventas en tienda {self.store_id}: {str(e)}")

        def exportar_pdf():
            try:
                fecha_desde = fecha_desde_var.get()
                fecha_hasta = fecha_hasta_var.get()
                metodo_pago = metodo_pago_var.get()
                cliente = cliente_var.get().strip() if cliente_var.get() else None
                datetime.strptime(fecha_desde, "%Y-%m-%d")
                datetime.strptime(fecha_hasta, "%Y-%m-%d")
                ventas = self.reportes_logic.obtener_ventas(fecha_desde, fecha_hasta, metodo_pago, cliente, offset=0, limit=None)
                if not ventas:
                    messagebox.showinfo("Información", "No hay datos para exportar.")
                    return
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                folio = f"REP-VENTAS-{timestamp}"
                pdf_path = self.reportes_logic.exportar_ventas_pdf(ventas, fecha_desde, fecha_hasta, folio)
                messagebox.showinfo("Éxito", f"Reporte exportado: {pdf_path}")
            except ValueError:
                messagebox.showerror("Error", "Formato de fecha inválido. Use YYYY-MM-DD.")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo exportar el reporte: {str(e)}")
                logger.error(f"Error al exportar reporte de ventas en tienda {self.store_id}: {str(e)}")

        def exportar_csv():
            try:
                fecha_desde = fecha_desde_var.get()
                fecha_hasta = fecha_hasta_var.get()
                metodo_pago = metodo_pago_var.get()
                cliente = cliente_var.get().strip() if cliente_var.get() else None
                datetime.strptime(fecha_desde, "%Y-%m-%d")
                datetime.strptime(fecha_hasta, "%Y-%m-%d")
                ventas = self.reportes_logic.obtener_ventas(fecha_desde, fecha_hasta, metodo_pago, cliente, offset=0, limit=None)
                if not ventas:
                    messagebox.showinfo("Información", "No hay datos para exportar.")
                    return
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                folio = f"REP-VENTAS-{timestamp}"
                csv_path = self.reportes_logic.exportar_ventas_csv(ventas, fecha_desde, fecha_hasta, folio)
                messagebox.showinfo("Éxito", f"Reporte exportado: {csv_path}")
            except ValueError:
                messagebox.showerror("Error", "Formato de fecha inválido. Use YYYY-MM-DD.")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo exportar el reporte: {str(e)}")
                logger.error(f"Error al exportar reporte de ventas a CSV en tienda {self.store_id}: {str(e)}")

        buttons_frame = ctk.CTkFrame(tab)
        buttons_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(buttons_frame, text="Cargar Reporte", command=cargar_ventas, width=150, height=40, font=("Arial", 14)).pack(side="left", padx=5)
        ctk.CTkButton(buttons_frame, text="Exportar a PDF", command=exportar_pdf, width=150, height=40, font=("Arial", 14)).pack(side="left", padx=5)
        ctk.CTkButton(buttons_frame, text="Exportar a CSV", command=exportar_csv, width=150, height=40, font=("Arial", 14)).pack(side="left", padx=5)

    def update_ventas_page(self, fecha_desde, fecha_hasta, metodo_pago, cliente):
        for item in self.ventas_tree.get_children():
            self.ventas_tree.delete(item)
        try:
            offset = self.ventas_current_page * self.ventas_page_size
            ventas = self.reportes_logic.obtener_ventas(fecha_desde, fecha_hasta, metodo_pago, cliente, offset, self.ventas_page_size)
            for venta in ventas:
                cliente_name = venta['nombre_completo'] if venta['nombre_completo'] else "Sin cliente"
                self.ventas_tree.insert("", "end", values=(
                    venta['id'],
                    venta['user_id'],
                    cliente_name,
                    venta['metodo_pago'],
                    venta['fecha'],
                    f"${venta['total']:.2f}"
                ))
            total_pages = (self.ventas_total_records + self.ventas_page_size - 1) // self.ventas_page_size
            self.ventas_page_label.configure(text=f"Página {self.ventas_current_page + 1} de {total_pages}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la página: {str(e)}")
            logger.error(f"Error al cargar página de ventas en tienda {self.store_id}: {str(e)}")

    def change_ventas_page(self, direction, fecha_desde_var, fecha_hasta_var, metodo_pago_var, cliente_var):
        try:
            fecha_desde = fecha_desde_var.get()
            fecha_hasta = fecha_hasta_var.get()
            metodo_pago = metodo_pago_var.get()
            cliente = cliente_var.get().strip() if cliente_var.get() else None
            total_pages = (self.ventas_total_records + self.ventas_page_size - 1) // self.ventas_page_size
            new_page = self.ventas_current_page + direction
            if 0 <= new_page < total_pages:
                self.ventas_current_page = new_page
                self.update_ventas_page(fecha_desde, fecha_hasta, metodo_pago, cliente)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cambiar de página: {str(e)}")
            logger.error(f"Error al cambiar página de ventas en tienda {self.store_id}: {str(e)}")

    def setup_inventario_tab(self, tab):
        filtros_frame = ctk.CTkFrame(tab)
        filtros_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(filtros_frame, text="Filtrar por stock bajo (< 5 unidades):").pack(side="left", padx=5)
        stock_bajo_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(filtros_frame, text="", variable=stock_bajo_var).pack(side="left", padx=5)

        tree_frame = ctk.CTkFrame(tab)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.inventario_tree = ttk.Treeview(
            tree_frame,
            columns=("SKU", "Nombre", "Inventario", "Ventas"),
            show="headings"
        )
        self.inventario_tree.heading("SKU", text="SKU")
        self.inventario_tree.heading("Nombre", text="Nombre")
        self.inventario_tree.heading("Inventario", text="Inventario")
        self.inventario_tree.heading("Ventas", text="Ventas")
        self.inventario_tree.column("SKU", width=100)
        self.inventario_tree.column("Nombre", width=200)
        self.inventario_tree.column("Inventario", width=100)
        self.inventario_tree.column("Ventas", width=100)
        self.inventario_tree.pack(fill="both", expand=True)

        self.inventario_current_page = 0
        self.inventario_page_size = 20
        self.inventario_total_records = 0

        pagination_frame = ctk.CTkFrame(tab)
        pagination_frame.pack(fill="x", padx=10, pady=5)
        self.inventario_page_label = ctk.CTkLabel(pagination_frame, text="Página 1")
        self.inventario_page_label.pack(side="left", padx=5)
        ctk.CTkButton(pagination_frame, text="Anterior", command=lambda: self.change_inventario_page(-1, stock_bajo_var)).pack(side="left", padx=5)
        ctk.CTkButton(pagination_frame, text="Siguiente", command=lambda: self.change_inventario_page(1, stock_bajo_var)).pack(side="left", padx=5)

        def cargar_inventario():
            try:
                self.inventario_current_page = 0
                self.inventario_total_records = self.reportes_logic.contar_inventario(stock_bajo_var.get())
                self.update_inventario_page(stock_bajo_var.get())
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo cargar el reporte: {str(e)}")
                logger.error(f"Error al cargar reporte de inventario en tienda {self.store_id}: {str(e)}")

        def exportar_pdf():
            try:
                productos = self.reportes_logic.obtener_inventario(stock_bajo_var.get(), offset=0, limit=None)
                if not productos:
                    messagebox.showinfo("Información", "No hay datos para exportar.")
                    return
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                folio = f"REP-INVENTARIO-{timestamp}"
                pdf_path = self.reportes_logic.exportar_inventario_pdf(productos, folio)
                messagebox.showinfo("Éxito", f"Reporte exportado: {pdf_path}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo exportar el reporte: {str(e)}")
                logger.error(f"Error al exportar reporte de inventario en tienda {self.store_id}: {str(e)}")

        def exportar_csv():
            try:
                productos = self.reportes_logic.obtener_inventario(stock_bajo_var.get(), offset=0, limit=None)
                if not productos:
                    messagebox.showinfo("Información", "No hay datos para exportar.")
                    return
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                folio = f"REP-INVENTARIO-{timestamp}"
                csv_path = self.reportes_logic.exportar_inventario_csv(productos, folio)
                messagebox.showinfo("Éxito", f"Reporte exportado: {csv_path}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo exportar el reporte: {str(e)}")
                logger.error(f"Error al exportar reporte de inventario a CSV en tienda {self.store_id}: {str(e)}")

        buttons_frame = ctk.CTkFrame(tab)
        buttons_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(buttons_frame, text="Cargar Reporte", command=cargar_inventario, width=150, height=40, font=("Arial", 14)).pack(side="left", padx=5)
        ctk.CTkButton(buttons_frame, text="Exportar a PDF", command=exportar_pdf, width=150, height=40, font=("Arial", 14)).pack(side="left", padx=5)
        ctk.CTkButton(buttons_frame, text="Exportar a CSV", command=exportar_csv, width=150, height=40, font=("Arial", 14)).pack(side="left", padx=5)

    def update_inventario_page(self, stock_bajo):
        for item in self.inventario_tree.get_children():
            self.inventario_tree.delete(item)
        try:
            offset = self.inventario_current_page * self.inventario_page_size
            productos = self.reportes_logic.obtener_inventario(stock_bajo, offset, self.inventario_page_size)
            for producto in productos:
                self.inventario_tree.insert("", "end", values=(
                    producto['sku'],
                    producto['nombre'],
                    producto['inventario'],
                    producto['ventas']
                ))
            total_pages = (self.inventario_total_records + self.inventario_page_size - 1) // self.inventario_page_size
            self.inventario_page_label.configure(text=f"Página {self.inventario_current_page + 1} de {total_pages}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la página: {str(e)}")
            logger.error(f"Error al cargar página de inventario en tienda {self.store_id}: {str(e)}")

    def change_inventario_page(self, direction, stock_bajo_var):
        try:
            total_pages = (self.inventario_total_records + self.inventario_page_size - 1) // self.inventario_page_size
            new_page = self.inventario_current_page + direction
            if 0 <= new_page < total_pages:
                self.inventario_current_page = new_page
                self.update_inventario_page(stock_bajo_var.get())
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cambiar de página: {str(e)}")
            logger.error(f"Error al cambiar página de inventario en tienda {self.store_id}: {str(e)}")

    def setup_apartados_tab(self, tab):
        filtros_frame = ctk.CTkFrame(tab)
        filtros_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(filtros_frame, text="Estado:").pack(side="left", padx=5)
        estado_var = ctk.StringVar(value="activo")
        ctk.CTkOptionMenu(filtros_frame, values=["activo", "vencido", "completado", "cancelado"], variable=estado_var).pack(side="left", padx=5)

        ctk.CTkLabel(filtros_frame, text="Cliente:").pack(side="left", padx=5)
        cliente_var = ctk.StringVar()
        ctk.CTkEntry(filtros_frame, textvariable=cliente_var, width=150).pack(side="left", padx=5)

        ctk.CTkLabel(filtros_frame, text="Rango de Fechas", font=("Arial", 14)).pack(side="left", padx=5)

        ctk.CTkLabel(filtros_frame, text="Desde:").pack(side="left", padx=5)
        fecha_desde_var = ctk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        fecha_desde_label = ctk.CTkLabel(filtros_frame, textvariable=fecha_desde_var, width=100)
        fecha_desde_label.pack(side="left", padx=5)

        def seleccionar_fecha_desde():
            top = Toplevel(self.root)
            top.title("Seleccionar Fecha Desde")
            cal = Calendar(top, selectmode="day", date_pattern="yyyy-mm-dd")
            cal.pack(pady=10)
            def set_date():
                fecha_desde_var.set(cal.get_date())
                top.destroy()
            ctk.CTkButton(top, text="Seleccionar", command=set_date).pack(pady=5)

        ctk.CTkButton(filtros_frame, text="📅", command=seleccionar_fecha_desde, width=30).pack(side="left", padx=5)

        ctk.CTkLabel(filtros_frame, text="Hasta:").pack(side="left", padx=5)
        fecha_hasta_var = ctk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        fecha_hasta_label = ctk.CTkLabel(filtros_frame, textvariable=fecha_hasta_var, width=100)
        fecha_hasta_label.pack(side="left", padx=5)

        def seleccionar_fecha_hasta():
            top = Toplevel(self.root)
            top.title("Seleccionar Fecha Hasta")
            cal = Calendar(top, selectmode="day", date_pattern="yyyy-mm-dd")
            cal.pack(pady=10)
            def set_date():
                fecha_hasta_var.set(cal.get_date())
                top.destroy()
            ctk.CTkButton(top, text="Seleccionar", command=set_date).pack(pady=5)

        ctk.CTkButton(filtros_frame, text="📅", command=seleccionar_fecha_hasta, width=30).pack(side="left", padx=5)

        tree_frame = ctk.CTkFrame(tab)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.apartados_tree = ttk.Treeview(
            tree_frame,
            columns=("ID", "Cliente", "Productos", "Anticipo", "Fecha Creación", "Fecha Vencimiento", "Estado"),
            show="headings"
        )
        self.apartados_tree.heading("ID", text="ID")
        self.apartados_tree.heading("Cliente", text="Cliente")
        self.apartados_tree.heading("Productos", text="Productos")
        self.apartados_tree.heading("Anticipo", text="Anticipo")
        self.apartados_tree.heading("Fecha Creación", text="Fecha Creación")
        self.apartados_tree.heading("Fecha Vencimiento", text="Fecha Vencimiento")
        self.apartados_tree.heading("Estado", text="Estado")
        self.apartados_tree.column("ID", width=50)
        self.apartados_tree.column("Cliente", width=150)
        self.apartados_tree.column("Productos", width=200)
        self.apartados_tree.column("Anticipo", width=100)
        self.apartados_tree.column("Fecha Creación", width=150)
        self.apartados_tree.column("Fecha Vencimiento", width=150)
        self.apartados_tree.column("Estado", width=100)
        self.apartados_tree.pack(fill="both", expand=True)

        self.apartados_current_page = 0
        self.apartados_page_size = 20
        self.apartados_total_records = 0

        pagination_frame = ctk.CTkFrame(tab)
        pagination_frame.pack(fill="x", padx=10, pady=5)
        self.apartados_page_label = ctk.CTkLabel(pagination_frame, text="Página 1")
        self.apartados_page_label.pack(side="left", padx=5)
        ctk.CTkButton(pagination_frame, text="Anterior", command=lambda: self.change_apartados_page(-1, estado_var, cliente_var, fecha_desde_var, fecha_hasta_var)).pack(side="left", padx=5)
        ctk.CTkButton(pagination_frame, text="Siguiente", command=lambda: self.change_apartados_page(1, estado_var, cliente_var, fecha_desde_var, fecha_hasta_var)).pack(side="left", padx=5)

        def cargar_apartados():
            try:
                estado = estado_var.get()
                cliente = cliente_var.get().strip() if cliente_var.get() else None
                fecha_desde = fecha_desde_var.get()
                fecha_hasta = fecha_hasta_var.get()
                datetime.strptime(fecha_desde, "%Y-%m-%d")
                datetime.strptime(fecha_hasta, "%Y-%m-%d")
                total_records = self.reportes_logic.contar_apartados(estado, cliente, fecha_desde, fecha_hasta)
                if total_records == 0:
                    messagebox.showinfo("Información", "No se encontraron apartados en el rango de fechas seleccionado.")
                    return
                self.apartados_current_page = 0
                self.apartados_total_records = total_records
                self.update_apartados_page(estado, cliente, fecha_desde, fecha_hasta)
            except ValueError:
                messagebox.showerror("Error", "Formato de fecha inválido. Use YYYY-MM-DD.")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo cargar el reporte: {str(e)}")
                logger.error(f"Error al cargar reporte de apartados en tienda {self.store_id}: {str(e)}")

        def exportar_pdf():
            try:
                estado = estado_var.get()
                cliente = cliente_var.get().strip() if cliente_var.get() else None
                fecha_desde = fecha_desde_var.get()
                fecha_hasta = fecha_hasta_var.get()
                datetime.strptime(fecha_desde, "%Y-%m-%d")
                datetime.strptime(fecha_hasta, "%Y-%m-%d")
                apartados = self.reportes_logic.obtener_apartados(estado, cliente, fecha_desde, fecha_hasta, offset=0, limit=None)
                if not apartados:
                    messagebox.showinfo("Información", "No hay datos para exportar.")
                    return
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                folio = f"REP-APARTADOS-{timestamp}"
                pdf_path = self.reportes_logic.exportar_apartados_pdf(apartados, estado, folio)
                messagebox.showinfo("Éxito", f"Reporte exportado: {pdf_path}")
            except ValueError:
                messagebox.showerror("Error", "Formato de fecha inválido. Use YYYY-MM-DD.")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo exportar el reporte: {str(e)}")
                logger.error(f"Error al exportar reporte de apartados en tienda {self.store_id}: {str(e)}")

        def exportar_csv():
            try:
                estado = estado_var.get()
                cliente = cliente_var.get().strip() if cliente_var.get() else None
                fecha_desde = fecha_desde_var.get()
                fecha_hasta = fecha_hasta_var.get()
                datetime.strptime(fecha_desde, "%Y-%m-%d")
                datetime.strptime(fecha_hasta, "%Y-%m-%d")
                apartados = self.reportes_logic.obtener_apartados(estado, cliente, fecha_desde, fecha_hasta, offset=0, limit=None)
                if not apartados:
                    messagebox.showinfo("Información", "No hay datos para exportar.")
                    return
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                folio = f"REP-APARTADOS-{timestamp}"
                csv_path = self.reportes_logic.exportar_apartados_csv(apartados, estado, folio)
                messagebox.showinfo("Éxito", f"Reporte exportado: {csv_path}")
            except ValueError:
                messagebox.showerror("Error", "Formato de fecha inválido. Use YYYY-MM-DD.")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo exportar el reporte: {str(e)}")
                logger.error(f"Error al exportar reporte de apartados a CSV en tienda {self.store_id}: {str(e)}")

        buttons_frame = ctk.CTkFrame(tab)
        buttons_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(buttons_frame, text="Cargar Reporte", command=cargar_apartados, width=150, height=40, font=("Arial", 14)).pack(side="left", padx=5)
        ctk.CTkButton(buttons_frame, text="Exportar a PDF", command=exportar_pdf, width=150, height=40, font=("Arial", 14)).pack(side="left", padx=5)
        ctk.CTkButton(buttons_frame, text="Exportar a CSV", command=exportar_csv, width=150, height=40, font=("Arial", 14)).pack(side="left", padx=5)

    def update_apartados_page(self, estado, cliente, fecha_desde, fecha_hasta):
        for item in self.apartados_tree.get_children():
            self.apartados_tree.delete(item)
        try:
            offset = self.apartados_current_page * self.apartados_page_size
            apartados = self.reportes_logic.obtener_apartados(estado, cliente, fecha_desde, fecha_hasta, offset, self.apartados_page_size)
            for apartado in apartados:
                productos = json.loads(apartado['productos'])
                productos_str = ", ".join([f"{item['sku']} (x{item['cantidad']})" for item in productos])
                self.apartados_tree.insert("", "end", values=(
                    apartado['id'],
                    apartado['nombre_completo'],
                    productos_str,
                    apartado['anticipo'],
                    apartado['fecha_creacion'],
                    apartado['fecha_vencimiento'],
                    apartado['estado']
                ))
            total_pages = (self.apartados_total_records + self.apartados_page_size - 1) // self.apartados_page_size
            self.apartados_page_label.configure(text=f"Página {self.apartados_current_page + 1} de {total_pages}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la página: {str(e)}")
            logger.error(f"Error al cargar página de apartados en tienda {self.store_id}: {str(e)}")

    def change_apartados_page(self, direction, estado_var, cliente_var, fecha_desde_var, fecha_hasta_var):
        try:
            estado = estado_var.get()
            cliente = cliente_var.get().strip() if cliente_var.get() else None
            fecha_desde = fecha_desde_var.get()
            fecha_hasta = fecha_hasta_var.get()
            total_pages = (self.apartados_total_records + self.apartados_page_size - 1) // self.apartados_page_size
            new_page = self.apartados_current_page + direction
            if 0 <= new_page < total_pages:
                self.apartados_current_page = new_page
                self.update_apartados_page(estado, cliente, fecha_desde, fecha_hasta)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cambiar de página: {str(e)}")
            logger.error(f"Error al cambiar página de apartados en tienda {self.store_id}: {str(e)}")

    def setup_analisis_tab(self, tab):
        ctk.CTkLabel(tab, text="Análisis", font=("Arial", 20)).pack(pady=10)

        filtros_frame = ctk.CTkFrame(tab)
        filtros_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(filtros_frame, text="Rango de Fechas para Gráficos", font=("Arial", 14)).pack(side="left", padx=5)

        ctk.CTkLabel(filtros_frame, text="Desde:").pack(side="left", padx=5)
        fecha_desde_var = ctk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        fecha_desde_label = ctk.CTkLabel(filtros_frame, textvariable=fecha_desde_var, width=100)
        fecha_desde_label.pack(side="left", padx=5)

        def seleccionar_fecha_desde():
            top = Toplevel(self.root)
            top.title("Seleccionar Fecha Desde")
            cal = Calendar(top, selectmode="day", date_pattern="yyyy-mm-dd")
            cal.pack(pady=10)
            def set_date():
                fecha_desde_var.set(cal.get_date())
                top.destroy()
            ctk.CTkButton(top, text="Seleccionar", command=set_date).pack(pady=5)

        ctk.CTkButton(filtros_frame, text="📅", command=seleccionar_fecha_desde, width=30).pack(side="left", padx=5)

        ctk.CTkLabel(filtros_frame, text="Hasta:").pack(side="left", padx=5)
        fecha_hasta_var = ctk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        fecha_hasta_label = ctk.CTkLabel(filtros_frame, textvariable=fecha_hasta_var, width=100)
        fecha_hasta_label.pack(side="left", padx=5)

        def seleccionar_fecha_hasta():
            top = Toplevel(self.root)
            top.title("Seleccionar Fecha Hasta")
            cal = Calendar(top, selectmode="day", date_pattern="yyyy-mm-dd")
            cal.pack(pady=10)
            def set_date():
                fecha_hasta_var.set(cal.get_date())
                top.destroy()
            ctk.CTkButton(top, text="Seleccionar", command=set_date).pack(pady=5)

        ctk.CTkButton(filtros_frame, text="📅", command=seleccionar_fecha_hasta, width=30).pack(side="left", padx=5)

        graficos_frame = ctk.CTkFrame(tab)
        graficos_frame.pack(fill="both", expand=True, padx=10, pady=5)

        ventas_canvas = Canvas(graficos_frame, width=600, height=400)
        ventas_canvas.pack(side="left", padx=5)
        productos_canvas = Canvas(graficos_frame, width=600, height=400)
        productos_canvas.pack(side="left", padx=5)

        clientes_frame = ctk.CTkFrame(tab)
        clientes_frame.pack(fill="both", expand=True, padx=10, pady=5)
        ctk.CTkLabel(clientes_frame, text="Clientes Frecuentes (Top 10)", font=("Arial", 16)).pack(anchor="w", padx=5)

        clientes_tree = ttk.Treeview(
            clientes_frame,
            columns=("Cliente", "Total Compras", "Total Gastado"),
            show="headings"
        )
        clientes_tree.heading("Cliente", text="Cliente")
        clientes_tree.heading("Total Compras", text="Total Compras")
        clientes_tree.heading("Total Gastado", text="Total Gastado")
        clientes_tree.column("Cliente", width=200)
        clientes_tree.column("Total Compras", width=100)
        clientes_tree.column("Total Gastado", width=100)
        clientes_tree.pack(fill="both", expand=True)

        productos_frame = ctk.CTkFrame(tab)
        productos_frame.pack(fill="both", expand=True, padx=10, pady=5)
        ctk.CTkLabel(productos_frame, text="Productos Más Vendidos", font=("Arial", 16)).pack(anchor="w", padx=5)

        productos_tree = ttk.Treeview(
            productos_frame,
            columns=("SKU", "Nombre", "Ventas", "Inventario"),
            show="headings"
        )
        productos_tree.heading("SKU", text="SKU")
        productos_tree.heading("Nombre", text="Nombre")
        productos_tree.heading("Ventas", text="Ventas")
        productos_tree.heading("Inventario", text="Inventario")
        productos_tree.column("SKU", width=100)
        productos_tree.column("Nombre", width=200)
        productos_tree.column("Ventas", width=100)
        productos_tree.column("Inventario", width=100)
        productos_tree.pack(fill="both", expand=True)

        self.productos_current_page = 0
        self.productos_page_size = 20
        self.productos_total_records = 0

        productos_pagination_frame = ctk.CTkFrame(tab)
        productos_pagination_frame.pack(fill="x", padx=10, pady=5)
        self.productos_page_label = ctk.CTkLabel(productos_pagination_frame, text="Página 1")
        self.productos_page_label.pack(side="left", padx=5)
        ctk.CTkButton(productos_pagination_frame, text="Anterior", command=lambda: self.change_productos_page(-1)).pack(side="left", padx=5)
        ctk.CTkButton(productos_pagination_frame, text="Siguiente", command=lambda: self.change_productos_page(1)).pack(side="left", padx=5)

        self.ventas_image = None
        self.productos_image = None

        def cargar_analisis():
            try:
                clientes = self.reportes_logic.obtener_clientes_frecuentes(limit=10)
                if not clientes:
                    messagebox.showinfo("Información", "No se encontraron clientes frecuentes.")
                else:
                    for item in clientes_tree.get_children():
                        clientes_tree.delete(item)
                    for cliente in clientes:
                        clientes_tree.insert("", "end", values=(
                            cliente['nombre_completo'],
                            cliente['total_compras'],
                            f"${cliente['total_gastado']:.2f}"
                        ))

                total_productos = self.reportes_logic.contar_productos_mas_vendidos()
                if total_productos == 0:
                    messagebox.showinfo("Información", "No se encontraron productos para mostrar.")
                else:
                    self.productos_current_page = 0
                    self.productos_total_records = total_productos
                    self.update_productos_page()

                fecha_desde = fecha_desde_var.get()
                fecha_hasta = fecha_hasta_var.get()
                datetime.strptime(fecha_desde, "%Y-%m-%d")
                datetime.strptime(fecha_hasta, "%Y-%m-%d")
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                folio = f"REP-ANALISIS-{timestamp}"

                ventas_por_dia = self.reportes_logic.obtener_ventas_por_dia(fecha_desde, fecha_hasta)
                if not ventas_por_dia:
                    messagebox.showinfo("Información", "No se encontraron datos de ventas para generar los gráficos en el rango de fechas seleccionado.")
                    return
                ventas_png = self.reportes_logic.generar_grafico_ventas_por_dia(ventas_por_dia, fecha_desde, fecha_hasta, folio)
                self.ventas_image = PhotoImage(file=ventas_png)
                ventas_canvas.create_image(0, 0, anchor="nw", image=self.ventas_image)

                productos_vendidos = self.reportes_logic.obtener_productos_mas_vendidos(limit=10)
                if not productos_vendidos:
                    messagebox.showinfo("Información", "No se encontraron productos más vendidos para generar el gráfico.")
                    return
                productos_png = self.reportes_logic.generar_grafico_productos_vendidos(productos_vendidos, folio)
                self.productos_image = PhotoImage(file=productos_png)
                productos_canvas.create_image(0, 0, anchor="nw", image=self.productos_image)
            except ValueError:
                messagebox.showerror("Error", "Formato de fecha inválido. Use YYYY-MM-DD.")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo cargar el análisis: {str(e)}")
                logger.error(f"Error al cargar análisis en tienda {self.store_id}: {str(e)}")

        def exportar_clientes_pdf():
            try:
                clientes = self.reportes_logic.obtener_clientes_frecuentes(limit=10)
                if not clientes:
                    messagebox.showinfo("Información", "No hay datos para exportar.")
                    return
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                folio = f"REP-CLIENTES-FRECUENTES-{timestamp}"
                pdf_path = self.reportes_logic.exportar_clientes_frecuentes_pdf(clientes, folio)
                messagebox.showinfo("Éxito", f"Reporte exportado: {pdf_path}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo exportar: {str(e)}")
                logger.error(f"Error al exportar clientes frecuentes a PDF en tienda {self.store_id}: {str(e)}")

        def exportar_productos_pdf():
            try:
                productos = self.reportes_logic.obtener_productos_mas_vendidos(offset=0, limit=None)
                if not productos:
                    messagebox.showinfo("Información", "No hay datos para exportar.")
                    return
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                folio = f"REP-PRODUCTOS-VENDIDOS-{timestamp}"
                pdf_path = self.reportes_logic.exportar_productos_vendidos_pdf(productos, folio)
                messagebox.showinfo("Éxito", f"Reporte exportado: {pdf_path}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo exportar: {str(e)}")
                logger.error(f"Error al exportar productos más vendidos a PDF en tienda {self.store_id}: {str(e)}")

        def exportar_clientes_csv():
            try:
                clientes = self.reportes_logic.obtener_clientes_frecuentes(limit=10)
                if not clientes:
                    messagebox.showinfo("Información", "No hay datos para exportar.")
                    return
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                folio = f"REP-CLIENTES-FRECUENTES-{timestamp}"
                csv_path = self.reportes_logic.exportar_analisis_csv(clientes, [], folio)
                messagebox.showinfo("Éxito", f"Reporte exportado: {csv_path}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo exportar: {str(e)}")
                logger.error(f"Error al exportar clientes frecuentes a CSV en tienda {self.store_id}: {str(e)}")

        def exportar_productos_csv():
            try:
                productos = self.reportes_logic.obtener_productos_mas_vendidos(offset=0, limit=None)
                if not productos:
                    messagebox.showinfo("Información", "No hay datos para exportar.")
                    return
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                folio = f"REP-PRODUCTOS-VENDIDOS-{timestamp}"
                csv_path = self.reportes_logic.exportar_analisis_csv([], productos, folio)
                messagebox.showinfo("Éxito", f"Reporte exportado: {csv_path}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo exportar: {str(e)}")
                logger.error(f"Error al exportar productos más vendidos a CSV en tienda {self.store_id}: {str(e)}")

        def generar_reporte_analisis():
            try:
                fecha_desde = fecha_desde_var.get()
                fecha_hasta = fecha_hasta_var.get()
                datetime.strptime(fecha_desde, "%Y-%m-%d")
                datetime.strptime(fecha_hasta, "%Y-%m-%d")
                total_ventas = self.reportes_logic.obtener_ventas(fecha_desde, fecha_hasta, "Todos", None, offset=0, limit=None)
                if not total_ventas:
                    messagebox.showinfo("Información", "No se encontraron datos de ventas en el rango de fechas seleccionado para generar el reporte.")
                    return
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                folio = f"REP-DATOS-{timestamp}"
                md_path = self.reportes_logic.generar_reporte_analisis_datos(fecha_desde, fecha_hasta, folio)
                messagebox.showinfo("Éxito", f"Reporte de análisis generado: {md_path}")
            except ValueError:
                messagebox.showerror("Error", "Formato de fecha inválido. Use YYYY-MM-DD.")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo generar el reporte: {str(e)}")
                logger.error(f"Error al generar reporte de análisis en tienda {self.store_id}: {str(e)}")

        buttons_frame = ctk.CTkFrame(tab)
        buttons_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(buttons_frame, text="Cargar Análisis", command=cargar_analisis, width=150, height=40, font=("Arial", 14)).pack(side="left", padx=5)
        ctk.CTkButton(buttons_frame, text="Exportar Clientes PDF", command=exportar_clientes_pdf, width=150, height=40, font=("Arial", 14)).pack(side="left", padx=5)
        ctk.CTkButton(buttons_frame, text="Exportar Productos PDF", command=exportar_productos_pdf, width=150, height=40, font=("Arial", 14)).pack(side="left", padx=5)
        ctk.CTkButton(buttons_frame, text="Exportar Clientes CSV", command=exportar_clientes_csv, width=150, height=40, font=("Arial", 14)).pack(side="left", padx=5)
        ctk.CTkButton(buttons_frame, text="Exportar Productos CSV", command=exportar_productos_csv, width=150, height=40, font=("Arial", 14)).pack(side="left", padx=5)
        ctk.CTkButton(buttons_frame, text="Generar Reporte de Análisis", command=generar_reporte_analisis, width=150, height=40, font=("Arial", 14)).pack(side="left", padx=5)

    def update_productos_page(self):
        for item in self.productos_tree.get_children():
            self.productos_tree.delete(item)
        try:
            offset = self.productos_current_page * self.productos_page_size
            productos = self.reportes_logic.obtener_productos_mas_vendidos(offset, self.productos_page_size)
            for producto in productos:
                self.productos_tree.insert("", "end", values=(
                    producto['sku'],
                    producto['nombre'],
                    producto['ventas'],
                    producto['inventario']
                ))
            total_pages = (self.productos_total_records + self.productos_page_size - 1) // self.productos_page_size
            self.productos_page_label.configure(text=f"Página {self.productos_current_page + 1} de {total_pages}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la página: {str(e)}")
            logger.error(f"Error al cargar página de productos más vendidos en tienda {self.store_id}: {str(e)}")

    def change_productos_page(self, direction):
        try:
            total_pages = (self.productos_total_records + self.productos_page_size - 1) // self.productos_page_size
            new_page = self.productos_current_page + direction
            if 0 <= new_page < total_pages:
                self.productos_current_page = new_page
                self.update_productos_page()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cambiar de página: {str(e)}")
            logger.error(f"Error al cambiar página de productos más vendidos en tienda {self.store_id}: {str(e)}")

    def pack(self, **kwargs):
        self.main_frame.pack(**kwargs)
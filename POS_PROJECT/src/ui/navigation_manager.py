import os
import customtkinter as ctk
from src.modules.auth.auth_manager import AuthManager
from src.core.config.db_manager import DatabaseManager
from src.modules.sales.pos_ventas import PosVentas
from src.modules.clients.client_manager import ClientManager
from src.modules.sales.apartados.apartados_manager import ApartadosManager
from src.modules.sales.presupuestos.presupuestos_manager import PresupuestosManager
from src.modules.reports.reports_manager import ReportesManager
from src.modules.inventory.entradas_salidas_manager import EntradasSalidasManager
from src.core.config.config import CONFIG
import logging
from tkinter import messagebox
from src.ui.generador_codigos import GeneradorCodigos
from src.core.config.controller import Controller
from src.modules.products.product_manager_window import ProductManagerWindow
from src.modules.users.users_manager import UsersManager

logger = logging.getLogger(__name__)

class NavigationManager:
    def __init__(self, user_id, root=None, icons=None, db_manager=None, store_id=1):
        logging.debug(f"Iniciando NavigationManager con store_id={store_id}")
        self.db_manager = db_manager or DatabaseManager()
        logging.debug("DatabaseManager creado")
        self.auth_manager = AuthManager(db_manager=self.db_manager)
        logging.debug("AuthManager creado")
        self.user_id = user_id
        self.store_id = store_id
        
        # Obtener el rol del usuario
        role_result = self.auth_manager.obtener_rol(user_id, store_id=store_id)
        logging.debug(f"Resultado de obtener_rol: {role_result}")
        if role_result["success"]:
            self.role = role_result["role"]
            logging.debug(f"Rol asignado: {self.role}")
            if self.role not in ["admin", "cajero", "vendedor"]:
                logging.error(f"Rol '{self.role}' no válido para navegación para usuario {user_id} en tienda {store_id}")
                raise ValueError(f"Rol '{self.role}' no válido para navegación.")
        else:
            logging.error(f"No se pudo obtener el rol para usuario {user_id} en tienda {store_id}: {role_result['message']}")
            raise ValueError(f"No se pudo obtener el rol: {role_result['message']}")
        
        if root is None:
            self.root = ctk.CTk()
        else:
            self.root = root
        self.root.title(CONFIG['POS_TITLE'])
        ctk.set_appearance_mode(CONFIG['THEME_MODE'])
        ctk.set_default_color_theme(CONFIG['THEME_COLOR'])
        self.icons = icons or {}
        self.root.icons = self.icons
        logging.debug("Configuración de root completada")

        self.pos_instance = None
        self.generador_instance = None
        self.client_instance = None
        self.apartados_instance = None
        self.presupuestos_instance = None
        self.reportes_instance = None
        self.users_manager_instance = None
        self.product_manager_instance = None
        self.entradas_salidas_instance = None
        self.setup_ui()
        logging.debug("setup_ui ejecutado")

    def setup_ui(self):
        logging.debug("Iniciando setup_ui")
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(padx=10, pady=10, fill="both", expand=True)
        logging.debug("main_frame creado y empaquetado")

        # Notificación de stock bajo
        notif_frame = ctk.CTkFrame(self.main_frame)
        notif_frame.pack(fill="x", pady=5)
        self.stock_bajo_label = ctk.CTkLabel(notif_frame, text="Productos con stock bajo: 0", font=("Arial", 12))
        self.stock_bajo_label.pack(anchor="e", padx=10)
        self.actualizar_notificacion_stock_bajo()

        self.nav_frame = ctk.CTkFrame(self.main_frame)
        self.nav_frame.pack(fill="x", pady=5)
        logging.debug("nav_frame creado y empaquetado")

        self.content_frame = ctk.CTkFrame(self.main_frame)
        self.content_frame.pack(fill="both", expand=True)
        logging.debug("content_frame creado y empaquetado")

        if self.role == "admin":
            ctk.CTkButton(self.nav_frame, text="Ventas", command=self.open_pos_ventas).pack(side="left", padx=5)
            ctk.CTkButton(self.nav_frame, text="Generador de Códigos", command=self.open_code_generator).pack(side="left", padx=5)
            ctk.CTkButton(self.nav_frame, text="Gestión de Productos", command=self.open_product_management).pack(side="left", padx=5)
            ctk.CTkButton(self.nav_frame, text="Clientes", command=self.open_client_management).pack(side="left", padx=5)
            ctk.CTkButton(self.nav_frame, text="Apartados y Clientes", command=self.open_apartado_management).pack(side="left", padx=5)
            ctk.CTkButton(self.nav_frame, text="Presupuestos", command=self.open_budget_management).pack(side="left", padx=5)
            ctk.CTkButton(self.nav_frame, text="Reportes", command=self.open_reports_management).pack(side="left", padx=5)
            ctk.CTkButton(self.nav_frame, text="Gestión de Usuarios", command=self.open_users_management, fg_color="#4CAF50", hover_color="#45A049").pack(side="left", padx=5)
            ctk.CTkButton(self.nav_frame, text="Entradas y Salidas", command=self.open_inventory_movements, fg_color="#2196F3", hover_color="#1976D2").pack(side="left", padx=5)
            logger.info("Botones de navegación completos añadidos para admin.")
        elif self.role == "cajero":
            ctk.CTkButton(self.nav_frame, text="Ventas", command=self.open_pos_ventas).pack(side="left", padx=5)
            ctk.CTkButton(self.nav_frame, text="Generador de Códigos", command=self.open_code_generator).pack(side="left", padx=5)
            ctk.CTkButton(self.nav_frame, text="Gestión de Productos", command=self.open_product_management).pack(side="left", padx=5)
            ctk.CTkButton(self.nav_frame, text="Clientes", command=self.open_client_management).pack(side="left", padx=5)
            ctk.CTkButton(self.nav_frame, text="Apartados y Clientes", command=self.open_apartado_management).pack(side="left", padx=5)
            ctk.CTkButton(self.nav_frame, text="Presupuestos", command=self.open_budget_management).pack(side="left", padx=5)
            ctk.CTkButton(self.nav_frame, text="Entradas y Salidas", command=self.open_inventory_movements, fg_color="#2196F3", hover_color="#1976D2").pack(side="left", padx=5)
            logger.info("Botones de navegación añadidos para cajero.")
        elif self.role == "vendedor":
            ctk.CTkButton(self.nav_frame, text="Ventas", command=self.open_pos_ventas).pack(side="left", padx=5)
            logger.info("Botón 'Ventas' añadido para vendedor.")

        self.open_pos_ventas()
        logging.debug("open_pos_ventas ejecutado")

    def actualizar_notificacion_stock_bajo(self):
        try:
            cursor = self.db_manager.get_cursor()
            cursor.execute("SELECT COUNT(*) FROM productos WHERE inventario < 5 AND store_id = ?", (self.store_id,))
            count = cursor.fetchone()[0]
            self.stock_bajo_label.configure(text=f"Productos con stock bajo: {count}")
            self.root.after(60000, self.actualizar_notificacion_stock_bajo)
        except Exception as e:
            logger.error(f"Error al actualizar notificación de stock bajo: {str(e)}")

    def clear_content_frame(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        logging.debug("Content frame limpiado")

    def open_pos_ventas(self):
        logging.debug("Iniciando open_pos_ventas")
        if self.pos_instance:
            self.pos_instance.main_frame.pack_forget()
        if self.generador_instance:
            self.generador_instance.main_frame.pack_forget()
        if self.client_instance:
            self.client_instance.main_frame.pack_forget()
        if self.apartados_instance:
            self.apartados_instance.main_frame.pack_forget()
        if self.presupuestos_instance:
            self.presupuestos_instance.main_frame.pack_forget()
        if self.reportes_instance:
            self.reportes_instance.main_frame.pack_forget()
        if self.users_manager_instance:
            self.users_manager_instance.main_frame.pack_forget()
        if self.product_manager_instance:
            self.product_manager_instance.main_frame.pack_forget()
        if self.entradas_salidas_instance:
            self.entradas_salidas_instance.main_frame.pack_forget()
        self.pos_instance = PosVentas(user_id=self.user_id, parent_frame=self.content_frame, root=self.root, db_manager=self.db_manager, store_id=self.store_id)
        self.root.nav_manager = self
        self.pos_instance.main_frame.pack(padx=10, pady=10, fill="both", expand=True)
        logger.info(f"Interfaz de ventas abierta para tienda {self.store_id}.")

    def open_code_generator(self):
        logging.debug("Iniciando open_code_generator")
        try:
            if self.pos_instance:
                self.pos_instance.main_frame.pack_forget()
            if self.generador_instance:
                self.generador_instance.main_frame.pack_forget()
            if self.client_instance:
                self.client_instance.main_frame.pack_forget()
            if self.apartados_instance:
                self.apartados_instance.main_frame.pack_forget()
            if self.presupuestos_instance:
                self.presupuestos_instance.main_frame.pack_forget()
            if self.reportes_instance:
                self.reportes_instance.main_frame.pack_forget()
            if self.users_manager_instance:
                self.users_manager_instance.main_frame.pack_forget()
            if self.product_manager_instance:
                self.product_manager_instance.main_frame.pack_forget()
            if self.entradas_salidas_instance:
                self.entradas_salidas_instance.main_frame.pack_forget()

            self.generador_instance = GeneradorCodigos(
                parent=self.content_frame,
                icons=self.icons,
                db_manager=self.db_manager,
                store_id=self.store_id
            )
            self.generador_instance.main_frame.pack(padx=10, pady=10, fill="both", expand=True)
            logger.info("Generador de Códigos abierto.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el Generador de Códigos: {str(e)}")
            logger.error(f"Error al abrir Generador de Códigos: {str(e)}")

    def open_product_management(self):
        logging.debug("Iniciando open_product_management")
        if self.pos_instance:
            self.pos_instance.main_frame.pack_forget()
        if self.generador_instance:
            self.generador_instance.main_frame.pack_forget()
        if self.client_instance:
            self.client_instance.main_frame.pack_forget()
        if self.apartados_instance:
            self.apartados_instance.main_frame.pack_forget()
        if self.presupuestos_instance:
            self.presupuestos_instance.main_frame.pack_forget()
        if self.reportes_instance:
            self.reportes_instance.main_frame.pack_forget()
        if self.users_manager_instance:
            self.users_manager_instance.main_frame.pack_forget()
        if self.product_manager_instance:
            self.product_manager_instance.main_frame.pack_forget()
        if self.entradas_salidas_instance:
            self.entradas_salidas_instance.main_frame.pack_forget()
        
        try:
            self.product_manager_instance = ProductManagerWindow(self, self.content_frame, self.root, self.icons, store_id=self.store_id)
            self.product_manager_instance.main_frame.pack(padx=10, pady=10, fill="both", expand=True)
            logger.info(f"Interfaz de gestión de productos abierta para tienda {self.store_id}.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir Gestión de Productos: {str(e)}")
            logger.error(f"Error al abrir Gestión de Productos: {str(e)}")

    def open_client_management(self):
        logging.debug("Iniciando open_client_management")
        if self.pos_instance:
            self.pos_instance.main_frame.pack_forget()
        if self.generador_instance:
            self.generador_instance.main_frame.pack_forget()
        if self.client_instance:
            self.client_instance.main_frame.pack_forget()
        if self.apartados_instance:
            self.apartados_instance.main_frame.pack_forget()
        if self.presupuestos_instance:
            self.presupuestos_instance.main_frame.pack_forget()
        if self.reportes_instance:
            self.reportes_instance.main_frame.pack_forget()
        if self.users_manager_instance:
            self.users_manager_instance.main_frame.pack_forget()
        if self.product_manager_instance:
            self.product_manager_instance.main_frame.pack_forget()
        if self.entradas_salidas_instance:
            self.entradas_salidas_instance.main_frame.pack_forget()
        self.client_instance = ClientManager(user_id=self.user_id, parent_frame=self.content_frame, root=self.root, db_manager=self.db_manager, store_id=self.store_id)
        self.client_instance.main_frame.pack(padx=10, pady=10, fill="both", expand=True)
        logger.info(f"Interfaz de gestión de clientes abierta para tienda {self.store_id}.")

    def CLEAR_CONTENT_FRAME(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        logging.debug("Content frame limpiado")

    def open_apartado_management(self):
        logging.debug("Iniciando open_apartado_management")
        if self.pos_instance:
            self.pos_instance.main_frame.pack_forget()
        if self.generador_instance:
            self.generador_instance.main_frame.pack_forget()
        if self.client_instance:
            self.client_instance.main_frame.pack_forget()
        if self.apartados_instance:
            self.apartados_instance.main_frame.pack_forget()
        if self.presupuestos_instance:
            self.presupuestos_instance.main_frame.pack_forget()
        if self.reportes_instance:
            self.reportes_instance.main_frame.pack_forget()
        if self.users_manager_instance:
            self.users_manager_instance.main_frame.pack_forget()
        if self.product_manager_instance:
            self.product_manager_instance.main_frame.pack_forget()
        if self.entradas_salidas_instance:
            self.entradas_salidas_instance.main_frame.pack_forget()
        self.apartados_instance = ApartadosManager(user_id=self.user_id, parent_frame=self.content_frame, root=self.root, db_manager=self.db_manager, store_id=self.store_id)
        self.apartados_instance.main_frame.pack(padx=10, pady=10, fill="both", expand=True)
        logger.info(f"Interfaz de gestión de apartados abierta para tienda {self.store_id}.")

    def open_budget_management(self):
        logging.debug("Iniciando open_budget_management")
        if self.pos_instance:
            self.pos_instance.main_frame.pack_forget()
        if self.generador_instance:
            self.generador_instance.main_frame.pack_forget()
        if self.client_instance:
            self.client_instance.main_frame.pack_forget()
        if self.apartados_instance:
            self.apartados_instance.main_frame.pack_forget()
        if self.presupuestos_instance:
            self.presupuestos_instance.main_frame.pack_forget()
        if self.reportes_instance:
            self.reportes_instance.main_frame.pack_forget()
        if self.users_manager_instance:
            self.users_manager_instance.main_frame.pack_forget()
        if self.product_manager_instance:
            self.product_manager_instance.main_frame.pack_forget()
        if self.entradas_salidas_instance:
            self.entradas_salidas_instance.main_frame.pack_forget()
        self.presupuestos_instance = PresupuestosManager(user_id=self.user_id, parent_frame=self.content_frame, root=self.root, db_manager=self.db_manager, store_id=self.store_id)
        self.presupuestos_instance.pack(padx=10, pady=10, fill="both", expand=True)
        logger.info(f"Interfaz de gestión de presupuestos abierta para tienda {self.store_id}.")

    def open_reports_management(self):
        logging.debug("Iniciando open_reports_management")
        if self.pos_instance:
            self.pos_instance.main_frame.pack_forget()
        if self.generador_instance:
            self.generador_instance.main_frame.pack_forget()
        if self.client_instance:
            self.client_instance.main_frame.pack_forget()
        if self.apartados_instance:
            self.apartados_instance.main_frame.pack_forget()
        if self.presupuestos_instance:
            self.presupuestos_instance.main_frame.pack_forget()
        if self.reportes_instance:
            self.reportes_instance.main_frame.pack_forget()
        if self.users_manager_instance:
            self.users_manager_instance.main_frame.pack_forget()
        if self.product_manager_instance:
            self.product_manager_instance.main_frame.pack_forget()
        if self.entradas_salidas_instance:
            self.entradas_salidas_instance.main_frame.pack_forget()
        self.reportes_instance = ReportesManager(user_id=self.user_id, parent_frame=self.content_frame, root=self.root, db_manager=self.db_manager, store_id=self.store_id)
        self.reportes_instance.pack(padx=10, pady=10, fill="both", expand=True)
        logger.info(f"Interfaz de gestión de reportes abierta para tienda {self.store_id}.")

    def open_users_management(self):
        logging.debug("Iniciando open_users_management")
        if self.role != "admin":
            messagebox.showerror("Acceso Denegado", "Solo los administradores pueden acceder a Gestión de Usuarios.")
            logger.warning(f"Usuario con ID {self.user_id} (rol: {self.role}) intentó acceder a Gestión de Usuarios.")
            return

        if self.pos_instance:
            self.pos_instance.main_frame.pack_forget()
        if self.generador_instance:
            self.generador_instance.main_frame.pack_forget()
        if self.client_instance:
            self.client_instance.main_frame.pack_forget()
        if self.apartados_instance:
            self.apartados_instance.main_frame.pack_forget()
        if self.presupuestos_instance:
            self.presupuestos_instance.main_frame.pack_forget()
        if self.reportes_instance:
            self.reportes_instance.main_frame.pack_forget()
        if self.users_manager_instance:
            self.users_manager_instance.main_frame.pack_forget()
        if self.product_manager_instance:
            self.product_manager_instance.main_frame.pack_forget()
        if self.entradas_salidas_instance:
            self.entradas_salidas_instance.main_frame.pack_forget()

        try:
            self.users_manager_instance = UsersManager(
                user_id=self.user_id,
                parent_frame=self.content_frame,
                root=self.root,
                db_manager=self.db_manager,
                store_id=self.store_id
            )
            self.users_manager_instance.main_frame.pack(padx=10, pady=10, fill="both", expand=True)
            logger.info(f"Interfaz de Gestión de Usuarios abierta para tienda {self.store_id}.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir Gestión de Usuarios: {str(e)}")
            logger.error(f"Error al abrir Gestión de Usuarios: {str(e)}")

    def open_inventory_movements(self):
        logging.debug("Iniciando open_inventory_movements")
        if self.pos_instance:
            self.pos_instance.main_frame.pack_forget()
        if self.generador_instance:
            self.generador_instance.main_frame.pack_forget()
        if self.client_instance:
            self.client_instance.main_frame.pack_forget()
        if self.apartados_instance:
            self.apartados_instance.main_frame.pack_forget()
        if self.presupuestos_instance:
            self.presupuestos_instance.main_frame.pack_forget()
        if self.reportes_instance:
            self.reportes_instance.main_frame.pack_forget()
        if self.users_manager_instance:
            self.users_manager_instance.main_frame.pack_forget()
        if self.product_manager_instance:
            self.product_manager_instance.main_frame.pack_forget()
        if self.entradas_salidas_instance:
            self.entradas_salidas_instance.main_frame.pack_forget()

        try:
            self.entradas_salidas_instance = EntradasSalidasManager(
                user_id=self.user_id,
                parent_frame=self.content_frame,
                root=self.root,
                db_manager=self.db_manager,
                store_id=self.store_id
            )
            self.entradas_salidas_instance.pack(padx=10, pady=10, fill="both", expand=True)
            logger.info(f"Interfaz de Entradas y Salidas abierta para tienda {self.store_id}.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir Entradas y Salidas: {str(e)}")
            logger.error(f"Error al abrir Entradas y Salidas: {str(e)}")

    def run(self):
        try:
            logging.debug("Iniciando root.mainloop")
            self.root.mainloop()
            logging.debug("root.mainloop finalizado")
        except Exception as e:
            logger.error(f"Error en el bucle principal: {str(e)}")
            raise

if __name__ == "__main__":
    try:
        nav = NavigationManager(user_id="test_user_id", icons={}, store_id=1)
        nav.run()
    except Exception as e:
        logger.error(f"Error al iniciar NavigationManager: {str(e)}")
        print(f"Error al iniciar: {str(e)}")
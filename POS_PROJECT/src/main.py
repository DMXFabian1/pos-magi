import os
import sys
import traceback
# Agregar el directorio raíz del proyecto al sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

# Importaciones originales
import customtkinter as ctk
import logging
import os
import shutil
from src.ui.generador_codigos import GeneradorCodigos
from src.core.config.db_manager import DatabaseManager
from src.core.config.db_setup import inicializar_db
from tkinter import messagebox
import platform
from pathlib import Path
from src.core.backup.backup_manager import BackupManager
from src.modules.auth.auth_manager import AuthManager
from src.ui.navigation_manager import NavigationManager
from src.core.config.config import CONFIG, LOGS_DIR, DOCS_DIR, BACKUPS_DIR, DB_NAME, QR_DIR, IMAGES_DIR, SALES_REPORTS_DIR, INVENTORY_REPORTS_DIR
from logging.handlers import RotatingFileHandler
from src.core.utils.utils import validate_path, check_disk_space
from PIL import Image
import keyboard

# Definir logger
logger = logging.getLogger(__name__)

root_folder = CONFIG['ROOT_FOLDER']

logs_folder = os.path.join(root_folder, CONFIG['LOGS_DIR'])
docs_folder = os.path.join(root_folder, CONFIG['DOCS_DIR'])
backups_folder = os.path.join(root_folder, CONFIG['BACKUPS_DIR'])
images_folder = os.path.join(root_folder, CONFIG['IMAGES_DIR'])
qr_folder = os.path.join(root_folder, CONFIG['QR_DIR'])
sales_reports_folder = os.path.join(root_folder, CONFIG['SALES_REPORTS_DIR'])
inventory_reports_folder = os.path.join(root_folder, CONFIG['INVENTORY_REPORTS_DIR'])
icons_folder = os.path.join(os.path.dirname(__file__), "icons")

os.makedirs(logs_folder, exist_ok=True)
os.makedirs(docs_folder, exist_ok=True)
os.makedirs(backups_folder, exist_ok=True)
os.makedirs(images_folder, exist_ok=True)
os.makedirs(qr_folder, exist_ok=True)
os.makedirs(sales_reports_folder, exist_ok=True)
os.makedirs(inventory_reports_folder, exist_ok=True)
os.makedirs(icons_folder, exist_ok=True)

validate_path(logs_folder)

log_handler = RotatingFileHandler(
    filename=os.path.join(logs_folder, 'app.log'),
    maxBytes=5*1024*1024,
    backupCount=3
)
logging.basicConfig(
    handlers=[log_handler],
    level=logging.DEBUG if os.getenv("DEBUG") else logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def create_readme_if_not_exists(readme_path, root_folder, logs_folder, backups_folder, images_folder, qr_folder, sales_reports_folder, inventory_reports_folder):
    if not os.path.exists(readme_path):
        with open(readme_path, "w") as f:
            f.write("Bienvenido a ClothesApp\n\n")
            f.write("Este programa permite generar códigos QR y etiquetas para productos.\n")
            f.write("Ubicación de los datos (dentro de ClothesAppData):\n")
            f.write(f"- Base de datos: {os.path.join(root_folder, CONFIG['DB_NAME'])}\n")
            f.write(f"- Códigos QR: {qr_folder}\n")
            f.write(f"- Imágenes de productos: {images_folder}\n")
            f.write(f"- Logs: {os.path.join(logs_folder, 'app.log')}\n")
            f.write(f"- Copias de seguridad: {backups_folder}\n")
            f.write(f"- Reportes de ventas: {sales_reports_folder}\n")
            f.write(f"- Reportes de inventario: {inventory_reports_folder}\n")

readme_path = os.path.join(docs_folder, "README.txt")
create_readme_if_not_exists(readme_path, root_folder, logs_folder, backups_folder, images_folder, qr_folder, sales_reports_folder, inventory_reports_folder)

def load_icons(icons_folder):
    icons = {}
    icon_files = {
        "edit": "edit_icon.png",
        "copy": "copy_icon.png",
        "delete": "delete_icon.png",
        "duplicate": "duplicate_icon.png",
        "price": "price_icon.png",
        "print": "print_icon.png"
    }
    for key, filename in icon_files.items():
        try:
            icon_path = os.path.join(icons_folder, filename)
            logger.debug(f"Intentando cargar icono desde: {icon_path}")
            print(f"Intentando cargar icono desde: {icon_path}")
            if not os.path.exists(icon_path):
                logger.error(f"Archivo de icono no encontrado: {icon_path}")
                print(f"Archivo de icono no encontrado: {icon_path}")
                icons[key] = None
                continue
            img = Image.open(icon_path).convert("RGBA")
            img = img.resize((32, 32), Image.Resampling.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(32, 32))
            icons[key] = ctk_img
            logger.debug(f"Icono {filename} cargado exitosamente")
            print(f"Icono {filename} cargado exitosamente")
        except Exception as e:
            logger.error(f"Error al cargar el icono {filename}: {str(e)}", exc_info=True)
            print(f"Error al cargar el icono {filename}: {str(e)}")
            icons[key] = None
    return icons

class LoginWindow(ctk.CTk):
    def __init__(self, icons=None):
        super().__init__()
        self.title("POS Boutique - Login")
        self.geometry("400x550")
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("dark-blue")

        logger.debug("Iniciando inicialización de LoginWindow")
        
        self.db_manager = DatabaseManager()
        logger.debug("DatabaseManager inicializado")
        self.db_manager.ensure_tables()
        logger.debug("Tablas migradas y aseguradas")
        inicializar_db()
        logger.debug("Índices creados")
        self.auth_manager = AuthManager(db_manager=self.db_manager)
        
        self.icons = icons or {}
        self.current_user = None
        self.current_role = None
        self.after_id = None
        self.entry_usuario = None  # Inicializar como None
        self.entry_contrasena = None  # Inicializar como None

        # Centrar la ventana
        window_width = 400
        window_height = 550
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.resizable(False, False)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.pack(padx=20, pady=20, fill="both", expand=True)

        ctk.CTkLabel(self.main_frame, text="POS Boutique", font=("Arial", 24, "bold")).pack(pady=20)

        # Selector de tienda
        ctk.CTkLabel(self.main_frame, text="Tienda", font=("Arial", 14)).pack(pady=5)
        self.store_list = self.get_stores()
        self.entry_tienda = ctk.CTkComboBox(
            self.main_frame,
            width=250,
            height=35,
            values=[f"{store['id']} - {store['nombre']}" for store in self.store_list],
            state="normal",
            command=self.update_store_id
        )
        self.entry_tienda.pack(pady=5)
        self.entry_tienda.set("1 - Tienda Principal")  # Valor por defecto
        self.store_id = 1  # Inicializar con valor por defecto
        self.update_store_id(self.entry_tienda.get())  # Actualizar store_id inicial

        ctk.CTkLabel(self.main_frame, text="Usuario", font=("Arial", 14)).pack(pady=5)
        self.user_list = self.auth_manager.get_active_users(store_id=self.store_id).get("active_users", [""])
        self.entry_usuario = ctk.CTkComboBox(
            self.main_frame,
            width=250,
            height=35,
            values=self.user_list,
            state="normal"
        )
        self.entry_usuario.pack(pady=5)
        self.entry_usuario.bind("<Return>", lambda event: self.entry_contrasena.focus_set() if self.entry_contrasena else None)

        self.caps_lock_label = ctk.CTkLabel(
            self.main_frame,
            text="Mayúsculas activadas",
            font=("Arial", 12),
            text_color="orange",
            wraplength=250
        )
        try:
            if keyboard.is_pressed("caps lock"):
                self.caps_lock_label.pack(pady=5)
            self.check_caps_lock()
        except Exception as e:
            logger.error(f"Error al inicializar detección de Caps Lock: {str(e)}", exc_info=True)
            # Continuar sin detección de Caps Lock
            pass

        ctk.CTkLabel(self.main_frame, text="Contraseña", font=("Arial", 14)).pack(pady=5)
        self.entry_contrasena = ctk.CTkEntry(self.main_frame, width=250, height=35, show="*", placeholder_text="Ingrese su contraseña")
        self.entry_contrasena.pack(pady=5)
        self.entry_contrasena.bind("<Return>", lambda event: self.iniciar_sesion())

        self.show_password_var = ctk.BooleanVar(value=False)
        self.show_password_button = ctk.CTkCheckBox(self.main_frame, text="Mostrar contraseña", variable=self.show_password_var, command=self.toggle_password)
        self.show_password_button.pack(pady=10)

        self.login_button = ctk.CTkButton(self.main_frame, text="Iniciar Sesión", command=self.iniciar_sesion, fg_color="#4CAF50", hover_color="#45A049", state="disabled")
        self.login_button.pack(pady=20)

        self.error_label = ctk.CTkLabel(self.main_frame, text="", font=("Arial", 12), text_color="red")
        self.error_label.pack()

        # Vincular eventos después de que todos los widgets estén creados
        self.entry_usuario.bind("<KeyRelease>", self.validate_fields)
        self.entry_contrasena.bind("<KeyRelease>", self.validate_fields)

        self.entry_tienda.focus_set()
        logger.info(f"Ventana de login inicializada con detección de Caps Lock y lista de usuarios para tienda {self.store_id}.")

    def get_stores(self):
        """Obtiene la lista de tiendas desde la base de datos."""
        try:
            cursor = self.db_manager.get_cursor()
            cursor.execute("SELECT id, nombre FROM stores")
            stores = [dict(row) for row in cursor.fetchall()]
            if not stores:
                stores = [{"id": 1, "nombre": "Tienda Principal"}]  # Valor por defecto si no hay tiendas
            logger.debug(f"Tiendas obtenidas: {stores}")
            return stores
        except Exception as e:
            logger.error(f"Error al obtener tiendas: {str(e)}", exc_info=True)
            return [{"id": 1, "nombre": "Tienda Principal"}]  # Fallback

    def update_store_id(self, selection):
        """Actualiza store_id basado en la selección del usuario y recarga la lista de usuarios."""
        try:
            selected_store_id = int(selection.split(" - ")[0])
            self.store_id = selected_store_id
            # Actualizar lista de usuarios según la tienda seleccionada
            self.user_list = self.auth_manager.get_active_users(store_id=self.store_id).get("active_users", [""])
            if self.entry_usuario:  # Asegurarse de que entry_usuario exista
                self.entry_usuario.configure(values=self.user_list)
                self.entry_usuario.set("")
            logger.debug(f"store_id actualizado a {self.store_id}, lista de usuarios recargada")
        except (ValueError, IndexError) as e:
            logger.error(f"Error al actualizar store_id: {str(e)}", exc_info=True)
            self.store_id = 1  # Fallback
            if self.entry_usuario:
                self.entry_usuario.configure(values=[""])
                self.entry_usuario.set("")

    def check_caps_lock(self):
        try:
            if keyboard.is_pressed("caps lock"):
                if not self.caps_lock_label.winfo_ismapped():
                    self.caps_lock_label.pack(pady=5)
            else:
                if self.caps_lock_label.winfo_ismapped():
                    self.caps_lock_label.pack_forget()
        except Exception as e:
            logger.warning(f"Error al verificar Caps Lock para tienda {self.store_id}: {str(e)}", exc_info=True)
        if self.winfo_exists():  # Solo programar si la ventana aún existe
            self.after_id = self.after(500, self.check_caps_lock)

    def validate_fields(self, *args):
        try:
            if not hasattr(self, 'entry_usuario') or not hasattr(self, 'entry_contrasena'):
                logger.debug("Widgets de entrada no inicializados, omitiendo validación")
                return
            if self.entry_usuario is None or self.entry_contrasena is None:
                logger.debug("Widgets de entrada no creados, omitiendo validación")
                return
            username = self.entry_usuario.get().strip()
            password = self.entry_contrasena.get().strip()
            if username and password:
                self.login_button.configure(state="normal")
                self.error_label.configure(text="")
            else:
                self.login_button.configure(state="disabled")
                self.error_label.configure(text="Por favor, complete todos los campos.")
        except Exception as e:
            logger.error(f"Error al validar campos en tienda {self.store_id}: {str(e)}", exc_info=True)

    def toggle_password(self):
        if self.show_password_var.get():
            self.entry_contrasena.configure(show="")
        else:
            self.entry_contrasena.configure(show="*")

    def iniciar_sesion(self):
        usuario = self.entry_usuario.get().strip()
        contrasena = self.entry_contrasena.get().strip()
        logger.debug(f"Intentando autenticar usuario: {usuario}, contraseña tipo: {type(contrasena)} para tienda {self.store_id}")
        if not usuario or not contrasena:
            self.error_label.configure(text="Por favor, ingrese usuario y contraseña.")
            logger.warning(f"Intento de iniciar sesión con campos vacíos para tienda {self.store_id}")
            return

        if not isinstance(contrasena, str):
            contrasena = str(contrasena, 'utf-8') if isinstance(contrasena, bytes) else str(contrasena)
            logger.warning(f"Contraseña convertida a str desde tipo: {type(contrasena)} para tienda {self.store_id}")

        result = self.auth_manager.autenticar_usuario(usuario, contrasena, store_id=self.store_id)
        if result["success"]:
            self.current_user = result["user_id"]
            role_result = self.auth_manager.obtener_rol(self.current_user, store_id=self.store_id)
            if role_result["success"]:
                self.current_role = role_result["role"]
                logger.debug(f"Rol asignado a current_role: {self.current_role} para usuario {usuario} en tienda {self.store_id}")
                if self.current_role in ["cajero", "vendedor", "admin"]:
                    messagebox.showinfo("Éxito", f"Bienvenido, {usuario}!")
                    self.abrir_ventana_principal()
                else:
                    self.error_label.configure(text=f"Rol '{self.current_role}' no válido para navegación.")
                    logger.error(f"Rol no válido para usuario '{usuario}' en tienda {self.store_id}: {self.current_role}")
            else:
                self.error_label.configure(text="Error al obtener rol del usuario.")
                logger.error(f"Error al obtener rol para usuario '{usuario}' en tienda {self.store_id}: {role_result['message']}")
                return  # Detener ejecución si no se pudo obtener el rol
        else:
            self.error_label.configure(text=result["message"])
            logger.warning(f"Fallo de autenticación para usuario '{usuario}' en tienda {self.store_id}: {result['message']}")
            return  # Detener ejecución si la autenticación falla

    def configure_window(self, root):
        logger.debug(f"Configurando ventana raíz para maximización para tienda {self.store_id}")
        root.withdraw()
        root.state('zoomed')
        root.update_idletasks()
        logger.debug(f"Estado de la ventana después de configure_window: {root.state()}")

    def initialize_navigation(self, root):
        logger.debug(f"Inicializando NavigationManager para tienda {self.store_id}")
        nav = NavigationManager(
            user_id=self.current_user,
            icons=self.icons,
            root=root,
            db_manager=self.db_manager,
            store_id=self.store_id
        )
        logger.debug(f"NavigationManager creado con store_id={self.store_id}")
        return nav

    def abrir_ventana_principal(self):
        logger.debug(f"Iniciando abrir_ventana_principal para tienda {self.store_id}")
        if self.after_id:
            self.after_cancel(self.after_id)
            logger.debug("Tarea check_caps_lock cancelada")
        self.destroy()
        logger.debug("Ventana de login destruida")
        try:
            ctk.set_appearance_mode(CONFIG['THEME_MODE'])
            ctk.set_default_color_theme(CONFIG['THEME_COLOR'])
            logger.debug("Tema configurado")
            root = ctk.CTk()
            logger.debug("Root creado")
            self.configure_window(root)
            logger.debug("Ventana configurada como maximizada")
            nav = self.initialize_navigation(root)
            root.protocol("WM_DELETE_WINDOW", lambda: on_closing(root, nav.pos_instance.db_manager if nav.pos_instance else None, self.db_manager))
            logger.debug("Protocolo de cierre configurado")
            root.after(100, lambda: [
                root.deiconify(),
                root.state('zoomed'),
                logger.debug(f"Ventana mostrada, estado final: {root.state()}")
            ])
            logger.debug("deiconify y maximización programados")
            nav.run()
            logger.debug("Nav.run ejecutado")
        except Exception as e:
            logger.error(f"Error al abrir la ventana principal para tienda {self.store_id}: {str(e)}", exc_info=True)
            messagebox.showerror("Error", f"No se pudo abrir la ventana principal: {str(e)}")
            raise

    def on_closing(self):
        if self.after_id:
            self.after_cancel(self.after_id)
            logger.debug("Tarea check_caps_lock cancelada al cerrar LoginWindow")
        on_closing(self, None, self.db_manager)

    def run(self):
        try:
            self.mainloop()
        except Exception as e:
            logger.error(f"Error en el bucle principal para tienda {self.store_id}: {str(e)}", exc_info=True)
            raise

def on_closing(root, pos_db_manager, login_db_manager):
    try:
        # Crear el BackupManager y ejecutar el respaldo asíncronamente
        backup_manager = BackupManager(pos_db_manager.db_path if pos_db_manager else login_db_manager.db_path, config={
            "max_backups": 15,
            "backup_filename_format": "productos_backup_{prefix}_{reason}_{timestamp}.db"
        })
        backup_manager.create_backup(reason="close", async_mode=True)
        logger.info("Copia de seguridad programada al cerrar (ejecutándose en segundo plano)")
    except Exception as e:
        logger.error(f"Error al programar copia de seguridad al cerrar: {str(e)}", exc_info=True)
        if not messagebox.askyesno("Advertencia", "No se pudo programar la copia de seguridad. ¿Desea cerrar de todos modos?"):
            return
    finally:
        if login_db_manager:
            login_db_manager.close()
        if pos_db_manager:
            pos_db_manager.close()
        root.destroy()
        logger.info("Aplicación cerrada")

def main():
    logger.info("Iniciando main")
    try:
        logger.debug("Cargando íconos")
        icons = load_icons(icons_folder)
        logger.debug("Íconos cargados, creando LoginWindow")
        login_window = LoginWindow(icons=icons)
        logger.debug("LoginWindow creado, ejecutando run")
        login_window.run()
    except FileNotFoundError as e:
        logger.error(f"Error de archivo no encontrado: {str(e)}", exc_info=True)
        messagebox.showerror("Error", f"Archivo no encontrado: {str(e)}")
    except OSError as e:

        logger.error(f"Error del sistema operativo: {str(e)}", exc_info=True)
        messagebox.showerror("Error", f"Error del sistema: {str(e)}")
    except Exception as e:
        logger.error(f"Error inesperado en main: {str(e)}", exc_info=True)
        messagebox.showerror("Error", f"Ocurrió un error al iniciar la aplicación: {str(e)}")

if __name__ == "__main__":
    main()
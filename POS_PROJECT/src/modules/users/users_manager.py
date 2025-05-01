import customtkinter as ctk
from tkinter import ttk, messagebox
from src.modules.auth.auth_manager import AuthManager
import logging
import bcrypt

logger = logging.getLogger(__name__)

class UsersManager:
    def __init__(self, user_id, parent_frame, root, db_manager=None, store_id=1):
        logging.debug("Iniciando UsersManager")
        self.user_id = user_id
        self.parent_frame = parent_frame
        self.root = root
        self.db_manager = db_manager
        self.store_id = store_id
        self.auth_manager = AuthManager(db_manager=self.db_manager)
        logging.debug("AuthManager creado")

        self.main_frame = ctk.CTkFrame(self.parent_frame)
        logging.debug("main_frame creado")

        self.tree_frame = ctk.CTkFrame(self.main_frame)
        self.tree_frame.pack(fill="both", expand=True, pady=5)
        self.tree = ttk.Treeview(
            self.tree_frame,
            columns=("ID", "Usuario", "Rol"),
            show="headings"
        )
        self.tree.heading("ID", text="ID")
        self.tree.heading("Usuario", text="Usuario")
        self.tree.heading("Rol", text="Rol")
        self.tree.column("ID", width=50)
        self.tree.column("Usuario", width=150)
        self.tree.column("Rol", width=100)
        self.tree.pack(side="left", fill="both", expand=True)
        logging.debug("tree creado y empaquetado")

        self.button_frame = ctk.CTkFrame(self.tree_frame)
        self.button_frame.pack(side="right", padx=5)
        ctk.CTkButton(self.button_frame, text="Agregar Usuario", command=self.agregar_usuario).pack(pady=5)
        ctk.CTkButton(self.button_frame, text="Editar Usuario", command=self.editar_usuario).pack(pady=5)
        ctk.CTkButton(self.button_frame, text="Eliminar Usuario", command=self.eliminar_usuario).pack(pady=5)
        ctk.CTkButton(self.button_frame, text="Refrescar", command=self.cargar_usuarios).pack(pady=5)
        logging.debug("button_frame configurado")

        self.cargar_usuarios()
        logger.info(f"Interfaz de gestión de usuarios inicializada para usuario con ID '{self.user_id}' en tienda {self.store_id}.")

    def cargar_usuarios(self):
        logging.debug("Cargando usuarios")
        for item in self.tree.get_children():
            self.tree.delete(item)
        try:
            # Obtener usuarios desde AuthManager
            result = self.auth_manager.obtener_usuarios(store_id=self.store_id)
            logging.debug(f"Resultado de obtener_usuarios: {result}")
            
            if not result["success"]:
                logger.error(f"No se pudo cargar los usuarios: {result['message']}")
                messagebox.showerror("Error", f"No se pudo cargar los usuarios: {result['message']}")
                return

            usuarios = result["usuarios"]
            if not isinstance(usuarios, list):
                logger.error(f"Los usuarios no son una lista: {type(usuarios)}")
                messagebox.showerror("Error", "Error en el formato de los datos de usuarios")
                return

            # Verificar que cada usuario sea un diccionario
            for usuario in usuarios:
                if not isinstance(usuario, dict):
                    logger.error(f"Elemento de usuarios no es un diccionario: {type(usuario)} - {usuario}")
                    continue
                if not all(key in usuario for key in ["id", "username", "role"]):
                    logger.error(f"Usuario no tiene las claves esperadas: {usuario}")
                    continue
                self.tree.insert("", "end", values=(
                    usuario["id"],
                    usuario["username"],
                    usuario["role"]
                ))
            logger.info(f"Se cargaron {len(usuarios)} usuarios para tienda {self.store_id}")
        except Exception as e:
            logger.error(f"Error al cargar usuarios en tienda {self.store_id}: {str(e)}", exc_info=True)
            messagebox.showerror("Error", f"No se pudo cargar los usuarios: {str(e)}")

    def agregar_usuario(self):
        def guardar_usuario():
            username = entry_usuario.get().strip()
            password = entry_contrasena.get().strip()
            role = role_var.get()

            if not username or not password or not role:
                messagebox.showerror("Error", "Todos los campos son obligatorios.")
                return

            result = self.auth_manager.agregar_usuario(username, password, role, store_id=self.store_id)
            if result["success"]:
                dialog.destroy()
                messagebox.showinfo("Éxito", f"Usuario '{username}' agregado correctamente.")
                self.cargar_usuarios()
                logger.info(f"Nuevo usuario agregado: {username}, rol: {role} en tienda {self.store_id}")
            else:
                messagebox.showerror("Error", result["message"])
                logger.error(f"Error al agregar usuario en tienda {self.store_id}: {result['message']}")

        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Agregar Usuario")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Usuario *:").pack(pady=5)
        entry_usuario = ctk.CTkEntry(dialog, width=200)
        entry_usuario.pack(pady=5)

        ctk.CTkLabel(dialog, text="Contraseña *:").pack(pady=5)
        entry_contrasena = ctk.CTkEntry(dialog, width=200, show="*")
        entry_contrasena.pack(pady=5)

        ctk.CTkLabel(dialog, text="Rol *:").pack(pady=5)
        role_var = ctk.StringVar()
        role_menu = ctk.CTkOptionMenu(dialog, values=["admin", "cajero", "vendedor"], variable=role_var)
        role_menu.pack(pady=5)

        ctk.CTkButton(dialog, text="Guardar", command=guardar_usuario).pack(pady=10)

    def editar_usuario(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Selección", "Seleccione un usuario para editar.")
            return
        if len(selected) > 1:
            messagebox.showinfo("Selección", "Seleccione solo un usuario para editar.")
            return

        item = self.tree.item(selected[0])
        user_id = item['values'][0]
        username = item['values'][1]
        role = item['values'][2]

        def guardar_cambios():
            new_password = entry_contrasena.get().strip()
            new_role = role_var.get()

            if not new_password or not new_role:
                messagebox.showerror("Error", "La contraseña y el rol son obligatorios.")
                return

            result = self.auth_manager.editar_usuario(user_id, new_password, new_role, store_id=self.store_id)
            if result["success"]:
                dialog.destroy()
                messagebox.showinfo("Éxito", f"Usuario '{username}' actualizado correctamente.")
                self.cargar_usuarios()
                logger.info(f"Usuario actualizado: ID {user_id}, nuevo rol: {new_role} en tienda {self.store_id}")
            else:
                messagebox.showerror("Error", result["message"])
                logger.error(f"Error al editar usuario en tienda {self.store_id}: {result['message']}")

        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Editar Usuario")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text=f"Usuario: {username}", font=("Arial", 14)).pack(pady=5)
        ctk.CTkLabel(dialog, text="Nueva Contraseña *:").pack(pady=5)
        entry_contrasena = ctk.CTkEntry(dialog, width=200, show="*")
        entry_contrasena.pack(pady=5)

        ctk.CTkLabel(dialog, text="Rol *:").pack(pady=5)
        role_var = ctk.StringVar(value=role)
        role_menu = ctk.CTkOptionMenu(dialog, values=["admin", "cajero", "vendedor"], variable=role_var)
        role_menu.pack(pady=5)

        ctk.CTkButton(dialog, text="Guardar", command=guardar_cambios).pack(pady=10)

    def eliminar_usuario(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Selección", "Seleccione un usuario para eliminar.")
            return
        if len(selected) > 1:
            messagebox.showinfo("Selección", "Seleccione solo un usuario para eliminar.")
            return

        item = self.tree.item(selected[0])
        user_id = item['values'][0]
        username = item['values'][1]

        if user_id == self.user_id:
            messagebox.showerror("Error", "No puedes eliminar tu propio usuario.")
            return

        if not messagebox.askyesno("Confirmar", f"¿Estás seguro de que deseas eliminar al usuario '{username}'?"):
            return

        result = self.auth_manager.eliminar_usuario(user_id, store_id=self.store_id)
        if result["success"]:
            messagebox.showinfo("Éxito", f"Usuario '{username}' eliminado correctamente.")
            self.cargar_usuarios()
            logger.info(f"Usuario eliminado: ID {user_id}, username: {username} en tienda {self.store_id}")
        else:
            messagebox.showerror("Error", result["message"])
            logger.error(f"Error al eliminar usuario en tienda {self.store_id}: {result['message']}")

    def pack(self, **kwargs):
        self.main_frame.pack(**kwargs)
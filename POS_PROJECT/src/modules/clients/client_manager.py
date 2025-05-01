import customtkinter as ctk
from tkinter import ttk, messagebox
from src.core.config.db_manager import DatabaseManager
from src.utils.ui_utils import mostrar_ventana_seleccion
import logging

logger = logging.getLogger(__name__)

class ClientManager:
    def __init__(self, user_id, parent_frame, root, db_manager=None, store_id=1):
        logging.debug(f"Iniciando ClientManager con store_id={store_id}")
        self.user_id = user_id
        self.store_id = store_id
        self.parent_frame = parent_frame
        self.root = root
        self.db_manager = db_manager or DatabaseManager()
        logging.debug("DatabaseManager creado")

        self.main_frame = ctk.CTkFrame(self.parent_frame)
        logging.debug("main_frame creado")

        self.search_frame = ctk.CTkFrame(self.main_frame)
        self.search_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(self.search_frame, text="Buscar Cliente (Nombre/Teléfono):").pack(side="left", padx=5)
        self.entry_busqueda = ctk.CTkEntry(self.search_frame, width=250)
        self.entry_busqueda.pack(side="left", padx=5)
        self.entry_busqueda.bind("<Return>", lambda event: self.buscar_clientes())
        ctk.CTkButton(self.search_frame, text="Buscar", command=self.buscar_clientes).pack(side="left", padx=5)
        ctk.CTkButton(self.search_frame, text="Refrescar", command=self.cargar_clientes).pack(side="left", padx=5)
        logging.debug("search_frame configurado")

        self.tree_frame = ctk.CTkFrame(self.main_frame)
        self.tree_frame.pack(fill="both", expand=True, pady=5)
        self.tree = ttk.Treeview(
            self.tree_frame,
            columns=("ID", "Nombre Completo", "Teléfono"),
            show="headings"
        )
        self.tree.heading("ID", text="ID")
        self.tree.heading("Nombre Completo", text="Nombre Completo")
        self.tree.heading("Teléfono", text="Teléfono")
        self.tree.column("ID", width=50)
        self.tree.column("Nombre Completo", width=250)
        self.tree.column("Teléfono", width=150)
        self.tree.pack(side="left", fill="both", expand=True)
        logging.debug("tree creado y empaquetado")

        self.button_frame = ctk.CTkFrame(self.tree_frame)
        self.button_frame.pack(side="right", padx=5)
        ctk.CTkButton(self.button_frame, text="Añadir Cliente", command=self.añadir_cliente).pack(pady=5)
        ctk.CTkButton(self.button_frame, text="Editar Cliente", command=self.editar_cliente).pack(pady=5)
        ctk.CTkButton(self.button_frame, text="Eliminar Cliente", command=self.eliminar_cliente).pack(pady=5)
        logging.debug("button_frame configurado")

        self.cargar_clientes()
        self.entry_busqueda.focus_set()
        logger.info(f"Interfaz de gestión de clientes inicializada para usuario con ID '{self.user_id}' en tienda {self.store_id}.")

    def cargar_clientes(self):
        logging.debug("Cargando clientes")
        for item in self.tree.get_children():
            self.tree.delete(item)
        try:
            clientes = self.db_manager.buscar_clientes(query="", limit=None)
            logging.debug(f"Clientes obtenidos: {len(clientes)} registros")
            if not clientes:
                messagebox.showinfo("Información", "No se encontraron clientes en la base de datos.")
            for cliente in clientes:
                logging.debug(f"Insertando cliente en Treeview: {cliente}")
                self.tree.insert("", "end", values=(
                    cliente['id'],
                    cliente['nombre_completo'],
                    cliente['numero'] or "N/A"
                ))
            logging.debug("Clientes cargados y Treeview actualizado")
        except Exception as e:
            logging.error(f"Error al cargar clientes: {str(e)}")
            messagebox.showerror("Error", f"No se pudo cargar los clientes: {str(e)}")

    def buscar_clientes(self):
        query = self.entry_busqueda.get().strip()
        logging.debug(f"Buscando clientes con query: {query}")
        try:
            clientes = self.db_manager.buscar_clientes(query=query, limit=50)
            logging.debug(f"Resultados de búsqueda: {len(clientes)} registros")
            if not clientes:
                messagebox.showinfo("Información", f"No se encontraron clientes para la búsqueda: '{query}'")
                return

            columns = ["ID", "Nombre Completo", "Teléfono"]
            column_widths = {"ID": 50, "Nombre Completo": 250, "Teléfono": 150}
            formatted_clientes = [
                {
                    "ID": cliente['id'],
                    "Nombre Completo": cliente['nombre_completo'],
                    "Teléfono": cliente['numero'] or "N/A"
                }
                for cliente in clientes
            ]

            def on_select(cliente):
                for item in self.tree.get_children():
                    self.tree.delete(item)
                self.tree.insert("", "end", values=(
                    cliente['ID'],
                    cliente['Nombre Completo'],
                    cliente['Teléfono']
                ))

            mostrar_ventana_seleccion(
                parent=self.root,
                title="Seleccionar Cliente",
                items=formatted_clientes,
                columns=columns,
                column_widths=column_widths,
                on_select_callback=on_select
            )

            logging.debug("Resultados de búsqueda cargados y Treeview actualizado")
        except Exception as e:
            logging.error(f"Error al buscar clientes: {str(e)}")
            messagebox.showerror("Error", f"No se pudo buscar clientes: {str(e)}")

    def añadir_cliente(self, callback=None):
        def guardar_cliente():
            nonlocal cliente_id, nombre_completo
            nombre = entry_nombre.get().strip()
            telefono = entry_telefono.get().strip()
            if not nombre:
                messagebox.showerror("Error", "El nombre es obligatorio.")
                cliente_id = None
                dialog.destroy()
                if callback:
                    callback(None, None)
                return
            try:
                cliente_id = self.db_manager.registrar_cliente(nombre, telefono)
                nombre_completo = nombre
                logging.debug(f"Cliente añadido con ID: {cliente_id}")
                dialog.destroy()
                messagebox.showinfo("Éxito", f"Cliente '{nombre}' registrado con ID: {cliente_id}.")
                self.cargar_clientes()
                logger.info(f"Nuevo cliente registrado: {nombre}")
                if callback:
                    callback(cliente_id, nombre_completo)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo registrar el cliente: {str(e)}")
                logger.error(f"Error al registrar cliente: {str(e)}")
                cliente_id = None
                if callback:
                    callback(None, None)

        cliente_id = None
        nombre_completo = None
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Añadir Cliente")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Nombre *:").pack(pady=5)
        entry_nombre = ctk.CTkEntry(dialog, width=200)
        entry_nombre.pack(pady=5)

        ctk.CTkLabel(dialog, text="Teléfono:").pack(pady=5)
        entry_telefono = ctk.CTkEntry(dialog, width=200)
        entry_telefono.pack(pady=5)

        ctk.CTkButton(dialog, text="Guardar", command=guardar_cliente).pack(pady=10)
        entry_nombre.focus_set()

    def abrir_ventana_crear_cliente(self, callback=None):
        self.añadir_cliente(callback=callback)

    def editar_cliente(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Selección", "Seleccione un cliente para editar.")
            return
        item = self.tree.item(selected[0])
        cliente_id = item['values'][0]
        nombre_actual = item['values'][1]
        telefono_actual = item['values'][2]

        def guardar_cambios():
            nombre = entry_nombre.get().strip()
            telefono = entry_telefono.get().strip()
            if not nombre:
                messagebox.showerror("Error", "El nombre es obligatorio.")
                return
            try:
                self.db_manager.actualizar_cliente(cliente_id, nombre, telefono)
                logging.debug(f"Cliente actualizado: ID {cliente_id}")
                dialog.destroy()
                messagebox.showinfo("Éxito", f"Cliente '{nombre}' actualizado.")
                self.cargar_clientes()
                logger.info(f"Cliente actualizado: ID {cliente_id}, Nombre: {nombre}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo actualizar el cliente: {str(e)}")
                logger.error(f"Error al actualizar cliente: {str(e)}")

        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Editar Cliente")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Nombre *:").pack(pady=5)
        entry_nombre = ctk.CTkEntry(dialog, width=200)
        entry_nombre.pack(pady=5)
        entry_nombre.insert(0, nombre_actual)

        ctk.CTkLabel(dialog, text="Teléfono:").pack(pady=5)
        entry_telefono = ctk.CTkEntry(dialog, width=200)
        entry_telefono.pack(pady=5)
        entry_telefono.insert(0, telefono_actual)

        ctk.CTkButton(dialog, text="Guardar", command=guardar_cambios).pack(pady=10)
        entry_nombre.focus_set()

    def eliminar_cliente(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Selección", "Seleccione un cliente para eliminar.")
            return
        item = self.tree.item(selected[0])
        cliente_id = item['values'][0]
        nombre = item['values'][1]
        if not messagebox.askyesno("Confirmar", f"¿Está seguro de que desea eliminar al cliente '{nombre}'?"):
            return
        try:
            self.db_manager.eliminar_cliente(cliente_id)
            logging.debug(f"Cliente eliminado: ID {cliente_id}")
            messagebox.showinfo("Éxito", f"Cliente '{nombre}' eliminado.")
            self.cargar_clientes()
            logger.info(f"Cliente eliminado: ID {cliente_id}, Nombre: {nombre}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar el cliente: {str(e)}")
            logger.error(f"Error al eliminar cliente: {str(e)}")
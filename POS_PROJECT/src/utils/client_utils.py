import logging
from tkinter import messagebox

logger = logging.getLogger(__name__)

def buscar_clientes_reutilizable(db_manager, query, limit=None, entry=None, set_id_callback=None, tree=None, show_messages=True):
    """
    Función reutilizable para buscar clientes en la base de datos.

    Args:
        db_manager: Instancia de DatabaseManager para acceder a la base de datos.
        query (str): Texto de búsqueda (nombre o número de teléfono).
        limit (int, optional): Número máximo de resultados. Por defecto None.
        entry (CTkEntry, optional): Campo de entrada donde se mostrará el nombre del cliente seleccionado.
        set_id_callback (callable, optional): Callback para actualizar el ID del cliente seleccionado.
        tree (ttk.Treeview, optional): Tabla donde se llenarán los resultados.
        show_messages (bool, optional): Indica si se deben mostrar mensajes al usuario. Por defecto True.

    Returns:
        list: Lista de clientes encontrados.
    """
    try:
        # Buscar clientes en la base de datos, ordenados por nombre_completo
        cursor = db_manager.get_cursor()
        query_sql = "SELECT id, nombre_completo, numero FROM clientes"
        params = []
        if query:
            query_sql += " WHERE nombre_completo LIKE ? OR numero LIKE ?"
            params = [f"%{query}%", f"%{query}%"]
        query_sql += " ORDER BY nombre_completo ASC"
        if limit:
            query_sql += f" LIMIT {limit}"
        cursor.execute(query_sql, params)
        clientes = [dict(row) for row in cursor.fetchall()]
        
        logger.debug(f"Resultados de búsqueda para query '{query}': {len(clientes)} registros")

        if not clientes and show_messages:
            messagebox.showinfo("No encontrado", f"No se encontraron clientes para la búsqueda: '{query}'")
            return []

        # Si se proporciona un tree, llenar la tabla con los resultados
        if tree:
            for item in tree.get_children():
                tree.delete(item)
            for cliente in clientes:
                tree.insert("", "end", values=(
                    cliente['id'],
                    cliente['nombre_completo'],
                    cliente['numero'] if cliente['numero'] else "N/A"
                ))
            return clientes

        # Si se proporciona entry y set_id_callback, seleccionar el primer cliente
        if entry and set_id_callback:
            cliente = clientes[0]
            entry.delete(0, "end")
            entry.insert(0, cliente['nombre_completo'])
            set_id_callback(cliente['id'])
            logger.info(f"Cliente seleccionado: {cliente['nombre_completo']} (ID: {cliente['id']})")
            return clientes

        # Si no se proporciona ni tree ni entry, devolver los resultados
        return clientes

    except Exception as e:
        logger.error(f"Error al buscar clientes con query '{query}': {str(e)}")
        if show_messages:
            messagebox.showerror("Error", f"No se pudo buscar clientes: {str(e)}")
        return []
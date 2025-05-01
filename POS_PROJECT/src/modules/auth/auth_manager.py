import logging
import sqlite3
import bcrypt

logger = logging.getLogger(__name__)

class AuthManager:
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        logger.debug("AuthManager inicializado")

    def _execute_query(self, query, params, fetch_one=True, commit=False):
        """Método auxiliar para ejecutar consultas SQL y manejar errores."""
        try:
            cursor = self.db_manager.get_cursor()
            cursor.execute(query, params)
            if commit:
                self.db_manager.commit()
            if fetch_one:
                result = cursor.fetchone()
                return dict(result) if result else None
            else:
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error al ejecutar consulta: {str(e)}", exc_info=True)
            return None

    def autenticar_usuario(self, username, password, store_id=1):
        """
        Autentica a un usuario verificando su contraseña.

        Args:
            username (str): Nombre de usuario.
            password (str): Contraseña en texto plano.
            store_id (int): ID de la tienda (por defecto 1).

        Returns:
            dict: Resultado con success, message y user_id.
        """
        try:
            if not username or not password:
                logger.warning(f"Intento de autenticación con datos vacíos para tienda {store_id}")
                return {
                    "success": False,
                    "message": "Nombre de usuario y contraseña son requeridos",
                    "user_id": None
                }

            query = "SELECT id, password FROM users WHERE username = ? AND store_id = ?"
            user = self._execute_query(query, (username, store_id), fetch_one=True)

            if user:
                stored_password = user['password']
                if isinstance(stored_password, str):
                    stored_password = stored_password.encode('utf-8')
                if isinstance(password, bytes):
                    password = password.decode('utf-8')
                if bcrypt.checkpw(password.encode('utf-8'), stored_password):
                    logger.info(f"Usuario {username} autenticado exitosamente para tienda {store_id}")
                    return {
                        "success": True,
                        "message": "Autenticación exitosa",
                        "user_id": user['id']
                    }
            logger.warning(f"Autenticación fallida para usuario {username} en tienda {store_id}")
            return {
                "success": False,
                "message": "Usuario o contraseña incorrectos",
                "user_id": None
            }
        except Exception as e:
            logger.error(f"Error al autenticar usuario {username} en tienda {store_id}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": f"Error al autenticar usuario: {str(e)}",
                "user_id": None
            }

    def obtener_rol(self, user_id, store_id=1):
        """
        Obtiene el rol de un usuario.

        Args:
            user_id (int): ID del usuario.
            store_id (int): ID de la tienda (por defecto 1).

        Returns:
            dict: Resultado con success, message y role.
        """
        try:
            if not user_id:
                logger.warning(f"Intento de obtener rol con user_id vacío para tienda {store_id}")
                return {
                    "success": False,
                    "message": "El ID del usuario es requerido",
                    "role": None
                }

            query = "SELECT role FROM users WHERE id = ? AND store_id = ?"
            result = self._execute_query(query, (user_id, store_id), fetch_one=True)

            if result:
                role = result['role']
                logger.debug(f"Rol {role} obtenido para usuario {user_id} en tienda {store_id}")
                return {
                    "success": True,
                    "message": "Rol obtenido exitosamente",
                    "role": role
                }
            logger.warning(f"No se encontró rol para usuario {user_id} en tienda {store_id}")
            return {
                "success": False,
                "message": f"No se encontró el usuario con ID {user_id}",
                "role": None
            }
        except Exception as e:
            logger.error(f"Error al obtener rol del usuario {user_id} en tienda {store_id}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": f"Error al obtener rol: {str(e)}",
                "role": None
            }

    def obtener_usuarios(self, store_id=1):
        """
        Obtiene la lista de todos los usuarios de una tienda.

        Args:
            store_id (int): ID de la tienda (por defecto 1).

        Returns:
            dict: Resultado con success, message y usuarios.
        """
        try:
            query = "SELECT id, username, role FROM users WHERE store_id = ?"
            usuarios = self._execute_query(query, (store_id,), fetch_one=False)

            logger.debug(f"Se obtuvieron {len(usuarios)} usuarios para tienda {store_id}")
            return {
                "success": True,
                "message": "Usuarios obtenidos exitosamente",
                "usuarios": usuarios
            }
        except Exception as e:
            logger.error(f"No se pudo obtener la lista de usuarios para tienda {store_id}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": f"Error al obtener usuarios: {str(e)}",
                "usuarios": []
            }

    def agregar_usuario(self, username, password, role, store_id=1):
        """
        Agrega un nuevo usuario.

        Args:
            username (str): Nombre de usuario.
            password (str): Contraseña en texto plano.
            role (str): Rol del usuario ('admin', 'cajero', 'vendedor').
            store_id (int): ID de la tienda (por defecto 1).

        Returns:
            dict: Resultado con success y message.
        """
        try:
            if not username or not password:
                logger.warning(f"Intento de agregar usuario con datos vacíos para tienda {store_id}")
                return {
                    "success": False,
                    "message": "Nombre de usuario y contraseña son requeridos"
                }

            if role not in ['admin', 'cajero', 'vendedor']:
                logger.error(f"Intento de agregar usuario con rol inválido: {role} en tienda {store_id}")
                return {
                    "success": False,
                    "message": "Rol inválido. Debe ser 'admin', 'cajero' o 'vendedor'"
                }

            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            query = "INSERT INTO users (username, password, role, store_id) VALUES (?, ?, ?, ?)"
            result = self._execute_query(query, (username, hashed_password, role, store_id), fetch_one=False, commit=True)

            if result is None:  # Indica un error en la ejecución
                logger.error(f"Error al intentar agregar usuario {username} en tienda {store_id}")
                return {
                    "success": False,
                    "message": "Error al agregar usuario"
                }

            logger.info(f"Usuario {username} agregado exitosamente para tienda {store_id}")
            return {
                "success": True,
                "message": "Usuario agregado exitosamente"
            }
        except sqlite3.IntegrityError:
            logger.error(f"El nombre de usuario '{username}' ya está en uso en tienda {store_id}")
            return {
                "success": False,
                "message": f"El nombre de usuario '{username}' ya está en uso"
            }
        except Exception as e:
            logger.error(f"Error al agregar usuario {username} en tienda {store_id}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": f"Error al agregar usuario: {str(e)}"
            }

    def editar_usuario(self, user_id, new_password, new_role, store_id=1):
        """
        Edita un usuario existente.

        Args:
            user_id (int): ID del usuario.
            new_password (str): Nueva contraseña.
            new_role (str): Nuevo rol.
            store_id (int): ID de la tienda (por defecto 1).

        Returns:
            dict: Resultado con success y message.
        """
        try:
            if not user_id:
                logger.warning(f"Intento de editar usuario con ID vacío en tienda {store_id}")
                return {
                    "success": False,
                    "message": "El ID del usuario es requerido"
                }

            if not new_password:
                logger.warning(f"Intento de editar usuario {user_id} con contraseña vacía en tienda {store_id}")
                return {
                    "success": False,
                    "message": "La contraseña es requerida"
                }

            if new_role not in ['admin', 'cajero', 'vendedor']:
                logger.error(f"Intento de editar usuario {user_id} con rol inválido: {new_role} en tienda {store_id}")
                return {
                    "success": False,
                    "message": "Rol inválido. Debe ser 'admin', 'cajero' o 'vendedor'"
                }

            # Verificar si el usuario existe
            query_check = "SELECT 1 FROM users WHERE id = ? AND store_id = ?"
            if not self._execute_query(query_check, (user_id, store_id), fetch_one=True):
                logger.warning(f"No se encontró el usuario con ID {user_id} en tienda {store_id}")
                return {
                    "success": False,
                    "message": f"No se encontró el usuario con ID {user_id}"
                }

            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            query = "UPDATE users SET password = ?, role = ? WHERE id = ? AND store_id = ?"
            self._execute_query(query, (hashed_password, new_role, user_id, store_id), fetch_one=False, commit=True)

            logger.info(f"Usuario {user_id} editado exitosamente para tienda {store_id}")
            return {
                "success": True,
                "message": "Usuario editado exitosamente"
            }
        except Exception as e:
            logger.error(f"Error al editar usuario {user_id} en tienda {store_id}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": f"Error al editar usuario: {str(e)}"
            }

    def eliminar_usuario(self, user_id, store_id=1):
        """
        Elimina un usuario.

        Args:
            user_id (int): ID del usuario.
            store_id (int): ID de la tienda (por defecto 1).

        Returns:
            dict: Resultado con success y message.
        """
        try:
            if not user_id:
                logger.warning(f"Intento de eliminar usuario con ID vacío en tienda {store_id}")
                return {
                    "success": False,
                    "message": "El ID del usuario es requerido"
                }

            # Verificar si el usuario existe
            query_check = "SELECT 1 FROM users WHERE id = ? AND store_id = ?"
            if not self._execute_query(query_check, (user_id, store_id), fetch_one=True):
                logger.warning(f"No se encontró el usuario con ID {user_id} en tienda {store_id}")
                return {
                    "success": False,
                    "message": f"No se encontró el usuario con ID {user_id}"
                }

            query = "DELETE FROM users WHERE id = ? AND store_id = ?"
            self._execute_query(query, (user_id, store_id), fetch_one=False, commit=True)

            logger.info(f"Usuario {user_id} eliminado exitosamente para tienda {store_id}")
            return {
                "success": True,
                "message": "Usuario eliminado exitosamente"
            }
        except Exception as e:
            logger.error(f"Error al eliminar usuario {user_id} en tienda {store_id}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": f"Error al eliminar usuario: {str(e)}"
            }

    def get_active_users(self, store_id=1):
        """
        Obtiene una lista de nombres de usuario activos.
        Como no hay un campo 'active', se asume que todos los usuarios en la tabla son activos.

        Args:
            store_id (int): ID de la tienda (por defecto 1).

        Returns:
            dict: Resultado con success, message y active_users.
        """
        try:
            result = self.obtener_usuarios(store_id)
            if not result["success"]:
                logger.error(f"Fallo al obtener usuarios activos para tienda {store_id}: {result['message']}")
                return {
                    "success": False,
                    "message": result["message"],
                    "active_users": []
                }

            usuarios = result["usuarios"]
            active_users = [usuario['username'] for usuario in usuarios]
            logger.debug(f"Se obtuvieron {len(active_users)} usuarios activos para tienda {store_id}")
            return {
                "success": True,
                "message": "Usuarios activos obtenidos exitosamente",
                "active_users": active_users
            }
        except Exception as e:
            logger.error(f"Error al obtener usuarios activos para tienda {store_id}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": f"Error al obtener usuarios activos: {str(e)}",
                "active_users": []
            }
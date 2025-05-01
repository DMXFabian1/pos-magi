import sys
import os
import random
import logging

# Ajustar sys.path para que el script funcione desde la carpeta src/scripts
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))  # Subir dos niveles desde src/scripts a POS_PROJECT
sys.path.append(project_root)

from src.core.config.db_manager import DatabaseManager

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Listas de nombres y apellidos comunes en español
NOMBRES = [
    "Ana", "Juan", "María", "Carlos", "Luis", "Sofía", "José", "Laura", "Diego", "Carmen",
    "Pedro", "Elena", "Miguel", "Isabel", "Javier", "Patricia", "Alejandro", "Clara", "Manuel", "Rosa",
    "David", "Lucía", "Francisco", "Beatriz", "Pablo", "Marta", "Andrés", "Paula", "Fernando", "Sara",
    "Ricardo", "Julia", "Alberto", "Natalia", "Enrique", "Verónica", "Raúl", "Alicia", "Eduardo", "Silvia"
]

APELLIDOS = [
    "García", "Martínez", "López", "González", "Rodríguez", "Fernández", "Pérez", "Gómez", "Sánchez", "Díaz",
    "Hernández", "Ruiz", "Álvarez", "Moreno", "Romero", "Jiménez", "Torres", "Domínguez", "Vázquez", "Ramos",
    "Gil", "Muñoz", "Serrano", "Blanco", "Molina", "Delgado", "Castro", "Ortiz", "Rubio", "Sanz",
    "Iglesias", "Núñez", "Medina", "Cortés", "Castillo", "Garrido", "Cruz", "Reyes", "Pascual", "Herrera"
]

# Prefijos de números de teléfono móviles en México
PREFIJOS = ["55", "33", "81", "44", "22", "66", "77", "99"]

def generar_nombre_completo():
    """Genera un nombre completo aleatorio combinando un nombre y dos apellidos."""
    nombre = random.choice(NOMBRES)
    apellido1 = random.choice(APELLIDOS)
    apellido2 = random.choice(APELLIDOS)
    return f"{nombre} {apellido1} {apellido2}"

def generar_numero_telefono():
    """Genera un número de teléfono aleatorio con un prefijo y 8 dígitos."""
    prefijo = random.choice(PREFIJOS)
    digitos = ''.join([str(random.randint(0, 9)) for _ in range(8)])
    return f"{prefijo}{digitos}"

def generar_clientes_aleatorios(num_clientes=70):
    """
    Genera una lista de clientes aleatorios con nombres y números de teléfono únicos.

    Args:
        num_clientes (int): Número de clientes a generar (por defecto 70).

    Returns:
        list: Lista de diccionarios con los datos de los clientes.
    """
    clientes = []
    numeros_usados = set()

    while len(clientes) < num_clientes:
        nombre_completo = generar_nombre_completo()
        numero = generar_numero_telefono()

        # Evitar duplicados en los números de teléfono
        if numero in numeros_usados:
            continue

        numeros_usados.add(numero)
        clientes.append({
            "nombre_completo": nombre_completo,
            "numero": numero
        })

    return clientes

def insertar_clientes(db_manager, clientes):
    """
    Inserta los clientes en la base de datos.

    Args:
        db_manager: Instancia de DatabaseManager.
        clientes (list): Lista de diccionarios con los datos de los clientes.
    """
    try:
        cursor = db_manager.get_cursor()
        for cliente in clientes:
            cursor.execute(
                "INSERT INTO clientes (nombre_completo, numero) VALUES (?, ?)",
                (cliente["nombre_completo"], cliente["numero"])
            )
        db_manager.conn.commit()
        logger.info(f"Se insertaron {len(clientes)} clientes en la base de datos.")
    except Exception as e:
        logger.error(f"Error al insertar clientes: {str(e)}")
        raise

def main():
    """Función principal para añadir 70 clientes aleatorios a la base de datos."""
    try:
        # Inicializar DatabaseManager
        db_manager = DatabaseManager()

        # Generar 70 clientes aleatorios
        clientes = generar_clientes_aleatorios(70)

        # Insertar los clientes en la base de datos
        insertar_clientes(db_manager, clientes)

        # Imprimir algunos ejemplos para verificar
        for i, cliente in enumerate(clientes[:5]):  # Mostrar los primeros 5 como ejemplo
            logger.info(f"Cliente {i+1}: {cliente['nombre_completo']}, {cliente['numero']}")

    except Exception as e:
        logger.error(f"Error en el script: {str(e)}")
    finally:
        db_manager.close()

if __name__ == "__main__":
    main()
import sqlite3
import os
import logging
from src.core.config.config import CONFIG

logger = logging.getLogger(__name__)

def inicializar_db():
    """Crea las tablas en la base de datos especificada si no existen y migra la estructura si es necesario."""
    db_path = os.path.join(CONFIG['ROOT_FOLDER'], CONFIG['DB_NAME'])
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Crear tabla stores
    c.execute('''CREATE TABLE IF NOT EXISTS stores (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 nombre TEXT NOT NULL,
                 ubicacion TEXT
             )''')
    # Insertar tienda por defecto si no existe
    c.execute("SELECT COUNT(*) FROM stores")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO stores (id, nombre, ubicacion) VALUES (1, 'Tienda Principal', 'San Felipe')")
        logger.info("Tabla 'stores' inicializada con tienda por defecto: ID=1, Nombre='Tienda Principal'.")
    
    # Crear o migrar tabla productos
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='productos'")
    if c.fetchone():
        c.execute("PRAGMA table_info(productos)")
        columns = [col[1] for col in c.fetchall()]
        expected_columns = ["sku", "nombre", "nivel_educativo", "escuela", "color", "tipo_prenda", "tipo_pieza",
                            "genero", "marca", "talla", "atributo", "ubicacion", "escudo", "qr_path",
                            "inventario", "ventas", "precio", "image_path", "store_id"]
        if not all(col in columns for col in expected_columns):
            logger.warning("La tabla 'productos' tiene una estructura incorrecta. Realizando migración...")
            c.execute("ALTER TABLE productos RENAME TO productos_temp")
            c.execute('''CREATE TABLE productos (
                         sku TEXT PRIMARY KEY,
                         nombre TEXT,
                         nivel_educativo TEXT,
                         escuela TEXT,
                         color TEXT,
                         tipo_prenda TEXT,
                         tipo_pieza TEXT,
                         genero TEXT,
                         marca TEXT,
                         talla TEXT,
                         atributo TEXT,
                         ubicacion TEXT,
                         escudo TEXT,
                         qr_path TEXT,
                         inventario INTEGER,
                         ventas INTEGER,
                         precio REAL DEFAULT 0.0,
                         image_path TEXT,
                         store_id INTEGER,
                         FOREIGN KEY (store_id) REFERENCES stores(id))''')
            columns_to_copy = [col for col in columns if col in expected_columns]
            if columns_to_copy:
                columns_str = ", ".join(columns_to_copy)
                values_str = ", ".join([f"productos_temp.{col}" for col in columns_to_copy])
                c.execute(f"INSERT INTO productos ({columns_str}, store_id) SELECT {values_str}, 1 FROM productos_temp")
            c.execute("DROP TABLE productos_temp")
            logger.info("Tabla 'productos' migrada exitosamente con store_id.")
    else:
        c.execute('''CREATE TABLE productos (
                     sku TEXT PRIMARY KEY,
                     nombre TEXT,
                     nivel_educativo TEXT,
                     escuela TEXT,
                     color TEXT,
                     tipo_prenda TEXT,
                     tipo_pieza TEXT,
                     genero TEXT,
                     marca TEXT,
                     talla TEXT,
                     atributo TEXT,
                     ubicacion TEXT,
                     escudo TEXT,
                     qr_path TEXT,
                     inventario INTEGER,
                     ventas INTEGER,
                     precio REAL DEFAULT 0.0,
                     image_path TEXT,
                     store_id INTEGER,
                     FOREIGN KEY (store_id) REFERENCES stores(id))''')
        logger.info("Tabla 'productos' creada con store_id.")
    
    # Crear tabla contador_sku
    c.execute('''CREATE TABLE IF NOT EXISTS contador_sku (
                 id INTEGER PRIMARY KEY,
                 ultimo_sku TEXT)''')
    c.execute("SELECT COUNT(*) FROM contador_sku")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO contador_sku (id, ultimo_sku) VALUES (1, '000000')")
        logger.info("Tabla 'contador_sku' inicializada.")
    
    # Crear tabla users
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT UNIQUE NOT NULL,
                 password TEXT NOT NULL,
                 role TEXT NOT NULL CHECK(role IN ('admin', 'cajero', 'vendedor')),
                 CONSTRAINT unique_username UNIQUE (username))''')
    
    # Crear o migrar tabla clientes
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clientes'")
    if c.fetchone():
        c.execute("PRAGMA table_info(clientes)")
        columns = [col[1] for col in c.fetchall()]
        expected_new_columns = ["id", "nombre_completo", "numero", "created_at"]
        has_new_structure = all(col in columns for col in expected_new_columns)
        if not has_new_structure:
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clientes_temp'")
            if c.fetchone():
                c.execute("DROP TABLE clientes_temp")
                logger.warning("Tabla 'clientes_temp' eliminada.")
            logger.warning("Migrando tabla 'clientes'...")
            c.execute("ALTER TABLE clientes RENAME TO clientes_temp")
            c.execute('''CREATE TABLE clientes (
                         id INTEGER PRIMARY KEY AUTOINCREMENT,
                         nombre_completo TEXT NOT NULL,
                         numero TEXT,
                         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                     )''')
            c.execute("PRAGMA table_info(clientes_temp)")
            old_columns = [col[1] for col in c.fetchall()]
            if "nombre" in old_columns and "telefono" in old_columns:
                c.execute("SELECT id, nombre, telefono FROM clientes_temp")
                rows = c.fetchall()
                for row in rows:
                    id_val, nombre, telefono = row[0], row[1], row[2]
                    c.execute("INSERT INTO clientes (id, nombre_completo, numero) VALUES (?, ?, ?)", 
                              (id_val, nombre or "", telefono or ""))
            else:
                c.execute("SELECT id FROM clientes_temp")
                rows = c.fetchall()
                for row in rows:
                    id_val = row[0]
                    c.execute("INSERT INTO clientes (id, nombre_completo, numero) VALUES (?, ?, ?)", 
                              (id_val, "Sin nombre", ""))
            c.execute("DROP TABLE clientes_temp")
            logger.info("Tabla 'clientes' migrada.")
        else:
            logger.info("Tabla 'clientes' ya tiene la estructura correcta.")
    else:
        c.execute('''CREATE TABLE clientes (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     nombre_completo TEXT NOT NULL,
                     numero TEXT,
                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                 )''')
        logger.info("Tabla 'clientes' creada.")
    
    # Crear tabla ventas
    c.execute('''CREATE TABLE IF NOT EXISTS ventas (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id TEXT,
                 id_cliente INTEGER,
                 metodo_pago TEXT,
                 fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                 total REAL,
                 items TEXT,
                 store_id INTEGER,
                 FOREIGN KEY (user_id) REFERENCES users(id),
                 FOREIGN KEY (id_cliente) REFERENCES clientes(id),
                 FOREIGN KEY (store_id) REFERENCES stores(id)
             )''')
    
    # Crear tabla apartados
    c.execute('''CREATE TABLE IF NOT EXISTS apartados (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 id_cliente INTEGER NOT NULL,
                 user_id TEXT NOT NULL,
                 productos TEXT NOT NULL,
                 anticipo REAL DEFAULT 0,
                 fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                 fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                 fecha_vencimiento TIMESTAMP NOT NULL,
                 estado TEXT DEFAULT 'activo',
                 store_id INTEGER,
                 FOREIGN KEY (id_cliente) REFERENCES clientes(id),
                 FOREIGN KEY (user_id) REFERENCES users(id),
                 FOREIGN KEY (store_id) REFERENCES stores(id)
             )''')
    
    # Crear tabla anticipos
    c.execute('''CREATE TABLE IF NOT EXISTS anticipos (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 apartado_id INTEGER NOT NULL,
                 monto REAL NOT NULL,
                 fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                 store_id INTEGER,
                 FOREIGN KEY (apartado_id) REFERENCES apartados(id),
                 FOREIGN KEY (store_id) REFERENCES stores(id)
             )''')
    
    # Crear tabla reembolsos
    c.execute('''CREATE TABLE IF NOT EXISTS reembolsos (
                 id_reembolso INTEGER PRIMARY KEY AUTOINCREMENT,
                 id_apartado INTEGER NOT NULL,
                 monto REAL NOT NULL,
                 fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                 user_id TEXT NOT NULL,
                 store_id INTEGER,
                 FOREIGN KEY (id_apartado) REFERENCES apartados(id),
                 FOREIGN KEY (user_id) REFERENCES users(id),
                 FOREIGN KEY (store_id) REFERENCES stores(id)
             )''')
    
    # Crear índices
    logger.info("Creando índices...")
    c.execute("CREATE INDEX IF NOT EXISTS idx_sku ON productos(sku)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_nombre ON productos(nombre)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_escuela ON productos(escuela)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_nivel_educativo ON productos(nivel_educativo)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_color ON productos(color)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_tipo_prenda ON productos(tipo_prenda)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_tipo_pieza ON productos(tipo_pieza)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_genero ON productos(genero)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_atributo ON productos(atributo)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_marca ON productos(marca)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_talla ON productos(talla)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_store_id_productos ON productos(store_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON ventas(user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_id_cliente ON ventas(id_cliente)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_store_id_ventas ON ventas(store_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_id ON clientes(id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_clientes_nombre_completo ON clientes(nombre_completo)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_clientes_numero ON clientes(numero)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_id_apartado ON reembolsos(id_apartado)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_store_id_apartados ON apartados(store_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_store_id_anticipos ON anticipos(store_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_store_id_reembolsos ON reembolsos(store_id)")

    conn.commit()
    conn.close()
    logger.info(f"Base de datos inicializada en {db_path} con índices creados.")
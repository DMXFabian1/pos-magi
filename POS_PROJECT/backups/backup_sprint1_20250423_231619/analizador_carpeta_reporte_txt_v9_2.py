import ast
import os
from collections import defaultdict
from datetime import datetime
import logging
import re
from difflib import SequenceMatcher
import json
import time
import shutil

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler('analizador.log'),
        logging.StreamHandler()
    ]
)

class AnalizadorCodigo:
    def __init__(self):
        self.funciones = {}
        self.grafo_llamadas = defaultdict(list)
        self.problemas = []
        self.importaciones = defaultdict(list)
        self.funciones_eventos = set()
        self.codigo_duplicado = []
        self.variables_no_usadas = []
        self.codigo_comentado = []
        self.sin_docstrings = []
        self.archivo_actual = ""

    def analizar_archivo(self, ruta_archivo):
        """Analiza un archivo Python y extrae métricas avanzadas."""
        start_time = time.time()
        self.archivo_actual = ruta_archivo
        logging.debug(f"Analizando: {ruta_archivo}")
        try:
            with open(ruta_archivo, 'r', encoding='utf-8-sig') as archivo:
                codigo = archivo.read()
                lineas = codigo.splitlines()

            # Detectar código comentado
            self._detectar_codigo_comentado(lineas, ruta_archivo)

            # Parsear código
            arbol = ast.parse(codigo, filename=ruta_archivo)

            # Extraer importaciones
            for nodo in ast.walk(arbol):
                if isinstance(nodo, ast.Import):
                    for alias in nodo.names:
                        self.importaciones[ruta_archivo].append(alias.name)
                elif isinstance(nodo, ast.ImportFrom):
                    for alias in nodo.names:
                        self.importaciones[ruta_archivo].append(f"{nodo.module}.{alias.name}")

                # Extraer funciones
                if isinstance(nodo, ast.FunctionDef):
                    nombre_completo = f"{os.path.basename(ruta_archivo)}:{nodo.name}"
                    cuerpo = ast.get_source_segment(codigo, nodo) or ""
                    docstring = ast.get_docstring(nodo)
                    self.funciones[nombre_completo] = {
                        'parametros': [arg.arg for arg in nodo.args.args],
                        'linea': nodo.lineno,
                        'cuerpo': cuerpo,
                        'num_lineas': cuerpo.count('\n') + 1,
                        'complejidad': self._calcular_complejidad(nodo),
                        'docstring': bool(docstring)
                    }
                    self._analizar_llamadas(nodo, nombre_completo)
                    self._detectar_funcion_evento(nodo, nombre_completo)
                    self._analizar_variables(nodo, nombre_completo)
                    if not docstring:
                        self.sin_docstrings.append(f"Función '{nombre_completo}' (Línea {nodo.lineno}): Sin docstring.")
                    logging.debug(f"Función encontrada: {nombre_completo}")

                # Analizar consultas SQL
                if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute):
                    if nodo.func.attr in ('execute', 'executemany') and 'cursor' in str(nodo.func.value):
                        self._analizar_consulta_sql(nodo, ruta_archivo)

            elapsed_time = time.time() - start_time
            logging.info(f"Procesado {ruta_archivo} en {elapsed_time:.2f} segundos")

        except SyntaxError as e:
            self.problemas.append(f"Error de sintaxis en {ruta_archivo}: {e}")
            logging.error(f"Sintaxis error en {ruta_archivo}: {e}")
        except UnicodeDecodeError as e:
            self.problemas.append(f"Error de codificación en {ruta_archivo}: {e}")
            logging.error(f"Codificación error en {ruta_archivo}: {e}")
        except Exception as e:
            self.problemas.append(f"Error al procesar {ruta_archivo}: {e}")
            logging.error(f"Error general en {ruta_archivo}: {e}")

    def _calcular_complejidad(self, nodo):
        """Calcula la complejidad ciclomatica incluyendo operadores lógicos."""
        complejidad = 1
        for hijo in ast.walk(nodo):
            if isinstance(hijo, (ast.If, ast.For, ast.While, ast.Try, ast.With)):
                complejidad += 1
            elif isinstance(hijo, ast.BoolOp):
                complejidad += len(hijo.values) - 1
        return complejidad

    def _analizar_llamadas(self, nodo, funcion_padre):
        """Identifica llamadas a funciones."""
        for hijo in ast.walk(nodo):
            if isinstance(hijo, ast.Call):
                if isinstance(hijo.func, ast.Name):
                    funcion_llamada = hijo.func.id
                    for nombre_completo in self.funciones:
                        if nombre_completo.endswith(f":{funcion_llamada}"):
                            self.grafo_llamadas[funcion_padre].append(nombre_completo)
                elif isinstance(hijo.func, ast.Attribute):
                    if isinstance(hijo.func.value, ast.Name) and hijo.func.value.id == 'self':
                        funcion_llamada = hijo.func.attr
                        for nombre_completo in self.funciones:
                            if nombre_completo.endswith(f":{funcion_llamada}"):
                                self.grafo_llamadas[funcion_padre].append(nombre_completo)

    def _detectar_funcion_evento(self, nodo, nombre_completo):
        """Detecta manejadores de eventos UI."""
        if re.match(r"(on_|handle_|_handle_|mostrar_|actualizar_|setup_|abrir_)", nodo.name, re.IGNORECASE):
            self.funciones_eventos.add(nombre_completo)
        for hijo in ast.walk(nodo):
            if isinstance(hijo, ast.Call) and isinstance(hijo.func, ast.Attribute):
                if hijo.func.attr in ('bind', 'configure', 'command'):
                    self.funciones_eventos.add(nombre_completo)

    def _analizar_variables(self, nodo, nombre_completo):
        """Detecta variables no usadas en una función."""
        variables_declaradas = set()
        variables_usadas = set()
        for hijo in ast.walk(nodo):
            if isinstance(hijo, ast.Assign):
                for target in hijo.targets:
                    if isinstance(target, ast.Name):
                        variables_declaradas.add(target.id)
            elif isinstance(hijo, ast.Name):
                if isinstance(hijo.ctx, (ast.Load, ast.Store)):
                    variables_usadas.add(hijo.id)
        no_usadas = variables_declaradas - variables_usadas
        for var in no_usadas:
            self.variables_no_usadas.append(f"Variable no usada '{var}' en '{nombre_completo}' (Línea {nodo.lineno}).")

    def _detectar_codigo_comentado(self, lineas, ruta_archivo):
        """Detecta bloques de código comentado."""
        comentario_bloque = False
        bloque = []
        for i, linea in enumerate(lineas, 1):
            linea = linea.strip()
            logging.debug(f"Procesando línea {i} en {ruta_archivo}: {linea}")
            if linea.startswith('"""') or linea.startswith("'''"):
                comentario_bloque = not comentario_bloque
                logging.debug(f"Cambio de estado comentario_bloque a {comentario_bloque}")
                continue
            if comentario_bloque or linea.startswith('#'):
                if linea.startswith('#') and any(c in linea for c in 'def class if for while'):
                    bloque.append(f"Línea {i}: {linea}")
            else:
                if bloque:
                    self.codigo_comentado.append(f"Código comentado en {ruta_archivo}: {bloque}")
                    bloque = []
        if bloque:
            self.codigo_comentado.append(f"Código comentado en {ruta_archivo}: {bloque}")

    def _analizar_consulta_sql(self, nodo, ruta_archivo):
        """Analiza consultas SQL para detectar ineficiencias."""
        if nodo.args and isinstance(nodo.args[0], ast.Str):
            query = nodo.args[0].s.strip().lower()
            if 'select' in query and 'where' not in query:
                self.problemas.append(f"Consulta SQL potencialmente ineficiente en {ruta_archivo} (Línea {nodo.lineno}): SELECT sin WHERE.")
            parent = nodo
            while hasattr(parent, 'parent'):
                if isinstance(parent, ast.For):
                    self.problemas.append(f"Consulta SQL en bucle en {ruta_archivo} (Línea {nodo.lineno}): Puede ser optimizada con una sola consulta.")
                    break
                parent = parent.parent

    def detectar_problemas(self):
        """Detecta problemas de optimización y modularidad."""
        logging.debug("Detectando problemas...")
        try:
            for nombre, detalles in self.funciones.items():
                cuerpo = detalles['cuerpo']
                if detalles['num_lineas'] > 20:
                    self.problemas.append(
                        f"Función '{nombre}' (Línea {detalles['linea']}): Es demasiado larga "
                        f"({detalles['num_lineas']} líneas). Divide en funciones más pequeñas."
                    )
                if len(detalles['parametros']) > 5:
                    self.problemas.append(
                        f"Función '{nombre}' (Línea {detalles['linea']}): Tiene demasiados parámetros "
                        f"({len(detalles['parametros'])}). Usa un objeto o diccionario."
                    )
                if detalles['complejidad'] > 10:
                    self.problemas.append(
                        f"Función '{nombre}' (Línea {detalles['linea']}): Alta complejidad "
                        f"(índice {detalles['complejidad']}). Simplifica la lógica."
                    )
                if "for " in cuerpo and "for " in cuerpo[cuerpo.index("for ") + 1:]:
                    self.problemas.append(
                        f"Función '{nombre}' (Línea {detalles['linea']}): Posible bucle anidado "
                        "ineficiente. Usa estructuras como diccionarios o listas por comprensión."
                    )

            for archivo, imports in self.importaciones.items():
                for imp in imports:
                    imp_name = imp.split('.')[-1]
                    used = any(imp_name in detalles['cuerpo'] for detalles in self.funciones.values())
                    if not used:
                        self.problemas.append(f"Importación no utilizada en {archivo}: {imp}")
        except Exception as e:
            logging.error(f"Error en detectar_problemas: {e}")
            self.problemas.append(f"Error al detectar problemas: {e}")

    def detectar_codigo_duplicado(self):
        """Identifica funciones con código similar (solo para funciones > 20 líneas)."""
        logging.debug("Detectando código duplicado...")
        try:
            cuerpos = [(nombre, detalles['cuerpo']) for nombre, detalles in self.funciones.items() if detalles['num_lineas'] > 20]
            for i, (nombre1, cuerpo1) in enumerate(cuerpos):
                for nombre2, cuerpo2 in cuerpos[i + 1:]:
                    if cuerpo1 and cuerpo2:
                        similarity = SequenceMatcher(None, cuerpo1, cuerpo2).ratio()
                        if similarity > 0.8:
                            self.codigo_duplicado.append(
                                f"Posible código duplicado entre '{nombre1}' y '{nombre2}' "
                                f"(similitud: {similarity:.2f}). Consolidar en una función común."
                            )
        except Exception as e:
            logging.error(f"Error en detectar_codigo_duplicado: {e}")
            self.problemas.append(f"Error al detectar código duplicado: {e}")

    def sugerir_mejoras(self):
        """Genera sugerencias para mejorar el código."""
        logging.debug("Generando sugerencias...")
        try:
            sugerencias = []
            for nombre, llamadas in self.grafo_llamadas.items():
                if len(llamadas) > 3:
                    sugerencias.append(
                        f"Función '{nombre}': Llama a muchas funciones ({len(llamadas)}). "
                        "Agrupa operaciones en una función intermedia."
                    )

            for nombre in self.funciones:
                if (nombre not in [llamada for llamadas in self.grafo_llamadas.values() for llamada in llamadas] and
                    nombre not in self.funciones_eventos):
                    sugerencias.append(
                        f"Función '{nombre}': No parece ser llamada ni vinculada a eventos. "
                        "Verifica si es necesaria o está obsoleta."
                    )

            sugerencias.extend(self.codigo_duplicado)
            sugerencias.extend(self.variables_no_usadas)
            sugerencias.extend(self.sin_docstrings)
            sugerencias.extend(self.codigo_comentado)
            return sugerencias
        except Exception as e:
            logging.error(f"Error en sugerir_mejoras: {e}")
            return [f"Error al generar sugerencias: {e}"]

    def generar_reporte_basico(self):
        """Genera un reporte básico si el avanzado falla."""
        logging.debug("Generando reporte básico...")
        try:
            reporte = [
                "=== Análisis Básico de Código ===",
                f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"Total de funciones analizadas: {len(self.funciones)}",
                f"Total de archivos procesados: {len(set([nombre.split(':')[0] for nombre in self.funciones]))}",
                "\n== Archivos Analizados =="
            ]
            archivos = sorted(set(nombre.split(':')[0] for nombre in self.funciones))
            for archivo in archivos:
                reporte.append(f"- {archivo}")
            return "\n".join(reporte)
        except Exception as e:
            logging.error(f"Error al generar reporte básico: {e}")
            return f"Error: No se pudo generar el reporte. Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    def generar_reporte(self):
        """Genera un reporte detallado en formato texto."""
        logging.debug("Iniciando generación de reporte TXT...")
        try:
            reporte = [
                "=== Análisis de Código en Carpeta ===",
                f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"Total de funciones analizadas: {len(self.funciones)}",
                f"Total de archivos procesados: {len(set([nombre.split(':')[0] for nombre in self.funciones]))}",
            ]

            # Funciones encontradas
            logging.debug("Generando sección de funciones encontradas...")
            reporte.append("\n== Funciones Encontradas ==")
            archivos = sorted(set(nombre.split(':')[0] for nombre in self.funciones))
            for archivo in archivos:
                reporte.append(f"\nArchivo: {archivo}")
                for nombre, detalles in sorted(self.funciones.items()):
                    if nombre.startswith(archivo + ':'):
                        reporte.append(f"- {nombre} (Línea {detalles['linea']}):")
                        reporte.append(f"  Parámetros: {detalles['parametros']}")
                        reporte.append(f"  Líneas: {detalles['num_lineas']}")
                        reporte.append(f"  Complejidad: {detalles['complejidad']}")
                        reporte.append(f"  Documentada: {'Sí' if detalles['docstring'] else 'No'}")
                        reporte.append(f"  Llama a: {self.grafo_llamadas[nombre] or 'Ninguna'}")
                        if nombre in self.funciones_eventos:
                            reporte.append("  Nota: Posible manejador de evento UI")

            # Importaciones
            logging.debug("Generando sección de importaciones...")
            reporte.append("\n== Importaciones Detectadas ==")
            for archivo, imports in sorted(self.importaciones.items()):
                reporte.append(f"Archivo: {archivo}")
                reporte.append(f"  Importaciones: {', '.join(sorted(imports)) or 'Ninguna'}")

            # Problemas
            logging.debug("Generando sección de problemas...")
            reporte.append("\n== Problemas Detectados ==")
            if self.problemas:
                for problema in sorted(self.problemas):
                    reporte.append(f"- {problema}")
            else:
                reporte.append("- Ninguno")

            # Sugerencias
            logging.debug("Generando sección de sugerencias...")
            reporte.append("\n== Sugerencias de Mejora ==")
            sugerencias = self.sugerir_mejoras()
            if sugerencias:
                for sugerencia in sorted(sugerencias):
                    reporte.append(f"- {sugerencia}")
            else:
                reporte.append("- Ninguna")

            logging.debug("Reporte TXT generado exitosamente.")
            return "\n".join(reporte)
        except Exception as e:
            logging.error(f"Error al generar reporte TXT: {e}")
            return self.generar_reporte_basico()

    def generar_reporte_json(self):
        """Genera un reporte en formato JSON."""
        logging.debug("Iniciando generación de reporte JSON...")
        try:
            reporte = {
                "fecha": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "total_funciones": len(self.funciones),
                "total_archivos": len(set([nombre.split(':')[0] for nombre in self.funciones])),
                "funciones": {},
                "importaciones": dict(self.importaciones),
                "problemas": self.problemas,
                "sugerencias": self.sugerir_mejoras()
            }
            for nombre, detalles in self.funciones.items():
                reporte["funciones"][nombre] = {
                    "parametros": detalles["parametros"],
                    "linea": detalles["linea"],
                    "num_lineas": detalles["num_lineas"],
                    "complejidad": detalles["complejidad"],
                    "docstring": detalles["docstring"],
                    "llama_a": self.grafo_llamadas[nombre],
                    "es_evento_ui": nombre in self.funciones_eventos
                }
            logging.debug("Reporte JSON generado exitosamente.")
            return json.dumps(reporte, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Error al generar reporte JSON: {e}")
            return json.dumps({"error": "No se pudo generar el reporte JSON", "fecha": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}, indent=2)

def analizar_carpeta(ruta_carpeta, ruta_respaldo=None, filtro_archivos=None, filtro_subcarpeta=None, excluir_archivos=None):
    """Analiza archivos Python y genera reportes en TXT y JSON."""
    logging.debug(f"Verificando carpeta: {ruta_carpeta}")
    if not os.path.exists(ruta_carpeta):
        logging.error(f"La carpeta {ruta_carpeta} no existe.")
        return "Error: La carpeta no existe."

    # Verificar espacio en disco
    try:
        disk_usage = shutil.disk_usage(ruta_carpeta)
        if disk_usage.free < 10 * 1024 * 1024:  # Menos de 10 MB
            logging.error(f"Espacio en disco insuficiente en {ruta_carpeta}: {disk_usage.free / (1024*1024):.2f} MB libres")
            return "Error: Espacio en disco insuficiente."
    except Exception as e:
        logging.error(f"Error al verificar espacio en disco: {e}")

    # Verificar permisos de escritura
    try:
        test_file = os.path.join(ruta_carpeta, "test_write.txt")
        with open(test_file, 'w') as f:
            f.write("Test")
        os.remove(test_file)
        logging.debug("Permisos de escritura verificados en carpeta principal.")
    except PermissionError as e:
        logging.error(f"Sin permisos de escritura en {ruta_carpeta}: {e}")
        if not ruta_respaldo:
            return f"Error: Sin permisos de escritura en {ruta_carpeta}"
        ruta_carpeta = ruta_respaldo

    # Verificar ruta de respaldo
    if ruta_respaldo and not os.path.exists(ruta_respaldo):
        try:
            os.makedirs(ruta_respaldo)
            logging.debug(f"Creada carpeta de respaldo: {ruta_respaldo}")
        except Exception as e:
            logging.error(f"No se pudo crear carpeta de respaldo {ruta_respaldo}: {e}")
            return f"Error: No se pudo crear carpeta de respaldo {ruta_respaldo}"

    analizador = AnalizadorCodigo()
    archivos_procesados = 0
    for raiz, _, archivos in os.walk(ruta_carpeta):
        if filtro_subcarpeta and not raiz.startswith(os.path.join(ruta_carpeta, filtro_subcarpeta)):
            continue
        for archivo in archivos:
            if archivo.endswith('.py'):
                if filtro_archivos and archivo not in filtro_archivos:
                    continue
                if excluir_archivos and archivo in excluir_archivos:
                    continue
                ruta_completa = os.path.join(raiz, archivo)
                logging.info(f"Procesando: {ruta_completa}")
                analizador.analizar_archivo(ruta_completa)
                archivos_procesados += 1

    if archivos_procesados == 0:
        logging.warning("No se encontraron archivos Python.")
        return "Error: No se encontraron archivos Python."

    logging.debug("Analizando problemas y duplicados...")
    analizador.detectar_problemas()
    analizador.detectar_codigo_duplicado()

    # Generar reportes
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_reporte_txt = f"reporte_analisis_{timestamp}.txt"
    nombre_reporte_json = f"reporte_analisis_{timestamp}.json"
    rutas_reportes = [
        (nombre_reporte_txt, analizador.generar_reporte, ruta_carpeta),
        (nombre_reporte_json, analizador.generar_reporte_json, ruta_carpeta)
    ]

    if ruta_respaldo:
        rutas_reportes.extend([
            (nombre_reporte_txt, analizador.generar_reporte, ruta_respaldo),
            (nombre_reporte_json, analizador.generar_reporte_json, ruta_respaldo)
        ])

    resultados = []
    for nombre, generador, ruta in rutas_reportes:
        ruta_completa = os.path.join(ruta, nombre)
        logging.debug(f"Intentando guardar {ruta_completa}")
        try:
            # Verificar permisos específicos para este archivo
            test_file = os.path.join(ruta, f"test_{nombre}")
            with open(test_file, 'w') as f:
                f.write("Test")
            os.remove(test_file)
            logging.debug(f"Permisos de escritura verificados para {ruta_completa}")

            with open(ruta_completa, 'w', encoding='utf-8') as archivo_reporte:
                archivo_reporte.write(generador())
            logging.info(f"Reporte guardado en: {ruta_completa}")
            resultados.append(f"Reporte guardado en: {ruta_completa}")
        except PermissionError as e:
            logging.error(f"Error de permisos al escribir {ruta_completa}: {e}")
        except OSError as e:
            logging.error(f"Error de sistema al escribir {ruta_completa}: {e}")
        except Exception as e:
            logging.error(f"Error inesperado al escribir {ruta_completa}: {e}")

    if resultados:
        return "\n".join(resultados)
    return "Error: No se pudieron generar los reportes. Revisa analizador.log."

if __name__ == "__main__":
    RUTA_CARPETA = r"C:\Users\Daniel\Documents\Versions\EXODIA\POS_PROJECT"
    RUTA_RESPALDO = r"C:\Users\Daniel\Documents\Versions\EXODIA"
    FILTRO_ARCHIVOS = ['pos_ventas.py', 'apartados_manager.py', 'product_manager_ui.py', 'db_manager.py']
    FILTRO_SUBCARPETA = None
    EXCLUIR_ARCHIVOS = ['__init__.py']
    print(analizar_carpeta(RUTA_CARPETA, RUTA_RESPALDO, FILTRO_ARCHIVOS, FILTRO_SUBCARPETA, EXCLUIR_ARCHIVOS))
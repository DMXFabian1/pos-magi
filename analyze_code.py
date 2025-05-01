import os
import ast
import re
from collections import Counter, defaultdict
import logging
from datetime import datetime
import networkx as nx
from pyvis.network import Network

# Configurar logging
logging.basicConfig(filename="code_analysis_report.txt", level=logging.INFO, format="%(message)s")
logger = logging.getLogger()

class CodeAnalyzer:
    def __init__(self, project_path):
        self.project_path = project_path
        self.files = []
        self.total_lines = 0
        self.functions = []
        self.classes = []
        self.try_except_count = 0
        self.logging_count = 0
        self.imports = Counter()
        self.dependencies = defaultdict(set)
        self.repeated_code = []
        self.long_functions = []
        self.comments_count = 0
        self.folder_map = []
        self.docstrings = []
        self.sql_queries = []
        self.hardcoded_values = []
        self.performance_issues = []
        self.requirements = set()
        self.customtkinter_usage = []
        self.pyinstaller_issues = []

    def analyze(self):
        """Analiza el proyecto y genera mapas, dependencias, documentación y plan de refactorización."""
        logger.info("Analizando proyecto POS MAGI...\n")
        self._collect_files()
        self._map_folder_structure()
        self._analyze_files()
        self._generate_report()
        self._generate_documentation()
        self._generate_refactor_plan()
        self._generate_interactive_graph()

    def _collect_files(self):
        """Recolecta todos los archivos .py en la carpeta, excluyendo backups."""
        for root, _, files in os.walk(self.project_path):
            if "backups" in root.split(os.sep):  # Excluir carpetas de backups
                continue
            for file in files:
                if file.endswith(".py"):
                    self.files.append(os.path.join(root, file))

    def _map_folder_structure(self):
        """Genera un mapa de la estructura de carpetas."""
        logger.info("Mapeando estructura de carpetas...")
        for root, dirs, files in os.walk(self.project_path):
            if "backups" in root.split(os.sep):  # Excluir backups
                continue
            level = root.replace(self.project_path, "").count(os.sep)
            indent = "  " * level
            self.folder_map.append(f"{indent}{os.path.basename(root)}/")
            for file in files:
                if file.endswith(".py"):
                    self.folder_map.append(f"{indent}  {file}")

    def _analyze_files(self):
        """Analiza cada archivo .py."""
        for file_path in self.files:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.total_lines += len(content.splitlines())
                self._analyze_file_content(file_path, content)

    def _analyze_file_content(self, file_path, content):
        """Analiza el contenido de un archivo."""
        relative_path = os.path.relpath(file_path, self.project_path)
        
        # Contar comentarios
        self.comments_count += len(re.findall(r"#.*", content)) + len(re.findall(r'"""[\s\S]*?"""', content))

        # Detectar consultas SQL
        sql_pattern = r"\.execute\s*\(\s*['\"](SELECT|INSERT|UPDATE|DELETE)[^'\"]*['\"]"
        self.sql_queries.extend((relative_path, m) for m in re.findall(sql_pattern, content))

        # Detectar valores hardcoded
        hardcoded_pattern = r"['\"](https?://[^'\"]+|/[^\s'\"]+|C:\\[^'\"]+|[A-Z0-9]{20,})['\"]"
        self.hardcoded_values.extend((relative_path, m) for m in re.findall(hardcoded_pattern, content))

        # Detectar uso de customtkinter
        if "customtkinter" in content or "ctk" in content:
            self.customtkinter_usage.append(relative_path)

        # Detectar posibles problemas con PyInstaller
        if any(lib in content for lib in ["customtkinter", "twilio", "requests"]):
            self.pyinstaller_issues.append((relative_path, "Asegúrate de incluir esta dependencia en PyInstaller con --add-data"))

        # Parsear el árbol AST
        try:
            tree = ast.parse(content)
        except SyntaxError:
            logger.warning(f"SyntaxError en {file_path}. Verifica la sintaxis.")
            return

        # Analizar nodos
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                lines = ast.unparse(node).count("\n")
                self.functions.append((relative_path, node.name, node.lineno, lines))
                if lines > 50:
                    self.long_functions.append((relative_path, node.name, node.lineno))
                if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
                    self.docstrings.append((relative_path, node.name, node.body[0].value.value))
                nested_loops = sum(1 for n in ast.walk(node) if isinstance(n, ast.For) or isinstance(n, ast.While))
                if nested_loops > 2:
                    self.performance_issues.append((relative_path, node.name, node.lineno, "Bucles anidados"))
            elif isinstance(node, ast.ClassDef):
                self.classes.append((relative_path, node.name, node.lineno))
                if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
                    self.docstrings.append((relative_path, node.name, node.body[0].value.value))
            elif isinstance(node, ast.Try):
                self.try_except_count += 1
            elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                for n in node.names:
                    self.imports[n.name] += 1
                    self.requirements.add(n.name)
                    if isinstance(node, ast.ImportFrom) and node.module:
                        for file in self.files:
                            if node.module in os.path.basename(file).replace(".py", ""):
                                self.dependencies[relative_path].add(os.path.relpath(file, self.project_path))

        # Buscar logging
        if "logging" in content or "logger" in content:
            self.logging_count += 1

        # Buscar código repetitivo
        lines = content.splitlines()
        for i in range(len(lines) - 2):
            block = "\n".join(lines[i:i+3])
            if block in content[i+3:]:
                self.repeated_code.append((relative_path, block, i+1))

    def _detect_circular_dependencies(self):
        """Detecta dependencias circulares."""
        circular = []
        for file1 in self.dependencies:
            for file2 in self.dependencies[file1]:
                if file1 in self.dependencies.get(file2, set()):
                    circular.append((file1, file2))
        return circular

    def _generate_dependency_graph(self):
        """Genera un grafo de dependencias en formato texto."""
        graph = ["Grafo de dependencias:"]
        for file, deps in self.dependencies.items():
            graph.append(f"{file} -> {', '.join(deps) or '(ninguna dependencia)'}")
        return "\n".join(graph)

    def _generate_interactive_graph(self):
        """Genera un grafo interactivo con networkx y pyvis."""
        try:
            G = nx.DiGraph()
            for file in self.files:
                relative_path = os.path.relpath(file, self.project_path)
                G.add_node(relative_path)
            for file, deps in self.dependencies.items():
                for dep in deps:
                    G.add_edge(file, dep)
            
            net = Network(height="600px", width="100%", directed=True)
            net.from_nx(G)
            net.save_graph(os.path.join(self.project_path, "dependencies.html"))
            logger.info("Grafo interactivo generado en dependencies.html")
        except ImportError:
            logger.warning("networkx o pyvis no están instalados. Instala con `pip install networkx pyvis`.")

    def _generate_report(self):
        """Genera un informe con puntos de mejora."""
        logger.info("=" * 50)
        logger.info("Informe de Análisis de Código - POS MAGI")
        logger.info("=" * 50)

        # Mapa de la carpeta
        logger.info("\nMapa de la carpeta:")
        for line in self.folder_map:
            logger.info(line)

        # Resumen
        logger.info(f"\nResumen:")
        logger.info(f"Archivos .py encontrados: {len(self.files)}")
        logger.info(f"Líneas totales de código: {self.total_lines}")
        logger.info(f"Clases definidas: {len(self.classes)}")
        logger.info(f"Funciones definidas: {len(self.functions)}")
        logger.info(f"Bloques try-except: {self.try_except_count}")
        logger.info(f"Archivos con logging: {self.logging_count}")
        logger.info(f"Comentarios detectados: {self.comments_count}")
        logger.info(f"Docstrings detectados: {len(self.docstrings)}")
        logger.info(f"Consultas SQL detectadas: {len(self.sql_queries)}")
        logger.info(f"Valores hardcoded detectados: {len(self.hardcoded_values)}")
        logger.info(f"Posibles problemas de rendimiento: {len(self.performance_issues)}")
        logger.info(f"Archivos con customtkinter: {len(self.customtkinter_usage)}")

        # Grafo de dependencias
        logger.info("\n" + self._generate_dependency_graph())

        # Dependencias circulares
        circular = self._detect_circular_dependencies()
        if circular:
            logger.info("\nDependencias circulares detectadas:")
            for file1, file2 in circular:
                logger.info(f"- {file1} <-> {file2}")

        # Dependencias externas
        logger.info("\nDependencias externas detectadas:")
        external_libs = [lib for lib in self.requirements if lib not in ["os", "sys", "datetime", "sqlite3"]]
        for lib in external_libs:
            logger.info(f"- {lib}")
        if os.path.exists(os.path.join(self.project_path, "requirements.txt")):
            with open(os.path.join(self.project_path, "requirements.txt"), "r") as f:
                reqs = set(line.strip().split("==")[0] for line in f if line.strip())
            missing = [lib for lib in external_libs if lib not in reqs]
            if missing:
                logger.info(f"- [Advertencia] Dependencias no listadas en requirements.txt: {', '.join(missing)}")

        # Consultas SQL
        if self.sql_queries:
            logger.info("\nConsultas SQL detectadas:")
            for file, query in self.sql_queries[:5]:
                logger.info(f"- {file}: {query[:50]}...")
            if len(set(file for file, _ in self.sql_queries)) > 2:
                logger.info("- [Optimización] Centraliza consultas SQL en core/database.py.")

        # Valores hardcoded
        if self.hardcoded_values:
            logger.info("\nValores hardcoded detectados:")
            for file, query in self.hardcoded_values[:5]:
                logger.info(f"- {file}: {query[:50]}...")
            logger.info("- [Optimización] Mueve valores a config.py o .env.")

        # Problemas de rendimiento
        if self.performance_issues:
            logger.info("\nPosibles problemas de rendimiento:")
            for file, name, line, issue in self.performance_issues:
                logger.info(f"- {file}:{line} - Función '{name}': {issue}")
            logger.info("- [Optimización] Revisa bucles anidados y optimiza consultas SQL.")

        # Uso de customtkinter
        if self.customtkinter_usage:
            logger.info("\nArchivos con uso de customtkinter:")
            for file in self.customtkinter_usage:
                logger.info(f"- {file}")
            logger.info("- [Optimización] Asegúrate de que la interfaz sea modular (ej., ui/ventas.py, ui/productos.py).")

        # Problemas con PyInstaller
        if self.pyinstaller_issues:
            logger.info("\nPosibles problemas con PyInstaller:")
            for file, issue in self.pyinstaller_issues:
                logger.info(f"- {file}: {issue}")

        # Puntos de mejora
        logger.info("\nPuntos de mejora:")
        if len(self.files) <= 2:
            logger.info("- [Modularidad] Pocos archivos. Divide en core/database.py, ui/ventas.py, utils/updater.py.")
        if circular:
            logger.info("- [Dependencias] Elimina dependencias circulares moviendo funciones a utils/.")
        if self.try_except_count < len(self.functions) / 2:
            logger.info("- [Manejo de errores] Añade try-except en consultas SQLite, conexiones de red, y actualizaciones.")
        if self.logging_count < len(self.files) / 2:
            logger.info("- [Logging] Implementa logging para registrar ventas, errores, y actualizaciones.")
        if self.comments_count < self.total_lines / 20:
            logger.info("- [Documentación] Añade comentarios y docstrings.")
        if len(self.docstrings) < len(self.functions) / 2:
            logger.info("- [Documentación] Añade docstrings a funciones y clases.")
        if not any("store_id" in query.lower() for _, query in self.sql_queries):
            logger.info("- [Escalabilidad] Añade store_id a tablas SQLite para múltiples tiendas.")

    def _generate_documentation(self):
        """Genera documentación automática."""
        logger.info("\nGenerando documentación...")
        readme_content = [
            "# POS MAGI - Documentación",
            f"Generado automáticamente el {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "\n## Descripción",
            "POS MAGI es un sistema de punto de venta para una tienda de uniformes, diseñado para escanear productos, gestionar ventas, comisiones, recordatorios, y notificaciones por WhatsApp. Usa customtkinter para la interfaz, SQLite para la base de datos, y se distribuye como .exe.",
            "\n## Estructura de la carpeta",
        ] + self.folder_map + [
            "\n## Módulos principales",
        ]

        for file in self.files:
            relative_path = os.path.relpath(file, self.project_path)
            classes_in_file = [c for c in self.classes if c[0] == relative_path]
            functions_in_file = [f for f in self.functions if f[0] == relative_path]
            readme_content.append(f"\n### {relative_path}")
            readme_content.append(f"- **Clases**: {', '.join(c[1] for c in classes_in_file) or 'Ninguna'}")
            readme_content.append(f"- **Funciones principales**: {', '.join(f[1] for f in functions_in_file[:5]) or 'Ninguna'}")
            readme_content.append(f"- **Dependencias**: {', '.join(self.dependencies.get(relative_path, [])) or 'Ninguna'}")

        readme_content.append("\n## Docstrings")
        for file, name, doc in self.docstrings[:5]:
            readme_content.append(f"\n### {file} - {name}")
            readme_content.append(f"```{doc}```")

        readme_content.append("\n## Pruebas unitarias sugeridas")
        for file, name, _, _ in self.functions[:3]:
            readme_content.append(f"\n### Test para {file} - {name}")
            readme_content.append("```python")
            readme_content.append(f"def test_{name}():")
            readme_content.append(f"    # TODO: Implementar prueba para {name}")
            readme_content.append("    assert True")
            readme_content.append("```")

        with open(os.path.join(self.project_path, "README.md"), "w", encoding="utf-8") as f:
            f.write("\n".join(readme_content))
        logger.info("README.md generado.")

        schema = [
            "# Esquema del Sistema - POS MAGI",
            "## Componentes Principales",
            "- **Interfaz (ui/)**: Maneja la interfaz gráfica con customtkinter.",
            "- **Base de datos (core/)**: Gestiona datos con SQLite (productos, ventas, comisiones, recordatorios).",
            "- **Utilidades (utils/)**: Incluye sistema de actualizaciones, notificaciones WhatsApp, y logging.",
            "## Flujo de Trabajo",
            "1. Login: Cada empleada inicia sesión con su cuenta.",
            "2. Ventas: Escanea productos, aplica descuentos, calcula cambio.",
            "3. Comisiones: Calcula y registra comisiones automáticamente.",
            "4. Recordatorios: Gestiona tareas (pedidos, promociones).",
            "5. Actualizaciones: Verifica y descarga nuevas versiones del .exe.",
        ]
        with open(os.path.join(self.project_path, "SCHEMA.md"), "w", encoding="utf-8") as f:
            f.write("\n".join(schema))
        logger.info("SCHEMA.md generado.")

    def _generate_refactor_plan(self):
        """Genera un plan de refactorización."""
        logger.info("\nGenerando plan de refactorización...")
        refactor_tasks = []
        if len(self.files) <= 2:
            refactor_tasks.append("- Dividir el código en módulos: core/database.py, ui/ventas.py, utils/updater.py.")
        if self._detect_circular_dependencies():
            refactor_tasks.append("- Eliminar dependencias circulares moviendo funciones compartidas a utils/common.py.")
        if self.try_except_count < len(self.functions) / 2:
            refactor_tasks.append("- Añadir try-except en funciones críticas (ej., add_to_cart, finalize_sale).")
        if self.logging_count < len(self.files) / 2:
            refactor_tasks.append("- Implementar logging en todos los módulos para registrar errores y eventos.")
        if self.sql_queries and len(set(file for file, _ in self.sql_queries)) > 2:
            refactor_tasks.append("- Centralizar consultas SQL en core/database.py.")
        if self.hardcoded_values:
            refactor_tasks.append("- Mover valores hardcoded a config.py o .env.")
        if self.performance_issues:
            refactor_tasks.append("- Optimizar funciones con bucles anidados o consultas SQL pesadas.")
        if not any("store_id" in query.lower() for _, query in self.sql_queries):
            refactor_tasks.append("- Añadir store_id a tablas SQLite para soportar múltiples tiendas.")
        if self.customtkinter_usage and len(set(file for file in self.customtkinter_usage)) > 2:
            refactor_tasks.append("- Modularizar la interfaz customtkinter en ui/ventas.py, ui/productos.py, etc.")
        
        refactor_plan = [
            "# Plan de Refactorización - POS MAGI",
            f"Generado el {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"Directorio: {self.project_path}",
            "\n## Tareas Priorizadas",
        ] + [f"- {task}" for task in refactor_tasks] + [
            "\n## Pasos Siguientes",
            "- Crear rama Git (git checkout -b refactor).",
            "- Ejecutar pruebas manuales tras cada cambio.",
            "- Empaquetar y probar .exe con PyInstaller.",
            "- Implementar sistema de actualizaciones tras refactorización.",
            "- Usar el módulo de recordatorios para seguir estas tareas."
        ]

        with open(os.path.join(self.project_path, "REFACTOR.md"), "w", encoding="utf-8") as f:
            f.write("\n".join(refactor_plan))
        logger.info("REFACTOR.md generado.")

def main():
    project_path = r"C:\Users\Daniel\Documents\Versions\Exodia 8\\Exidia 7\\POS_MAGI"
    if not os.path.isdir(project_path):
        logger.error("Ruta inválida. Por favor, verifica la carpeta.")
        return
    analyzer = CodeAnalyzer(project_path)
    analyzer.analyze()

if __name__ == "__main__":
    main()

import os
from pathlib import Path

# Estructura esperada del proyecto
EXPECTED_STRUCTURE = {
    "assets/": ["icons/"],
    "assets/icons/": ["delete_icon.png", "duplicate_icon.png", "edit_icon.png", "price_icon.png", "print_icon.png"],
    "config/": ["config.json"],
    "src/": ["main.py"],
    "src/core/": ["config/", "utils/", "backup/"],
    "src/core/config/": ["__init__.py", "config.py", "controller.py", "db_manager.py", "db_setup.py"],
    "src/core/utils/": ["__init__.py", "toolstips.py", "utils.py"],
    "src/core/backup/": ["__init__.py", "backup_manager.py"],
    "src/modules/": ["inventory/", "products/", "sales/", "reports/", "clients/", "users/", "auth/", "maintenance/"],
    "src/modules/inventory/": ["__init__.py", "inventory_manager.py", "entradas_salidas_logic.py", "entradas_salidas_manager.py"],
    "src/modules/products/": ["__init__.py", "product_manager.py", "product_manager_logic.py", "product_manager_ui.py"],
    "src/modules/sales/": ["__init__.py", "pos_ventas.py", "apartados/", "presupuestos/"],
    "src/modules/sales/apartados/": ["__init__.py", "apartados_logic.py", "apartados_manager.py", "apartados_creation_window.py"],
    "src/modules/sales/presupuestos/": ["__init__.py", "presupuestos_app.py", "presupuestos_manager.py"],
    "src/modules/reports/": ["__init__.py", "reports_logic.py", "reports_manager.py"],
    "src/modules/clients/": ["__init__.py", "client_manager.py"],
    "src/modules/users/": ["__init__.py", "users_manager.py"],
    "src/modules/auth/": ["__init__.py", "auth_manager.py"],
    "src/modules/maintenance/": ["__init__.py", "maintenance.py"],
    "src/ui/": ["__init__.py", "ui_components.py", "generador_codigos.py", "qr_generator.py", "navigation_manager.py"],
}

# Importaciones esperadas en generador_codigos.py
EXPECTED_IMPORTS = {
    "from src.core.config.config import CONFIG, exportar_configuraciones": False,
    "from src.core.config.controller import Controller": False,
    "from src.modules.products.product_manager_window import abrir_gestion_productos": False,
    "from src.modules.maintenance.maintenance import abrir_mantenimiento": False,
    "from src.core.utils.tooltips import ToolTip": False,
    "from src.ui.ui_components import create_field, validate_string, validate_numeric_entry": False,
    "from src.core.utils.utils import validate_path, check_disk_space": False,
    "from src.core.config.db_manager import DatabaseManager": False,
}

def check_structure():
    print("=== Revisando estructura de carpetas y archivos ===")
    all_correct = True
    for folder, expected_contents in EXPECTED_STRUCTURE.items():
        folder_path = Path(folder)
        # Verificar si la carpeta existe
        if not folder_path.exists():
            print(f"❌ Carpeta no encontrada: {folder}")
            all_correct = False
            continue
        print(f"✔ Carpeta encontrada: {folder}")

        # Verificar los contenidos de la carpeta
        for content in expected_contents:
            content_path = folder_path / content
            if content.endswith("/"):
                # Es una subcarpeta
                if not content_path.exists():
                    print(f"❌ Subcarpeta no encontrada: {content_path}")
                    all_correct = False
            else:
                # Es un archivo
                if not content_path.exists():
                    print(f"❌ Archivo no encontrado: {content_path}")
                    all_correct = False
                else:
                    print(f"✔ Archivo encontrado: {content_path}")

    if all_correct:
        print("✔ Estructura de carpetas y archivos correcta.")
    else:
        print("❌ Hay errores en la estructura de carpetas y archivos.")
    return all_correct

def check_imports(file_path, expected_imports):
    print(f"\n=== Revisando importaciones en {file_path} ===")
    all_imports_correct = True
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        for expected_import, found in expected_imports.items():
            if expected_import in content:
                expected_imports[expected_import] = True
                print(f"✔ Importación encontrada: {expected_import}")
            else:
                print(f"❌ Importación no encontrada: {expected_import}")
                all_imports_correct = False

        # Verificar si hay importaciones antiguas que no deberían estar
        old_imports = [
            "from config import CONFIG, exportar_configuraciones",
            "from controller import Controller",
            "from product_manager_window import abrir_gestion_productos",
            "from maintenance import abrir_mantenimiento",
            "from utils.tooltips import ToolTip",
            "from ui_components import create_field, validate_string, validate_numeric_entry",
            "from utils.utils import validate_path, check_disk_space",
            "from db_manager import DatabaseManager",
        ]
        for old_import in old_imports:
            if old_import in content:
                print(f"❌ Importación antigua encontrada (debe actualizarse): {old_import}")
                all_imports_correct = False

        if all_imports_correct:
            print(f"✔ Todas las importaciones en {file_path} están correctas.")
        else:
            print(f"❌ Hay errores en las importaciones de {file_path}.")
        return all_imports_correct

    except FileNotFoundError:
        print(f"❌ Archivo no encontrado: {file_path}")
        return False
    except Exception as e:
        print(f"❌ Error al revisar importaciones en {file_path}: {str(e)}")
        return False

def main():
    # Revisar estructura de carpetas
    structure_correct = check_structure()

    # Revisar importaciones en generador_codigos.py
    generador_codigos_path = Path("src/ui/generador_codigos.py")
    imports_correct = check_imports(generador_codigos_path, EXPECTED_IMPORTS)

    # Resumen
    print("\n=== Resumen ===")
    if structure_correct and imports_correct:
        print("✔ Todo está en orden para generador_codigos.py. Puedes continuar con el siguiente archivo.")
    else:
        print("❌ Hay errores que deben corregirse antes de continuar.")

if __name__ == "__main__":
    main()
# POS EXODIA - Documentación
Generado automáticamente el 2025-04-30 19:16

## Descripción
POS EXODIA es un sistema de punto de venta para una tienda de uniformes, diseñado para escanear productos, gestionar ventas, comisiones, recordatorios, y notificaciones por WhatsApp. Usa customtkinter para la interfaz, SQLite para la base de datos, y se distribuye como .exe.

## Estructura de la carpeta
EXODIA/
  analyze_code.py
  POS_PROJECT/
    assets/
      icons/
    config/
    src/
      main.py
      __init__.py
      core/
        backup/
          backup_manager.py
          __init__.py
          __pycache__/
        config/
          config.py
          controller.py
          db_manager.py
          db_setup.py
          __init__.py
          __pycache__/
        utils/
          tooltips.py
          utils.py
          __init__.py
          __pycache__/
      icons/
      modules/
        auth/
          auth_manager.py
          __init__.py
          __pycache__/
        clients/
          client_manager.py
          __init__.py
          __pycache__/
        inventory/
          entradas_salidas_logic.py
          entradas_salidas_manager.py
          inventory_manager.py
          __init__.py
          __pycache__/
        maintenance/
          maintenance.py
          __init__.py
          __pycache__/
        products/
          product_manager.py
          product_manager_logic.py
          product_manager_ui.py
          product_manager_window.py
          __init__.py
          __pycache__/
        reports/
          reports_logic.py
          reports_manager.py
          __init__.py
          __pycache__/
        sales/
          pos_ventas.py
          __init__.py
          apartados/
            apartados_actions.py
            apartados_creation_window.py
            apartados_data.py
            apartados_logic.py
            apartados_manager.py
            apartados_tab.py
            apartados_ui.py
            clientes_tab.py
            __init__.py
            __pycache__/
          presupuestos/
            presupuestos_manager.py
            __init__.py
            __pycache__/
          __pycache__/
        users/
          users_manager.py
          __init__.py
          __pycache__/
      scripts/
        add_random_clients.py
      ui/
        generador_codigos.py
        navigation_manager.py
        qr_generator.py
        ui_components.py
        __init__.py
        __pycache__/
      utils/
        client_utils.py
        pagination.py
        ticket_utils.py
        ui_utils.py
        updater.py
        __pycache__/
      __pycache__/
    tests/
      test_ticket_utils.py
      __pycache__/
    tickets/
    tools/
      check_structure_and_imports.py
  sales_reports/
    abonos/
    modificaciones/

## Módulos principales

### analyze_code.py
- **Clases**: CodeAnalyzer
- **Funciones principales**: main, __init__, analyze, _collect_files, _map_folder_structure
- **Dependencias**: Ninguna

### POS_PROJECT\src\main.py
- **Clases**: LoginWindow
- **Funciones principales**: create_readme_if_not_exists, load_icons, on_closing, main, __init__
- **Dependencias**: Ninguna

### POS_PROJECT\src\__init__.py
- **Clases**: Ninguna
- **Funciones principales**: Ninguna
- **Dependencias**: Ninguna

### POS_PROJECT\src\core\backup\backup_manager.py
- **Clases**: BackupManager
- **Funciones principales**: __init__, create_backup, _create_backup_sync, _limit_auto_backups, list_backups
- **Dependencias**: Ninguna

### POS_PROJECT\src\core\backup\__init__.py
- **Clases**: Ninguna
- **Funciones principales**: Ninguna
- **Dependencias**: Ninguna

### POS_PROJECT\src\core\config\config.py
- **Clases**: Ninguna
- **Funciones principales**: clean_config, cargar_config, guardar_datos_personalizados, exportar_configuraciones, importar_configuraciones
- **Dependencias**: Ninguna

### POS_PROJECT\src\core\config\controller.py
- **Clases**: Controller
- **Funciones principales**: __init__, toggle_field, show_message, show_success_dialog, añadir_valor
- **Dependencias**: Ninguna

### POS_PROJECT\src\core\config\db_manager.py
- **Clases**: DatabaseManager
- **Funciones principales**: __new__, connect, ensure_connection, migrate_dates, initialize_default_user
- **Dependencias**: Ninguna

### POS_PROJECT\src\core\config\db_setup.py
- **Clases**: Ninguna
- **Funciones principales**: inicializar_db
- **Dependencias**: Ninguna

### POS_PROJECT\src\core\config\__init__.py
- **Clases**: Ninguna
- **Funciones principales**: Ninguna
- **Dependencias**: Ninguna

### POS_PROJECT\src\core\utils\tooltips.py
- **Clases**: ToolTip
- **Funciones principales**: __init__, schedule_tooltip, show_tooltip, hide_tooltip
- **Dependencias**: Ninguna

### POS_PROJECT\src\core\utils\utils.py
- **Clases**: Ninguna
- **Funciones principales**: validate_path, check_disk_space, copy_to_clipboard, copy_image_to_clipboard, sanitize_filename
- **Dependencias**: Ninguna

### POS_PROJECT\src\core\utils\__init__.py
- **Clases**: Ninguna
- **Funciones principales**: Ninguna
- **Dependencias**: Ninguna

### POS_PROJECT\src\modules\auth\auth_manager.py
- **Clases**: AuthManager
- **Funciones principales**: __init__, _execute_query, autenticar_usuario, obtener_rol, obtener_usuarios
- **Dependencias**: Ninguna

### POS_PROJECT\src\modules\auth\__init__.py
- **Clases**: Ninguna
- **Funciones principales**: Ninguna
- **Dependencias**: Ninguna

### POS_PROJECT\src\modules\clients\client_manager.py
- **Clases**: ClientManager
- **Funciones principales**: __init__, cargar_clientes, buscar_clientes, añadir_cliente, abrir_ventana_crear_cliente
- **Dependencias**: Ninguna

### POS_PROJECT\src\modules\clients\__init__.py
- **Clases**: Ninguna
- **Funciones principales**: Ninguna
- **Dependencias**: Ninguna

### POS_PROJECT\src\modules\inventory\entradas_salidas_logic.py
- **Clases**: EntradasSalidasLogic
- **Funciones principales**: __init__, _validate_sku, _validate_stock_for_salida, _exportar_pdf, registrar_movimiento
- **Dependencias**: Ninguna

### POS_PROJECT\src\modules\inventory\entradas_salidas_manager.py
- **Clases**: EntradasSalidasManager
- **Funciones principales**: __init__, setup_ui, mostrar_entradas, mostrar_salidas, setup_treeview
- **Dependencias**: Ninguna

### POS_PROJECT\src\modules\inventory\inventory_manager.py
- **Clases**: InventoryManager
- **Funciones principales**: __init__, validate_numeric_entry, open_price_modification_window, update_selected_prices, update_mass_prices
- **Dependencias**: Ninguna

### POS_PROJECT\src\modules\inventory\__init__.py
- **Clases**: Ninguna
- **Funciones principales**: Ninguna
- **Dependencias**: Ninguna

### POS_PROJECT\src\modules\maintenance\maintenance.py
- **Clases**: MaintenanceTool
- **Funciones principales**: abrir_mantenimiento, __init__, setup_ui, setup_data_correction, setup_incomplete_data
- **Dependencias**: Ninguna

### POS_PROJECT\src\modules\maintenance\__init__.py
- **Clases**: Ninguna
- **Funciones principales**: Ninguna
- **Dependencias**: Ninguna

### POS_PROJECT\src\modules\products\product_manager.py
- **Clases**: ProductManagerWindow
- **Funciones principales**: abrir_gestion_productos, __init__, setup_window, initialize_state, setup_keybindings
- **Dependencias**: Ninguna

### POS_PROJECT\src\modules\products\product_manager_logic.py
- **Clases**: ProductManagerLogic
- **Funciones principales**: __init__, get_unique_values, update_filters, apply_quick_search, _perform_quick_search
- **Dependencias**: Ninguna

### POS_PROJECT\src\modules\products\product_manager_ui.py
- **Clases**: PrintPreviewWindow, ProductManagerUI
- **Funciones principales**: __init__, setup_ui, print_labels, __init__, setup_ui
- **Dependencias**: Ninguna

### POS_PROJECT\src\modules\products\product_manager_window.py
- **Clases**: ProductManagerWindow
- **Funciones principales**: abrir_gestion_productos, __init__, setup_window, initialize_state, setup_keybindings
- **Dependencias**: Ninguna

### POS_PROJECT\src\modules\products\__init__.py
- **Clases**: Ninguna
- **Funciones principales**: Ninguna
- **Dependencias**: Ninguna

### POS_PROJECT\src\modules\reports\reports_logic.py
- **Clases**: ReportesLogic
- **Funciones principales**: __init__, _execute_query, obtener_ventas, contar_ventas, obtener_inventario
- **Dependencias**: Ninguna

### POS_PROJECT\src\modules\reports\reports_manager.py
- **Clases**: ReportesManager
- **Funciones principales**: __init__, setup_ui, setup_ventas_tab, update_ventas_page, change_ventas_page
- **Dependencias**: Ninguna

### POS_PROJECT\src\modules\reports\__init__.py
- **Clases**: Ninguna
- **Funciones principales**: Ninguna
- **Dependencias**: Ninguna

### POS_PROJECT\src\modules\sales\pos_ventas.py
- **Clases**: PosVentas
- **Funciones principales**: __init__, agregar_o_actualizar_item, abrir_ventana_apartado, agregar_cliente, cliente_creado
- **Dependencias**: Ninguna

### POS_PROJECT\src\modules\sales\__init__.py
- **Clases**: Ninguna
- **Funciones principales**: Ninguna
- **Dependencias**: Ninguna

### POS_PROJECT\src\modules\sales\apartados\apartados_actions.py
- **Clases**: ApartadosActions
- **Funciones principales**: __init__, _create_dialog, _show_success_dialog, _get_selected_apartado, _build_confirm_dialog
- **Dependencias**: Ninguna

### POS_PROJECT\src\modules\sales\apartados\apartados_creation_window.py
- **Clases**: ApartadoCreationWindow
- **Funciones principales**: __init__, on_closing, combinar_productos, actualizar_tabla_productos, restar_producto
- **Dependencias**: Ninguna

### POS_PROJECT\src\modules\sales\apartados\apartados_data.py
- **Clases**: ApartadosData
- **Funciones principales**: __init__, parse_date, format_apartado_row, actualizar_dias_vencimiento, cargar_apartados_paginated
- **Dependencias**: Ninguna

### POS_PROJECT\src\modules\sales\apartados\apartados_logic.py
- **Clases**: ApartadosLogic
- **Funciones principales**: __init__, initialize_modificaciones_apartados_table, generate_cancellation_receipt, generate_completion_receipt, generate_creation_receipt
- **Dependencias**: Ninguna

### POS_PROJECT\src\modules\sales\apartados\apartados_manager.py
- **Clases**: ApartadosManager
- **Funciones principales**: __init__, setup_ui, cargar_apartados, pack, on_ver_apartados
- **Dependencias**: Ninguna

### POS_PROJECT\src\modules\sales\apartados\apartados_tab.py
- **Clases**: ApartadosTab
- **Funciones principales**: __init__, setup_ui
- **Dependencias**: Ninguna

### POS_PROJECT\src\modules\sales\apartados\apartados_ui.py
- **Clases**: ApartadosUI
- **Funciones principales**: __init__, setup_ui, _setup_notif_frame, _setup_search_frame, _setup_treeview
- **Dependencias**: Ninguna

### POS_PROJECT\src\modules\sales\apartados\clientes_tab.py
- **Clases**: ClientesTab
- **Funciones principales**: __init__, setup_ui, cargar_clientes_paginated, cargar_clientes, buscar_clientes
- **Dependencias**: Ninguna

### POS_PROJECT\src\modules\sales\apartados\__init__.py
- **Clases**: Ninguna
- **Funciones principales**: Ninguna
- **Dependencias**: Ninguna

### POS_PROJECT\src\modules\sales\presupuestos\presupuestos_manager.py
- **Clases**: PresupuestosManager
- **Funciones principales**: __init__, iniciar_proceso, seleccionar_cliente, agregar_productos, pack
- **Dependencias**: Ninguna

### POS_PROJECT\src\modules\sales\presupuestos\__init__.py
- **Clases**: Ninguna
- **Funciones principales**: Ninguna
- **Dependencias**: Ninguna

### POS_PROJECT\src\modules\users\users_manager.py
- **Clases**: UsersManager
- **Funciones principales**: __init__, cargar_usuarios, agregar_usuario, editar_usuario, eliminar_usuario
- **Dependencias**: Ninguna

### POS_PROJECT\src\modules\users\__init__.py
- **Clases**: Ninguna
- **Funciones principales**: Ninguna
- **Dependencias**: Ninguna

### POS_PROJECT\src\scripts\add_random_clients.py
- **Clases**: Ninguna
- **Funciones principales**: generar_nombre_completo, generar_numero_telefono, generar_clientes_aleatorios, insertar_clientes, main
- **Dependencias**: Ninguna

### POS_PROJECT\src\ui\generador_codigos.py
- **Clases**: GeneradorCodigos
- **Funciones principales**: __init__, validate_field, validate_price, validate_price_final, select_image
- **Dependencias**: Ninguna

### POS_PROJECT\src\ui\navigation_manager.py
- **Clases**: NavigationManager
- **Funciones principales**: __init__, setup_ui, actualizar_notificacion_stock_bajo, clear_content_frame, open_pos_ventas
- **Dependencias**: Ninguna

### POS_PROJECT\src\ui\qr_generator.py
- **Clases**: QRGenerator
- **Funciones principales**: validate_string, adjust_font_size, generar_qr, generar_etiqueta, generate_product_labels
- **Dependencias**: Ninguna

### POS_PROJECT\src\ui\ui_components.py
- **Clases**: Ninguna
- **Funciones principales**: create_labeled_entry, create_labeled_combobox, create_filter_combobox, create_treeview, create_field
- **Dependencias**: Ninguna

### POS_PROJECT\src\ui\__init__.py
- **Clases**: Ninguna
- **Funciones principales**: Ninguna
- **Dependencias**: Ninguna

### POS_PROJECT\src\utils\client_utils.py
- **Clases**: Ninguna
- **Funciones principales**: buscar_clientes_reutilizable
- **Dependencias**: Ninguna

### POS_PROJECT\src\utils\pagination.py
- **Clases**: Paginator
- **Funciones principales**: __init__, set_total_items, get_offset, prev_page, next_page
- **Dependencias**: Ninguna

### POS_PROJECT\src\utils\ticket_utils.py
- **Clases**: Ninguna
- **Funciones principales**: generar_ticket_pdf
- **Dependencias**: Ninguna

### POS_PROJECT\src\utils\ui_utils.py
- **Clases**: Ninguna
- **Funciones principales**: mostrar_ventana_seleccion, filtrar_items, seleccionar_item
- **Dependencias**: Ninguna

### POS_PROJECT\src\utils\updater.py
- **Clases**: Updater
- **Funciones principales**: __init__, check_for_updates, update_program
- **Dependencias**: Ninguna

### POS_PROJECT\tests\test_ticket_utils.py
- **Clases**: TestTicketUtils
- **Funciones principales**: test_generar_ticket_venta, test_generar_ticket_apartado
- **Dependencias**: Ninguna

### POS_PROJECT\tools\check_structure_and_imports.py
- **Clases**: Ninguna
- **Funciones principales**: check_structure, check_imports, main
- **Dependencias**: Ninguna

## Docstrings

### analyze_code.py - analyze
```Analiza el proyecto y genera mapas, dependencias, documentación y plan de refactorización.```

### analyze_code.py - _collect_files
```Recolecta todos los archivos .py en la carpeta, excluyendo backups.```

### analyze_code.py - _map_folder_structure
```Genera un mapa de la estructura de carpetas.```

### analyze_code.py - _analyze_files
```Analiza cada archivo .py.```

### analyze_code.py - _analyze_file_content
```Analiza el contenido de un archivo.```

## Pruebas unitarias sugeridas

### Test para analyze_code.py - main
```python
def test_main():
    # TODO: Implementar prueba para main
    assert True
```

### Test para analyze_code.py - __init__
```python
def test___init__():
    # TODO: Implementar prueba para __init__
    assert True
```

### Test para analyze_code.py - analyze
```python
def test_analyze():
    # TODO: Implementar prueba para analyze
    assert True
```
# Plan de Refactorización - POS EXODIA
Generado el 2025-04-30 19:16
Directorio: C:\Users\Daniel\Documents\Versions\Exodia 8\Exidia 7\EXODIA

## Tareas Priorizadas
- - Añadir try-except en funciones críticas (ej., add_to_cart, finalize_sale).
- - Centralizar consultas SQL en core/database.py.
- - Mover valores hardcoded a config.py o .env.
- - Optimizar funciones con bucles anidados o consultas SQL pesadas.
- - Añadir store_id a tablas SQLite para soportar múltiples tiendas.
- - Modularizar la interfaz customtkinter en ui/ventas.py, ui/productos.py, etc.

## Pasos Siguientes
- Crear rama Git (git checkout -b refactor).
- Ejecutar pruebas manuales tras cada cambio.
- Empaquetar y probar .exe con PyInstaller.
- Implementar sistema de actualizaciones tras refactorización.
- Usar el módulo de recordatorios para seguir estas tareas.
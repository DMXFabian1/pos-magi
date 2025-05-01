# Esquema del Sistema - POS MAGI
## Componentes Principales
- **Interfaz (ui/)**: Maneja la interfaz gráfica con customtkinter.
- **Base de datos (core/)**: Gestiona datos con SQLite (productos, ventas, comisiones, recordatorios).
- **Utilidades (utils/)**: Incluye sistema de actualizaciones, notificaciones WhatsApp, y logging.
## Flujo de Trabajo
1. Login: Cada empleada inicia sesión con su cuenta.
2. Ventas: Escanea productos, aplica descuentos, calcula cambio.
3. Comisiones: Calcula y registra comisiones automáticamente.
4. Recordatorios: Gestiona tareas (pedidos, promociones).
5. Actualizaciones: Verifica y descarga nuevas versiones del .exe.
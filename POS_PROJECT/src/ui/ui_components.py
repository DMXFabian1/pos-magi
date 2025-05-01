import tkinter as tk
import customtkinter as ctk
from tkinter import ttk
from src.core.utils.tooltips import ToolTip

def create_labeled_entry(parent, label_text, placeholder_text="", width=200, row=0, column=0, sticky="w", omit_var=None, toggle_callback=None, tooltip=None):
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.grid(row=row, column=column, sticky=sticky, padx=5, pady=2)
    label = ctk.CTkLabel(frame, text=label_text, font=("Helvetica", 12))
    label.pack(side="left", padx=(0, 5))
    entry = ctk.CTkEntry(frame, placeholder_text=placeholder_text, width=width)
    entry.pack(side="left")
    if omit_var is not None and toggle_callback is not None:
        checkbox = ctk.CTkCheckBox(frame, text="Omitir", variable=omit_var, command=lambda: toggle_callback(omit_var, entry))
        checkbox.pack(side="left", padx=(10, 0))
    if tooltip:
        ToolTip(entry, tooltip)
    return {"entry": entry, "frame": frame}

def create_labeled_combobox(parent, label_text, values, width=200, row=0, column=0, sticky="w", omit_var=None, toggle_callback=None, tooltip=None):
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.grid(row=row, column=column, sticky=sticky, padx=5, pady=2)
    label = ctk.CTkLabel(frame, text=label_text, font=("Helvetica", 12))
    label.pack(side="left", padx=(0, 5))
    combobox = ctk.CTkComboBox(frame, values=values, width=width)
    combobox.pack(side="left")
    if omit_var is not None and toggle_callback is not None:
        checkbox = ctk.CTkCheckBox(frame, text="Omitir", variable=omit_var, command=lambda: toggle_callback(omit_var, combobox))
        checkbox.pack(side="left", padx=(10, 0))
    if tooltip:
        ToolTip(combobox, tooltip)
    return {"combobox": combobox, "frame": frame}

def create_filter_combobox(parent, label_text, values, width=150, command=None):
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(side="left", padx=5, pady=2)
    label = ctk.CTkLabel(frame, text=label_text, font=("Helvetica", 10))
    label.pack(side="left", padx=(0, 5))
    combobox = ctk.CTkComboBox(frame, values=[""] + values, width=width, command=command)
    combobox.pack(side="left")
    return combobox

def create_treeview(parent, columns, visible_columns, height=20):
    tree = ttk.Treeview(parent, columns=["checkbox"] + visible_columns, show="headings", height=height)
    tree.heading("checkbox", text="")
    for col in visible_columns:
        tree.heading(col, text=col.capitalize(), command=lambda c=col: parent.sort_by_column(c))
        tree.column(col, width=100, anchor="center")
    tree.column("checkbox", width=30, anchor="center")
    tree.tag_configure("evenrow", background="#F0F0F0")
    tree.tag_configure("oddrow", background="#FFFFFF")
    return tree

def create_field(parent, label_text, values, row, omit_var, toggle_command, add_command=None, default_value="", update_callback=None):
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=3, pady=3)

    ctk.CTkLabel(frame, text=label_text, font=("Helvetica", 12, "bold"), text_color="#1A2E5A", width=120).grid(row=0, column=0, sticky="e", padx=3, pady=3)

    field_frame = ctk.CTkFrame(frame, fg_color="transparent")
    field_frame.grid(row=0, column=1, sticky="w")

    # Hacer el combobox editable
    combo = ctk.CTkComboBox(field_frame, values=values, width=300, border_color="#A3BFFA", state="normal", text_color="#4B5EAA")
    combo.set(default_value if default_value else "")
    combo.grid(row=0, column=0, sticky="w", padx=3, pady=3)

    # Lista original de valores para restaurar después de filtrar
    original_values = values.copy()
    # Lista de valores filtrados y índice para navegación
    filtered_values = original_values.copy()
    current_index = -1  # Índice de la opción seleccionada

    # Función para filtrar las opciones según lo que el usuario escribe
    def on_key_release(event):
        nonlocal filtered_values, current_index
        typed_text = combo.get().strip().lower()
        if not typed_text:
            filtered_values = original_values.copy()
            combo.configure(values=filtered_values)
            current_index = -1
            return
        # Filtrar los valores que coincidan con el texto escrito
        filtered_values = [item for item in original_values if item.lower().startswith(typed_text)]
        combo.configure(values=filtered_values if filtered_values else original_values)
        current_index = -1  # Reiniciar el índice al filtrar

    # Función para navegar con las teclas de flecha
    def on_arrow_key(event):
        nonlocal current_index, filtered_values
        if not filtered_values:  # Si no hay opciones filtradas, no hacer nada
            return
        # Asegurarse de que current_index esté dentro de los límites
        if current_index == -1:
            # Si no hay selección previa, empezar desde el primer elemento
            if event.keysym == "Down":
                current_index = 0
            elif event.keysym == "Up":
                current_index = len(filtered_values) - 1
        else:
            # Navegar hacia arriba o abajo de manera cíclica
            if event.keysym == "Down":
                current_index = (current_index + 1) % len(filtered_values)
            elif event.keysym == "Up":
                current_index = (current_index - 1) % len(filtered_values)

        # Actualizar el valor del combobox con la opción seleccionada
        if current_index >= 0 and current_index < len(filtered_values):
            combo.set(filtered_values[current_index])

    # Función para confirmar la selección y actualizar el nombre
    def confirm_selection(event=None):
        nonlocal current_index
        typed_text = combo.get().strip().lower()
        if not typed_text:
            return
        # Si hay un índice seleccionado, usar ese valor; si no, buscar el primer elemento que coincida
        if current_index >= 0 and current_index < len(filtered_values):
            combo.set(filtered_values[current_index])
        else:
            for item in original_values:
                if item.lower().startswith(typed_text):
                    combo.set(item)
                    break
        # Llamar al callback para actualizar el nombre del producto
        if update_callback:
            update_callback()
        current_index = -1  # Reiniciar el índice después de confirmar

    # Vincular el evento <KeyRelease> para filtrar las opciones
    combo.bind("<KeyRelease>", on_key_release)
    # Vincular las teclas de flecha para navegar por las opciones filtradas
    combo.bind("<Up>", on_arrow_key)
    combo.bind("<Down>", on_arrow_key)
    # Vincular el evento <Return> para confirmar la selección
    combo.bind("<Return>", confirm_selection)
    # Vincular el evento de selección del combobox para actualizar el nombre
    combo.bind("<<ComboboxSelected>>", lambda event: [update_callback() if update_callback else None])

    checkbox = ctk.CTkCheckBox(field_frame, text=f"Omitir {label_text.strip(':')}", variable=omit_var, 
                               command=lambda: toggle_command(omit_var, combo), fg_color="#4A90E2", text_color="#4B5EAA")
    checkbox.grid(row=1, column=0, sticky="w", padx=3, pady=3)

    add_button = None
    if add_command:
        add_button = ctk.CTkButton(field_frame, text="+", command=add_command, width=30, 
                                   fg_color="#4A90E2", hover_color="#2A6EBB", corner_radius=8)
        add_button.grid(row=0, column=1, padx=5)

    return {"combo": combo, "checkbox": checkbox, "add_button": add_button}

def validate_numeric_entry(entry, field_name, is_int=False):
    value = entry.get().strip()
    try:
        if value:
            num = int(value) if is_int else float(value)
            if num < 0:
                entry.configure(fg_color="#FFE6E6", border_color="#FF5555")
                tk.messagebox.showwarning("Advertencia", f"El campo {field_name} no puede ser negativo.")
                return False
        entry.configure(fg_color="#FFFFFF", border_color="#A3BFFA")
        return True
    except ValueError:
        entry.configure(fg_color="#FFE6E6", border_color="#FF5555")
        tk.messagebox.showwarning("Advertencia", f"El campo {field_name} debe ser un {'entero' if is_int else 'número'} válido.")
        return False

def validate_string(entry, field_name, allow_empty=False):
    value = entry.get().strip()
    if not value and not allow_empty:
        entry.configure(fg_color="#FFE6E6", border_color="#FF5555")
        return False
    entry.configure(fg_color="#FFFFFF", border_color="#A3BFFA")
    return True
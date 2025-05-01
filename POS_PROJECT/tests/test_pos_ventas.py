import pytest
from src.modules.sales.pos_ventas import PosVentas
from unittest.mock import Mock, patch

@pytest.fixture
def pos_ventas():
    db_manager = Mock()
    db_manager.buscar_productos.return_value = [
        {"sku": "SKU001", "nombre": "Camisa", "precio": 50000, "inventario": 10}
    ]
    db_manager.validar_stock.return_value = True
    cursor = Mock()
    cursor.execute.return_value = None
    cursor.fetchone.return_value = {"role": "admin"}  # Simula resultado de la consulta
    db_manager.get_cursor.return_value = cursor

    # Simula customtkinter y ttk widgets
    with patch("src.modules.sales.pos_ventas.ctk.CTkFrame", autospec=True) as mock_ctk_frame, \
         patch("src.modules.sales.pos_ventas.ctk.CTkLabel", autospec=True) as mock_ctk_label, \
         patch("src.modules.sales.pos_ventas.ctk.CTkEntry", autospec=True) as mock_ctk_entry, \
         patch("src.modules.sales.pos_ventas.ctk.CTkButton", autospec=True) as mock_ctk_button, \
         patch("src.modules.sales.pos_ventas.ctk.CTkOptionMenu", autospec=True) as mock_ctk_optionmenu, \
         patch("src.modules.sales.pos_ventas.ctk.CTkToplevel", autospec=True) as mock_ctk_toplevel, \
         patch("src.modules.sales.pos_ventas.ctk.StringVar", autospec=True) as mock_string_var, \
         patch("src.modules.sales.pos_ventas.ctk.CTkComboBox", autospec=True) as mock_ctk_combobox, \
         patch("src.modules.sales.pos_ventas.ttk.Treeview", autospec=True) as mock_ttk_treeview, \
         patch("src.modules.sales.pos_ventas.ttk.Style", autospec=True) as mock_ttk_style, \
         patch("src.modules.sales.pos_ventas.messagebox.showerror", autospec=True) as mock_showerror, \
         patch("src.modules.sales.pos_ventas.messagebox.showinfo", autospec=True) as mock_showinfo:

        # Configura los mocks para que no fallen
        mock_frame_instance = Mock()
        mock_ctk_frame.return_value = mock_frame_instance
        mock_label_instance = Mock()
        mock_ctk_label.return_value = mock_label_instance
        mock_entry_instance = Mock()
        mock_ctk_entry.return_value = mock_entry_instance
        mock_button_instance = Mock()
        mock_ctk_button.return_value = mock_button_instance
        mock_optionmenu_instance = Mock()
        mock_ctk_optionmenu.return_value = mock_optionmenu_instance
        mock_toplevel_instance = Mock()
        mock_ctk_toplevel.return_value = mock_toplevel_instance
        mock_string_var_instance = Mock()
        mock_string_var.return_value = mock_string_var_instance
        mock_combobox_instance = Mock()
        mock_ctk_combobox.return_value = mock_combobox_instance
        mock_treeview_instance = Mock()
        mock_ttk_treeview.return_value = mock_treeview_instance
        mock_style_instance = Mock()
        mock_ttk_style.return_value = mock_style_instance
        mock_style_instance.configure.return_value = None  # Simula ttk.Style().configure

        pos_ventas = PosVentas(user_id=1, parent_frame=Mock(), root=Mock(), db_manager=db_manager)
        pos_ventas.mostrar_error = Mock()  # Evita messagebox.showerror
        pos_ventas.actualizar_tabla = Mock()  # Evita actualizar la interfaz gráfica
        return pos_ventas

def test_add_to_cart_new_item(pos_ventas):
    pos_ventas.entry_busqueda = Mock(get=lambda: "SKU001")
    pos_ventas.entry_cantidad = Mock(get=lambda: "1")
    pos_ventas.entry_descuento = Mock(get=lambda: "0")
    pos_ventas.buscar_y_agregar()
    assert len(pos_ventas.items) == 1
    assert pos_ventas.items[0]["sku"] == "SKU001"
    assert pos_ventas.items[0]["cantidad"] == 1
    assert pos_ventas.items[0]["precio"] == 50000
    assert pos_ventas.items[0]["descuento"] == 0

def test_add_to_cart_existing_sku(pos_ventas):
    pos_ventas.entry_busqueda = Mock(get=lambda: "SKU001")
    pos_ventas.entry_cantidad = Mock(get=lambda: "1")
    pos_ventas.entry_descuento = Mock(get=lambda: "0")
    pos_ventas.buscar_y_agregar()  # Primer producto
    pos_ventas.buscar_y_agregar()  # Segundo producto
    assert len(pos_ventas.items) == 1  # Agrupa por SKU
    assert pos_ventas.items[0]["cantidad"] == 2
    assert pos_ventas.items[0]["descuento"] == 0

def test_add_to_cart_invalid_stock(pos_ventas):
    pos_ventas.db_manager.validar_stock.return_value = False
    pos_ventas.entry_busqueda = Mock(get=lambda: "SKU001")
    pos_ventas.entry_cantidad = Mock(get=lambda: "1")
    pos_ventas.entry_descuento = Mock(get=lambda: "0")
    pos_ventas.buscar_y_agregar()
    assert len(pos_ventas.items) == 0

def test_finalize_sale_with_discount(pos_ventas):
    pos_ventas.entry_busqueda = Mock(get=lambda: "SKU001")
    pos_ventas.entry_cantidad 
import pytest
from src.formatters.telegram_formatter import format_telegram_message
from src.domain.entities import ProductInfo

def test_format_telegram_message_basic():
    product = ProductInfo(
        asin="B00XYZ123",
        titulo="Producto de Prueba",
        precio_actual=10.0,
        precio_anterior=20.0,
        descuento_porcentaje=50,
        url_afiliado="https://amzn.to/3xyz",
        imagen_principal="https://img.com/1.jpg",
        imagenes_extra=["https://img.com/2.jpg"]
    )
    product.descripcion_gpt = "Descripción corta de prueba."
    
    message = format_telegram_message(product)
    
    assert "Producto de Prueba" in message
    assert "10.0" in message
    assert "20.0" in message
    assert "50%" in message or "50 %" in message # Depende de cómo formatee el %
    assert "amzn.to" in message

def test_format_telegram_message_no_discount():
    product = ProductInfo(
        asin="B00XYZ123",
        titulo="Producto sin Descuento",
        precio_actual=10.0,
        precio_anterior=None,
        url_afiliado="https://amzn.to/3xyz",
        imagen_principal="https://img.com/1.jpg",
        imagenes_extra=["https://img.com/2.jpg"]
    )
    
    message = format_telegram_message(product)
    
    assert "Producto sin Descuento" in message
    assert "10.0" in message
    assert "%" not in message # No debería mostrar porcentaje si no hay precio anterior

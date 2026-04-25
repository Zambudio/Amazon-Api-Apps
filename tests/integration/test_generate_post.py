import pytest
from unittest.mock import MagicMock
from src.use_cases.generate_post import GeneratePostUseCase
from src.domain.entities import ProductInfo
from src.domain.category import CategoryCatalog

def test_generate_post_flow_success():
    # Mocks de servicios
    mock_amazon = MagicMock()
    mock_gpt = MagicMock()
    
    # Simular respuesta de Amazon
    product = ProductInfo(
        asin="B00TEST",
        titulo="Producto Test",
        precio_actual=10.0,
        precio_anterior=20.0,
        descuento_porcentaje=50,
        url_afiliado="https://amzn.to/test",
        imagen_principal="https://img.com/1.jpg",
        imagenes_extra=["https://img.com/2.jpg"],
        descripcion="Descripción larga de Amazon"
    )
    mock_amazon.get_product.return_value = product
    
    # Simular síntesis de GPT
    mock_gpt.sintetizar_descripcion.return_value = "Descripción corta by GPT"
    mock_gpt.seleccionar_categorias.return_value = ["#Hogar", "#Oferta"]
    
    # Caso de uso
    use_case = GeneratePostUseCase(amazon_service=mock_amazon, gpt_service=mock_gpt)
    
    # Inyectar repositorio de categorías mockeado con categorías disponibles
    catalog = CategoryCatalog()
    catalog.add_many(["#Hogar", "#Oferta", "#Informatica"])
    use_case.category_repository = MagicMock()
    use_case.category_repository.load_catalog.return_value = catalog
    
    result = use_case.execute("https://www.amazon.es/dp/B00TEST")
    
    # Verificaciones
    assert result["product"] is not None
    assert "Producto Test" in result["text"]
    assert "Descripción corta by GPT" in result["text"]
    assert "#Hogar" in result["text"]
    assert "#Oferta" in result["text"]
    
    # Verificar llamadas
    mock_amazon.get_product.assert_called_once()
    mock_gpt.sintetizar_descripcion.assert_called_once_with("Descripción larga de Amazon")

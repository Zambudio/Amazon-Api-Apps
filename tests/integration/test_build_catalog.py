import pytest
from unittest.mock import MagicMock
from src.use_cases.build_category_catalog_from_channel import BuildCategoryCatalogFromChannelUseCase
from src.use_cases.ports.category_repository import CategoryRepository
from src.use_cases.ports.channel_history_reader import ChannelHistoryReader
from src.domain.category import CategoryCatalog

def test_build_category_catalog_from_channel_success():
    # Mocks
    mock_repo = MagicMock(spec=CategoryRepository)
    mock_reader = MagicMock(spec=ChannelHistoryReader)
    
    # Preparar catálogo inicial vacío
    mock_repo.load_catalog.return_value = CategoryCatalog()
    
    # Simular mensajes de Telegram con hashtags
    mock_reader.iter_messages.return_value = [
        "Chollo en #Informatica y #Gaming",
        "Oferta para el #Hogar",
        "Sin hashtags aquí"
    ]
    
    use_case = BuildCategoryCatalogFromChannelUseCase(mock_repo, mock_reader)
    result = use_case.execute(channel_id="@canal_test", persist=True)
    
    # Verificaciones
    assert result["processed_messages"] == 3
    assert result["new_categories"] == 3
    assert result["total_categories"] == 3
    
    # Verificar que se guardó el catálogo
    mock_repo.save_catalog.assert_called_once()
    
    # Verificar que los hashtags son correctos (normalizados)
    catalog_saved = mock_repo.save_catalog.call_args[0][0]
    assert "#Informatica" in catalog_saved.categories
    assert "#Gaming" in catalog_saved.categories
    assert "#Hogar" in catalog_saved.categories

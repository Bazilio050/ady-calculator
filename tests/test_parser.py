# ------------------------------------------------------------------------------
# БЛОК 1: Юнит-тест NLU-парсера (проверка извлечения сущностей)
# ------------------------------------------------------------------------------
import pytest
from unittest.mock import patch, MagicMock
from core.parser import parse_user_input, RawParsedEntities


def test_parse_user_input_mock():
    mock_json_response = (
        '{"raw_from": "ТРК", "raw_to": "Баку тов", "raw_gng": "3404", '
        '"raw_wagon": "цистерна", "raw_weight": 50.0, "raw_owner": "спс"}'
    )

    with patch("google.genai.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.text = mock_json_response
        mock_client.models.generate_content.return_value = mock_response

        with patch.dict("os.environ", {"GEMINI_API_KEY": "test_key"}):
            result = parse_user_input("ТРК Баку тов 3404 цистерна 50т спс")

            assert result.raw_from == "ТРК"
            assert result.raw_to == "Баку тов"
            assert result.raw_gng == "3404"
            assert result.raw_wagon == "цистерна"
            assert result.raw_weight == 50.0
            assert result.raw_owner == "спс"

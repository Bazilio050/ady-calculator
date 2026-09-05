# ------------------------------------------------------------------------------
# БЛОК 1: Извлечение сырых сущностей из текста (Gemini NLU Parser)
# ------------------------------------------------------------------------------
import os
import json
from typing import Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types


class RawParsedEntities(BaseModel):
    raw_from: Optional[str] = Field(default=None, description="Сырое название станции отправления")
    raw_to: Optional[str] = Field(default=None, description="Сырое название станции назначения")
    raw_gng: Optional[str] = Field(default=None, description="Сырой код или название груза GNG/ГНГ")
    raw_wagon: Optional[str] = Field(default=None, description="Сырой тип или код вагона")
    raw_weight: Optional[float] = Field(default=None, description="Вес груза в тоннах")
    raw_owner: Optional[str] = Field(default=None, description="Принадлежность вагона (спс, инв, собст)")


SYSTEM_PROMPT = """
Ты — слепой NLU-парсер текста для железнодорожных перевозок.
Твоя единственная задача: извлечь из входного текста упоминания сущностей и вернуть JSON.

Правила:
1. Никаких догадок, автодополнений, исправлений ошибок или поиска ЕСР.
2. Извлекай только то, что явно написано в тексте.
3. Порядок станций: первая упомянутая станция -> raw_from, вторая -> raw_to.
4. Если сущность отсутствует в тексте, возвращай null.

Структура JSON:
{
  "raw_from": string | null,
  "raw_to": string | null,
  "raw_gng": string | null,
  "raw_wagon": string | null,
  "raw_weight": float | null,
  "raw_owner": string | null
}
"""


def parse_user_input(text: str) -> RawParsedEntities:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Переменная окружения GEMINI_API_KEY не установлена")

    client = genai.Client(api_key=api_key)

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        temperature=0.0,
        response_mime_type="application/json",
        response_schema=RawParsedEntities,
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=text,
        config=config,
    )

    parsed_data = json.loads(response.text)
    return RawParsedEntities(**parsed_data)

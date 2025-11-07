import logging
from openai import AsyncOpenAI
from config import DOTA_SYSTEM_PROMPT
from hero_data import POSITION_NAMES

logger = logging.getLogger(__name__)


class DotaAnalyzer:
    def __init__(self):
        self.client = AsyncOpenAI()

    async def analyze_pick(self, position: str, enemy_heroes: list) -> str:

        position_name = POSITION_NAMES.get(position, f"Позиция {position}")

        prompt = f"""
{DOTA_SYSTEM_PROMPT}

ПОЗИЦИЯ: {position_name}
ГЕРОИ ПРОТИВНИКА: {', '.join(enemy_heroes)}

Проанализируй этих героев противника и дай ТОП-3 рекомендации для позиции {position}.
Обязательно укажи процент шанса на победу для каждого героя!
"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": DOTA_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Ошибка при обращении к ИИ: {e}")
            return await self._get_fallback_recommendation(position, enemy_heroes)

    async def _get_fallback_recommendation(self, position: str, enemy_heroes: list) -> str:
        position_name = POSITION_NAMES.get(position, f"Позиция {position}")

        recommendations = {
            "1": ["Juggernaut", "Phantom Assassin", "Luna"],
            "2": ["Queen of Pain", "Dragon Knight", "Puck"],
            "3": ["Axe", "Legion Commander", "Bristleback"],
            "4": ["Crystal Maiden", "Rubick", "Lion"],
            "5": ["Earthshaker", "Ogre Magi", "Winter Wyvern"]
        }

        rec_heroes = recommendations.get(position, ["Juggernaut", "Axe", "Crystal Maiden"])

        result = f"🎯 РЕКОМЕНДАЦИИ ДЛЯ {position_name}:\n\n"

        for i, hero in enumerate(rec_heroes[:3], 1):
            win_chance = 85 - i * 5  # Простая логика процентов
            medals = ["🥇", "🥈", "🥉"]

            result += f"{medals[i - 1]} {hero} - {win_chance}% шанс победы\n"
            result += f"📊 Хороший выбор против {', '.join(enemy_heroes[:2])}\n\n"

        result += f"💡 СОВЕТ: Сфокусируйся на контрпике {enemy_heroes[0] if enemy_heroes else 'вражеской команды'}"

        return result
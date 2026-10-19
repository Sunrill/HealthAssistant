"""知识卡加载与查询：医学解释外置在 data/knowledge/lab_cards.json。"""
import json
import os

CARD_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data", "knowledge", "lab_cards.json",
)

_cards: dict | None = None


def _load() -> dict:
    global _cards
    if _cards is None:
        if not os.path.exists(CARD_PATH):
            _cards = {}
        else:
            with open(CARD_PATH, encoding="utf-8") as f:
                _cards = json.load(f)
    return _cards


def get_card(name: str) -> dict | None:
    """按标准名或别名查知识卡。"""
    cards = _load()
    if name in cards:
        return cards[name]
    for card in cards.values():
        if name in card.get("aliases", []):
            return card
    return None


def canonical_name(name: str) -> str:
    card = get_card(name)
    if card and card.get("aliases"):
        return card["aliases"][0]
    return name

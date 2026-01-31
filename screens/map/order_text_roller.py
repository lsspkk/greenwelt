# Order text roller - generates random text for order plants from YAML sentences

import random
from pathlib import Path
from typing import List, Dict
from shared.shared_components import Order
from shared.debug_log import debug

# Try to import yaml, fall back to simple parsing if not available
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def load_sentences_from_yaml(yaml_path: str) -> Dict[str, List[str]]:
    """
    Load sentences from YAML file.

    Returns dict with keys 'plant' and 'amount', each containing list of phrases.
    """
    sentences = {
        'plant': [],
        'amount': []
    }

    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            if HAS_YAML:
                data = yaml.safe_load(f)
            else:
                # Simple fallback parsing without yaml library
                data = _parse_yaml_simple(f.read())

        if data is None:
            debug.error("YAML file is empty or invalid")
            return sentences

        sentence_list = data.get('sentences', [])

        for item in sentence_list:
            sentence_type = item.get('sentence_type', '')
            phrase = item.get('phrase', '')

            if sentence_type == 'plant' and phrase:
                sentences['plant'].append(phrase)
            elif sentence_type == 'amount' and phrase:
                sentences['amount'].append(phrase)

        debug.info(f"Loaded {len(sentences['plant'])} plant sentences, {len(sentences['amount'])} amount sentences")

    except Exception as e:
        debug.error(f"Failed to load sentences YAML: {e}")

    return sentences


def _parse_yaml_simple(content: str) -> Dict:
    """
    Simple YAML parser for the specific format we use.
    Only handles our sentence list format.
    """
    result = {'sentences': []}
    current_item = None

    lines = content.split('\n')
    for line in lines:
        stripped = line.strip()

        if stripped.startswith('- sentence_type:'):
            if current_item is not None:
                result['sentences'].append(current_item)
            sentence_type = stripped.replace('- sentence_type:', '').strip()
            current_item = {'sentence_type': sentence_type, 'phrase': ''}

        elif stripped.startswith('phrase:') and current_item is not None:
            phrase = stripped.replace('phrase:', '').strip()
            # Remove surrounding quotes if present
            if phrase.startswith('"') and phrase.endswith('"'):
                phrase = phrase[1:-1]
            elif phrase.startswith("'") and phrase.endswith("'"):
                phrase = phrase[1:-1]
            current_item['phrase'] = phrase

    if current_item is not None:
        result['sentences'].append(current_item)

    return result


def roll_text_for_orders(orders: List[Order], sentences: Dict[str, List[str]]):
    """
    For each order, for each plant, roll random plant_text and amount_text.

    Replaces placeholders:
    - {order_plant_name} -> plant.name_fi
    - {order_amount} -> plant.amount
    """
    plant_sentences = sentences.get('plant', [])
    amount_sentences = sentences.get('amount', [])

    if not plant_sentences:
        debug.error("No plant sentences available for text rolling")
        return

    if not amount_sentences:
        debug.error("No amount sentences available for text rolling")
        return

    for order in orders:
        for plant in order.plants:
            # Roll random plant sentence
            plant_template = random.choice(plant_sentences)
            plant.plant_text = plant_template.replace('{order_plant_name}', plant.name_fi)

            # Roll random amount sentence
            amount_template = random.choice(amount_sentences)
            plant.amount_text = amount_template.replace('{order_amount}', str(plant.amount))

    debug.info(f"Rolled text for {len(orders)} orders")


class OrderTextRoller:
    """
    Helper class to load sentences once and roll text for orders.
    """

    def __init__(self):
        self.sentences: Dict[str, List[str]] = {'plant': [], 'amount': []}
        self.is_loaded = False

    def load_sentences(self, yaml_path: str = None):
        """Load sentences from YAML file."""
        if yaml_path is None:
            # Default path
            yaml_path = Path(__file__).parent.parent.parent / "data" / "order_sentences.yaml"

        self.sentences = load_sentences_from_yaml(str(yaml_path))
        self.is_loaded = True

    def roll_for_orders(self, orders: List[Order]):
        """Roll text for all plants in the given orders."""
        if not self.is_loaded:
            self.load_sentences()

        roll_text_for_orders(orders, self.sentences)

import json
import random
from itertools import product, islice
from datetime import datetime, timedelta
from typing import Dict, List, Iterator
from seed.core.path_utils import resource_path

from pricing import generate_prices
# from ..config.seed_settings import CURRENT_PROFILE
from ..config.seed_settings import load_settings

class ProductGenerator:
    def __init__(
        self,
        base_file: str | None = None,
        max_variations_per_product: int = 40
    ):
        if base_file is None:
            base_file = resource_path("products_base.json")

        self.base_file = base_file
        self.max_variations_per_product = max_variations_per_product

        with open(base_file, encoding="utf-8") as f:
            self.base_data = json.load(f)

        # 🔑 Mapeia categoria → id baseado na ORDEM do JSON
        self.category_id_map = {
            category_name: idx + 1
            for idx, category_name in enumerate(self.base_data.keys())
        }

    # =========================
    # VARIAÇÕES
    # =========================
    def _generate_variation_combinations(
        self,
        variations: Dict[str, List[str]]
    ) -> Iterator[Dict[str, str]]:
        if not variations:
            return iter([{}])

        keys = list(variations.keys())
        values = [variations[k] for k in keys]

        combinations = product(*values)
        limited = islice(combinations, self.max_variations_per_product)

        for combo in limited:
            yield dict(zip(keys, combo))

    # =========================
    # PRODUTO
    # =========================
    def _format_product_name(
        self,
        base_name: str,
        attributes: Dict[str, str]
    ) -> str:
        if not attributes:
            return base_name
        return f"{base_name} " + " ".join(attributes.values())

    def _build_product(
        self,
        base_name: str,
        attributes: Dict[str, str],
        category: str
    ) -> Dict:
        cost_price, sale_price = generate_prices(category)
        date_added = datetime.now() - timedelta(days=random.randint(0, 180))

        name = self._format_product_name(base_name, attributes)

        return {
            "name": name,
            "description": f"Produto {name}",
            "cost_price": cost_price,
            "sale_price": sale_price,
            "date_added": date_added.date().isoformat(),
            "active": False,
            "category_id": self.category_id_map[category]
        }

    # =========================
    # API PÚBLICA (SEED)
    # =========================
    def generate(self, count: int = None) -> List[Dict]:
        limit = count or load_settings()["CURRENT_PROFILE"].products_count
        products: List[Dict] = []

        categories = list(self.base_data.items())
        per_category_limit = max(1, limit // len(categories))

        for category, category_data in categories:
            category_products: List[Dict] = []

            for subcategory_data in category_data.values():

                base_products = subcategory_data.get("base_products", [])
                variations = subcategory_data.get("variations", {})

                variation_combinations = list(
                    self._generate_variation_combinations(variations)
                )

                for base_name in base_products:
                    for attrs in variation_combinations:
                        category_products.append(
                            self._build_product(
                                base_name=base_name,
                                attributes=attrs,
                                category=category
                            )
                        )

                        if len(category_products) >= per_category_limit:
                            break
                    if len(category_products) >= per_category_limit:
                        break
                if len(category_products) >= per_category_limit:
                    break

            products.extend(category_products)

            if len(products) >= limit:
                # random.shuffle(products)
                return products

        random.shuffle(products)
        return products[:limit]

import json
import random
from itertools import product, islice
from datetime import datetime, timedelta
from typing import Dict, List, Iterator

from pricing import generate_prices


# =========================
# VARIAÇÕES
# =========================

def generate_variation_combinations(
    variations: Dict[str, List[str]],
    max_combinations: int
) -> Iterator[Dict[str, str]]:
    """
    Gera combinações de variações de forma controlada (lazy),
    evitando explosão combinatória.
    """
    if not variations:
        return iter([{}])

    keys = list(variations.keys())
    values = [variations[k] for k in keys]

    combinations = product(*values)
    limited = islice(combinations, max_combinations)

    for combo in limited:
        yield dict(zip(keys, combo))


# =========================
# PRODUTO
# =========================

def format_product_name(base_name: str, attributes: Dict[str, str]) -> str:
    if not attributes:
        return base_name
    return f"{base_name} " + " ".join(attributes.values())


def build_product(
    base_name: str,
    attributes: Dict[str, str],
    category: str
) -> Dict:
    cost_price, sale_price = generate_prices(category)
    date_added = datetime.now() - timedelta(days=random.randint(0, 180))

    name = format_product_name(base_name, attributes)

    return {
        "name": name,
        "description": f"Produto {name}",
        "cost_price": cost_price,
        "sale_price": sale_price,
        "date_added": date_added.date().isoformat(),
        "active": False,
        "category": category
    }


# =========================
# GERADOR PRINCIPAL
# =========================

def generate_products(
    base_file: str = "products_base.json",
    limit: int = 500,
    max_variations_per_product: int = 40
) -> List[Dict]:
    """
    Gera produtos respeitando limite global e evitando processamento desnecessário.
    """
    with open(base_file, encoding="utf-8") as f:
        base_data = json.load(f)

    products: List[Dict] = []

    for category, category_data in base_data.items():
        for subcategory_data in category_data.values():

            base_products = subcategory_data.get("base_products", [])
            variations = subcategory_data.get("variations", {})

            variation_combinations = list(
                generate_variation_combinations(
                    variations,
                    max_variations_per_product
                )
            )

            for base_name in base_products:
                for attrs in variation_combinations:

                    products.append(
                        build_product(
                            base_name=base_name,
                            attributes=attrs,
                            category=category
                        )
                    )

                    if len(products) >= limit:
                        random.shuffle(products)
                        return products

    random.shuffle(products)
    return products


# =========================
# EXPORTAÇÃO
# =========================

def export_json(
    products: List[Dict],
    filename: str = "generated_products.json"
) -> None:
    payload = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_products": len(products)
        },
        "products": products
    }

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=4)

    print(f"Exported {len(products)} products to {filename}")


# =========================
# EXECUÇÃO (opcional)
# =========================

if __name__ == "__main__":
    products = generate_products(limit=500)
    export_json(products)

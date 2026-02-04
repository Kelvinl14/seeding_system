import random

PRICE_RANGES = {
    "Eletrônicos": (1200, 4000),
    "Informática": (80, 5000),
    "Alimentos": (5, 60),
    "Bebidas": (3, 15),
    "Higiene": (6, 40),
    "Limpeza": (4, 50),
    "Papelaria": (3, 80),
    "Acessórios": (15, 200)
}

def generate_prices(category):
    min_price, max_price = PRICE_RANGES[category]
    sale_price = round(random.uniform(min_price, max_price), 2)
    cost_price = round(sale_price * random.uniform(0.6, 0.8), 2)
    return cost_price, sale_price

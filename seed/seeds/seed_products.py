from ..core.base_seed import BaseSeed
from ..core.db_utils import fast_insert
from ..generators.product_generator import ProductGenerator


class SeedProducts(BaseSeed):
    def execute(self, cur):
        generator = ProductGenerator()
        products = generator.generate(self.profile.products_count)
        
        columns = ["name", "description", "cost_price", "sale_price", "date_added", "active", "category_id"]
        values = [
            (p["name"], p["description"], p["cost_price"], p["sale_price"], p["date_added"], p["active"], p["category_id"])
            for p in products
        ]
        
        # Usamos ON CONFLICT (name) DO NOTHING para garantir idempotência
        fast_insert(cur, "products", columns, values, on_conflict="(name) DO NOTHING")
        
        # Retornar IDs para os próximos estágios
        cur.execute("SELECT id FROM products")
        return [row[0] for row in cur.fetchall()]

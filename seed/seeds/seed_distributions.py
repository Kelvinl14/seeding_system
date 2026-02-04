import random
import requests
from datetime import datetime, timedelta
from ..core.base_seed import BaseSeed
from ..core.db_utils import fast_insert

API_URL = "https://systock-api.onrender.com/internal-distributions"
STOCK_API_URL = "https://systock-api.onrender.com/stock"

class SeedDistributions(BaseSeed):
    def execute(self, cur):
        cur.execute("SELECT id FROM products")
        product_ids = [r[0] for r in cur.fetchall()]
        
        cur.execute("SELECT id FROM stores")
        stores = [r[0] for r in cur.fetchall()]
        if len(stores) < 2:
            # Garantir pelo menos duas lojas para distribuição
            fast_insert(cur, "stores", ["name", "location"], [("Estoque Central", "Sede"), ("Loja Filial", "Shopping")])
            cur.execute("SELECT id FROM stores")
            stores = [r[0] for r in cur.fetchall()]

        dist_count = self.profile.distributions_count
        
        for _ in range(dist_count):
            from_store, to_store = random.sample(stores, 2)
            cur.execute(
                "INSERT INTO internal_distributions (from_store_id, to_store_id, distribution_date, status) VALUES (%s, %s, %s, 'completed') RETURNING id",
                (from_store, to_store, datetime.now() - timedelta(days=random.randint(0, 30)))
            )
            dist_id = cur.fetchone()[0]
            
            num_items = random.randint(3, 10)
            selected_products = random.sample(product_ids, min(num_items, len(product_ids)))
            
            items_values = [(dist_id, pid, random.randint(5, 20)) for pid in selected_products]
            fast_insert(cur, "internal_distribution_items", ["internal_distribution_id", "product_id", "quantity"], items_values)
            
        return True

class SeedDistributionsAPI(BaseSeed):
    """
    Seed de distribuições internas via API
    (garante transfer_in / transfer_out corretamente)
    """

    def execute(self, cur):
        # =============================
        # Buscar Stock
        # =============================
        stock = requests.get(
            f"{STOCK_API_URL}/all",
            timeout=30
        ).json()

        if not stock:
            raise RuntimeError("Nenhum dado de estoque retornado pela API")

        quantity_map = {item['product_id']: item['quantity'] for item in stock if item['quantity'] > 0}

        # =============================
        # Buscar lojas
        # =============================
        cur.execute("SELECT id FROM stores ORDER BY id")
        store_ids = [r[0] for r in cur.fetchall()]

        if len(store_ids) < 2:
            raise RuntimeError("São necessárias ao menos 2 lojas para distribuição")

        FROM_STORE_ID = 1
        target_stores = [sid for sid in store_ids if sid != FROM_STORE_ID]

        # # =============================
        # # Buscar produtos
        # # =============================
        # cur.execute("SELECT id FROM products")
        # product_ids = [r[0] for r in cur.fetchall()]
        #
        # if not product_ids:
        #     raise RuntimeError("Nenhum produto encontrado para seed de distribuições")


        distributions_count = self.profile.distributions_count

        for _ in range(distributions_count):
            to_store_id = random.choice(target_stores)

            distribution_date = datetime.utcnow() - timedelta(
                days=random.randint(0, 180)
            )

            num_items = random.randint(3, 8)
            selected_products = random.sample(
                list(quantity_map.items()), min(num_items, len(quantity_map))
            )

            items = []
            for itens in selected_products:
                product_id = itens[0]
                if quantity_map[product_id] <= 1:
                    continue

                quantity = random.randint(1, itens[1])

                items.append({
                    "product_id": product_id,
                    "quantity": quantity,
                    "registered_at": distribution_date.isoformat(),
                })

                # Diminuir a quantidade disponível para evitar overbooking
                quantity_map[product_id] -= quantity

            payload = {
                "from_store_id": FROM_STORE_ID,
                "to_store_id": to_store_id,
                "distribution_date": distribution_date.isoformat(),
                "status": "completed",
                "items": items,
            }

            response = requests.post(API_URL, json=payload, timeout=30)

            if response.status_code not in (200, 201):
                raise RuntimeError(
                    f"Erro ao criar distribuição via API: "
                    f"{response.status_code} - {response.text}"
                )

        return True
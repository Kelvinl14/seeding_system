import random
import requests
from datetime import datetime, timedelta
from ..core.base_seed import BaseSeed
from ..core.db_utils import fast_insert

API_BASE = "https://systock-api.onrender.com"

class SeedSales(BaseSeed):
    def execute(self, cur):
        cur.execute("SELECT id FROM products")
        product_ids = [r[0] for r in cur.fetchall()]
        
        cur.execute("SELECT id FROM stores")
        store_ids = [r[0] for r in cur.fetchall()]
        
        cur.execute("SELECT id FROM clients LIMIT 100")
        client_ids = [r[0] for r in cur.fetchall()]
        if not client_ids:
            # Criar alguns clientes se não existirem
            clients = [(f"Cliente {i}", f"cliente{i}@email.com") for i in range(10)]
            fast_insert(cur, "clients", ["name", "email"], clients)
            cur.execute("SELECT id FROM clients")
            client_ids = [r[0] for r in cur.fetchall()]

        sales_count = self.profile.sales_count
        
        for _ in range(sales_count):
            cur.execute(
                "INSERT INTO sales (client_id, store_id, sale_date, status) VALUES (%s, %s, %s, 'completed') RETURNING id",
                (random.choice(client_ids), random.choice(store_ids), datetime.now() - timedelta(days=random.randint(0, 60)))
            )
            sale_id = cur.fetchone()[0]
            
            num_items = random.randint(1, 5)
            selected_products = random.sample(product_ids, min(num_items, len(product_ids)))
            
            items_values = []
            for pid in selected_products:
                qty = random.randint(1, 3)
                price = round(random.uniform(50, 500), 2)
                items_values.append((sale_id, pid, qty, price, round(qty * price, 2)))
            
            fast_insert(cur, "sale_items", ["sale_id", "product_id", "quantity", "unit_price", "total_price"], items_values)
            
        return True

# class SeedSalesAPI(BaseSeed):
#     def execute(self, cur):
#         # =========================
#         # CLIENTES
#         # =========================
#         cur.execute("SELECT id FROM clients")
#         client_ids = [r[0] for r in cur.fetchall()]
#         if not client_ids:
#             raise RuntimeError("Nenhum cliente encontrado para gerar vendas.")
#
#         # =========================
#         # LOJA (fixa)
#         # =========================
#         store_id = 1
#
#         # =========================
#         # ESTOQUE VIA API
#         # =========================
#         resp = requests.get(f"{API_BASE}/stock", timeout=30)
#         resp.raise_for_status()
#         stock_data = resp.json()
#
#
#         # Filtrar apenas produtos com estoque disponível na loja 1
#         available_stock = [
#             s for s in stock_data
#             if s["store_id"] == store_id and s["quantity"] > 0
#         ]
#
#         quantity_map = {item['product_id']: item['quantity'] for item in stock_data if item['quantity'] > 0}
#
#         if not available_stock:
#             raise RuntimeError("Nenhum produto com estoque disponível para vendas.")
#
#         sales_count = self.profile.sales_count
#
#         for _ in range(sales_count):
#             # =========================
#             # DATA DA VENDA
#             # =========================
#             sale_date = datetime.utcnow() - timedelta(days=random.randint(0, 180))
#
#             # =========================
#             # ITENS DA VENDA
#             # =========================
#             num_items = random.randint(1, min(5, len(available_stock)))
#             selected_items = random.sample(available_stock, num_items)
#
#             items = []
#             total_value = 0.0
#
#             for stock in selected_items:
#                 product_id = stock["product_id"]
#
#                 # quantidade respeitando estoque
#                 qty = random.randint(1, min(5, stock["quantity"]))
#
#                 # buscar preço do produto no banco
#                 cur.execute(
#                     "SELECT sale_price FROM products WHERE id = %s",
#                     (product_id,)
#                 )
#                 row = cur.fetchone()
#                 if not row:
#                     continue
#
#                 unit_price = float(row[0])
#                 total_price = round(unit_price * qty, 2)
#                 total_value += total_price
#
#                 items.append({
#                     "product_id": product_id,
#                     "quantity": qty,
#                     "unit_price": unit_price,
#                     "total_price": total_price,
#                     "removed_at": sale_date.isoformat()
#                 })
#
#             if not items:
#                 continue
#
#             # =========================
#             # PAYLOAD DA VENDA
#             # =========================
#             payload = {
#                 "client_id": random.choice(client_ids),
#                 "store_id": store_id,
#                 "sale_date": sale_date.isoformat(),
#                 "delivery_type": random.choice(["pickup", "delivery"]),
#                 "tracking_code": f"TRK-{random.randint(100000, 999999)}",
#                 "status": "completed",
#                 "predicted_delivery": (sale_date + timedelta(days=3)).isoformat(),
#                 "delivered_at": (sale_date + timedelta(days=3)).isoformat(),
#                 "total_value": round(total_value, 2),
#                 "items": items
#             }
#
#             # =========================
#             # POST NA API
#             # =========================
#             response = requests.post(
#                 f"{API_BASE}/sales",
#                 json=payload,
#                 timeout=30
#             )
#
#             if response.status_code not in (200, 201):
#                 raise RuntimeError(
#                     f"Erro ao criar venda: {response.status_code} - {response.text}"
#                 )
#
#         return True

class SeedSalesAPI(BaseSeed):
    """
    Seed de vendas via API
    - Vende apenas de lojas != 1
    - Valida estoque via API
    - Evita overbooking
    """

    def execute(self, cur):
        # =============================
        # Buscar estoque via API
        # =============================
        stock_data = requests.get(f"{API_BASE}/stock/all", timeout=30).json()

        if not stock_data:
            raise RuntimeError("Nenhum estoque encontrado para seed de vendas")

        # stock_map[store_id][product_id] = quantity
        stock_map = {}
        for item in stock_data:
            if item["quantity"] > 0 and item["store_id"] != 1:
                stock_map.setdefault(item["store_id"], {})[
                    item["product_id"]
                ] = item["quantity"]

        if not stock_map:
            raise RuntimeError("Nenhuma loja com estoque disponível para vendas")

        # =============================
        # Buscar clientes
        # =============================
        cur.execute("SELECT id FROM clients")
        client_ids = [r[0] for r in cur.fetchall()]

        if not client_ids:
            raise RuntimeError("Nenhum cliente encontrado para seed de vendas")

        sales_count = self.profile.sales_count

        for _ in range(sales_count):
            # =============================
            # Escolher loja válida
            # =============================
            valid_stores = [
                sid for sid, products in stock_map.items()
                if any(qty > 0 for qty in products.values())
            ]

            if not valid_stores:
                break  # estoque acabou

            store_id = random.choice(valid_stores)

            # Produtos disponíveis nessa loja
            available_products = [
                (pid, qty)
                for pid, qty in stock_map[store_id].items()
                if qty > 0
            ]

            if not available_products:
                continue

            num_items = random.randint(1, min(5, len(available_products)))
            selected_products = random.sample(available_products, num_items)

            items = []
            total_value = 0.0

            sale_date = datetime.utcnow() - timedelta(
                days=random.randint(0, 180)
            )

            for product_id, available_qty in selected_products:
                if available_qty <= 1:
                    continue

                quantity = random.randint(1, available_qty)

                # Buscar preço do produto
                cur.execute(
                    "SELECT sale_price FROM products WHERE id = %s",
                    (product_id,)
                )
                row = cur.fetchone()
                if not row:
                    continue

                unit_price = float(row[0])
                total_price = round(unit_price * quantity, 2)

                items.append({
                    "product_id": product_id,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "total_price": total_price,
                    "removed_at": sale_date.isoformat(),
                })

                total_value += total_price

                # Atualizar estoque local
                stock_map[store_id][product_id] -= quantity

            if not items:
                continue

            payload = {
                "client_id": random.choice(client_ids),
                "store_id": store_id,
                "sale_date": sale_date.isoformat(),
                "delivery_type": random.choice(["pickup", "delivery"]),
                "tracking_code": f"TRK-{random.randint(100000,999999)}",
                "status": "completed",
                "predicted_delivery": sale_date.isoformat(),
                "delivered_at": sale_date.isoformat(),
                "total_value": round(total_value, 2),
                "items": items,
            }

            response = requests.post(f"{API_BASE}/sales", json=payload, timeout=30)

            if response.status_code not in (200, 201):
                raise RuntimeError(
                    f"Erro ao criar venda: "
                    f"{response.status_code} - {response.text}"
                )

        return True
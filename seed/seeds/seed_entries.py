import random
import uuid
import requests
from datetime import datetime, timedelta
from ..core.base_seed import BaseSeed
from ..core.db_utils import fast_insert


# Categorias que NÃO possuem validade
NO_EXPIRATION_CATEGORIES = {1}  # Ex: Eletrônicos = 1

API_URL = "https://systock-api.onrender.com/entries"

class SeedEntries(BaseSeed):
    def execute(self, cur):
        # Produtos com dados necessários
        cur.execute("""
            SELECT id, sale_price, category_id
            FROM products
        """)
        products = cur.fetchall()
        if not products:
            raise RuntimeError("Nenhum produto encontrado para gerar entradas.")

        # Fornecedores
        cur.execute("SELECT id FROM suppliers")
        supplier_ids = [r[0] for r in cur.fetchall()]
        if not supplier_ids:
            raise RuntimeError("Nenhum fornecedor encontrado.")

        entries_count = self.profile.entries_count

        for _ in range(entries_count):
            supplier_id = random.choice(supplier_ids)

            entry_date = datetime.now() - timedelta(days=random.randint(0, 180))
            invoice_number = f"INV-{uuid.uuid4().hex[:12].upper()}"

            # Cria entrada
            cur.execute(
                """
                INSERT INTO product_entries
                    (supplier_id, entry_date, invoice_number, status)
                VALUES (%s, %s, %s, 'completed')
                RETURNING id
                """,
                (supplier_id, entry_date, invoice_number)
            )
            entry_id = cur.fetchone()[0]

            # Selecionar itens
            num_items = random.randint(3, 10)
            selected_products = random.sample(products, min(num_items, len(products)))

            items = []
            total_entry_value = 0.0

            for product_id, sale_price, category_id in selected_products:
                quantity = random.randint(5, 100)
                unit_price = sale_price
                total_price = round(quantity * unit_price, 2)
                total_entry_value += total_price

                lot_number = f"LOT-{uuid.uuid4().hex[:8].upper()}"

                expiration_date = None
                if category_id not in NO_EXPIRATION_CATEGORIES:
                    expiration_date = datetime.now() + timedelta(days=random.randint(90, 720))

                items.append((
                    entry_id,
                    product_id,
                    quantity,
                    unit_price,
                    total_price,
                    lot_number,
                    expiration_date,
                    entry_date
                ))

            fast_insert(
                cur,
                "product_entry_items",
                [
                    "product_entry_id",
                    "product_id",
                    "quantity",
                    "unit_price",
                    "total_price",
                    "lot_number",
                    "expiration_date",
                    "received_at"
                ],
                items
            )

            # Atualizar total da entrada
            cur.execute(
                "UPDATE product_entries SET total_value = %s WHERE id = %s",
                (round(total_entry_value, 2), entry_id)
            )

        return True

class SeedEntriesAPI(BaseSeed):
    """
    Seed de entradas usando a API (garante estoque + movimentos)
    """

    def execute(self, cur):
        # =============================
        # Buscar produtos
        # =============================
        cur.execute("""
            SELECT id, sale_price, category_id
            FROM products
        """)
        products = cur.fetchall()

        if not products:
            raise RuntimeError("Nenhum produto encontrado para seed de entradas")

        # =============================
        # Buscar fornecedores
        # =============================
        cur.execute("SELECT id FROM suppliers")
        suppliers = [r[0] for r in cur.fetchall()]

        if not suppliers:
            raise RuntimeError("Nenhum fornecedor encontrado para seed de entradas")

        entries_count = self.profile.entries_count

        for _ in range(entries_count):
            supplier_id = random.choice(suppliers)

            entry_date = datetime.utcnow() - timedelta(
                days=random.randint(0, 180)
            )

            invoice_number = f"NF-{random.randint(100000, 999999)}"

            # =============================
            # Criar itens
            # =============================
            num_items = random.randint(3, 10)
            selected_products = random.sample(
                products, min(num_items, len(products))
            )

            items = []
            total_value = 0.0

            for product_id, sale_price, category_id in selected_products:
                quantity = random.randint(5, 50)
                unit_price = float(sale_price)
                total_price = round(quantity * unit_price, 2)

                total_value += total_price

                # 👉 validade apenas para categorias que exigem
                expiration_date = None
                if self._category_has_expiration(category_id):
                    expiration_date = datetime.utcnow() + timedelta(
                        days=random.randint(90, 720)
                    )

                items.append({
                    "product_id": product_id,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "total_price": total_price,
                    "lot_number": f"LOT-{random.randint(1000, 9999)}",
                    "expiration_date": expiration_date.isoformat() if expiration_date else None,
                    "received_at": entry_date.isoformat(),
                })

            payload = {
                "supplier_id": supplier_id,
                "entry_date": entry_date.isoformat(),
                "invoice_number": invoice_number,
                "total_value": round(total_value, 2),
                "status": "completed",
                "items": items,
            }

            response = requests.post(API_URL, json=payload, timeout=30)

            if response.status_code not in (200, 201):
                raise RuntimeError(
                    f"Erro ao criar entrada via API: {response.status_code} - {response.text}"
                )

        return True

    # =====================================================
    # Regra simples de validade (ajuste conforme domínio)
    # =====================================================
    def _category_has_expiration(self, category_id: int) -> bool:
        """
        Exemplo:
        - Eletrônicos -> False
        - Alimentos / Farmácia -> True
        """
        CATEGORIES_WITH_EXPIRATION = {2, 3, 4}  # ajuste conforme seu banco
        return category_id in CATEGORIES_WITH_EXPIRATION
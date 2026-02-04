import requests

STOCK_API_URL = "https://systock-api.onrender.com/stock"

def test_stock_api_connection():
    try:
        response = requests.get(STOCK_API_URL)
        if response.status_code == 200:
            print("Conexão bem-sucedida com a API de estoque.")
        else:
            print(f"Falha na conexão com a API de estoque. Status code: {response.status_code}")
    except Exception as e:
        print(f"Ocorreu um erro ao tentar conectar à API de estoque: {e}")

# product_ids = list(range(1, 51))
# FROM_STORE_ID = 1
#
# for product_id in product_ids:
#     stock = requests.get(
#         f"{STOCK_API_URL}?store_id={FROM_STORE_ID}&product_id={product_id}",
#         timeout=30
#     ).json()
#
#     # verificar se a chave "quantity" existe na resposta
#     if not stock or "quantity" not in stock[0]:
#         print(f"Resposta inválida para o produto {product_id}: {stock}")
#         continue
#
#     qtn_available = stock[0].get("quantity")
#     print(qtn_available)
import random

stock = requests.get(
    f"{STOCK_API_URL}/all",
    timeout=30
).json()

# products_in_stock = [item['product_id'] for item in stock if item['quantity'] > 0]
quantity_map = {item['product_id']: item['quantity'] for item in stock if item['quantity'] > 0}
print(quantity_map)

num_items = random.randint(3, 8)
selected_products = random.sample(
    list(quantity_map.items()), min(num_items, len(quantity_map))
)
for itens in selected_products:
    product_id = itens[0]
    quantity = random.randint(1, itens[1])
    print(f"Produto ID: {product_id}, Quantidade a distribuir: {quantity}")


    quantity_map[product_id] -= quantity
print(quantity_map)
# for item in stock:
#     print(f"Produto ID: {item['product_id']}, Quantidade: {item['quantity']}")

# fução para retornar a lista de produtos com estoque maior que zero e a quantidade disponível
def get_available_products(stock_data):
    available_products = []
    for item in stock_data:
        if item['quantity'] > 0:
            available_products.append((item['product_id'], item['quantity']))
    return available_products

# for product_id, quantity in get_available_products(stock):
#     print(f"Produto ID: {product_id}, Quantidade disponível: {quantity}")

if __name__ == "__main__":
    pass
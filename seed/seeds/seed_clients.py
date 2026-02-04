from ..core.base_seed import BaseSeed
from ..core.db_utils import fast_insert
from ..generators.client_generator import ClientGenerator

class SeedClients(BaseSeed):
    def execute(self, cur):
        generator = ClientGenerator()
        clients = generator.generate(self.profile.clients_count)
        
        columns = ["name", "cpf_cnpj", "email", "phone", "address"]
        values = [
            (c["name"], c["cpf_cnpj"], c["email"], c["phone"], c["address"])
            for c in clients
        ]
        
        # Usamos ON CONFLICT (cpf_cnpj) DO NOTHING para garantir idempotência
        fast_insert(cur, "clients", columns, values, on_conflict="(cpf_cnpj) DO NOTHING")
        
        cur.execute("SELECT id FROM clients")
        return [row[0] for row in cur.fetchall()]

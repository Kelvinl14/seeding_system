import random
import hashlib
from typing import List, Dict
# from ..config.seed_settings import CURRENT_PROFILE
from ..config.seed_settings import load_settings
class ClientGenerator:
    def __init__(self):
        self.first_names = ["João", "Maria", "José", "Ana", "Pedro", "Paula", "Lucas", "Julia", "Carlos", "Beatriz", "Rafael", "Mariana", "Gabriel", "Larissa", "Felipe", "Camila"]
        self.last_names = ["Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves", "Pereira", "Lima", "Gomes", "Ribeiro", "Carvalho", "Martins", "Rocha", "Dias", "Nunes"]
        self.domains = ["gmail.com", "outlook.com", "hotmail.com", "empresa.com.br", "yahoo.com.br", "uol.com.br"]

    def generate_cpf(self) -> str:
        """Gera um CPF fictício formatado."""
        cpf = [random.randint(0, 9) for _ in range(9)]
        for _ in range(2):
            val = sum([(len(cpf) + 1 - i) * v for i, v in enumerate(cpf)]) % 11
            cpf.append(11 - val if val > 1 else 0)
        return "{}{}{}.{}{}{}.{}{}{}-{}{}".format(*cpf)

    def generate(self, count: int = None) -> List[Dict]:
        count = count or getattr(load_settings()["CURRENT_PROFILE"], 'clients_count', 100)
        clients = []
        
        for i in range(count):
            first = random.choice(self.first_names)
            last = random.choice(self.last_names)
            segundo_last = random.choice(self.last_names)

            if last == segundo_last:
                name = f"{first} {last}"
            else:
                name = f"{first} {last} {segundo_last}"

            
            email = f"{first.lower()}.{last.lower()}{i}@{random.choice(self.domains)}"
            cpf = self.generate_cpf()
            phone = f"(11) 9{random.randint(7000, 9999)}-{random.randint(1000, 9999)}"
            address = f"Rua {random.choice(self.last_names)}, {random.randint(1, 2000)} - Bairro {random.choice(self.first_names)}"
            
            clients.append({
                "name": name,
                "cpf_cnpj": cpf,
                "email": email,
                "phone": phone,
                "address": address
            })
        return clients

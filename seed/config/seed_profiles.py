from enum import Enum
from dataclasses import dataclass

class SeedSize(Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    STRESS = "stress"
    CUSTOM = "custom"

@dataclass
class SeedProfile:
    products_count: int
    clients_count: int
    entries_count: int
    distributions_count: int
    sales_count: int
    batch_size: int = 500

PROFILES = {
    SeedSize.SMALL: SeedProfile(
        products_count=50,
        clients_count=20,
        entries_count=20,
        distributions_count=15,
        sales_count=30
    ),
    SeedSize.MEDIUM: SeedProfile(
        products_count=500,
        clients_count=100,
        entries_count=200,
        distributions_count=150,
        sales_count=300
    ),
    SeedSize.LARGE: SeedProfile(
        products_count=5000,
        clients_count=1000,
        entries_count=2000,
        distributions_count=1500,
        sales_count=3000
    ),
    SeedSize.STRESS: SeedProfile(
        products_count=50000,
        clients_count=10000,
        entries_count=20000,
        distributions_count=15000,
        sales_count=30000,
        batch_size=1000
    )
}

# Arquitetura de Seeding de Dados para Projeto Python + PostgreSQL

## 1. Introdução

Este documento apresenta a proposta de arquitetura e implementação de um sistema de *seeding* de dados profissional, robusto e de alta performance para o projeto Python + PostgreSQL existente. O sistema foi projetado para atender aos requisitos de **idempotência**, **configurabilidade**, **segurança** e **otimização** para o ambiente **Render** e o banco de dados **PostgreSQL**.

## 2. Arquitetura Proposta

A estrutura de diretórios proposta adota um padrão modular e escalável, separando claramente as responsabilidades:

```
seed/
 ├─ config/
 │   ├─ seed_settings.py        # Configurações de ambiente e flags de segurança
 │   └─ seed_profiles.py        # Definição dos perfis de volume (SMALL, MEDIUM, LARGE, STRESS)
 │
 ├─ core/
 │   ├─ base_seed.py            # Classe base para todos os seeds (logging, transação, rollback)
 │   ├─ seed_runner.py          # Orquestrador de execução e guardrails de segurança
 │   └─ db_utils.py             # Funções otimizadas de DB (e.g., fast_insert com execute_values)
 │
 ├─ generators/
 │   ├─ product_generator.py    # Lógica de geração de dados realistas e determinísticos
 │
 ├─ seeds/
 │   ├─ seed_products.py        # Seed específico para a tabela 'products'
 │   ├─ seed_entries.py         # Seed específico para a tabela 'product_entries'
 │   ├─ seed_distributions.py   # Seed específico para a tabela 'internal_distributions'
 │   └─ seed_sales.py           # Seed específico para a tabela 'sales'
 │
 └─ seed_database_v2.py         # Ponto de entrada principal
```

## 3. Sistema de Configuração (Mandatório)

O sistema de configuração é baseado em variáveis de ambiente e um módulo de perfis (`seed_profiles.py`), garantindo flexibilidade e segurança.

| Variável de Ambiente | Descrição | Valores Possíveis | Padrão |
| :--- | :--- | :--- | :--- |
| `APP_ENV` | Ambiente de execução | `DEV`, `STAGING`, `RENDER`, `PROD` | `DEV` |
| `SEED_SIZE` | Perfil de volume de dados | `SMALL`, `MEDIUM`, `LARGE`, `STRESS`, `CUSTOM` | `MEDIUM` |
| `FORCE_SEED` | Flag de segurança para ambientes de produção | `true`, `false` | `false` |
| `DRY_RUN` | Simulação (não implementado, mas reservado) | `true`, `false` | `false` |
| `SEED_PRODUCTS` | Volume customizado de produtos | Inteiro | 500 |
| `SEED_CLIENTS` | Volume customizado de clientes | Inteiro | 100 |

**Perfis de Volume (`seed_profiles.py`):**

| Perfil | Produtos | Clientes | Entradas | Distribuições | Vendas | Tamanho do Batch |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SMALL** | 50 | 20 | 20 | 15 | 30 | 500 |
| **MEDIUM** | 500 | 100 | 200 | 150 | 300 | 500 |
| **LARGE** | 5.000 | 1.000 | 2.000 | 1.500 | 3.000 | 500 |
| **STRESS** | 50.000 | 10.000 | 20.000 | 15.000 | 30.000 | 1.000 |

## 4. Data Integrity & Idempotência

A idempotência é crucial para permitir que o script seja executado com segurança em qualquer ambiente.

### 4.1. Estratégias de Idempotência

| Cenário | Estratégia Recomendada | Justificativa |
| :--- | :--- | :--- |
| **Tabelas Base** (e.g., `products`) | `ON CONFLICT (unique_column) DO NOTHING` | Ideal para dados que devem ser únicos e estáticos. Evita a re-inserção e é mais performático que um `SELECT` prévio. |
| **Tabelas de Transação** (e.g., `sales`, `entries`) | **Sempre Inserir** | Dados transacionais devem ser inseridos a cada execução, a menos que haja uma chave de unicidade de negócio clara (o que é raro para seeds). |
| **Dados Relacionais** (e.g., `product_entry_items`) | **Fetch de IDs Existentes** | Antes de inserir dados que dependem de chaves estrangeiras (FKs), o seed deve buscar os IDs existentes (e.g., `product_ids`, `store_ids`) para garantir a integridade referencial. |

### 4.2. Geração de Dados Únicos

O `product_generator.py` utiliza um **gerador determinístico de SKU** baseado em hash (`hashlib.md5`) do nome do produto. Isso garante que, para o mesmo nome de produto, o SKU gerado será sempre o mesmo, facilitando a idempotência baseada em chaves de negócio.

## 5. Otimização de Performance (PostgreSQL)

A performance é aprimorada através de técnicas específicas para o PostgreSQL.

### 5.1. Uso de `execute_values`

A função `fast_insert` em `db_utils.py` encapsula o uso de `psycopg2.extras.execute_values`. Esta é a otimização mais significativa, pois envia múltiplos registros em uma única consulta SQL, reduzindo drasticamente o *overhead* de comunicação de rede (*round-trips*) entre a aplicação e o banco de dados.

### 5.2. Controle de Transação

Cada estágio de seed (`SeedProducts`, `SeedEntries`, etc.) é executado dentro de um bloco `try...except` na classe `BaseSeed`.

*   **Sucesso:** `self.conn.commit()` é chamado ao final do método `run()`.
*   **Falha:** `self.conn.rollback()` é chamado, garantindo a **atomicidade** por estágio.

Isso evita *commits* desnecessários dentro de *loops* apertados, que degradam a performance do PostgreSQL.

### 5.3. Desativação de Triggers/Índices (Opcional)

Para volumes de dados na casa dos milhões (perfil `STRESS`), pode-se considerar a desativação temporária de *triggers* e índices não-únicos.

```python
# Em db_utils.py
def toggle_constraints(cur, table, enable=True):
    action = "ENABLE" if enable else "DISABLE"
    cur.execute(f"ALTER TABLE {table} {action} TRIGGER ALL")
```

**Quando é seguro:** Apenas para tabelas que não possuem chaves estrangeiras que seriam violadas e onde a lógica de negócio dos *triggers* pode ser ignorada durante o *seeding*. **Recomendação:** Usar apenas em testes de estresse e evitar em ambientes de produção, a menos que o volume de dados justifique e o risco seja mitigado.

## 6. Segurança e Confiabilidade

### 6.1. Guardrails de Produção

O `seed_runner.py` implementa um *guardrail* de segurança:

```python
if IS_PRODUCTION_LIKE and not FORCE_SEED:
    logger.warning("Targeting a production-like environment without FORCE_SEED=true. Aborting.")
    return
```

Se a variável `APP_ENV` for `RENDER`, `STAGING` ou `PROD`, a execução será abortada, a menos que a variável `FORCE_SEED=true` esteja explicitamente definida.

### 6.2. Ordem de Execução

A ordem de execução é estritamente definida para respeitar as chaves estrangeiras:

1.  1. `SeedProducts` (Tabelas Base)
2. `SeedClients` (Tabelas Base)
3. `SeedEntries` (Depende de `products` e `suppliers`)
4. `SeedDistributions` (Depende de `products` e `stores`)
5. `SeedSales` (Depende de `products`, `stores` e `clients`)

## 7. Considerações Específicas para o Render

O ambiente Render impõe restrições que foram consideradas no design:

| Restrição do Render | Solução na Arquitetura |
| :--- | :--- |
| **Long-running executions** | Uso de `BaseSeed` com *logging* explícito e *commits* por estágio. Isso permite rastrear o progresso e evita que uma única transação demore demais. |
| **Connection pooling limits** | O script abre e fecha a conexão uma única vez (`get_connection()` no `main`), minimizando o uso de *pools* e evitando a exaustão de conexões. |
| **Memory constraints** | Uso de `execute_values` e processamento em *batches* (`batch_size` no `SeedProfile`). Isso evita a construção de listas gigantescas de tuplas na memória antes da inserção. |
| **Network latency** | Otimização de *round-trips* através do `execute_values`, que é a melhor prática para reduzir o impacto da latência em inserções em massa. |

## 8. Guia de Uso

### 8.1. Execução

O script principal para CLI é `seed_database_v2.py`. Para a interface gráfica, use `seed_gui.py`.

```bash
# Execução padrão (Perfil MEDIUM)
python3 seed_database_v2.py

# Execução com perfil LARGE
SEED_SIZE=LARGE python3 seed_database_v2.py

# Execução customizada
SEED_SIZE=CUSTOM SEED_PRODUCTS=10000 SEED_SALES=5000 python3 seed_database_v2.py

# Execução em ambiente de produção (Render)
# O script irá abortar se não houver FORCE_SEED
APP_ENV=RENDER python3 seed_database_v2.py

# Execução forçada em ambiente de produção
APP_ENV=RENDER FORCE_SEED=true python3 seed_database_v2.py
```

### 8.2. Estrutura de Dados Necessária

O sistema assume a existência das seguintes tabelas (baseado na análise dos scripts originais):

*   `products`
*   `product_entries`
*   `product_entry_items`
*   `internal_distributions`
*   `internal_distribution_items`
*   `sales`
*   `sale_items`
*   `s* `suppliers`
* `stores`
* `clients` (com colunas `cpf_cnpj`, `email`, `phone`, `address`)

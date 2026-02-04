## Seeding System — Aplicação Desktop para Geração de Dados Fictícios

O **Seeding System** é uma **aplicação desktop independente**, desenvolvida especificamente para **povoar o banco de dados do Systock com dados fictícios**, permitindo testes, validações e análises de forma controlada e reproduzível.

Diferentemente de um script simples de seed, o Seeding System foi concebido como uma **ferramenta de apoio ao desenvolvimento e à análise de dados**, com foco em usabilidade, flexibilidade e geração de cenários realistas.

### 1 Objetivo do Seeding System

A aplicação desktop tem como principais objetivos:

* Automatizar a geração de grandes volumes de dados fictícios
* Simular cenários reais de estoque e produtos
* Facilitar testes funcionais, analíticos e de performance
* Garantir consistência dos dados utilizados no dashboard
* Reduzir dependência de dados reais em ambiente de desenvolvimento

### 2 Tipo de Aplicação

* **Tipo**: Aplicação Desktop
* **Finalidade**: Geração e inserção de dados fictícios
* **Integração**: Conexão direta com o banco de dados do sistema ou via API

A aplicação pode ser executada de forma isolada, sem dependência do front-end web.

### 3 Dados Gerados

O Seeding System é responsável pela geração de:

* Produtos fictícios
* Categorias de produtos
* Preços simulados
* Quantidades de estoque
* Distribuições variadas de dados para análise

Os dados são gerados com base em **regras controladas**, evitando valores inconsistentes ou inviáveis para análise.

### 4 Regras de Geração de Dados

Durante o processo de seeding, a aplicação respeita regras como:

* Preços dentro de faixas configuráveis
* Quantidades mínimas e máximas de estoque
* Distribuição equilibrada entre categorias
* Relacionamentos válidos entre entidades

Essas regras permitem a criação de cenários previsíveis ou aleatórios, conforme a necessidade do teste.

### 5 Funcionamento Técnico

O fluxo de funcionamento do Seeding System segue as etapas:

1. Configuração dos parâmetros de geração (quantidade de registros, faixas de valores, categorias)
2. Validação dos parâmetros
3. Geração dos dados fictícios
4. Inserção controlada no banco de dados ou envio para a API principal
5. Confirmação da operação

O processo foi projetado para minimizar erros e garantir integridade referencial.

### 6 Benefícios Arquiteturais

A adoção de uma aplicação desktop dedicada ao seeding traz benefícios como:

* Separação clara entre dados reais e dados de teste
* Maior controle sobre cenários de análise
* Facilidade de replicação do ambiente
* Apoio direto ao desenvolvimento do dashboard analítico

### 7 Uso em Análise de Dados

O Seeding System permite:

* Geração de dados suficientes para análise estatística
* Testes de performance das APIs
* Validação visual de gráficos e indicadores
* Simulação de crescimento de estoque e volume de dados

Isso garante que o dashboard seja validado em cenários próximos ao uso real.

### 8 Contexto no Projeto Systock

No contexto do Systock, o Seeding System atua como uma **ferramenta auxiliar**, essencial para:

* Desenvolvimento contínuo
* Demonstrações do sistema
* Avaliação técnica do projeto em ambiente acadêmico e profissional

---
### 9 Telas do sistema
![WhatsApp Image 2025-12-29 at 19 57 10](https://github.com/user-attachments/assets/305cdafc-d4b7-4683-b8a0-9df1dbf32d94)
![WhatsApp Image 2025-12-29 at 19 57 10 (1)](https://github.com/user-attachments/assets/7aac1f84-06fa-45c5-a0fb-7e0de40fe2ec)

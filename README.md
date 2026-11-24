# 💰 iFinanças — Sistema de Gestão Financeira Pessoal

<p align="center">
  <img src="logo.png" alt="Logo iFinanças" width="180">
</p>

<p align="center">
  **Organize suas finanças, acompanhe seus gastos e planeje seu futuro financeiro.**
</p>


## 📌 Sobre o projeto

O **iFinanças** é uma aplicação web desenvolvida para auxiliar no gerenciamento e planejamento financeiro pessoal.

A plataforma permite que os usuários controlem suas receitas e despesas, acompanhem sua situação financeira, estabeleçam objetivos de economia e realizem simulações de investimentos e financiamentos.

Além disso, o sistema conta com a importação de extratos bancários no formato OFX, facilitando o registro e a organização das movimentações financeiras.

O projeto foi desenvolvido como Trabalho de Conclusão de Curso (TCC), com o objetivo de aplicar conhecimentos de desenvolvimento web, programação, banco de dados e análise de informações.

## 🚀 Funcionalidades

### 👤 Gerenciamento de usuários
- Cadastro de novos usuários.
- Autenticação por e-mail e senha.
- Criptografia de senhas utilizando Bcrypt.
- Edição de informações do perfil.
- Exclusão de conta.

### 📊 Dashboard financeiro
- Visualização do saldo atual.
- Acompanhamento do total de receitas.
- Acompanhamento do total de despesas.
- Visualização das metas financeiras.
- Centralização das principais informações financeiras.

### 💵 Controle financeiro
- Cadastro de receitas.
- Cadastro de despesas.
- Registro de valores, datas, descrições e categorias.
- Organização das movimentações financeiras.
- Acompanhamento do saldo disponível.

### 📁 Importação de extratos bancários
- Importação de arquivos no formato OFX.
- Leitura automatizada das movimentações bancárias.
- Extração de datas, descrições e valores.
- Identificação e categorização de transações.
- Integração das movimentações com o controle financeiro.

### 🎯 Metas financeiras
- Criação de objetivos financeiros.
- Definição de valores e prazos.
- Acompanhamento do progresso das metas.
- Adição de valores às metas.
- Controle do saldo destinado aos objetivos.

### 📈 Simuladores financeiros

**Simulador de investimentos**
- Simulação de aplicações financeiras.
- Cálculo de rendimentos.
- Projeção de valores futuros.

**Simulador de financiamentos**
- Simulação de financiamentos.
- Definição do valor total do bem.
- Informações sobre entrada, juros e prazo.
- Cálculo das parcelas e dos valores envolvidos.

## 🛠️ Tecnologias utilizadas

| Tecnologia | Aplicação |
|---|---|
| Python | Linguagem principal do projeto |
| Flask | Framework para desenvolvimento web |
| MySQL | Gerenciamento do banco de dados |
| HTML5 | Estrutura das páginas |
| CSS3 | Estilização e interface |
| JavaScript | Recursos de interatividade |
| Pandas | Manipulação e análise de dados |
| NumPy | Operações e cálculos numéricos |
| OFXParse | Leitura de extratos bancários |
| Bcrypt | Hash e verificação de senhas |
| Jinja2 | Renderização dinâmica de páginas |

## 📂 Estrutura do projeto

```text
IFinancas/
│
├── conexao.py
├── simulador.py
├── style.css
├── logo.png
│
├── login.html
├── cadastro.html
├── dashboard.html
├── perfil.html
│
├── receita.html
├── despesa.html
├── meta.html
│
├── upload.html
├── simulador.html
├── simular-investimento.html
└── simular-financiamento.html
```

## ⚙️ Como executar o projeto

### 1. Clone o repositório

```bash
git clone https://github.com/henrymedeiros2007/IFinan-as.git
```

Entre na pasta:

```bash
cd IFinan-as
```

### 2. Crie um ambiente virtual

```bash
python -m venv venv
```

Ative o ambiente virtual:

**Windows:**
```bash
venv\Scripts\activate
```

**Linux / macOS:**
```bash
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install flask mysql-connector-python bcrypt pandas numpy ofxparse
```

### 4. Configure o banco de dados

Certifique-se de que o MySQL esteja instalado e em execução.

Crie o banco de dados:

```sql
CREATE DATABASE ifinancas;
```

Configure as credenciais de acesso ao MySQL no arquivo `conexao.py`, conforme seu ambiente.

**Importante:** o banco também precisa conter as tabelas utilizadas pela aplicação, como `usuario`, `receita`, `despesa` e `meta_financeira`.

### 5. Execute a aplicação

```bash
python conexao.py
```

Após iniciar o servidor, acesse:

```text
http://127.0.0.1:5000
```

## 🔐 Segurança

O projeto utiliza mecanismos para proteção das informações dos usuários, incluindo:

- Hash de senhas com Bcrypt.
- Controle de autenticação por sessão.
- Proteção de rotas que exigem login.
- Consultas parametrizadas ao banco de dados.

> Para utilização em produção, é necessário configurar corretamente as chaves secretas, credenciais do banco de dados, HTTPS e demais mecanismos de segurança.

## 🎓 Objetivo acadêmico

O iFinanças foi desenvolvido como Trabalho de Conclusão de Curso (TCC), buscando demonstrar a aplicação prática de conceitos de Engenharia de Software e Desenvolvimento de Sistemas na construção de uma solução para gestão financeira pessoal.

O projeto reúne conhecimentos de desenvolvimento backend, frontend, banco de dados, processamento de arquivos e implementação de funcionalidades financeiras.

## 👨‍💻 Desenvolvedores

**Henry Medeiros**

**Laís dos Santos Rosa**

## 📄 Licença

Projeto desenvolvido para fins acadêmicos e educacionais.

---

<p align="center">
  Desenvolvido com 💚 para facilitar a organização financeira.
</p>

# 📄 Extrator de Protocolos - SynSuite

Uma aplicação desktop desenvolvida em **Python + PySide6** para realizar login automático no sistema [SynSuite](https://synsuite.teninternet.com.br), extrair protocolos de atendimento com base em filtros específicos e exportá-los diretamente para uma planilha Excel (`.xlsx`).

---

## 🚀 Funcionalidades

- 🧾 Autenticação no sistema SynSuite via interface gráfica
- 📥 Extração automatizada dos protocolos visíveis na aba "Solicitações - Minhas"
- 📊 Apresentação dos resultados em uma tabela interativa
- 📤 Exportação dos dados diretamente para Excel (.xlsx)

---

## 🖼️ Interface Gráfica

A interface foi construída com **PySide6**, oferecendo uma experiência fluida:

- Tela de login com campos para usuário e senha
- Tabela de protocolos extraídos
- Botão para exportar os dados em Excel

---

## 🧰 Tecnologias Utilizadas

| Tecnologia     | Função                             |
|----------------|------------------------------------|
| `Python 3.10+` | Linguagem principal                |
| `PySide6`      | Interface gráfica (GUI)            |
| `requests`     | Comunicação com o SynSuite         |
| `pandas`       | Manipulação e exportação de dados  |

---

## 📦 Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/protocols_synsuite.git
cd protocols_synsuite

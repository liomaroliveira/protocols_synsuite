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

3. Instale as dependências
bash
Copiar
Editar
pip install -r requirements.txt
Se você ainda não criou o requirements.txt, pode fazer isso com:

bash
Copiar
Editar
pip freeze > requirements.txt

▶️ Como Executar
bash
Copiar
Editar
python seu_arquivo.py
Será aberta uma janela solicitando o login no SynSuite. Após o login, a extração é iniciada automaticamente.

📤 Exportação
Clique em "Exportar para Excel" para salvar os dados extraídos em um arquivo .xlsx. Um diálogo de salvamento será aberto para você escolher o local.

🛡️ Requisitos para funcionar
Acesso válido ao sistema SynSuite

O filtro "Solicitações - Minhas" precisa estar ativado por padrão

Conexão com a internet

📌 Observações Técnicas
A extração é feita via requests.Session, simulando os headers e payloads esperados pela interface SynSuite.

Os dados são buscados em pacotes de 25 registros por vez até atingir o limite ou os dados se esgotarem.

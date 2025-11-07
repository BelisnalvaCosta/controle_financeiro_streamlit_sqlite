# Controle Financeiro com Streamlit

Aplicativo web simples para controle financeiro pessoal usando Streamlit e SQLite.[^1]

<img width="1912" height="837" alt="controle-financeiro-streamlit" src="https://github.com/user-attachments/assets/0e7aba4b-2ee0-4d35-b9a7-119fb887f8a0" />

## 🚀 Funcionalidades
- Controle de despesas fixas e variáveis
- Configuração de saldo e renda mensal
- Interface amigável e fácil de usar
- Dados salvos localmente (SQLite)

## 📋 Requisitos
- Python 3.10 ou superior
- PowerShell (Windows) ou Terminal (Linux/Mac)

## ⚙️ Instalação Rápida

1. Clone o repositório e entre na pasta:
```powershell
git clone https://github.com/BelisnalvaCosta/controle_financeiro_streamlit_sqlite.git
cd controle_financeiro_streamlit_sqlite
```

2. Crie e ative o ambiente virtual:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Instale as dependências e rode:
```powershell
pip install -r requirements.txt
streamlit run app.py
```

## 💡 Como Usar
1. Configure seu perfil (nome, saldo, renda)
2. Adicione despesas fixas (aluguel, luz, etc)
3. Registre despesas variáveis do mês
4. Acompanhe seu saldo disponível

## 🔧 Problemas Comuns
- Erro "experimental_data_editor": Atualize o Streamlit (`pip install --upgrade streamlit`)
- Porta 8501 ocupada: Use `streamlit run app.py --server.port 8502`

## 📝 Licença
Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para detalhes.

## 👩‍💻 Contribuição
Contribuições são bem-vindas! Faça um fork e envie seu Pull Request.

[^1]: Projeto pessoal - fictício, pondo em prática a linguagem Python.

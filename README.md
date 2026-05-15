# 🛡️ ERP Guardian AI

**ERP Guardian AI** é uma plataforma de revisão de código e QA automatizado de nível empresarial, desenvolvida especificamente para ambientes ERP legados em Delphi. O sistema preenche a lacuna entre softwares empresariais tradicionais e fluxos de trabalho modernos de desenvolvimento orientados por IA.

---

## 🚀 Visão Geral

A plataforma oferece uma arquitetura modular e escalável para monitorar, analisar e testar sistemas ERP sem exigir mudanças invasivas no código legado.

### Principais Funcionalidades
- **Monitoramento Local**: Um agente Windows leve que rastreia modificações no **Jedi VCS**.
- **Análise de Impacto por IA**: Detecta mudanças críticas nos fluxos de trabalho do ERP e aciona revisões de código automatizadas.
- **QA Automatizado**: Integração com **FlaUI** para automação de interface em módulos Delphi (Pedidos, Notas Fiscais, Estoque, etc.).
- **Consistência de Banco de Dados**: Verificações automatizadas em bancos Oracle para garantir a integridade dos dados durante atualizações.
- **Segurança em Primeiro Lugar**: Comunicação HTTPS apenas de saída (outbound-only), garantindo exposição zero de portas de entrada.

---

## 🏗️ Arquitetura

O sistema está dividido em quatro módulos principais:

1.  **`agent/`**: Agente nativo Windows (Delphi/C#) para monitoramento local de VCS e automação de UI (FlaUI).
2.  **`backend/`**: Serviço FastAPI hospedado na nuvem, utilizando Neon (PostgreSQL) para gerenciamento de estado.
3.  **`frontend/`**: Dashboard em Next.js para visualização de análise de impacto, resultados de QA e relatórios de revisão de código.
4.  **`shared/`**: Modelos de dados comuns e camadas de abstração de IA para análise de Delphi/SQL.

---

## 🛠️ Stack Tecnológica

- **Core**: Python (FastAPI), Next.js, Delphi (Object Pascal).
- **Banco de Dados**: Neon (PostgreSQL), Oracle (Suporte Legado).
- **IA**: Google Gemini (Pro/Flash) para análise estruturada de código.
- **Automação**: FlaUI para RPA/QA desktop.

---

## 🚦 Primeiros Passos

### Pré-requisitos
- Python 3.10+
- Node.js 18+
- Delphi (para desenvolvimento do Agente)

### Instalação

1.  **Clonar o repositório**:
    ```bash
    git clone https://github.com/usuario/erp-guardian-ai.git
    cd erp-guardian-ai
    ```

2.  **Configuração do Backend**:
    ```bash
    cd backend
    pip install -r requirements.txt
    cp .env.example .env
    python main.py
    ```

3.  **Configuração do Frontend**:
    ```bash
    cd frontend
    npm install
    npm run dev
    ```

---

## 🔒 Segurança e Conformidade

O ERP Guardian AI foi construído com a segurança corporativa como prioridade:
- Não requer privilégios de administrador local para operação básica.
- Comunicação estritamente de saída (outbound-only).
- Criptografia de ponta a ponta para metadados de revisão de IA.

---

## 📄 Licença

Proprietário - Todos os direitos reservados.

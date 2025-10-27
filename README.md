# NFe MultiSource - Extrator da 'Natureza da operação'

Este repositório contém um serviço **gratuito** (deploy no Render) que consulta múltiplas fontes públicas para extrair o campo **Natureza da operação** a partir da chave de acesso da NF-e.

## Conteúdo
- `app.py` - aplicação FastAPI com UI e endpoint `/processar`.
- `utils/consulta_nfe.py` - motor que tenta várias fontes para obter a Natureza.
- `templates/index.html` - página web para upload/colar chaves.
- `static/statick.keep` - arquivo para garantir upload da pasta static.
- `requirements.txt` - dependências.
- `render.yaml` - configuração para deploy automático no Render.

## Instalação local (opcional)
1. Python 3.11
2. `python -m venv .venv` / `source .venv/bin/activate`
3. `pip install -r requirements.txt`
4. `uvicorn app:app --reload --port 10000`
5. Acesse `http://localhost:10000` e teste.

## Deploy no Render (passo a passo)
1. Crie repositório público `nfe-multisource` no GitHub.
2. Faça upload dos arquivos deste pacote.
3. No Render, conecte o repositório e crie um Web Service (Build: `pip install -r requirements.txt`, Start: `uvicorn app:app --host 0.0.0.0 --port 10000`).
4. Acesse a URL do serviço e use a interface para processar as chaves.

## Observações
- O portal nacional pode exigir reCAPTCHA; para esses casos o sistema tenta outras fontes.
- Para 100% de cobertura em produção considere uso de certificado A1 para acesso ao WebService SOAP da SEFAZ.

import asyncio, aiohttp, async_timeout, re
from lxml import etree
import chardet

# Lista de templates de consulta - ajuste conforme portais conhecidos da sua operação
SOURCE_URLS = [
    "https://www.nfe.fazenda.gov.br/portal/consultaRecaptcha.aspx?chNFe={chave}",
    "https://nfe.fazenda.mg.gov.br/paginas/consultacf/consultaXmlNFE.aspx?chNFe={chave}",
    "https://nfce.sefaz.rs.gov.br/nfe/consulta?chNFe={chave}",
    "https://www.sefa.pr.gov.br/nfe/consulta?chNFe={chave}",
    "https://www.sef.sc.gov.br/nfe/consulta?chNFe={chave}",
    "https://www.sefaz.ba.gov.br/nfe/consulta?chNFe={chave}",
    "https://www.sefaz.ms.gov.br/nfe/consulta?chNFe={chave}",
    "https://www.sefaz.pe.gov.br/nfe/consulta?chNFe={chave}",
    "https://www.sefaz.ce.gov.br/nfe/consulta?chNFe={chave}",
    "https://www.fazenda.rj.gov.br/nfe/consulta?chNFe={chave}",
    # Adicione APIs públicas conhecidas (ex.: api.nfe.io) se tiver chave/credenciais
]

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; NFe-Natureza/1.0)"}

async def fetch_text(session, url, timeout=12):
    try:
        async with async_timeout.timeout(timeout):
            async with session.get(url, headers=HEADERS) as resp:
                content = await resp.read()
                enc = chardet.detect(content).get('encoding') or 'utf-8'
                return content.decode(enc, errors='ignore'), resp.status
    except Exception:
        return '', 0

def extract_natureza_from_html(content):
    # tenta por regex direta
    s = " ".join(content.split())
    low = s.lower()
    m = re.search(r'natureza\s+da\s+opera[cç][aã]o[:\s\-]*([^<\n]{3,250})', low, flags=re.IGNORECASE)
    if m:
        return m.group(1).strip().upper()
    # tenta parse HTML
    try:
        parser = etree.HTMLParser()
        tree = etree.fromstring(content.encode('utf-8', errors='ignore'), parser)
        nodes = tree.xpath("//*[contains(translate(text(), 'NATUREZA', 'natureza'), 'natureza')]")
        for n in nodes:
            text = ''.join(n.itertext()).strip()
            mm = re.search(r'natureza[^:>\n]*[:>\s]*([\w\W]{1,250})', text, flags=re.IGNORECASE)
            if mm:
                return mm.group(1).strip().upper()
            if text:
                cleaned = re.sub(r'(?i)natureza\s*[:\-]*', '', text).strip()
                return cleaned.upper()
    except Exception:
        pass
    # procura tag XML <natOp>
    mm = re.search(r'<natOp>([^<]+)</natOp>', content, flags=re.IGNORECASE)
    if mm:
        return mm.group(1).strip().upper()
    return ''

async def try_sources_for_chave(session, chave):
    for tmpl in SOURCE_URLS:
        url = tmpl.format(chave=chave)
        text, status = await fetch_text(session, url)
        if not text:
            continue
        # detecta recaptcha/captcha
        if 'recaptcha' in text.lower() or 'captcha' in text.lower():
            # não é possível extrair dessa fonte sem resolver captcha
            continue
        nat = extract_natureza_from_html(text)
        if nat:
            return nat, f'OK from {url} (HTTP {status})'
    return '', 'Natureza não encontrada (fallback)'

async def process_chaves_batch(batch, concurrency=12):
    results = []
    sem = asyncio.Semaphore(concurrency)
    async with aiohttp.ClientSession() as session:
        async def worker(ch):
            async with sem:
                nat, status = await try_sources_for_chave(session, ch)
                return ch, nat, status
        tasks = [asyncio.create_task(worker(ch)) for ch in batch]
        for coro in asyncio.as_completed(tasks):
            results.append(await coro)
    return results

async def process_chaves_batch_stream(all_chaves, batch_size=200, concurrency=12):
    for i in range(0, len(all_chaves), batch_size):
        batch = all_chaves[i:i+batch_size]
        results = await process_chaves_batch(batch, concurrency=concurrency)
        for item in results:
            yield item
            await asyncio.sleep(0)

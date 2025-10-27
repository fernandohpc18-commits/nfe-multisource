from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import csv, io, re, asyncio
from utils.consulta_nfe import process_chaves_batch_stream

app = FastAPI(title='NFe Natureza - Web UI')
templates = Jinja2Templates(directory='templates')
app.mount('/static', StaticFiles(directory='static'), name='static')

@app.get('/', response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})

@app.post('/processar')
async def processar(file: UploadFile = File(None), paste: str = Form(None)):
    # aceita upload de arquivo .txt ou colagem no campo 'paste'
    raw_text = ''
    if file is not None:
        content = await file.read()
        raw_text = content.decode('utf-8', errors='ignore')
    elif paste:
        raw_text = paste
    else:
        return HTMLResponse('<h3>Envie um arquivo .txt ou cole as chaves no campo.</h3>', status_code=400)

    lines = [re.sub(r"\D", '', ln).strip() for ln in raw_text.splitlines() if ln.strip()]
    if not lines:
        return HTMLResponse('<h3>Arquivo vazio ou inválido.</h3>', status_code=400)

    async def stream():
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(['chave_acesso','natureza_operacao','status_consulta'])
        yield buffer.getvalue().encode('utf-8')
        buffer.seek(0); buffer.truncate(0)
        async for chave, nat, status in process_chaves_batch_stream(lines, batch_size=200, concurrency=20):
            writer.writerow([chave, nat, status])
            yield buffer.getvalue().encode('utf-8')
            buffer.seek(0); buffer.truncate(0)
            await asyncio.sleep(0)
    return StreamingResponse(stream(), media_type='text/csv',
                             headers={'Content-Disposition': 'attachment; filename="resultado_nfe.csv"'})

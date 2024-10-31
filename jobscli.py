import typer
import requests
import re
import csv

url = "https://api.itjobs.pt/job"
api_key = "22f572f4c8057d196327a8ce71c85bd7"
headers = {
    'User-Agent': ''
}
payload = {}

app=typer.Typer()

def request_api(metodo: str, params: dict) -> dict:
    params['api_key'] = api_key
    response = requests.get(f"{url}/{metodo}.json", headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        typer.echo(f"Erro ao acessar a API: {response.status_code}")
        return {}

#e)Para cada uma das funcionalidades (a), (b) e (d) deve poder exportar para CSV a informacao com os seguintes campo:
#titulo;empresa;descricao;data_de_publicacao;salario;localizacao.
def cria_csv(dados, nome_arquivo='jobs.csv'):
    with open(nome_arquivo, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        
        writer.writerow(['titulo', 'empresa', 'descricao', 'data_de_publicacao', 'salario', 'localizacao'])
        
        for job in dados.get('results', []):
            descricao_limpa = re.sub(r'<.*?>', '', job.get('body', ''))
            
            salario = job.get('wage', 'não_encontrado') if job.get('wage') is not None else ' '
            
            linha = [
                job.get('title', ''),
                job.get('company', {}).get('name', ''),
                descricao_limpa,
                job.get('publishedAt', ''),
                salario,
                ', '.join(location['name'] for location in job.get('locations', []))
            ]
            
            writer.writerow(linha)
    
    typer.echo(f"Dados exportados para {nome_arquivo}")

#b)Listar todos os trabalhos do tipo full-time, publicados por uma determinada empresa, numa determinada localidade e determinado numero.
#python jobscli.py search Braga EmpresaX 4
@app.command()
def search(localidade: str, empresa: str, limit: int, csv: bool = False):
    params={
        'q': f"{localidade},{empresa}",
        'limit': limit,
        'type': '1' 
    }
    response=request_api('search',params)
    print(response)
    if csv:
        cria_csv(response)
    
app()
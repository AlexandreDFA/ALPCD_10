import typer
import requests
import re

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

@app.command()
def top(n: int):
    params={
        "limit":n
    }
    response=request_api('list',params)
    typer.echo(response['results'])

@app.command()
def salary(jobid: int):
    params={
        "id":jobid
    }
    response=request_api('get',params)
    typer.echo(response)
    if response['wage'] == None:
        print('a')
app()
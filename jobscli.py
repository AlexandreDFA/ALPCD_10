import typer
import requests

url = "https://api.itjobs.pt/job"
api_key = "22f572f4c8057d196327a8ce71c85bd7"
headers = {
    'User-Agent': ''
}
payload = {}

app=typer.Typer()
    
@app.command()
def teste(n: int):
    url_teste = f"{url}/list.json?api_key={api_key}&limit={n}"
    response = requests.request("GET",url_teste, headers=headers, data=payload)
    res=response.json()
    print(res.get('limit'))
    print(res['results'])
    

app()
import typer
import requests
from datetime import datetime

url = "https://api.itjobs.pt/job"
api_key = "22f572f4c8057d196327a8ce71c85bd7"
headers = {
    'User-Agent': ''
}
payload = {}

app=typer.Typer()

#função para n tar sempre a por isto em todas as funções
def request_api(metodo: str, params: dict):
    params['api_key'] = api_key
    response = requests.get(f"{url}/{metodo}.json", headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        typer.echo(f"Erro ao acessar a API: {response.status_code}")
        return {}
#alinea d)
#procura trabalhos que requerem determinadas skills e que foram publicadas num determinado intervalo de tempo
#valida as datas, pede dados à API para procurar trabalhos com os filtros do utilizador, mostra a msg
@app.command()
def skills(skills: list[str], data_inicial: str, data_final: str):
    """
    Mostra trabalhos que requerem uma lista de skills num determinado período de tempo.
    """
    try: #conversão das datas para o formato YYYY/MM/DD
        data_inicial_dt = datetime.strptime(data_inicial, "%Y-%m-%d")
        data_final_dt = datetime.strptime(data_final, "%Y-%m-%d")
    except ValueError: #isto caso as datas nao estejam no formato correto 
        typer.echo("Erro: As datas devem estar no formato 'YYYY-MM-DD'.")
        return

    if data_inicial_dt>data_final_dt: #verificação de coenrência 
        typer.echo("Erro: A data inicial não pode ser posterior à data final.")
        return

    trabalhos_filtrados = [] #armazenamento dos trabalhos q requerem aquelas skills
    skills = ','.join(skills) #as strings dadas na lista pelo usuário passam a ser unidas por virgulas 

    params = {
        'limit':1500,
        "q": skills
    } #dicionário q contem as skills
    trabalhos = request_api("search", params) #verificacao do 200

    if not trabalhos or "results" not in trabalhos:
        typer.echo("Nenhum resultado encontrado ou erro na API.")
        return #se der erro

    for trabalho in trabalhos["results"]: #percorre se tds os trabalhos
        published_at_dt = datetime.strptime(trabalho["publishedAt"], "%Y-%m-%d %H:%M:%S") #converte se a data de publicação
        if data_inicial_dt <= published_at_dt <= data_final_dt:
            trabalhos_filtrados.append(trabalho) #adição do trabalho

    if trabalhos_filtrados:
        trabalhos_filtrados = {"results": trabalhos_filtrados}  # Formato esperado pela função cria_csv
        typer.echo(trabalhos_filtrados)  # Exibe os trabalhos filtrados
    else:
        typer.echo("Nenhum trabalho encontrado no período especificado.")

#mostra detalhes de uma vaga especifica 
#recebe o id de um rabalho, solicia à API, imprime os detalhes da vaga 
@app.command()
def detalhes(job_id: int): #parametro q representa o id da vaga 
    params={
            "id":job_id
    } #dicionario para identificar a vaga para a solicitação à API 
    trabalho=request_api("get",params)
    if "error" in trabalho:
        print("O id do trabalho não existe!")
    else:
        print(trabalho) #título, descrição, requisitos, empresa, localização, salário...
      
#contar qts vagas há numa localização 
#definir os parametros, filtra as vagas, faz a contagem
@app.command()
def contar_vagas_localizacao(localizacao: str): #parametro dado pelo usuário
    params={
        "limit":1500
    }
    vagas_na_localizacao = []#lista q irá armazenar as vagas correspondentes à localização especificada 
    trabalhos = request_api("search", params)
        
    if "results" in trabalhos:
        vagas_na_localizacao.extend([
            vaga for vaga in trabalhos["results"]
            if any(loc["name"].lower() == localizacao.lower() for loc in vaga.get("locations", []))
        ]) #verifica se a localização da vaga corresponde à localização dada 
    

    # Conta o número total de vagas na localização
    numero_de_vagas = len(vagas_na_localizacao) #conta o nº total de vagas encontradas
    if numero_de_vagas > 0:
        typer.echo(f"Há {numero_de_vagas} vagas disponíveis em {localizacao}.")
    else:
        typer.echo(f"Não há vagas disponíveis em {localizacao}.")

app()
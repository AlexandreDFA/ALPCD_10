import typer
import requests
from datetime import datetime

url = "https://api.itjobs.pt/job"
api_key = "22f572f4c8057d196327a8ce71c85bd7"
headers = {
    'User-Agent': 'ALPC10'
}

app=typer.Typer()

def request_api(metodo, params):
    params['api_key'] = api_key

    if 'limit' in params:
        tamanho_pagina = 200
        total = params['limit']

        if total < tamanho_pagina:
            tamanho_pagina = total

        paginas_totais = (total // tamanho_pagina) + (1 if total % tamanho_pagina != 0 else 0)
        resultado = []

        for page in range(1, paginas_totais + 1):
            params['limit'] = tamanho_pagina
            params['page'] = page

            response = requests.get(f"{url}/{metodo}.json", headers=headers, params=params)

            if response.status_code == 200:
                response_data = response.json()
                if 'results' in response_data:
                    resultado.extend(response_data['results'])
                if len(resultado) >= total:
                    break
            else:
                print(f"Erro ao acessar a API: {response.status_code}")
                return {}

        return {"results": resultado}

    else:
        response = requests.get(f"{url}/{metodo}.json", headers=headers, params=params)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Erro ao acessar a API: {response.status_code}")
            return {}

#e)Para cada uma das funcionalidades (a), (b) e (d) deve poder exportar para CSV a informacao com os seguintes campo:
#titulo;empresa;descricao;data_de_publicacao;salario;localizacao.
def cria_csv(dados, nome_arquivo='trabalhos.csv'):
    with open(nome_arquivo, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        
        writer.writerow(['Título', 'Empresa', 'Descrição', 'Data_De_Publicação', 'Salário', 'Localização'])
        
        for trabalho in dados.get('results'):
            descricao_limpa = re.sub(r'<.*?>', '', trabalho.get('body'))
            salario = trabalho.get('wage')
            titulo = trabalho.get('title')
            empresa = trabalho.get('company', {}).get('name')
            data_de_publicacao = trabalho.get('publishedAt')
            localizacao = ', '.join(location['name'] for location in trabalho.get('locations', []))
            
            linha = [
                titulo if titulo else 'dados_não_disponíveis',
                empresa if empresa else 'dados_não_disponíveis',
                descricao_limpa if descricao_limpa else 'dados_não_disponíveis',
                data_de_publicacao if data_de_publicacao else 'dados_não_disponíveis',
                salario if salario else 'dados_não_disponíveis',
                localizacao if localizacao else 'dados_não_disponíveis'
            ]
            
            writer.writerow(linha)
    
    print(f"Dados exportados para {nome_arquivo}")

#b)Listar todos os trabalhos do tipo full-time, publicados por uma determinada empresa, numa determinada localidade e determinado numero.
#python trabalhoscli.py search Braga EmpresaX 4
@app.command()
def search(localidade: str, empresa: str, limit: int, csv: bool = False):
    '''
    Filtragem de trabalhos mediante a localidade, empresa e quantidade
    '''

    params = {
        'limit': 1500,
        'type': '1'
    }

    response = request_api('search', params)

    if 'results' in response:
        trabalhos_filtrados = [
            trabalho for trabalho in response['results']
            if trabalho.get('company', {}).get('name', '').strip().lower() == empresa.strip().lower() and
            any(loc.get('name', '').strip().lower() == localidade.strip().lower() for loc in trabalho.get('locations', []))
        ]

        trabalhos_filtrados = trabalhos_filtrados[:limit]

        if trabalhos_filtrados:
            print(trabalhos_filtrados)
            print(f"Encontrados {len(trabalhos_filtrados)} resultados para a empresa '{empresa}' na localidade '{localidade}'.")
            if csv:
                cria_csv({'results': trabalhos_filtrados})
        else:
            print(f"Nenhum resultado encontrado para a empresa '{empresa}' na localidade '{localidade}'.")
    else:
        print("Nenhum resultado encontrado.")
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
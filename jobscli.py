import typer
import csv
import re
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Fire-fox/98.0', 
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language':'en-US,en;q=0.5', 
    'Accept-Encoding': 'gzip, deflate', 
    'Connection': 'keep-alive', 
    'Upgrade-Insecure-Requests': '1', 
    'Sec-Fetch-Dest':'document', 
    'Sec-Fetch-Mode': 'navigate', 
    'Sec-Fetch-Site': 'none', 
    'Sec-Fetch-User': '?1', 
    'Cache-Control': 'max-age=0'
}

app=typer.Typer()

def request_api(metodo, params):
    url = "https://api.itjobs.pt/job"
    api_key = "22f572f4c8057d196327a8ce71c85bd7"
    params['api_key'] = api_key

    if 'limit' in params:
        tamanho_pagina = 500
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
                if len(response_data['results']) < tamanho_pagina:
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

def request_website(url):
    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "lxml")
            return soup
        else:
            print(f"Erro {response.status_code}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição: {e}")
        return None
    
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

    if limit!=0:
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
    else:
        print("Limite 0")

#alinea d)
#procura trabalhos que requerem determinadas skills e que foram publicadas num determinado intervalo de tempo
#valida as datas, pede dados à API para procurar trabalhos com os filtros do utilizador, mostra a msg
@app.command()
def skills(skills: list[str], data_inicial: str, data_final: str,csv: bool = False):
    """
    Mostra trabalhos que requerem uma lista de skills num determinado período de tempo.
    """
    try: #conversão das datas para o formato YYYY/MM/DD
        data_inicial_dt = datetime.strptime(data_inicial, "%Y-%m-%d")
        data_final_dt = datetime.strptime(data_final, "%Y-%m-%d")
    except ValueError: #isto caso as datas nao estejam no formato correto 
        print("Erro: As datas devem estar no formato 'YYYY-MM-DD'.")
        return

    if data_inicial_dt>data_final_dt: #verificação de coenrência 
        print("Erro: A data inicial não pode ser posterior à data final.")
        return

    trabalhos_filtrados = [] #armazenamento dos trabalhos q requerem aquelas skills
    skills = ','.join(skills) #as strings dadas na lista pelo usuário passam a ser unidas por virgulas 

    if len(skills)==0:
        params = {
            'limit':1500,
            "q": skills
        } #dicionário q contem as skills
        trabalhos = request_api("search", params) #verificacao do 200

        if not trabalhos or "results" not in trabalhos:
            print("Nenhum resultado encontrado ou erro na API.")
            return #se der erro
        
        for trabalho in trabalhos["results"]: #percorre se tds os trabalhos
            published_at_dt = datetime.strptime(trabalho["publishedAt"], "%Y-%m-%d %H:%M:%S") #converte se a data de publicação
            if data_inicial_dt <= published_at_dt <= data_final_dt:
                trabalhos_filtrados.append(trabalho) #adição do trabalho

        if trabalhos_filtrados:
            trabalhos_filtrados = {"results": trabalhos_filtrados}  # Formato esperado pela função cria_csv
            print(trabalhos_filtrados) # Exibe os trabalhos filtrados
            if csv:
                cria_csv(trabalhos_filtrados)
        else:
            print("Nenhum trabalho encontrado no período especificado.")
    else:
        print("Lista de skills vazia!")

#mostra detalhes de uma vaga especifica 
#recebe o id de um rabalho, solicia à API, imprime os detalhes da vaga 
@app.command()
def detalhes(job_id: int): #parametro q representa o id da vaga 
    '''
    Detalhes sobre uma vaga de trabalho
    '''
    params={
            "id":job_id
    } #dicionario para identificar a vaga para a solicitação à API 
    trabalho=request_api("get",params)
    if "error" in trabalho:
        print(f"Erro: A vaga com o ID {job_id} não foi encontrada.")
    else:
        print(trabalho) #título, descrição, requisitos, empresa, localização, salário...
      
#contar qts vagas há numa localização 
#definir os parametros, filtra as vagas, faz a contagem
@app.command()
def contar_vagas_localizacao(localizacao: str): #parametro dado pelo usuário
    '''
    Número de vagas por localização
    '''
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
        print(f"Há {numero_de_vagas} vagas disponíveis em {localizacao}.")
    else:
        print(f"Não há vagas disponíveis em {localizacao}.")

@app.command()
def top(n: int,csv: bool = False):
    '''
    N trabalhos mais recentes
    '''
    params={
        "limit":n
    }
    if n!=0:
        response=request_api('list',params)
        print(response['results'])
        if len(response['results'])<n:
            print(f"Só existem {len(response['results'])} atualmente")
        if csv:
            cria_csv(response)
    else:
        print("O número tem de ser maior do que 0!")

@app.command()
def salary(jobid: int):
    '''
    Salário de um trabalho especifico
    '''
    params={
        "id":jobid
    }
    response=request_api('get',params)
    if not response:
        print("Não foi possível obter os dados do job.")
        return
    elif "error" in response:
        print(f"Erro: A vaga com o ID {jobid} não foi encontrada.")
    else:
        wage = response.get('wage')
        
        if wage is not None:
            # Se o campo 'wage' não for nulo, exibe o salário
            print(f"Salário: {wage}")
        else:
            # Caso 'wage' seja nulo, procurar no corpo da descrição usando regex
            print("Salário não especificado")
            body = response.get('body', '')
            
            # expressão regular simples para procurar salários(491805,491581,490897,491330)
            match = re.search(r"([€$R]\s?)([0-9]{1,10}([\.,][0-9]{2,3})*)(\s?[\–e]\s?([€$R]\s?[0-9]{1,10}([\.,][0-9]{2,3})*))?(/[a-zA-Z]* [a-zA-Z]*)?|([0-9]{1,10}([\.,][0-9]{2,3})*)(\s?[€$R])(\s?[\–e]\s?([0-9]{1,10}([\.,][0-9]{2,3})*)(\s?[€$R]))?(/[a-zA-Z]* [a-zA-Z]*)?", body)
            
            if match:
                salary_found = match.group(0)
                print(f"Salário encontrado na descrição: {salary_found}")
            else:
                print("Salário não encontrado na descrição.")       

#tp2c) Ir buscar skills ao website 
@app.command()
def list_skills(trabalho: str, guardar: bool = False):
    skills_count = {}
    trabalho = trabalho.lower().replace(" ", "-")
    while True:
        try:
            total_trabalhos = int(input("Quantos trabalhos quer pesquisar no total? "))
            if total_trabalhos > 0:
                break
            else:
                print("Por favor, insira um número inteiro positivo.")
        except ValueError:
            print("Entrada inválida. Por favor, insira um número inteiro.")

    paginas_necessarias = (total_trabalhos // 10) + (1 if total_trabalhos % 10 != 0 else 0)
    lista_urls = []

    for n in range(1, paginas_necessarias + 1):
        soup = request_website(f'https://www.ambitionbox.com/jobs/{trabalho}-jobs-prf?page={n}')
        links = soup.find_all('meta', itemprop="url")
        urls = [link['content'] for link in links]
        
        if not urls:
            print("Nenhum URL válido encontrado. Encerrando a execução.")
            return

        urls.pop(0)
        lista_urls.extend(urls)

        if len(lista_urls) >= total_trabalhos:
            lista_urls = lista_urls[:total_trabalhos]
            break

    print("URLs adquiridos.")
    u = 1

    for url in lista_urls:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(extra_http_headers=headers)
            page = context.new_page()

            try:
                page.goto(url, wait_until="load")

                more_button = page.query_selector(".chip.more")
                if more_button:
                    page.click(".chip.more")

                skills_list = []
                skills = page.query_selector_all(".body-medium.chip")
                for skill in skills:
                    skill_text = skill.inner_text()
                    skills_list.append(skill_text)

                for skill in skills_list:
                    if skill in skills_count:
                        skills_count[skill] += 1
                    else:
                        skills_count[skill] = 1

                print(f"Skills do trabalho {u} adiquiridas.")
                u += 1
            except Exception as e:
                print(f"Erro ao processar URL {url}: {e}")
            finally:
                browser.close()

    skills_json = [{"skill": skill, "count": count} for skill, count in skills_count.items()]

    skills_json = sorted(skills_json, key=lambda x: x['count'], reverse=True)
    while True:
        try:
            top = int(input("Quantas skills? "))
            if top > 0:
                break
            else:
                print("Por favor, insira um número inteiro positivo.")
        except ValueError:
            print("Entrada inválida. Por favor, insira um número inteiro.")
    skills_json = skills_json[:top]

    print(skills_json)
    if guardar:
        csv_filename = f"{trabalho}-skills.csv"
        with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=["skill", "count"])
            writer.writeheader()
            writer.writerows(skills_json)

        print(f"Dados salvos em {csv_filename}")

app()



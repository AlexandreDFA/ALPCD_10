import typer
import requests
import re
import csv

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

app()
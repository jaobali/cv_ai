from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
import time

from langchain.callbacks import get_openai_callback

from dotenv import load_dotenv, find_dotenv
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from typing import Optional
from typing import List

# Carregar variáveis de ambiente
dotenv_path = find_dotenv()
_ = load_dotenv(dotenv_path)

class ResumoCurriculo(BaseModel):
    nome_completo: Optional[str] = Field(None, description="Nome completo do candidato. Deve estar escrito todo em letra maiúscula.")
    experiencia: List[str] = Field(None, description="Resumo da experiência profissional")
    habilidades: List[str] = Field(None, description="Principais habilidades")
    educacao: List[str] = Field(None, description="Formação educacional")
    idiomas: List[str] = Field(None, description="Idiomas conhecidos")

    def dict(self, *args, **kwargs):
        return super().dict(*args, **kwargs, exclude_none=True)


def iniciar_modelo():
    # return ChatGroq(model='llama-3.3-70b-versatile'
    #     # model='llama3-70b-8192'
    # )
    model = ChatOpenAI(model='gpt-4o-mini') # foi o que teve as avaliações mais honestas
    # return ChatOpenAI(model='gpt-4.1-nano')
    return model

# Exemplo de análise: resumo de currículo
def gerar_resumo_curriculo(texto_markdown):
    start_time = time.time()
    
    parser = PydanticOutputParser(pydantic_object=ResumoCurriculo)
    format_instructions = parser.get_format_instructions()

    prompt = ChatPromptTemplate.from_messages([
        ("system", '''
        Você é um assistente de RH com muita experiência na análise crítica de currículos.
        A seguir você será apresentado ao curriculo e terá instruções precisas para parsea-lo.
        Seu objetivo é extrair as informações do curriculo e retornar um resumo do mesmo em formato JSON.
        Lembre-se de que esses curriculos estão em formato markdown e foram extraídos de arquivos pdf por um certo processo de extração de texto.
        Portanto, as vezes, as informações não estarão perfeitamente em seu capítulos correspondentes. Assim, analise as informação como um todo.
        Se você não encontrar alguma informação pedida no corriculo coloque ["Não encontrado"] no campo correspondente neste formato de lista mencionado.
        Necessariamente preciso que o output seja em formato JSON para análises posteriores.
        Ignore strings no formato "<!-- image -->", elas representam posições onde imagens foram detectadas no curriculo.
        Não escreva nada além do formato JSON solicitado.
        '''),
        ("human", "{format_instructions}\n\nCurrículo do candidato para resumir:\n\n{curriculo}")
    ]).partial(format_instructions=format_instructions)

    modelo = iniciar_modelo()
    chain = prompt | modelo | parser

    with get_openai_callback() as cb:
        resultado = chain.invoke({"curriculo": texto_markdown})

        processing_time = time.time() - start_time

        tokens_entrada = cb.prompt_tokens
        tokens_saida = cb.completion_tokens
        custo_chamada = cb.total_cost
        tempo_processamento = processing_time

        print("Tokens de entrada:", tokens_entrada)
        print("Tokens de saída:", tokens_saida)
        print("Total de tokens:", cb.total_tokens)
        print("Custo da chamada (USD):", custo_chamada)
        print("Tempo de processamento (s):", tempo_processamento)

    return resultado, processing_time, tokens_entrada, tokens_saida, modelo.model_name, custo_chamada

def gerar_opiniao_curriculo(resumo, desc_vaga):
    start_time = time.time()
    
    system_prompt = '''
        Você é um avaliador de currículos com muitos anos de experiência e receberá certas instruções para atribuir uma nota ao curriculo.
        A sua resposta deve ser apenas o número da nota final do candidato.
        Não responda com nada além da nota final do candidato.
        Não responda com as notas intermediárias do seu cálculo.
        Responda apenas a nota final do candidato.
    '''
    
    human_prompt = '''
        A seguir você receberá um resumo do currículo do candidato e uma descrição da vaga para a qual ele se candidatou.
        Seu objetivo é analisar o currículo do candidato e gerar uma opinião descritiva sobre o mesmo em relação à vaga.
        Você deve pensar como o recrutador chefe que está analisando e gerando uma opinião descritiva sobre o currículo do conditato que se candidatou para a vaga.
        Essa opinião deve ser crítica e detalhada.
        Essa opinião deve ser formatada em markdown e deve conter títulos grandes nas sessões.
        Essa opinião será usada para descrever as qualidades e deficiencias do candidato em relação à vaga e avaliar qual o melhor canditado para a vaga.

        A sua análise deve incluir os seguintes pontos:

        1. **Pontos de Alinhamento**:** Identifique e discuta os aspectos do currículo que estão diretamente alinhados com os requisitos da vaga.
        Inclua exemplos específicos de experiências, habilidades ou qualificações que a vaga está procurando.

        2. **Pontos de Desalinhamento**:** Destaque e discuta as áreas onde o candidato não atende aos requisitos da vaga.
        Isso pode incluir falta de experiência em áreas chaves, ausência de habilidades técnicas específicas ou qualificações que não correspondam às espectativas da vaga.

        Sua análise deve ser objetiva, baseada em evidências apresentadas no currículo e na descrição da vaga.

        Não dedusa ou suponha que o condidato tenha experiência em algo que a vaga pede caso não esteja mencionado no currículo.
        Exemplo: O candidato tem experiência como gestor de uma área. Você não deve supor que ele entenda de analise de dados ou ferramentas de dados.

        Trabalhe apenas com as informações contidas no currículo do candidadto.

        Seja detalhado e forneça uma avaliação honesta dos pontos fortes e fracos do candidato em relação à vaga.

        *Resumo curriculo original.**
        {resumo}

        *Descrição da vaga.**
        {desc_vaga}

        Em sua conclusão, não seja tão duro ao descartar um candidato. Apenas diga que ele não é qualificado se ele não tiver nenhuma relação com a vaga.
        Caso o canditado tenha vários pontos de alinhamento com a vaga, diga que ele deve ser considerado para uma entrevista.

        Você deve devolver essa análise crítica formatada como se fosse um relatório analítico do currículo com a vaga, deve estar formatado com títulos grandes em desteque no formato markdown.
    '''

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", human_prompt)
    ])

    modelo = iniciar_modelo()

    chain = prompt | modelo

    with get_openai_callback() as cb:
        resultado = chain.invoke({"resumo": resumo, "desc_vaga": desc_vaga})

        processing_time = time.time() - start_time

        tokens_entrada = cb.prompt_tokens
        tokens_saida = cb.completion_tokens
        custo_chamada = cb.total_cost
        tempo_processamento = processing_time

        print("Tokens de entrada:", tokens_entrada)
        print("Tokens de saída:", tokens_saida)
        print("Total de tokens:", cb.total_tokens)
        print("Custo da chamada (USD):", custo_chamada)
        print("Tempo de processamento (s):", tempo_processamento)

    return resultado.content, processing_time, tokens_entrada, tokens_saida, modelo.model_name, custo_chamada

def gerar_score_curriculo(resumo, desc_vaga):
    start_time = time.time()

    system_prompt = '''
        Você é um avaliador de currículos com muitos anos de experiência e receberá certas instruções para atribuir uma nota ao curriculo.
        A sua resposta deve ser apenas o número da nota final do candidato com 1 casa decimal de precisão.
        Não responda com nada além da nota final do candidato.
        Não responda com as notas intermediárias do seu cálculo.
        Responda apenas a nota final do candidato com 1 casa decimal de precisão.
    '''

    human_prompt = '''
        Ojetivo: Avaliar um currículo com base em uma vaga específica e calcular a pontuação final. A nota máxima é 10.0.

        Instruções:

        1. Experiência (Peso: 35%)**:
        Avalie a relevância da experiência em relação à vaga.
        Experiências anteriores em trablahos relacionados com a vaga devem ser consideradas.
        Experiências em áreas de liderança relacionadas com a vaga devem ser consideradas.
        Experiências anteriores em trabalhos não relacionados com a vaga não devem ser consideradas.

        2. Habilidades técnicas (Peso: 40%)**:
        Verifique o alinhamento das habilidades técnicas com os requisitos da vaga.
        Habilidades do candidato que não relacionados com a vaga não devem ser consideradas.
        A falta de alguma habilidade técnica exigida pela vaga deve contribuir negativamente para a nota deste tópco.

        3. Educação (Peso: 20%)**:
        Avalie a relevância da formação acadêmica para a vaga.
        Caso a formação do candidato seja em áreas correlatas com a vaga ele deve receber pontos.
        Exemplo: Se a vaga pega experiência em alguma formação da área de exatas e o candidato tenha formação em física, você deve dar os pontos para o candidato.

        4. Idiomas (Peso: 5%)**:
        Avalie os idiomas e sua proficiência em relação à vaga.

        Resumo do curriculo:

        {resumo}

        Vaga que o candidato está se candidatando:

        {desc_vaga}

        Lembre-se de que a nota máxima é 10.0 e de retornar apenas o score final do canditato com 1 casa decimal de precisão.
    '''

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", human_prompt)
    ])

    modelo = iniciar_modelo()

    chain = prompt | modelo

    with get_openai_callback() as cb:
        resultado = chain.invoke({"resumo": resumo, "desc_vaga": desc_vaga})

        processing_time = time.time() - start_time

        tokens_entrada = cb.prompt_tokens
        tokens_saida = cb.completion_tokens
        custo_chamada = cb.total_cost
        tempo_processamento = processing_time

        print("Tokens de entrada:", tokens_entrada)
        print("Tokens de saída:", tokens_saida)
        print("Total de tokens:", cb.total_tokens)
        print("Custo da chamada (USD):", custo_chamada)
        print("Tempo de processamento (s):", tempo_processamento)

    return resultado.content, processing_time, tokens_entrada, tokens_saida, modelo.model_name, custo_chamada

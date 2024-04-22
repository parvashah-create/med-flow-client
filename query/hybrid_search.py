# from langchain_community.vectorstores.neo4j_vector import Neo4jVector

from query.vector_search import vector_query
from dotenv import load_dotenv
import os
import re
import textwrap
from string import Template


# Langchain
from langchain_community.graphs.neo4j_graph import Neo4jGraph
from langchain_community.vectorstores import Neo4jVector
from langchain_openai import OpenAIEmbeddings
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.prompts.prompt import PromptTemplate
from langchain.chains.graph_qa.cypher import GraphCypherQAChain
from langchain_openai import ChatOpenAI

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE")

kg = Neo4jGraph(
    url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD, database=NEO4J_DATABASE
)


# kg.refresh_schema()
# print(textwrap.fill(kg.schema, 60))

CYPHER_GENERATION_TEMPLATE = """
Task Description:
Write a Cypher query based on a specific requirement for querying a graph database.

Instructions:
1. Use only the relationship types, properties, and schema elements provided below. Do not introduce any elements that are not listed.
2. The given nodes and relationships result from vector searches in the graph database. These can provide context for your Cypher query construction to get more context if necessary.
3. Your Cypher query should never return the "embedding" property. Instead, focus on returning specific, relevant properties.
4. Your response should consist solely of the Cypher statement. Please avoid adding explanations or answering questions not directly tied to the Cypher query construction.

Schema Information:
{schema}

Context from Vector Search:
{vector_text}

Guidelines:
- Consider the schema carefully to identify how entities are connected.
- Focus on crafting a query that is as efficient as possible, avoiding unnecessary traversals.
- When filtering results, be precise in targeting the properties mentioned in the task.

Cypher Query Examples:

Query to find all drugs with a high risk of toxicity.
MATCH (d:Drug)-[:HAS_TOXICITY]->(t:Toxicity) WHERE t.description CONTAINS 'high risk' RETURN d.name

Query to identify drugs metabolized primarily in the liver.
MATCH (d:Drug)-[:HAS_METABOLISM]->(met:Metabolism) WHERE met.description CONTAINS 'liver' RETURN d.name

If no context is found, answer with your knowledge appropriately

Your question to create the cypher for:

"""
QA_GENERATION_TEMPLATE = """
You are ChatGPT, with the knowledge and expertise of an experienced medical doctor specializing in pharmacology. Your task is 
to provide accurate, detailed, and understandable answers to questions about various drugs, including prescription medications, 
over-the-counter treatments, and supplements.

Your answers should be framed in a way that is easy for a layperson to understand, using simple language and avoiding medical 
jargon whenever possible. Additionally, always remind users that your information does not replace professional medical advice 
and that they should consult their healthcare provider for personalized guidance.

You will be provided with the full context of the query from the drugbank databse. If there is no context, you canreply with 
a appropriate answer.
Question:

"""



def create_prompts(cyper_template, qa_template):
    CYPHER_GENERATION_PROMPT = PromptTemplate(
        input_variables=["question"], 
        template=cyper_template
    )

    QA_GENERATION_PROMPT = PromptTemplate(
        input_variables=["question"], 
        template=qa_template
    )

    return CYPHER_GENERATION_PROMPT, QA_GENERATION_PROMPT

# print(CYPHER_GENERATION_PROMPT)
def create_cypher_chain(cypher_prompt, qa_prompt):
    cypherChain = GraphCypherQAChain.from_llm(
        cypher_llm=ChatOpenAI(temperature=0, model="gpt-3.5-turbo"),
        qa_llm=ChatOpenAI(temperature=0.5, model="gpt-3.5-turbo-16k"),
        graph=kg,
        verbose=True,
        cypher_prompt=cypher_prompt,
        # qa_prompt=qa_prompt
    )
    return cypherChain

def prettyCypherChain(question: str) -> str:
    vector_search = vector_query(question,3)
    vector_text  = re.sub(r"[{}]", "", str(vector_search))
    kg_schema  = re.sub(r"[{}]", "", str(kg.schema))

    print(vector_text)
    chain_inputs = {
        "vector_text": vector_text,
        "schema": kg_schema
    }


    cypher_template = CYPHER_GENERATION_TEMPLATE.format(**chain_inputs) + "{question}"
    qa_template = QA_GENERATION_TEMPLATE + "{question}"

    print(cypher_template,qa_template)

    cypher_prompt, qa_prompt = create_prompts(cypher_template,qa_template)


    cypherChain = create_cypher_chain(cypher_prompt, qa_prompt)
    chain_response = cypherChain.invoke(question)
    
    response = chain_response['result']
    return response




# prettyCypherChain("How does Lepirudin interact with Tibolone ?")

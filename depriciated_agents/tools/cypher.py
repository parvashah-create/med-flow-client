from langchain.chains.graph_qa.cypher import GraphCypherQAChain

from llm.llm import llm
from config.neo_conn import graph




cypher_qa = GraphCypherQAChain.from_llm(
        llm,       
        graph=graph,
)


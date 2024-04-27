from langchain_community.graphs.neo4j_graph import Neo4jGraph
import os
from dotenv import load_dotenv



load_dotenv()


# graph = Neo4jGraph(
#     url=os.getenv("NEO4J_URI"),
#     username=os.getenv("NEO4J_USERNAME"),
#     password=os.getenv("NEO4J_PASSWORD"),
# )

NEO4J_URI="bolt://localhost:7687"
NEO4J_USERNAME="neo4j"
NEO4J_PASSWORD="admin@123"

graph = Neo4jGraph(
    url=NEO4J_URI,
    username=NEO4J_USERNAME,
    password=NEO4J_PASSWORD,
)

# print(graph.schema)
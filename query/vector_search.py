from langchain_community.vectorstores.neo4j_vector import Neo4jVector
from embeddings.clinical_bert import get_clinicalbert_embeddings
import os
from dotenv import load_dotenv

from embeddings.openai_embeds import embeddings
from langchain_community.embeddings.openai import OpenAIEmbeddings

from neo4j import GraphDatabase

load_dotenv()






def vector_query(sample_text, top_K):
    NEO4J_URI = os.getenv("NEO4J_URI")
    NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
    NEO4J_DATABASE = os.getenv("NEO4J_DATABASE")


    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    session = driver.session()
    # List of embedding indexes
    indexes = [
        "Clearance_embedding_index", "Drug_embedding_index",
        "HalfLife_embedding_index", "Indication_embedding_index",
        "MechanismOfAction_embedding_index", "Metabolism_embedding_index",
        "Pharmacodynamics_embedding_index", "ProteinBinding_embedding_index",
        "RouteOfElimination_embedding_index", "Toxicity_embedding_index",
        "VolumeOfDistribution_embedding_index"
    ]
    # indexes = [
    #     "openai_embedding_index"
    # ]
    # Generate an embedding for the sample text
    query_vector = get_clinicalbert_embeddings(sample_text)
    
    all_results = []

    for index in indexes:
        query_results = session.run("""
            CALL db.index.vector.queryNodes($index_name, 10, $embedding) 
            YIELD node, score
            RETURN labels(node) AS labels, id(node) AS id, node, score
            """, index_name=index, embedding=query_vector)
    
    for result in query_results:
        # Exclude 'embedding' property from the node if it exists
        node_data = {key: value for key, value in result['node'].items() if key != 'embedding'}
        all_results.append({
            "node": node_data, 
            "score": result['score'], 
            "index": index,
            "labels": result['labels'], 
            "id": result['id'] 
        })
    
    # Sort all results by score in descending order and pick the top_K
    top_results = sorted(all_results, key=lambda x: x['score'], reverse=True)[:top_K]
    
    # Prepare the final list to return
    final_results = []

    for result in top_results:
        final_result = {
            "Index": result['index'],
            "Node": result['node'],
            "Score": result['score'],
            "Labels": result['labels'],  # Include labels in the output
            "ID": result['id']  # Include ID in the output
        }
        final_results.append(final_result)
    
    return final_results



def openai_vector_query(sample_text, top_K):
    NEO4J_URI = os.getenv("NEO4J_URI")
    NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
    NEO4J_DATABASE = os.getenv("NEO4J_DATABASE")


    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    session = driver.session()

    query_vector = embeddings.embed_query(sample_text)

    query_results = session.run("""
                                CALL db.index.vector.queryNodes($index_name, 10, $embedding) 
                                YIELD node, score
                                RETURN labels(node) AS labels, id(node) AS id, node.name, score
                                """, index_name="openai_embedding_index", embedding=query_vector)
    
    print(query_results) 

    final_results = []

    for result in query_results:

        print(result)
        # final_result = {
        #     "Index": result['index'],
        #     "Node": result['node'],
        #     "Score": result['score'],
        #     "Labels": result['labels'], 
        #     "ID": result['id']  
        # }
        # final_results.append(final_result)

    return final_results


# Example usage
# print(vector_query("Lepirudin is a recombinant hirudin", 10))
# print(openai_vector_query("What is Lepirudin ?", 10))



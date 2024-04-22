from transformers import AutoModel, AutoTokenizer
import torch



def get_clinicalbert_embeddings(text):
    # Load tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained("medicalai/ClinicalBERT")
    model = AutoModel.from_pretrained("medicalai/ClinicalBERT")
    
    # Tokenize input text
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
    
    # Get embeddings
    with torch.no_grad(): # Disable gradient calculation for inference
        outputs = model(**inputs)
    
    # The embeddings can be taken from the last hidden state
    embeddings = outputs.last_hidden_state
    
    # You might want to pool the embeddings for the entire input
    # Here, we simply average them to get a single vector for the input text
    pooled_embeddings = torch.mean(embeddings, dim=1)

    vector_list = pooled_embeddings[0].detach().cpu().numpy().tolist()
    
    return vector_list


# from transformers import AutoModel, AutoTokenizer
# import torch
# from typing import List

# class ClinicalBERTEmbeddings:
#     def __init__(self):
#         # Load tokenizer and model
#         self.tokenizer = AutoTokenizer.from_pretrained("medicalai/ClinicalBERT")
#         self.model = AutoModel.from_pretrained("medicalai/ClinicalBERT")

#     def embed_query(self, text: str) -> List[float]:
#         # Tokenize input text
#         inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
        
#         # Get embeddings
#         with torch.no_grad():  # Disable gradient calculation for inference
#             outputs = self.model(**inputs)
        
#         # The embeddings can be taken from the last hidden state
#         embeddings = outputs.last_hidden_state
        
#         # Pool the embeddings for the entire input, here simply averaging
#         pooled_embeddings = torch.mean(embeddings, dim=1)
        
#         # Convert to list
#         vector_list = pooled_embeddings[0].detach().cpu().numpy().tolist()
        
#         return vector_list
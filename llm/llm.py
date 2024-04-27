import streamlit as st
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()



llm = ChatOpenAI(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    model=os.getenv("OPENAI_MODEL"),
    temperature=0

)



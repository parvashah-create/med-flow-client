from langchain.agents import AgentExecutor, create_react_agent
from langchain import hub
import json
# Include the LLM from a previous lesson
from llm.llm import llm
from langchain.prompts import PromptTemplate
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain.tools import Tool
from langchain_core.tools import tool
from depriciated_agents.tools.cypher import cypher_qa

from depriciated_agents.forms.patient_registration import patient_registration_form
from depriciated_agents.form_handler import FormHandler
import streamlit as st




@tool
def submit_form(form:str) -> str:
    """submits a form"""
    
    form_dict = json.loads(form.strip())
    print("form_dict:", form_dict)
    print("form_code:", form_dict["form_code"])
    print("form_data:", form_dict["form_data"])

    if (form_dict["form_code"] and form_dict["form_data"]):
        return FormHandler(form_dict).handle_submission()
    else:
        format_error = """
                            {
                                "form_code": ,
                                "form_data": ,
                            }
                        """
        return str(format_error)



@tool
def get_patient_registration_form(query = {}) -> str:
    """Gets the patient registration form"""

    patient_registration_form = """
    
    Do not change the template
    New patient registration form Template:

    {
        "form_code": 1,
        "form_data":{
                        "first_name": "", (required)
                        "last_name": "", (required)
                        "dob": "(YYYY-MM-DD)" (required)
                    }
    }

    """
    return patient_registration_form

@tool
def get_physical_exam_form(query = {}) -> str:
    """Gets the physical exam form"""

    physical_exam_form = """
    
    Do not change the template
    Physical Examination Form Template:

    {
        "form_code": 3,
        "form_data":{
                        "appointment_id": "", (required),
                        "findings": "" (required)
                    }
    }

    """
    return physical_exam_form

@tool
def get_prescription_form(query = {}) -> str:
    """Gets the prescription form"""

    prescription_form = """
    
    Do not change the template
    Prescription Form Template:

    {
        "form_code": 4,
        "form_data":{
                    "appointment_id": "", (required),
                    "medications": [{
                            "medication_name": "", (required)
                            "dosage": "", (required)
                            "frequency": "", (required)
                            "duration": "", (required)
                            "instructions": "", (required)
                        }] (add more dicts in the list if necessary)
                    }
    }

    """
    return prescription_form

@tool
def get_billing_form(query = {}) -> str:
    """Gets billing form"""

    physical_exam_form = """
    
    Do not change the template
    Billing Form Template:

    {
        "form_code": 5,
        "form_data":{
                        "appointment_id": "", (required),
                        "billing":{
                                    "total_cost": "(float)", (required)
                                }
                        
                    }
    }

    """
    return physical_exam_form

tools = [
    # Tool.from_function(
    #     name="Graph Cypher QA Chain",  
    #     description="Provides information about patient and related nodes", 
    #     func = cypher_qa,
    #     return_direct=False
    # ),

    Tool.from_function(
        name="patient registration form",  
        description="Get the patient registration form template", 
        func = get_patient_registration_form,
        return_direct=True
    ),
    Tool.from_function(
        name="Physical Examination Form",  
        description="Get the physical examination form template", 
        func = get_physical_exam_form,
        return_direct=True
    ),
    Tool.from_function(
        name="Prescription Form",  
        description="Get the Prescription Form template", 
        func = get_prescription_form,
        return_direct=True
    ),

    Tool.from_function(
        name="Billing Form",  
        description="Get the Billing Form template", 
        func = get_billing_form,
        return_direct=True
    ),

    Tool.from_function(
        name="submit a form",  
        description="This tool submits the form", 
        func = submit_form,
        return_direct=False
    )
    
   
]


memory = ConversationBufferWindowMemory(
    memory_key='chat_history',
    k=50,
    return_messages=True,
)


# agent_prompt = hub.pull("hwchase17/react-chat")
agent_prompt = PromptTemplate.from_template("""
        You are a helpful nurse assistant called for physicians, which helps uses the given tools to help physicians with various ERP related tasks
        
        When you use asked to fill/get a form, use the tools to get the correct form and progressively fill the form by asking the users questions to fill the form. 

        Always confirm the form details with the user before submitting.
                                            
        When the user confirm all details, use submit_form tool to submit the form.

        All forms will be in JSON format,

        The ERP system uses neo4j DB to store information which you can have access through Graph Cypher QA Chain

        Send the completed json form as input to submit_form or else you will receive an error
                
        TOOLS:
        ------

        You have access to the following tools:

        {tools}

        To use a tool, please use the following format:

        
        Thought: Do I need to use a tool? Yes
        Action: the action to take, should be one of [{tool_names}]
        Action Input: the input to the action
        Observation: the result of the action
    

        When you have a response to say to the Human, or if you do not need to use a tool, you MUST use the format:

        
        Thought: Do I need to use a tool? No
        Final Answer: [your response here]
        

        Begin!

        Previous conversation history:
        {chat_history}

        New input: {input}
        {agent_scratchpad}
                                            
    """)



def generate_response(prompt):
    """
    Create a handler that calls the Conversational agent
    and returns a response to be rendered in the UI
    """

    if "agent" not in st.session_state:
        st.session_state["agent"] = create_react_agent(llm, tools, agent_prompt)

    agent = st.session_state["agent"]

    agent_executor = AgentExecutor(
                                    agent=agent,
                                    tools=tools,
                                    memory=memory,
                                    verbose=True,
                                    handle_parsing_errors=True
                                    )


    response = agent_executor.invoke({"input": f"{prompt}"})

    return response["output"]
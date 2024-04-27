from config.neo_conn import graph
from llm.llm import llm
from langchain_core.prompts import PromptTemplate
import json
from openai import OpenAI
import re

class FormHandler:
    def __init__(self, form):
        self.form = form
        

    def handle_submission(self):
        form_data = self.form
        if form_data["form_code"] == 1:
            return self.patient_registration()
        elif form_data["form_code"] == 2:
            return self.submit_medical_history_form()
        elif form_data["form_code"] == 3:
            return self.submit_physical_examination_form()
        elif form_data["form_code"] == 4:
            return self.submit_medication_form()
        elif form_data["form_code"] == 5:
            return self.submit_billing_form()

    
    def patient_registration(self):
        form_data = self.form["form_data"]
        query = """
        CREATE (p:Patient {first_name: $first_name, last_name: $last_name, dob: date($dob)})
        RETURN ID(p) AS patientId
        """
        parameters = {
            "first_name": form_data["first_name"],
            "last_name": form_data["last_name"],
            "dob": form_data["dob"]
        }

        patient_id = graph.query(query=query, params=parameters)


        return f"Patient registration successful with Patient ID {patient_id}"

    def submit_physical_examination_form(self):
        form_data = self.form["form_data"]
        query = """
        MATCH (a:Appointment {appointmentId: $appointment_id})
        CREATE (a)-[:HAS_PHYSICAL_EXAM]->(pe:PhysicalExam {findings: $findings})
        RETURN ID(pe) AS physicalExamId
        """

        #TODO: RN it creates an appointment node when none exists

        query = """
            // First, create or find the appointment node
            MERGE (a:Appointment {appointmentId: $appointment_id})

            // Use the internal ID to match the patient node
            WITH a
            MATCH (p) WHERE ID(p) = $patient_id

            // Create a relationship from the patient to the appointment
            CREATE (p)-[:HAS_APPOINTMENT]->(a)

            // Create a physical exam node and link it to the appointment
            CREATE (a)-[:HAS_PHYSICAL_EXAM]->(pe:PhysicalExam {findings: $findings})

            // Return the ID of the newly created physical exam node
            RETURN ID(pe) AS physicalExamId
        """
        parameters = {
            "appointment_id": form_data["appointment_id"],
            "patient_id": int(form_data["patient_id"]),
            "findings": form_data["findings"]
        }

        physical_exam_id = graph.query(query=query, params=parameters)

        return f"Physical examination form submitted successfully with Physical Exam ID {physical_exam_id}"

    def submit_medical_history_form(self):
        form_data = self.form["form_data"]
        patient_id = int(form_data["patient_id"])  

        query = """
        MATCH (p:Patient) WHERE ID(p) = $patient_id
        CREATE (p)-[:HAS_MEDICAL_HISTORY]->(mh:MedicalHistory {
            allergies: $allergies,
            current_medications: $current_medications,
            past_medical_history: $past_medical_history,
            family_medical_history: $family_medical_history,
            surgical_history: $surgical_history,
            smoking_status: $smoking_status,
            alcohol_intake: $alcohol_intake,
            exercise: $exercise,
            diet: $diet,
            hydration: $hydration,
            caffeine_intake: $caffeine_intake,
            recent_health_issues: $recent_health_issues
        })
        RETURN ID(mh) AS medicalHistoryId
        """
        parameters = {
            "patient_id": patient_id,
            "allergies": form_data["allergies"],
            "current_medications": form_data["current_medications"],
            "past_medical_history": form_data["past_medical_history"],
            "family_medical_history": form_data["family_medical_history"],
            "surgical_history": form_data["surgical_history"],
            "smoking_status": form_data["lifestyle"]["smoking_status"],
            "alcohol_intake": form_data["lifestyle"]["alcohol_intake"],
            "exercise": form_data["lifestyle"]["exercise"],
            "diet": form_data["lifestyle"]["diet"],
            "hydration": form_data["lifestyle"]["hydration"],
            "caffeine_intake": form_data["lifestyle"]["caffeine_intake"],
            "recent_health_issues": form_data["recent_health_issues"]
        }

        medical_history_id = graph.query(query=query, params=parameters)
        print(f"Medical history submitted successfully with MedicalHistory ID {medical_history_id}")

        return "Medical history form submission complete."

    def submit_medication_form(self):
        form_data = self.form["form_data"]
        appointment_id = form_data["appointment_id"]
        medications = form_data["medications"]
        drug_check = str(form_data["drugs_check"])

        if drug_check.lower() == "true":
            medical_history = self.get_medical_history(appointment_id)
            
            interaction_json = self.get_interactions_json(medical_history,medications)

            drug_interactions = self.check_drug_interactions(interaction_json["drug_interactions_to_check"])
            
            food_interactions_json = self.get_food_interactions(medications)

            response_prompt = f"""
                    Use analytical reasoning to analyze patterns in the medical history which may cause adverse drug interactions with the current medications.
                    Medical History: {medical_history}
                    Prescription Drugs: {medications}
                    Drug Interactions: {drug_interactions}
                    Food Interactions: {food_interactions_json}
                    """

            return response_prompt
        #mh = get medical history

        # pass to llm medical history and prescription form to get interaction json
        # pass the interaction json to check for interaction_checker



        else:
            for medication in medications:
                query = """
                MATCH (a:Appointment {appointmentId: $appointment_id})
                CREATE (a)-[:HAS_MEDICATION]->(m:Medication {
                    medication_name: $medication_name, 
                    dosage: $dosage, 
                    frequency: $frequency, 
                    duration: $duration, 
                    instructions: $instructions
                })
                RETURN ID(m) AS medicationId
                """
                parameters = {
                    "appointment_id": appointment_id,
                    "medication_name": medication["medication_name"],
                    "dosage": medication["dosage"],
                    "frequency": medication["frequency"],
                    "duration": medication["duration"],
                    "instructions": medication["instructions"]
                }

                medication_id = graph.query(query=query, params=parameters)
                print(f"Medication submitted successfully with Medication ID {medication_id}")

            return "Medication form submission complete."


    


    def submit_billing_form(self):
        form_data = self.form["form_data"]
        appointment_id = form_data["appointment_id"]
        total_cost = form_data["billing"]["total_cost"]

        query = """
        MATCH (a:Appointment {appointmentId: $appointment_id})
        MERGE (a)-[:HAS_BILLING]->(b:BillingInformation {appointmentId: $appointment_id})
        ON CREATE SET b.total_cost = $total_cost
        ON MATCH SET b.total_cost = $total_cost
        RETURN ID(b) AS billingId
        """
        parameters = {
            "appointment_id": appointment_id,
            "total_cost": total_cost
        }

        billing_id = graph.query(query=query, params=parameters)

        return f"Billing form submitted successfully with Billing ID {billing_id}"
    

    def get_medical_history(self, appointment_id):
        # Cypher query to first match the Appointment node using the provided ID
        # then follow the relationship back to the Patient node
        # and finally follow the relationship to the MedicalHistory node
        query = """
        MATCH (a:Appointment)<-[:HAS_APPOINTMENT]-(p:Patient)-[:HAS_MEDICAL_HISTORY]->(m:MedicalHistory)
        WHERE ID(a) = $appointment_id
        RETURN properties(m) AS medicalHistoryProperties
        """
        query = """
        MATCH (a:Appointment {appointmentId: $appointment_id})<-[:HAS_APPOINTMENT]-(p:Patient)-[:HAS_MEDICAL_HISTORY]->(m:MedicalHistory)
        RETURN properties(m) AS medicalHistoryProperties
        """

        # Parameters to be used in the query
        parameters = {
            "appointment_id": int(appointment_id)
        }

        # Executing the query on the graph database
        result = graph.query(query=query, params=parameters)
        print("result:", result)
        # Fetching the properties of the MedicalHistory node as a string
        if result:
            medical_history_properties = result[0]['medicalHistoryProperties']
            return str(medical_history_properties)
        else:
            return "No medical history found for the given appointment ID."



    def get_food_interactions(self,medications):
        interaction_results = []
        for medication in medications:
            medication_name = medication['medication_name']
            query = """
            MATCH (d:`drugbank_vocabulary:Drug`)-[:`drugbank_vocabulary:food-interaction`]->(fi:`drugbank_vocabulary:Food-interaction`)
            WHERE d.title=$medication_name
            RETURN fi.value AS food_interaction
            """
            parameters = {'medication_name': medication_name}
            result = graph.query(query=query, params=parameters)
            
            # Prepare the output dictionary for the current medication
            medication_info = {
                "medication_name": medication['medication_name'],
                "food_interaction": ", ".join([record['food_interaction'] for record in result]) if result else "No food interaction found"
            }
            interaction_results.append(medication_info)
        
        return interaction_results

    def get_interactions_json(self,medical_history,medications):
        prompt_template = PromptTemplate.from_template("""          
                    analyze the medications prescribed and medical history
                    medical history: 
                    {medical_history}

                    medicine prescription:
                    {medications} 
                    give me all possible drug-drug interactions that should be checked. 

                    give response in the below JSON format ONLY

                    {{
                        "drug_interactions_to_check": [
                            {{
                                "drug_a": "",
                                "drug_b": ""
                            }},...(add more dicts if needed)
                        ]
                    }}

                """)

        prompt = prompt_template.format(medical_history=medical_history,medications=medications)
        
        
        client = OpenAI()

        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            response_format={ "type": "json_object" },
            messages=[
                {"role": "system", "content": "You are a drug expert."},
                {"role": "user", "content": f"{prompt}"}
            ]
        )

        response = completion.choices[0].message.content
        res_json = json.loads(response)
        return res_json

        
    def check_drug_interactions(self,interactions):
        results = []
        for interaction in interactions:
            drug_a = interaction['drug_a']
            drug_b = interaction['drug_b']
            query = """
            MATCH (d1:`drugbank_vocabulary:Drug`) WHERE d1.title = $drug_a
            MATCH (d2:`drugbank_vocabulary:Drug`) WHERE d2.title = $drug_b
            MATCH (d1)-[:`drugbank_vocabulary:ddi-interactor-in`]->(n:`drugbank_vocabulary:Drug-Drug-Interaction`)
            MATCH (d2)-[:`drugbank_vocabulary:ddi-interactor-in`]->(n)
            RETURN n.title AS interaction_title
            """
            parameters = {'drug_a': drug_a, 'drug_b': drug_b}
            result = graph.query(query=query, params=parameters)
            
            if result:
                interaction_titles = ', '.join([record['interaction_title'] for record in result])
                results.append({
                    'drug_a': drug_a,
                    'drug_b': drug_b,
                    'ddi_db_search_context': interaction_titles,
                    'ddi_vector_context': self.vector_ddi_query(f"{drug_a} and {drug_b}")

                })
            else:
                results.append({
                    'drug_a': drug_a,
                    'drug_b': drug_b,
                    'ddi_db_search_context': '',
                    'ddi_vector_context': self.vector_ddi_query(f"{drug_a} and {drug_b}")
                })

        return results
    

    def vector_ddi_query(self, sample_text, top_k=1):
        # Generate an embedding for the sample text
        clean_text = re.sub(r'[^a-zA-Z0-9\s,.]', '', sample_text)

        client = OpenAI()

        embedding_response = client.embeddings.create(
                    input=clean_text,
                    model="text-embedding-3-small"  
                )
        query_vector = embedding_response.data[0].embedding
        


        query = """
                CALL db.index.vector.queryNodes("ddi_index", $top_k, $embedding) 
                YIELD node, score
                RETURN node, score
                """
        parameters = {'top_k': top_k, 'embedding': query_vector}
                
        query_results = graph.query(query=query, params=parameters)
        

        results_list = [f"{drug['node']['title']} -- {drug['score']}" for drug in query_results]
        return ", ".join(results_list)


medications = [
            {
                "medication_name": "Amlodipine",
                "dosage": "5 mg",
                "frequency": "Once daily",
                "duration": "30 days",
                "instructions": "Take one tablet by mouth once daily"
            },
            {
                "medication_name": "Metformin",
                "dosage": "500 mg",
                "frequency": "Twice daily",
                "duration": "60 days",
                "instructions": "Take one tablet by mouth twice daily"
            },
            {
                "medication_name": "Melatonin",
                "dosage": "3 mg",
                "frequency": "As needed for insomnia",
                "duration": "30 days",
                "instructions": "Take one tablet by mouth at bedtime"
            }
        ]


medical_history = """
                {'current_medications': 'Amlodipine 5mg daily (for hypertension), Multivitamin daily, Metformin 500mg twice daily 
                (for prediabetes), Ibuprofen as needed (for occasional headaches), Melatonin 3mg at bedtime (for insomnia)', 
                'hydration': 'Drinks 2 liters of water daily', 'diet': 'Vegetarian, avoids high sodium and high sugar foods, 
                regularly consumes fruits, vegetables, and whole grains', 'past_medical_history': 'Hypertension (diagnosed 2010), 
                Prediabetes (diagnosed 2018), Chickenpox (as a child)', 'surgical_history': 'Appendectomy (2005), C-section (2012)', 
                'family_medical_history': 'Father: Type 2 Diabetes, Hypertension; Mother: Breast Cancer (survivor)', 'smoking_status': 
                'Never smoked', 'exercise': 'Jogging 30 minutes, 3 days a week', 'recent_health_issues': 'Occasional headaches, insomnia', 
                'caffeine_intake': 'Enjoys caffeine daily (1 cup of coffee in the morning)', 'allergies': 'Penicillin, peanuts', 
                'alcohol_intake': 'Social drinker (1-2 drinks per week)'}
                """

interactions = {
    "drug_interactions_to_check": [
        {
            "drug_a": "Amlodipine",
            "drug_b": "Metformin"
        },
        {
            "drug_a": "Amlodipine",
            "drug_b": "Melatonin"
        },
        {
            "drug_a": "Metformin",
            "drug_b": "Melatonin"
        }
    ]
}




# response = vector_ddi_query("Amlodipine and Ibuprofen",1)
# print(response)

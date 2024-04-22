from config.neo_conn import graph




class FormHandler:
    def __init__(self, form):
        self.form = form
        

    def handle_submission(self):
        form_data = self.form
        if form_data["form_code"] == 1:
            return self.patient_registration()
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
        MERGE (a:Appointment {appointmentId: $appointment_id})
        WITH a
        CREATE (a)-[:HAS_PHYSICAL_EXAM]->(pe:PhysicalExam {findings: $findings})
        RETURN ID(pe) AS physicalExamId
        """
        parameters = {
            "appointment_id": form_data["appointment_id"],
            "findings": form_data["findings"]
        }

        physical_exam_id = graph.query(query=query, params=parameters)

        return f"Physical examination form submitted successfully with Physical Exam ID {physical_exam_id}"



    def submit_medication_form(self):
        form_data = self.form["form_data"]
        appointment_id = form_data["appointment_id"]
        medications = form_data["medications"]

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
import os
from dotenv import load_dotenv
import openai
import requests
import json

import time
import logging
from datetime import datetime
import streamlit as st


load_dotenv()
openai.api_key = os.environ.get("OPENAI_API_KEY")
news_api_key = os.environ.get("NEWS_API_KEY")

client = openai.OpenAI()

model = "gpt-3.5-turbo-16k"







class AssistantManager:
    # Static variables to store the thread and assistant IDs

    thread_id = "thread_5Gj8QDXPmcup8H540rhEqhEa"
    assistant_id = None

    def __init__(self, model: str = "gpt-3.5-turbo-16k"):
        self.client = openai.OpenAI()
        self.model = model
        self.assistant = None
        self.thread = None
        self.run = None



        # Retrieve existing assistant and thread if IDs are already set
        if AssistantManager.assistant_id:
            self.assistant = self.client.beta.assistants.retrieve(
                AssistantManager.assistant_id
            )
        if AssistantManager.thread_id:
            self.thread = self.client.beta.threads.retrieve(AssistantManager.thread_id)

    def create_assistant(self, name, instructions, tools):
        if not self.assistant:
            assistant_obj = self.client.beta.assistants.create(
                name=name, instructions=instructions, tools=tools, model=self.model
            )
            AssistantManager.assistant_id = assistant_obj.id
            self.assistant = assistant_obj
            print(f"AssisID: {self.assistant.id}")



    def create_thread(self):
        if not self.thread:
            thread_obj = self.client.beta.threads.create()
            AssistantManager.thread_id = thread_obj.id
            self.thread = thread_obj
            print(f"ThreadID: {self.thread.id}")

    def add_message_to_thread(self, role, content):
        if self.thread:
            self.client.beta.threads.messages.create(
                thread_id=self.thread.id,
                role=role,
                content=content,
            )

    def run_assistant(self, instructions):
        if self.thread and self.assistant:
            self.run = self.client.beta.threads.runs.create(
                thread_id=self.thread.id,
                assistant_id=self.assistant.id,
                instructions=instructions,
            )

    def process_messages(self):
        if self.thread:
            messages = self.client.beta.threads.messages.list(thread_id=self.thread.id)
            summary = []
            # just get the last message of the thread
            last_message = messages.data[0]
            role = last_message.role
            response = last_message.content[0].text.value
            print(f"SUMMARY: {role.capitalize()}: ==> {response}")
            summary.append(response)
            self.summary = "\n".join(summary)

            # loop through all messages in this thread
            # for msg in messages.data:
            #     role = msg.role
            #     content = msg.content[0].text.value
            #     print(f"SUMMARY:: {role.capitalize()}: {content}")

    def wait_for_completion(self):
        if self.thread and self.run:
            while True:
                time.sleep(5)
                run_status = self.client.beta.threads.runs.retrieve(
                    thread_id=self.thread.id,
                    run_id=self.run.id,
                )

                print(f"RUN STATUS: {run_status.model_dump_json(indent=4)}")

                if run_status.status == "completed":
                    self.process_messages()
                    break
                elif run_status.status == "requires_action":
                    print("Function calling now....")
                    self.call_required_functions(
                        run_status.required_action.submit_tool_outputs.model_dump()
                    )
                else:
                    print("Waiting for the Assistant to process...")
    
    def call_required_functions(self, required_actions):
        if not self.run:
            return

        tool_outputs = []

        for action in required_actions["tool_calls"]:
            func_name = action["function"]["name"]
            arguments = json.loads(action["function"]["arguments"])

            if func_name == "get_news":
                output = get_news(topic=arguments["topic"])
                print(f"STUFF ===> {output}")
                final_str = ""
                for item in output:
                    final_str += "".join(item)

                tool_outputs.append({"tool_call_id": action["id"], "output": final_str})
            else:
                raise ValueError(f"Unknown function: {func_name}")

        print("Submitting outputs back to the Assistant...")

        self.client.beta.threads.runs.submit_tool_outputs(
            thread_id=self.thread.id,
            run_id=self.run.id,
            tool_outputs=tool_outputs,
        )
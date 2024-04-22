import streamlit as st
from depriciated_agents.agent import generate_response
from time import sleep
from streamlit_mic_recorder import mic_recorder, speech_to_text
from speech_to_text.transcribe import transcribe_audio
import io




def handle_submit(message):
    """
    Submit handler:

    You will modify this method to talk with an LLM and provide
    context using data from Neo4j.
    """

    # Handle the response
    with st.spinner('Thinking...'):
        response = generate_response(message)
        print("response: ", response)
        sleep(1)
        write_message('assistant', response)


# end::submit[]
def write_message(role, content, save = True):
    """
    This is a helper function that saves a message to the
     session state and then writes a message to the UI
    """
    # Append to session state
    if save:
        st.session_state.messages.append({"role": role, "content": f"{content}"})


    # Write to UI
    with chat_hist_container:
        with st.chat_message(role):
            st.markdown(content)




st.set_page_config("Doc Flow")


chat_hist_container = st.container(height=600, border=False)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "How can I help you ?"},
    ]
    for message in st.session_state.messages:
                write_message(message['role'], message['content'], save=False)


with st.container():

    c1, c2 = st.columns([0.9,0.1])

    with c1:
        text_input = st.chat_input("What is up?")

    with c2:
        audio_input = mic_recorder(
                    start_prompt="🔴",
                    stop_prompt="⬜️",
                    just_once=True,
                    use_container_width=True,
                    format="webm",
                    callback=None,
                    args=(),
                    kwargs={},
                    key=None
                )

        if audio_input:
            audio_bio = io.BytesIO(audio_input['bytes'])
            audio_bio.name = 'audio.webm'
            text_input = transcribe_audio(audio_bio)

    # Handle any user input
    if prompt := text_input:

        with chat_hist_container:
            for message in st.session_state.messages:
                write_message(message['role'], message['content'], save=False)
            
            write_message('user', prompt)

            handle_submit(prompt)



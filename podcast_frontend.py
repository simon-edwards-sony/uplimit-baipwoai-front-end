import streamlit as st
import modal
import json
import os
import openai

def load_sidebar():
  st.sidebar.image('./logo.png', width=200)
  st.sidebar.title("Podcastatron")
  st.sidebar.subheader("Available Podcasts Feeds")
  available_podcasts = get_podcasts_from_files('.')
  selected_podcast = st.sidebar.selectbox("Select Podcast", options=sorted(available_podcasts.keys()))
  if selected_podcast:
    load_podcast_info(available_podcasts[selected_podcast])
    load_chatbot(available_podcasts[selected_podcast])
  
  #st.sidebar.subheader("Add New Podcast url")
  with st.sidebar.expander("Add New Podcast url", expanded=False):
    url = st.text_input("RSS Feed:")
    process_button = st.button(":heavy_check_mark: Add RSS Feed")
    if process_button:
         with st.spinner("Processing RSS url. This may take up to 5 minutes..."):
          if process_podcast_info(url):
            st.success("Successfully processed RSS url")
          else:
            st.error("Error processing RSS url")

def load_podcast_info(podcast_info):
  # Load Episide Title / Image / Summary
  st.subheader(podcast_info['podcast_details']['episode_title'])
  headercol_l, headercol_r = st.columns([3, 7])
  with headercol_l:
    st.image(podcast_info['podcast_details']['episode_image'], width=300, use_column_width="auto")
    
  with headercol_r:
    st.write(podcast_info['podcast_summary'])
  
  st.divider()

  # Load guest Info
  st.subheader("_Guest Info_")
  guest_l, guest_r= st.columns([3, 7])
  with guest_l:
    if podcast_info['podcast_guest'][6] != '':
      st.image(podcast_info['podcast_guest'][6], caption=podcast_info['podcast_guest'][0], width=300, use_column_width="auto")
    else:
      st.write(podcast_info['podcast_guest'][0])
  with guest_r:
    st.write(podcast_info["podcast_guest"][4])
    st.write(podcast_info["podcast_guest"][5])
  
  st.divider()

  # Load highlights
  st.subheader("_Episode Highlights_")
  st.write(podcast_info['podcast_highlights'])

def load_chatbot(podcast_info):
  openai.api_key = st.secrets["OPENAI_API_KEY"]

  st.divider()
  st.subheader("_Chat with an AI version of our guest, %s_" % podcast_info['podcast_guest'][0])

  # Set a default model
  if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo-16k"
  
  # Initialize chat
  if "guest" not in st.session_state:
    st.session_state["guest"] = ""

  # Clear history if guest has changed
  if st.session_state["guest"] != podcast_info['podcast_guest'][0]:
     st.session_state.messages = []
     st.session_state["guest"] = podcast_info['podcast_guest'][0]
  
  # Display chat messages from history on app rerun
  for i, message in enumerate(st.session_state.messages):
    if i > 1:
      with st.chat_message(message["role"]):
        st.markdown(message["content"])

  # Initialize messages
  st.session_state["guest"] = podcast_info['podcast_guest'][0]
  if len(st.session_state.messages) == 0:
    instruction = "You are person named %s, you should answer every question as if you are %s. Your responses should be as natural as possible and feel like a chat with a friend, with great excitement. Here is what we know about you from wikipedia: %s. If we know nothing you should derive as much information from third party sources. You were a guest a podcast with the following transcript, try to direct questions relating to the following podcast transcript: %s" % (podcast_info['podcast_guest'][0], podcast_info['podcast_guest'][0], podcast_info["podcast_guest"][4], podcast_info['podcast_details']['episode_transcript'])
    st.session_state.messages.append({"role": "user", "content": instruction})
    st.session_state.messages.append({"role": "assistant", "content": "Absolutely"})

  # Accept user input
  if prompt := st.chat_input("What is up?"):

        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Display user message in chat message container
        with st.chat_message("user"):
          st.markdown(prompt)

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                for response in openai.ChatCompletion.create(
                    model=st.session_state["openai_model"],
                    messages=[
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages
                    ],
                    stream=True,
                ):
                    full_response += response.choices[0].delta.get("content", "")
                    message_placeholder.markdown(full_response + "▌")
                message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})

  
def get_podcasts_from_files(folder_path):
  # Load podcast json files to dictionary
  json_files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
  data_dict = {}

  for file_name in json_files:
    with open(os.path.join(folder_path, file_name), 'r') as file:
      podcast_info = json.load(file)
      podcast_name = podcast_info['podcast_details']['podcast_title']
      data_dict[podcast_name] = podcast_info

  return data_dict

def process_podcast_info(url):
  # Process rss feed via modal
  try:
    f = modal.Function.lookup("corise-podcast-project", "process_podcast")
    output = f.call(url, '/content/podcast/')

    if output:
      filename = "./podcast-%i.json" % (len(get_podcasts_from_files('.'))+1)
      with open(filename, "w") as outfile:
        json.dump(output, outfile)
      return True
    else:
      return False
  except:
    return False

# Main entry point
if __name__ == '__main__':
    st.set_page_config(layout="wide")
    load_sidebar()
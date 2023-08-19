import streamlit as st
import modal
import json
import os

def load_sidebar():
  st.sidebar.image('./logo.png', width=200)
  st.sidebar.title("Podcastatron")
  st.sidebar.subheader("Available Podcasts Feeds")
  available_podcasts = get_podcasts_from_files('.')
  selected_podcast = st.sidebar.selectbox("Select Podcast", options=sorted(available_podcasts.keys()))
  if selected_podcast:
    load_podcast_info(available_podcasts[selected_podcast])
  
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
    st.image(podcast_info['podcast_details']['episode_image'], width=300, use_column_width=True)
    
  with headercol_r:
    st.write(podcast_info['podcast_summary'])
  
  st.divider()

  # Load guest Info
  st.subheader("_Guest Info_")
  guest_l, guest_r = st.columns([3, 7])
  with guest_l:
    if podcast_info['podcast_guest'][6] != '':
      st.image(podcast_info['podcast_guest'][6], caption=podcast_info['podcast_guest'][0], width=300, use_column_width=True)
    else:
      st.write(podcast_info['podcast_guest'][0])
  with guest_r:
    st.write(podcast_info["podcast_guest"][4])
    st.write(podcast_info["podcast_guest"][5])
  
  st.divider()

  # Load highlights
  st.subheader("_Episode Highlights_")
  st.write(podcast_info['podcast_highlights'])

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
    load_sidebar()
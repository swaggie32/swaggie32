
from dotenv import load_dotenv
from audiocraft.models import MusicGen
import streamlit as st
import torch
import torchaudio
import os
import numpy as np
import base64
import pathlib
import textwrap
import google.generativeai as genai
from IPython.display import display
from IPython.display import Markdown
import pickle
import pandas as pd
import requests
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import webbrowser
import shutil
from PIL import Image
import mysql.connector
from mysql.connector import Error
import hashlib



CLIENT_ID = "70a9fb89662f4dac8d07321b259eaad7"
CLIENT_SECRET = "4d6710460d764fbbb8d8753dc094d131"


load_dotenv()
os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))



# Function to check if user is logged in
def is_user_logged_in():
    return 'logged_in' in st.session_state and st.session_state.logged_in

# Function to connect to MySQL database
def connect_to_database():
    try:
        connection = mysql.connector.connect(
            host='sql6.freesqldatabase.com',
            database='sql6703543',
            user='sql6703543',
            password='l7jwpiZfB2'
        )
        if connection.is_connected():
            print('Connected to MySQL database')
            return connection
    except Error as e:
        print(f'Error connecting to MySQL database: {e}')

# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Function for user signup
def signup(username, password, contact_number, email, image):
    try:
        connection = connect_to_database()
        cursor = connection.cursor()

        # Hash password
        hashed_password = hash_password(password)

        # Save image to directory
        image_filename = save_image(image)

        # Insert user data into database
        query = "INSERT INTO users (username, password, contact_number, email, image) VALUES (%s, %s, %s, %s, %s)"
        data = (username, hashed_password, contact_number, email, image_filename)
        cursor.execute(query, data)
        connection.commit()

        st.success('Sign up successful. Please log in.')
    except Error as e:
        print(f'Error signing up user: {e}')
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

            # Function to save image to directory
def save_image(image):
    # Create directory if it doesn't exist
    if not os.path.exists('dbimg'):
        os.makedirs('dbimg')

    # Save image to directory
    image_path = os.path.join('dbimg', image.name)
    with open(image_path, 'wb') as f:
        f.write(image.read())

    return image_path

# Function for user login
def login(username, password):
    try:
        connection = connect_to_database()
        cursor = connection.cursor()

        hashed_password = hash_password(password)

        query = "SELECT * FROM users WHERE username = %s AND password = %s"
        data = (username, hashed_password)

        cursor.execute(query, data)
        user = cursor.fetchone()

        if user:
            print('Login successful')
            st.session_state.logged_in = True
            st.session_state.user_id = user[0]  # Assuming user ID is the first column in the users table
            return True
        else:
            print('Invalid username or password')
            return False
    except Error as e:
        print(f'Error logging in user: {e}')
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Streamlit UI for signup page
def signup_page():
    st.title("Signup Page")

    username = st.text_input('Username')
    password = st.text_input('Password', type='password')
    confirm_password = st.text_input('Confirm Password', type='password')
    contact_number = st.text_input('Contact Number')
    email = st.text_input('Email')
    image = st.file_uploader('Upload Image', type=['jpg', 'png', 'jpeg'])

    if st.button('Sign Up'):
        if password == confirm_password:
            signup(username, password, contact_number, email, image)
        else:
            st.error('Passwords do not match')

# Streamlit UI for login page
def login_page():
    st.title('Log In')
    username = st.text_input('Username', key='username_input')
    password = st.text_input('Password', type='password', key='password_input')

    if st.button('Log In'):
        if login(username, password):
            st.success('Login successful')
            main_page()
        else:
            st.error('Invalid username or password')

# Main function to run Streamlit app
def main():
    st.set_page_config(page_title="Autonetics: Your Music Companion", page_icon=":musical_note:🤖")
    st.sidebar.title('🤖 Autonetar Music Ai Recomender.')

    if is_user_logged_in():
        main_page()
    else:
        signup_page()
        login_page()

# Function to handle logout
def logout():
    if 'logged_in' in st.session_state:
        del st.session_state.logged_in
    st.experimental_rerun()

# Add logout button on main_page()

def get_gemini_response(question, chat):
    response = chat.send_message(question, stream=True)
    return response

def show_chatbot(chat):
    st.title("Autonetar Music Ai Recomender.🤖")
    st.title("Conversational Music Recommender Chatbot")
    with st.expander("Why Conversational Music Recommender Chatbot need ?"):
        st.write("The Conversational Music Recommender Chatbot using GEMINI (Generative Music Inquiry Neural Interface) is an innovative application that leverages AI technology to recommend music to users in a conversational manner. GEMINI is a neural network architecture designed specifically for music-related tasks, such as generating music, analyzing music preferences, and providing personalized recommendations.")
   

    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = []

    input = st.text_input("Input: ", key="input")
    submit = st.button("Ask the question")

    if submit and input:
        response = get_gemini_response(input, chat)
        # Add user query and response to session state chat history
        st.session_state['chat_history'].append(("You", input))
        st.subheader("The Response is")
        for chunk in response:
            st.write(chunk.text)
            st.session_state['chat_history'].append(("Bot", chunk.text))
    st.subheader("The Chat History is")
        
    for role, text in st.session_state['chat_history']:
        st.write(f"{role}: {text}")




# Initialize the Spotify client
client_credentials_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

def get_song_album_cover_url(song_name, artist_name):
    search_query = f"track:{song_name} artist:{artist_name}"
    results = sp.search(q=search_query, type="track")

    if results and results["tracks"]["items"]:
        track = results["tracks"]["items"][0]
        album_cover_url = track["album"]["images"][0]["url"]
        return album_cover_url
    else:
        return "https://i.postimg.cc/0QNxYz4V/social.png"

@st.cache_resource

def load_model():
    model = MusicGen.get_pretrained('facebook/musicgen-small')
    return model


def generate_music_tensors(description, duration: int):
    model = load_model()

    model.set_generation_params(
        use_sampling=True,
        top_k=250,
        duration=duration
    )

    output = model.generate(
        descriptions=[description],
        progress=True,
        return_tokens=True
    )

    return output[0]


def save_audio(samples: torch.Tensor):
    sample_rate = 32000
    save_path = "audio_output/"
    assert samples.dim() == 2 or samples.dim() == 3

    samples = samples.detach().cpu()
    if samples.dim() == 2:
        samples = samples[None, ...]

    for idx, audio in enumerate(samples):
        audio_path = os.path.join(save_path, f"audio_{idx}.wav")
        torchaudio.save(audio_path, audio, sample_rate)

    return audio_path


def get_binary_file_downloader_html(bin_file, file_label='File'):
    with open(bin_file, 'rb') as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{os.path.basename(bin_file)}">Download {file_label}</a>'
    return href

def recommend(music, similarity, song):
    index = music[music['song'] == song].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    recommended_music_names = []
    recommended_music_posters = []
    recommended_music_uris = []
    for i in distances[1:6]:
        # fetch the album cover and Spotify URI
        artist = music.iloc[i[0]].artist
        track_name = music.iloc[i[0]].song
        results = sp.search(q=f"track:{track_name} artist:{artist}", type="track")
        if results and results["tracks"]["items"]:
            album_cover_url = results["tracks"]["items"][0]["album"]["images"][0]["url"]
            spotify_uri = results["tracks"]["items"][0]["uri"]
            # Append recommended song name, album cover URL, and Spotify URI to lists
            recommended_music_names.append(track_name)
            recommended_music_posters.append(album_cover_url)
            recommended_music_uris.append(spotify_uri)

    return recommended_music_names, recommended_music_posters, recommended_music_uris

def fetch_poster_and_link(music_title):
    try:
        API_KEY = "aedd7d6e8bdb5297123ae81e2c77c321"
        response = requests.get(f"http://ws.audioscrobbler.com/2.0/?method=track.search&track={music_title}&api_key={API_KEY}&format=json")
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()
        tracks = data.get('results', {}).get('trackmatches', {}).get('track', [])
        if tracks:
            # Assuming the first track found is the one we want
            poster_url = tracks[0].get('image', [])[2].get('#text', '')
            track_url = tracks[0].get('url', '')
            return poster_url, track_url
        else:
            st.error("No results found for the music title.")
            return None, None
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching poster and track link: {e}")
        return None, None
    except ValueError as ve:
        st.error(f"Error parsing JSON response: {ve}")
        return None, None


def recommend1(musics):
    try:
        music_index = music[music['title'] == musics].index[0]
        distances = similarity[music_index]
        music_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]
        recommended_music = []
        recommended_music_poster = []
        recommended_music_links = []
        for i in music_list:
            music_title = music.iloc[i[0]].title
            poster_link, track_link = fetch_poster_and_link(music_title)
            if poster_link:
                recommended_music.append(music_title)
                recommended_music_poster.append(poster_link)
                recommended_music_links.append(track_link)
        return recommended_music, recommended_music_poster, recommended_music_links
    except IndexError:
        st.error("Music not found or insufficient data for recommendation.")
        return [], [], []


music_dict = pickle.load(open(r'C:\Users\dj414\autonater\autonater\music\music_rec_new\musicrec.pkl', 'rb'))
music = pd.DataFrame(music_dict)


similarity = pickle.load(open(r'C:\Users\dj414\autonater\autonater\music\music_rec_new\similarities.pkl', 'rb'))

def update_profile(username, new_password, contact_number, email, image):
    try:
        connection = connect_to_database()
        cursor = connection.cursor()

        # Hash new password if provided
        if new_password:
            hashed_password = hash_password(new_password)

        # Save new image to directory
        if image:
            image_filename = save_image(image)
        else:
            image_filename = None

        # Update user data in database
        if new_password:
            query = "UPDATE users SET password = %s WHERE username = %s"
            cursor.execute(query, (hashed_password, username))
        if contact_number:
            query = "UPDATE users SET contact_number = %s WHERE username = %s"
            cursor.execute(query, (contact_number, username))
        if email:
            query = "UPDATE users SET email = %s WHERE username = %s"
            cursor.execute(query, (email, username))
        if image_filename:
            query = "UPDATE users SET image = %s WHERE username = %s"
            cursor.execute(query, (image_filename, username))

        connection.commit()
        st.success("Profile updated successfully")
    except Error as e:
        print(f'Error updating profile: {e}')
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Add a new page in the sidebar for the profile
def profile_page():
    st.title("Autonetar Music Ai Recomender.🤖")
    with st.expander("Why Profile Page and Delete account need?"):
        st.write("A profile page enables users to personalize their experience and manage their preferences. The option to delete an account ensures transparency, compliance with data regulations, and user control over personal data and privacy.")
    st.title("Profile")
    st.write("Change your username and password below:")
    new_username = st.text_input("New Username", key="new_username_input")
    new_password = st.text_input("New Password", type="password", key="new_password_input")
    confirm_password = st.text_input("Confirm New Password", type="password", key="confirm_password_input")

    if st.button("Update"):
        if new_password == confirm_password:
            update_profile(new_username, new_password)
        else:
            st.error("Passwords do not match")

    if st.button("Delete Profile"):
        delete_profile()

def get_user_info(user_id):
    try:
        # Establish connection to MySQL database
        connection = mysql.connector.connect(
             host='sql6.freesqldatabase.com',
            database='sql6703543',
            user='sql6703543',
            password='l7jwpiZfB2'
        )

        if connection.is_connected():
            cursor = connection.cursor()

            # Execute query to fetch user information based on user ID
            query = "SELECT username, contact_number, email, image FROM users WHERE id = %s"
            cursor.execute(query, (user_id,))
            user_info = cursor.fetchone()

            if user_info:
                # Convert user_info tuple to dictionary
                user_info_dict = {
                    'username': user_info[0],
                    'contact_number': user_info[1],
                    'email': user_info[2],
                    'image': user_info[3]
                }
                print("User information fetched successfully:", user_info_dict)  # Add this line for debugging
                return user_info_dict
            else:
                print("User not found.")
                return None

    except mysql.connector.Error as e:
        print(f"Error fetching user information: {e}")
        return None

    finally:
        # Close database connection
        if connection.is_connected():
            cursor.close()
            connection.close()


def update_profile_page():
    st.title("Profile")
    st.write("Here is your profile information:")

    # Fetch user information from the database based on user ID
    user_id = st.session_state.user_id
    print("User ID:", user_id)  # Add this line for debugging
    user_info = get_user_info(user_id)  # Implement this function to fetch user info from the database
    print("User Info:", user_info)  # Add this line for debugging

    if user_info:
        st.write(f"Username: {user_info['username']}")
        st.write(f"Contact Number: {user_info['contact_number']}")
        st.write(f"Email: {user_info['email']}")
        st.image(user_info['image'], caption="Your Profile Image")
    else:
        st.error("User information not found.") 
    st.title("Update Profile")

    # Generate unique keys for each input widget
    username_key = "Username_input"
    new_password_key = "New_Password_input"
    confirm_password_key = "Confirm_New_Password_input"
    contact_number_key = "Contact_Number_input"
    email_key = "Email_input"
    image_key = "Image_upload"

    # Create input widgets with unique keys
    username = st.text_input('Username', key=username_key)
    new_password = st.text_input('New Password', type='password', key=new_password_key)
    confirm_password = st.text_input('Confirm New Password', type='password', key=confirm_password_key)
    contact_number = st.text_input('Contact Number', key=contact_number_key)
    email = st.text_input('Email', key=email_key)
    image = st.file_uploader('Upload New Image', type=['jpg', 'png', 'jpeg'], key=image_key)

    if st.button('Update'):
        if new_password == confirm_password:
            update_profile(username, new_password, contact_number, email, image)
        else:
            st.error('Passwords do not match')



# Implement backend function to delete profile
def delete_profile():
    try:
        # Connect to database
        connection = connect_to_database()
        cursor = connection.cursor()

        # Delete user's profile from the database
        query = "DELETE FROM users WHERE id = %s"
        data = (st.session_state.user_id,)
        cursor.execute(query, data)

        connection.commit()
        st.success("Profile deleted successfully")
        
        # Clear session state
        st.session_state = {}

        # Rerun the app to redirect to login page
        st.experimental_rerun()
    except Error as e:
        print(f'Error deleting profile: {e}')
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def main_page():
    
    
    st.markdown(
        """
        <style>
            .sidebar .sidebar-content {
                background-color: #2c3e50;
                color: white;
            }
            .sidebar .sidebar-content .block-container {
                color: white;
            }
            .sidebar .sidebar-content .block-container .stRadio {
                color: white;
            }
            .sidebar .sidebar-content .block-container .stRadio label {
                color: white;
            }
            .stButton>button {
                background-color: #3498db;
                color: white;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 16px;
                transition: background-color 0.3s;
            }
            .stButton>button:hover {
                background-color: #2980b9;
            }
            .home-background {
                background-image: linear-gradient(rgba(52, 73, 94, 0.8), rgba(52, 73, 94, 0.8)), url('https://example.com/background.jpg');
                background-size: cover;
                background-repeat: no-repeat;
                background-position: center;
                height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                text-align: center;
            }
            .home-content {
                color: white;
                padding: 40px;
                border-radius: 20px;
                background-color: rgba(0, 0, 0, 0.5);
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
            }
            .primary-text {
                color: #3498db;
            }
            .secondary-text {
                color: #2ecc71;
            }
            .about-us {
                margin-top: 50px;
                display: flex;
                justify-content: space-around;
                flex-wrap: wrap;
                background-image: linear-gradient(rgba(0, 0, 0, 0.8), rgba(0, 0, 0, 0.8)), url('https://example.com/about_us_background.jpg');
                background-size: cover;
                background-repeat: no-repeat;
                background-position: center;
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
            }
            .creator-card {
                background-color: rgba(255, 255, 255, 0.8);
                padding: 20px;
                border-radius: 10px;
                margin: 20px;
                max-width: 300px;
                text-align: center;
            }
            .creator-name {
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 10px;
            }
            .creator-role {
                font-size: 18px;
                margin-bottom: 10px;
            }
            .creator-photo {
                width: 150px;
                height: 150px;
                border-radius: 50%;
                margin-bottom: 10px;
            }
            .references {
                margin-top: 50px;
                background-image: linear-gradient(rgba(0, 0, 0, 0.8), rgba(0, 0, 0, 0.8)), url('https://example.com/references_background.jpg');
                background-size: cover;
                background-repeat: no-repeat;
                background-position: center;
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
            }
            .reference-card {
                background-color: rgba(255, 255, 255, 0.8);
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
            }
            .references h2 {
                color: #3498db;
                margin-bottom: 20px;
            }
        </style>
        """,
        unsafe_allow_html=True
    )
    

    
    st.sidebar.title("Menu")
    
    selected_page = st.sidebar.radio("Go to", ["Home", "Conversational Music Recommender Chatbot", "Text-to-Music Generator", "Music Recommender Spotyfi English", "Music Recommender Lastfm Hindi", "Profile"])

    if selected_page == "Home":
        show_homepage()
    elif selected_page == "Conversational Music Recommender Chatbot":
        chat = genai.GenerativeModel("gemini-pro").start_chat(history=[])
        show_chatbot(chat)
    elif selected_page == "Text-to-Music Generator":
        show_text_to_music_generator()
    elif selected_page == "Music Recommender Spotyfi English":
        music, similarity = load_data()
        show_music_recommender(music, similarity)
    elif selected_page == "Music Recommender Lastfm Hindi":
        show_music_recommender_lastfm()
    elif selected_page == "Profile":
        update_profile_page()
    st.sidebar.button('Logout', on_click=logout)

    st.markdown(
    """
    <style>
    .footer {
        background-color: #2c3e50;
        padding: 20px;
        color: white;
        text-align: center;
        width: 100%;
        position: fixed;
        bottom: 0;
        left: 0;
    }
    </style>
    <div class="footer">
        <p style="font-size: 18px;">Contact: [admincontact_us@autonater.com] | Address: [Sahyog Thane]</p>
        <p style="font-size: 18px;">Project Name: Autonetar Music AI Recommender | Team Members: Shubham Maurya & Devesh Jadhav </p>
        <p style="font-size: 14px;">© 2024 Autonetar Music. All rights reserved.</p>
    </div>
    """,
    unsafe_allow_html=True
)

def load_data():
    # Load data from pickle files
    music = pickle.load(open('df.pkl','rb'))
    similarity = pickle.load(open('similarity.pkl','rb'))
    return music, similarity


def show_homepage():
    st.title("Autonetar Music Ai Recomender.🤖")
    st.markdown(
        """
        <div class="home-background">
            <div class="home-content">
                <h1 class="primary-text">Welcome to Our Interactive Hub!</h1>
                <p>Explore a world of dynamic features tailored just for you:</p>
                <ul>
                    <li><strong>Autonetics:</strong> Engage in real-time conversations with Gemini, our friendly chatbot. Ask questions, seek assistance, or simply chat for fun!</li>
                    <li><strong>Text-to-Music Generator:</strong> Transform your words into melodies with our innovative text-to-music generator. Watch as your messages come to life in beautiful compositions.</li>
                    <li><strong>Personalized Music Recommendations:</strong> Discover your next favorite song with our music recommendation engine powered by LastFM and Spotify APIs. Tailored just for you based on your preferences. Hindi and English both available. LastFM is used for Bollywood categories and Spotify is used for Hollywood categories.</li>
                </ul>
                <p>Experience the future of interaction and entertainment. Start exploring now!</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown(
        """
        <style>
            /* Add the CSS styles for the creator card here */
            .about-us {
                margin-top: 50px;
                display: flex;
                justify-content: space-around;
                flex-wrap: wrap;
            }
            .creator-card {
                background-color: rgba(255, 255, 255, 0.8);
                padding: 20px;
                border-radius: 10px;
                margin: 20px;
                max-width: 300px;
                text-align: center;
            }
            .creator-name {
                color: rgb(205, 92, 92);
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 10px;
            }
            .creator-role {
                color: rgb(255, 160, 122);
                font-size: 18px;
                margin-bottom: 10px;
            }
            .creator-photo {
                width: 150px;
                height: 150px;
                border-radius: 50%;
                margin-bottom: 10px;
            }
        </style>
        <div class="about-us">
            <div class="creator-card">
                <img src="img\shubham.jpg" alt="Girl in a jacket" width="500" height="600">
                <div class="creator-name">Shubham Maurya</div>
                <div class="creator-role">Co-founder & Developer</div>
            </div>
            <div class="creator-card">
                <img src="\img\devesh.jpg" alt="Girl in a jacket" width="500" height="600">
                <div class="creator-name">Devesh Jadhav</div>
                <div class="creator-role">Co-founder & Designer</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <style>
            /* Add the CSS styles for the reference card here */
            .references {
                margin-top: 50px;
                background-color: rgba(255, 255, 255, 0);
                color: rgb(205, 92, 92);
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 4px 8px rgba(255, 255, 255, 0;
            }
            .references h2 {
                color: rgb(205, 92, 92);
                
                margin-bottom: 20px;
            }
            .reference-card {
                background-color: rgba(255, 255, 255, 0);
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
            }
        </style>
        <div class="references">
            <h2>References</h2>
            <div class="reference-card">
                <p>This project is inspired by:</p>
                <ul>
                    <li>Streamlit - For building interactive web apps with Python</li>
                    <li>LastFM API - For music data and recommendations</li>
                    <li>Spotify API - For music streaming and recommendations</li>
                </ul>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def show_text_to_music_generator():
    st.title("Autonetar Music Ai Recomender.🤖")
    st.title("Text to Music Generator🎵")

    with st.expander("why Text to Music Generator need?"):
        st.write("Building a Music Generator app using Meta's Audiocraft library and leveraging the Music Gen Small model sounds like an exciting project! Meta's Audiocraft library provides developers with tools and resources to create innovative audio applications, while the Music Gen Small model is likely a neural network specifically trained for generating music.")

    text_area = st.text_area("Enter your description.......")
    time_slider = st.slider("Select time duration (In Seconds)", 0, 20, 10)

    if text_area and time_slider:
        st.json({
            'Your Description': text_area,
            'Selected Time Duration (in Seconds)': time_slider
        })

        st.subheader("Generated Music")
        music_tensors = generate_music_tensors(text_area, time_slider)
        save_music_file = save_audio(music_tensors)
        audio_file = open(save_music_file, 'rb')
        audio_bytes = audio_file.read()
        st.audio(audio_bytes)
        st.markdown(get_binary_file_downloader_html(save_music_file, 'Audio'))

def show_music_recommender(music, similarity):
    st.title("Autonetar Music Ai Recomender.🤖")
    st.title("Music Recommender Spotyfi English.🎵")
    with st.expander("Why Music Recommender Spotyfi English need?"):
        st.write("Creating a music recommender system integrated with Spotify in English can be an engaging project. Here's a general outline of how you might approach it.")

    music_list = music['song'].values
    selected_song = st.selectbox(
        "Type or select a song from the dropdown",
        music_list
    )

    if st.button('Show Recommendation'):
        recommended_music_names, recommended_music_posters, _ = recommend(music, similarity, selected_song)
        col1, col2, col3, col4, col5= st.columns(5)
        for i in range(5):
            with col1:
                st.write(recommended_music_names[i])
                st.image(recommended_music_posters[i])
                st.markdown(f"[Listen on Spotify](https://open.spotify.com/search/{recommended_music_names[i].replace(' ', '%20')})")

def show_music_recommender_lastfm():
    st.title("Autonetar Music Ai Recomender.🤖")
    st.title('Music Recommender Lastfm Hindi.🎵')
    with st.expander("Why Music Recommender Lastfm Hindi need?"):
        st.write("Creating a music recommender system integrated with Last.fm in Hindi could be a fantastic project, especially for users who prefer Hindi-language content. Here's a basic outline to get you started.")

    selected_music_name = st.selectbox('Select a music you like', music['title'].values)

    if st.button('Recommend'):
        names, posters, links = recommend1(selected_music_name)

        col1, col2, col3, col4, col5 = st.columns(5)

        for name, poster, link in zip(names, posters, links):
            with col1:
                st.text(name)
                st.markdown(f"[![Poster]({poster})]({link})")

if __name__ == '__main__':
    main()


    


import streamlit as st
import paho.mqtt.client as mqtt
import json
import pandas as pd
import queue
from datetime import datetime

# 1. CONFIGURATION
st.set_page_config(page_title="Core-AI Industrial", layout="wide")

# Initialisation des données dans la session
if 'motors_data' not in st.session_state:
    st.session_state.motors_data = {}

# 2. RECEPTION MQTT
def on_message(client, userdata, msg):
    try:
        # On attend motor/M1/data
        topic_parts = msg.topic.split('/')
        motor_id = topic_parts[1].upper() 
        payload = json.loads(msg.payload.decode('utf-8'))
        payload['motor_id'] = motor_id
        payload['Time'] = datetime.now().strftime("%H:%M:%S")
        userdata.put(payload)
    except Exception as e:
        pass

FLESPI_TOKEN = "PlEgqU3lgSi87roUYQ9t7oKjrtTeytcfHHUbYiDcfJgk6Ct0SxICHvdOB2jb6TtD"

@st.cache_resource
def init_mqtt():
    q = queue.Queue()
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, userdata=q)
    client.username_pw_set(FLESPI_TOKEN, "") 
    client.on_message = on_message
    client.connect("mqtt.flespi.io", 1883, 60)
    client.subscribe("motor/+/data") # Ton topic Flespi
    client.loop_start()
    return client, q

mqtt_client, data_queue = init_mqtt()

# --- CETTE PARTIE DOIT ÊTRE EXÉCUTÉE À CHAQUE RUN ---
# On vide la queue et on remplit le session_state
while not data_queue.empty():
    msg = data_queue.get()
    m_id = msg['motor_id']
    if m_id not in st.session_state.motors_data:
        st.session_state.motors_data[m_id] = []
    
    st.session_state.motors_data[m_id].append(msg)
    
    # On garde seulement les 60 derniers points
    if len(st.session_state.motors_data[m_id]) > 60:
        st.session_state.motors_data[m_id].pop(0)

# 3. INTERFACE (Sidebar)
with st.sidebar:
    st.title("🏭 FLOTTE IA")
    if not st.session_state.motors_data:
        st.warning("⚠️ En attente de données Flespi...")
        st.info("Topic attendu : motor/+/data")
        # Bouton pour forcer le rafraîchissement
        if st.button("Rafraîchir manuellement"):
            st.rerun()
    
    motor_list = sorted(list(st.session_state.motors_data.keys()))
    if motor_list:
        selected_motor = st.selectbox("Sélection unité", motor_list)
    else:
        selected_motor = None

# ... (Le reste du code pour l'affichage des graphiques reste identique)

# 4. AUTO-RAFRAÎCHISSEMENT (Placé à la fin)
import time
time.sleep(2) # On attend 2 secondes avant de relancer[cite: 1]
st.rerun()
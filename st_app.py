import streamlit as st
import pandas as pd
import requests
from matplotlib import pyplot as plt
from datetime import datetime

# Sunucudan veri çekme
response = requests.get("http://172.20.10.5:5000/data")

if response.status_code == 200:
    data = response.json()
    veri = {
        "timestamp": [datetime.now()],
        "LED1_Status" : [0],
        "LED2_Status" : [0],
        "LED3_Status" : [0],
    }
    if not data:
        df = pd.DataFrame(veri)
    else:
        df = pd.DataFrame(data)

    # Timestamp'i datetime formatına çevir
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Aynı timestamp'e sahip satırları grupla ve değerleri birleştir
    result = df.groupby('timestamp', as_index=False).first()
    result = result.fillna(method='ffill')

    result['time_diff'] = result['timestamp'].diff().shift(-1).dt.total_seconds()
    result['time_diff'] = result['time_diff'].fillna(0)


    # İnsan sayısını hesaplama (ilk 3 kolondan herhangi biri 2 değerinde ise)
    def calculate_people_count(row):
        if 2 in row[['LED1_Status', 'LED2_Status', 'LED3_Status']].values:
            return 1  # İnsan sayısı arttı
        return 0  # İnsan sayısı artmadı

    # Yeni bir sütun ekleyerek her satır için insan sayısını hesapla
    result['people_count'] = result.apply(calculate_people_count, axis=1)

    # İnsan sayısını toplam olarak göster
    total_people_count = result['people_count'].sum()

    LED1_mode0 = result[result["LED1_Status"]==0]["time_diff"].sum()
    LED1_mode1 = result[result["LED1_Status"]==1]["time_diff"].sum()
    LED1_mode2 = result[result["LED1_Status"]==2]["time_diff"].sum()

    LED2_mode0 = result[result["LED2_Status"]==0]["time_diff"].sum()
    LED2_mode1 = result[result["LED2_Status"]==1]["time_diff"].sum()
    LED2_mode2 = result[result["LED2_Status"]==2]["time_diff"].sum()

    LED3_mode0 = result[result["LED3_Status"]==0]["time_diff"].sum()
    LED3_mode1 = result[result["LED3_Status"]==1]["time_diff"].sum()
    LED3_mode2 = result[result["LED3_Status"]==2]["time_diff"].sum()

    st.dataframe(result)

    # Function to create a custom metric-like box with resized font
    def create_custom_metric(label, value):
        return f"""
        <div style="padding: 10px; border-radius: 8px; width: 100%; ">
            <strong>{label}</strong><br>
            <span style="font-size: 20px; color: #333;">{value} seconds</span>
        </div>
        """
    
    def plot_pie_chart(labels, sizes, title):
        fig, ax = plt.subplots()
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=['#ff9999','#66b3ff','#99ff99'])
        ax.axis('equal')  # Equal aspect ratio ensures that pie chart is drawn as a circle.
        st.pyplot(fig)


    st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)  # Adjust height as needed

    # Layout using columns to show LED mode values
    col1, col2, col3 = st.columns(3)

    with col1:
        st.write("### LED 1")
        st.markdown(create_custom_metric("Mode 0", f"{LED1_mode0:.2f}"), unsafe_allow_html=True)
        st.markdown(create_custom_metric("Mode 1", f"{LED1_mode1:.2f}"), unsafe_allow_html=True)
        st.markdown(create_custom_metric("Mode 2", f"{LED1_mode2:.2f}"), unsafe_allow_html=True)
        if LED1_mode0 or LED1_mode1 or LED1_mode2 :
            # Pie chart for LED 1
            plot_pie_chart(
                labels=['Mode 0', 'Mode 1', 'Mode 2'],
                sizes=[LED1_mode0, LED1_mode1, LED1_mode2],
                title="LED 1 Mode Distribution"
            )

    with col2:
        st.write("### LED 2")
        st.markdown(create_custom_metric("Mode 0", f"{LED2_mode0:.2f}"), unsafe_allow_html=True)
        st.markdown(create_custom_metric("Mode 1", f"{LED2_mode1:.2f}"), unsafe_allow_html=True)
        st.markdown(create_custom_metric("Mode 2", f"{LED2_mode2:.2f}"), unsafe_allow_html=True)
        # Pie chart for LED 2
        if LED2_mode0 or LED2_mode1 or LED2_mode2 :
            plot_pie_chart(
                labels=['Mode 0', 'Mode 1', 'Mode 2'],
                sizes=[LED2_mode0, LED2_mode1, LED2_mode2],
                title="LED 2 Mode Distribution"
            )

    with col3:
        st.write("### LED 3")
        st.markdown(create_custom_metric("Mode 0", f"{LED3_mode0:.2f}"), unsafe_allow_html=True)
        st.markdown(create_custom_metric("Mode 1", f"{LED3_mode1:.2f}"), unsafe_allow_html=True)
        st.markdown(create_custom_metric("Mode 2", f"{LED3_mode2:.2f}"), unsafe_allow_html=True)
        # Pie chart for LED 3
        if LED3_mode0 or LED3_mode1 or LED3_mode2:
            plot_pie_chart(
                labels=['Mode 0', 'Mode 1', 'Mode 2'],
                sizes=[LED3_mode0, LED3_mode1, LED3_mode2],
                title="LED 3 Mode Distribution"
            )

    st.write(f"**Toplam İnsan Sayısı**: {total_people_count}")
else:
    st.error("Veri çekilemedi!")

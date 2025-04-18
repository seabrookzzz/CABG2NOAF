import streamlit as st
import shap
import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def web_app():
    st.set_page_config(page_title='NOAF Risk in CABG Patients')
    # xgb = joblib.load('./git/xgb8.pkl')
    xgb = joblib.load('./xgb8.pkl')

    class Subject:
        def __init__(self, SHR, Age, BMI, SBP, Hemoglobin, BUN, PO2, Beta_blocker):
            self.SHR = SHR
            self.Age = Age
            self.BMI = BMI
            self.SBP = SBP
            self.Hemoglobin = Hemoglobin
            self.BUN = BUN
            self.PO2 = PO2
            self.Beta_blocker = Beta_blocker

        def make_predict(self):
            subject_data = {
                "SHR": [self.SHR],
                "Age": [self.Age],
                "BMI": [self.BMI],
                "SBP": [self.SBP],
                "Hemoglobin": [self.Hemoglobin],
                "BUN": [self.BUN],
                "PO2": [self.PO2],
                "Beta_blocker": [self.Beta_blocker],
            }

            df_subject = pd.DataFrame(subject_data)
            prediction = xgb.predict_proba(df_subject)[:, 1]
            cutoff = 0.20563838
            if prediction >= cutoff:
                adjusted_prediction = (prediction - cutoff) * (0.5 / (1 - cutoff)) + 0.5
                adjusted_prediction = np.clip(adjusted_prediction, 0.5, 1)
            else:
                adjusted_prediction = prediction * (0.5 / cutoff)
                adjusted_prediction = np.clip(adjusted_prediction, 0, 0.5)

            adjusted_prediction = np.round(adjusted_prediction * 100, 2)
            st.write(f"""
                        <div class='all'>
                            <p style='text-align: center; color: #3a3838; font-size: 20px;'>
                                <b>According to the provided information,<br>the model estimates a {adjusted_prediction}% probability of NOAF.</b>
                            </p>
                        </div>
                    """, unsafe_allow_html=True)

            explainer = shap.TreeExplainer(xgb)
            shap_values = explainer.shap_values(df_subject)
            shap.force_plot(explainer.expected_value, shap_values[0, :], df_subject.iloc[0, :], matplotlib=True)
            st.pyplot(plt.gcf())

    st.markdown(f"""
        <div class='all'>
            <h1 style='text-align: center; color: #3a3838;'>Web App<br> NOAF Risk in CABG Patients</h1>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        glucose = st.number_input("Blood Glucose (mg/dL)", min_value=50, max_value=600, value=180)
        Age = st.number_input("Age (years)", min_value=18, max_value=100, value=85)
        SBP = st.number_input("Diastolic Blood Pressure (mmHg)", min_value=60, max_value=180, value=120)
        Hemoglobin = st.number_input("Hemoglobin (g/dL)", min_value=2.0, max_value=20.0, value=8.0, format="%.1f")

    with col2:
        hba1c = st.number_input("HbA1c (%)", min_value=3.0, max_value=15.0, value=5.0, format="%.1f")
        BMI = st.number_input("Body Mass Index (BMI)", min_value=10.0, max_value=60.0, value=25.0, format="%.1f")
        PO2 = st.number_input("PO2 (mmHg)", min_value=100, max_value=600, value=230)
        BUN = st.number_input("Blood Urea Nitrogen (mg/dL)", min_value=1, max_value=80, value=25)
    Beta_blocker = st.slider("β-blocker (0: No, 1: Yes)", min_value=0, max_value=1, value=1)
    # Beta_blocker = st.selectbox("β-blocker", options=[0, 1], index=0)
    # Beta_blocker = st.radio("Beta blocker", options=['No', 'Yes'], index=0)
    # Beta_blocker = 1 if Beta_blocker == 'Yes' else 0

    if st.button(label="Submit"):
        try:
            SHR = glucose / (28.7 * hba1c - 46.7)
            if SHR <= 0 or np.isnan(SHR) or np.isinf(SHR):
                st.error("Invalid SHR calculation. Please check your glucose and HbA1c values.")
            else:
                SHR = round(SHR, 2)
                # st.write(f"Calculated SHR: {SHR}")
                user = Subject(SHR, Age, BMI, SBP, Hemoglobin, BUN, PO2, Beta_blocker)
                user.make_predict()
        except Exception as e:
            st.error(f"An error occurred while calculating SHR: {e}")


web_app()

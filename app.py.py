import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Sinter Plant Dashboard", layout="wide")
st.title("🏭 Sinter Plant KPI Dashboard")
st.markdown("Monitor TI, RDI, RI and track correlations using real-time DoE visualizations.")

# --- SIDEBAR: File Uploaders ---
st.sidebar.header("Upload Data Files")
beta_file = st.sidebar.file_uploader("Upload Beta File (Chemical/Size - 3 Yr)", type=["csv", "xlsx"])
gamma_file = st.sidebar.file_uploader("Upload Gamma File (Process - 1 Yr)", type=["csv", "xlsx"])

@st.cache_data
def load_beta(file):
    # Depending on format, read skipping the multi-header
    df = pd.read_csv(file, header=[0, 1]) if file.name.endswith('.csv') else pd.read_excel(file, header=[0,1])
    
    # Flatten MultiIndex columns
    new_cols = []
    for c1, c2 in df.columns:
        if "Unnamed" in str(c1): new_cols.append(str(c2).strip())
        elif "Unnamed" in str(c2): new_cols.append(str(c1).strip())
        else: new_cols.append(f"{str(c1).strip()}_{str(c2).strip()}" if str(c1).strip() != str(c2).strip() else str(c1).strip())
    
    df.columns = new_cols
    date_col = [c for c in df.columns if 'DATE' in c.upper()][0]
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df.set_index(date_col, inplace=True)
    return df.select_dtypes(include=[np.number])

@st.cache_data
def load_gamma(file):
    df = pd.read_csv(file, skiprows=1) if file.name.endswith('.csv') else pd.read_excel(file, skiprows=1)
    df = df.dropna(axis=1, how='all')
    df.rename(columns={'Date ': 'Date', '%6.3MM(TI)': 'TI'}, inplace=True)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df.set_index('Date', inplace=True)
    return df.select_dtypes(include=[np.number])

if beta_file and gamma_file:
    beta_df = load_beta(beta_file)
    gamma_df = load_gamma(gamma_file)
    
    st.success("Files loaded successfully!")
    
    tab1, tab2, tab3 = st.tabs(["KPI Time Trends", "Correlation Analysis", "DoE Response Surfaces"])
    
    with tab1:
        st.subheader("Historical Trends (TI, RDI, RI)")
        fig_beta = go.Figure()
        for col in ['TI', 'RDI', 'RI']:
            if col in beta_df.columns:
                # Resampling monthly for cleaner visualization
                monthly_data = beta_df[col].resample('M').mean()
                fig_beta.add_trace(go.Scatter(x=monthly_data.index, y=monthly_data.values, mode='lines+markers', name=col))
        fig_beta.update_layout(title="Beta File: Metallurgical Properties over Time", xaxis_title="Date", yaxis_title="Index Value")
        st.plotly_chart(fig_beta, use_container_width=True)
        
    with tab2:
        st.subheader("Process & Chemical Correlations")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Beta (Chemistry & Size) vs Targets**")
            corr_b = beta_df.corr()[['TI', 'RDI', 'RI']].drop(['TI', 'RDI', 'RI']).sort_values(by='TI', ascending=False)
            fig_corr_b = px.imshow(corr_b, text_auto=".2f", aspect="auto", color_continuous_scale="RdBu_r")
            st.plotly_chart(fig_corr_b, use_container_width=True)
            
        with col2:
            st.markdown("**Gamma (Process Params) vs Targets**")
            # Exclude overlapping target columns if present to avoid errors
            targets = [t for t in ['TI', 'RDI', 'RI'] if t in gamma_df.columns]
            corr_g = gamma_df.corr()[targets].drop(targets).sort_values(by=targets[0], ascending=False)
            fig_corr_g = px.imshow(corr_g, text_auto=".2f", aspect="auto", color_continuous_scale="RdBu_r")
            st.plotly_chart(fig_corr_g, use_container_width=True)

    with tab3:
        st.subheader("DoE Contour Plots (Response Surface Modeling)")
        st.markdown("Identify the optimum operational windows by analyzing 2D surface interactions.")
        
        c1, c2 = st.columns(2)
        with c1:
            # RI vs MgO/Al2O3 and %Al2O3
            if 'MgO/Al2O3' in beta_df.columns and '%Al2O3' in beta_df.columns:
                fig_contour1 = px.density_contour(beta_df.reset_index(), x="%Al2O3", y="MgO/Al2O3", z="RI", histfunc="avg", title="DoE: Reducibility Index (RI) Surface")
                fig_contour1.update_traces(contours_coloring="fill", colorscale="Viridis")
                st.plotly_chart(fig_contour1, use_container_width=True)
        with c2:
             # TI vs Windbox Press and Product Temp (Gamma)
             if 'WB 1 Press. (mbar)' in gamma_df.columns and 'Product Temp' in gamma_df.columns:
                fig_contour2 = px.density_contour(gamma_df.reset_index(), x="Product Temp", y="WB 1 Press. (mbar)", z="TI", histfunc="avg", title="DoE: Tumbler Index (TI) Surface")
                fig_contour2.update_traces(contours_coloring="fill", colorscale="Plasma")
                st.plotly_chart(fig_contour2, use_container_width=True)
                
else:
    st.info("Please upload both the Beta and Gamma files from the sidebar to interact with the dashboard.")
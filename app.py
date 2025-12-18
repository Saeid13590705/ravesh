import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO

# تنظیمات اولیه
st.set_page_config(
    page_title="داشبورد کارنامه",
    layout="wide",
    initial_sidebar_state="expanded"
)

# عنوان
st.title("📊 تحلیل کارنامه تحصیلی")
st.markdown("---")

# آپلود فایل در سایدبار
with st.sidebar:
    st.header("📁 آپلود فایل")
    uploaded_file = st.file_uploader(
        "فایل اکسل کارنامه را انتخاب کنید",
        type=['xlsx', 'xls']
    )
    
    if uploaded_file is not None:
        st.success("✅ فایل آماده است")
        file_name = uploaded_file.name
        file_size = uploaded_file.size / 1024  # به کیلوبایت
        st.info(f"**نام فایل:** {file_name}\n**حجم:** {file_size:.1f} KB")
    else:
        st.info("⏳ در انتظار آپلود فایل...")

# بخش اصلی
if uploaded_file is not None:
    try:
        # خواندن فایل
        xls = pd.ExcelFile(uploaded_file)
        
        # نمایش شیت‌ها
        st.header("📋 اطلاعات فایل")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("تعداد شیت‌ها", len(xls.sheet_names))
        with col2:
            st.metric("فرمت فایل", uploaded_file.name.split('.')[-1].upper())
        
        # انتخاب شیت
        selected_sheet = st.selectbox(
            "انتخاب شیت برای تحلیل",
            xls.sheet_names
        )
        
        # خواندن داده‌ها
        df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
        
        # نمایش داده‌ها
        with st.expander("👀 مشاهده داده‌ها", expanded=True):
            st.dataframe(df, use_container_width=True)
        
        # تحلیل ساده
        st.header("📈 تحلیل اولیه")
        
        # شناسایی ستون‌های عددی
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if numeric_cols:
            col1, col2, col3 = st.columns(3

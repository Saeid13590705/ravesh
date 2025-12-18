import streamlit as st
import pandas as pd
import plotly.express as px

# تنظیمات
st.set_page_config(
    page_title="داشبورد کارنامه",
    layout="wide"
)

st.title("📊 تحلیل کارنامه تحصیلی")
st.markdown("---")

# آپلود فایل
uploaded_file = st.file_uploader(
    "📁 فایل اکسل کارنامه را آپلود کنید",
    type=['xlsx', 'xls']
)

if uploaded_file is not None:
    try:
        # خواندن فایل
        df = pd.read_excel(uploaded_file)
        
        st.success(f"✅ فایل با موفقیت خوانده شد!")
        st.write(f"تعداد دانش‌آموزان: **{len(df)}** نفر")
        st.write(f"تعداد ستون‌ها: **{len(df.columns)}**")
        
        # نمایش ستون‌ها
        st.write("### ستون‌های موجود:")
        st.write(df.columns.tolist())
        
        # نمایش نمونه داده
        st.write("### نمونه داده‌ها:")
        st.dataframe(df.head())
        
        # تحلیل ساده
        st.write("### تحلیل اولیه:")
        
        # پیدا کردن ستون‌های عددی
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if numeric_cols:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("تعداد دروس", len(numeric_cols))
            
            with col2:
                # میانگین کلی
                overall_avg = df[numeric_cols].mean().mean()
                st.metric("میانگین کل", f"{overall_avg:.2f}")
            
            with col3:
                # بهترین نمره
                max_score = df[numeric_cols].max().max()
                st.metric("بیشترین نمره", f"{max_score:.1f}")
            
            # نمودار ساده
            st.write("### نمودار میانگین دروس:")
            
            # میانگین هر درس
            subject_avg = df[numeric_cols].mean().sort_values(ascending=False)
            fig = px.bar(
                x=subject_avg.index,
                y=subject_avg.values,
                title="میانگین نمره هر درس",
                labels={'x': 'درس', 'y': 'میانگین نمره'}
            )
            st.plotly_chart(fig)
        
        else:
            st.warning("هیچ ستون عددی در فایل یافت نشد.")
            
    except Exception as e:
        st.error(f"❌ خطا در پردازش فایل: {str(e)}")
        
else:
    st.info("👆 لطفاً یک فایل اکسل کارنامه آپلود کنید.")
    st.markdown("""
    ### ساختار مورد انتظار فایل:
    - ستون «کلاس» (اختیاری)
    - ستون‌های «نام» و «نام خانوادگی» (اختیاری)
    - ستون‌های دروس با نمرات عددی
    
    ### مثال:
    | کلاس | نام | نام خانوادگی | ریاضی | علوم | ادبیات |
    |------|-----|--------------|-------|------|--------|
    | هفتم/1 | علی | رضایی | 18 | 17 | 19 |
    """)

st.markdown("---")
st.write("ساخته شده با ❤️ توسط Streamlit")

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO
import os

# ----------------- تنظیمات صفحه -----------------
st.set_page_config(
    page_title="داشبورد تحلیل کارنامه تحصیلی",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 داشبورد تحلیل کارنامه ترم اول")
st.markdown("---")

# ----------------- بخش آپلود فایل -----------------
st.sidebar.header("📁 آپلود فایل جدید")

uploaded_file = st.sidebar.file_uploader(
    "فایل اکسل کارنامه را انتخاب کنید",
    type=['xlsx', 'xls'],
    help="فایل باید ساختار استاندارد کارنامه را داشته باشد"
)

# ----------------- مدیریت فایل -----------------
if uploaded_file is not None:
    # استفاده از فایل آپلود شده
    file_source = "آپلود شده"
    
    # خواندن فایل
    try:
        xls = pd.ExcelFile(BytesIO(uploaded_file.read()))
        # Reset file pointer
        uploaded_file.seek(0)
    except Exception as e:
        st.error(f"❌ خطا در خواندن فایل اکسل: {str(e)}")
        st.stop()
        
else:
    # استفاده از فایل پیش‌فرض
    FILE_NAME = "14040919_1300.xlsx"
    file_source = "پیش‌فرض"
    
    if not os.path.exists(FILE_NAME):
        st.warning("⚠️ فایل پیش‌فرض یافت نشد. لطفاً فایل اکسل را آپلود کنید.")
        st.stop()
    
    try:
        xls = pd.ExcelFile(FILE_NAME)
    except Exception as e:
        st.error(f"❌ خطا در خواندن فایل اکسل: {str(e)}")
        st.stop()

st.sidebar.info(f"منبع فایل: **{file_source}**")

# ----------------- Sidebar -----------------
with st.sidebar:
    st.markdown("---")
    st.header("⚙️ تنظیمات تحلیل")
    
    # انتخاب شیت
    selected_base = st.selectbox(
        "انتخاب پایه / شیت",
        xls.sheet_names,
        index=0
    )
    
    st.markdown("---")
    st.header("ℹ️ اطلاعات فایل")
    st.write(f"تعداد شیت‌ها: **{len(xls.sheet_names)}**")
    st.write(f"شیت‌های موجود: {', '.join(xls.sheet_names)}")

# ----------------- بارگذاری شیت انتخابی -----------------
def load_sheet_data(sheet_name, uploaded_file_obj=None, file_path=None):
    """بارگذاری داده‌های یک شیت"""
    try:
        if uploaded_file_obj is not None:
            uploaded_file_obj.seek(0)
            df = pd.read_excel(BytesIO(uploaded_file_obj.read()), sheet_name=sheet_name)
        else:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
        return df
    except Exception as e:
        st.error(f"❌ خطا در خواندن شیت {sheet_name}: {str(e)}")
        return None

# بارگذاری داده‌ها
if uploaded_file is not None:
    df = load_sheet_data(selected_base, uploaded_file_obj=uploaded_file)
else:
    df = load_sheet_data(selected_base, file_path=FILE_NAME)

if df is None:
    st.stop()

# نمایش اطلاعات فایل
with st.expander("🔍 مشاهده اطلاعات فایل آپلود شده", expanded=False):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("تعداد ردیف‌ها", df.shape[0])
    with col2:
        st.metric("تعداد ستون‌ها", df.shape[1])
    with col3:
        st.metric("حجم داده", f"{df.memory_usage().sum() / 1024:.1f} KB")
    
    st.write("نمونه‌ای از داده‌ها:")
    st.dataframe(df.head(), use_container_width=True)

# ----------------- شناسایی خودکار ستون‌های دروس -----------------
def identify_subject_columns(df):
    """شناسایی خودکار ستون‌های دروس"""
    # لیست احتمالی نام دروس
    subject_patterns = [
        'قرآن', 'دینی', 'املا', 'انشا', 'ادبیات', 'عربی', 'زبان',
        'علوم', 'ریاضی', 'اجتماعی', 'تفکر', 'هنر', 'هوش', 
        'کار و فناوری', 'فیزیک', 'شیمی', 'زیست', 'تاریخ', 'جغرافیا'
    ]
    
    subject_columns = []
    for col in df.columns:
        col_str = str(col).strip()
        for pattern in subject_patterns:
            if pattern in col_str:
                subject_columns.append(col)
                break
    
    # اگر ستون درسی پیدا نشد
    if not subject_columns:
        for col in df.columns:
            try:
                numeric_check = pd.to_numeric(df[col].head(10), errors='coerce')
                if numeric_check.notna().sum() > 5:
                    subject_columns.append(col)
            except:
                continue
    
    return subject_columns

# شناسایی دروس
subject_columns = identify_subject_columns(df)

if not subject_columns:
    st.error("❌ هیچ ستون درسی شناسایی نشد! لطفاً مطمئن شوید فایل ساختار صحیحی دارد.")
    st.stop()

st.success(f"✅ {len(subject_columns)} ستون درسی شناسایی شد")

# ----------------- محاسبه میانگین نمرات -----------------
df_clean = df.copy()
for col in subject_columns:
    df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')

df_clean['میانگین نمرات'] = df_clean[subject_columns].mean(axis=1).round(2)
df_clean = df_clean.dropna(subset=['میانگین نمرات'])

# ----------------- شناسایی ستون کلاس -----------------
def identify_class_column(df):
    """شناسایی خودکار ستون کلاس"""
    class_patterns = ['کلاس', 'class', 'پایه', 'رشته', 'گروه']
    
    for col in df.columns:
        col_str = str(col).strip().lower()
        for pattern in class_patterns:
            if pattern in col_str:
                return col
    
    # اگر پیدا نشد
    for col in df.columns:
        if col not in subject_columns and col != 'میانگین نمرات':
            try:
                pd.to_numeric(df[col].head(10), errors='raise')
            except:
                return col
    
    return df.columns[0]

class_column = identify_class_column(df_clean)
df_clean[class_column] = df_clean[class_column].astype(str).str.strip()

# ----------------- شناسایی ستون‌های نام -----------------
def identify_name_columns(df):
    """شناسایی ستون‌های نام و نام خانوادگی"""
    name_cols = {'نام': None, 'نام خانوادگی': None}
    
    for col in df.columns:
        col_str = str(col).strip().lower()
        if 'نام' in col_str and 'خانوادگی' in col_str:
            name_cols['نام خانوادگی'] = col
        elif 'نام' in col_str and name_cols['نام'] is None:
            name_cols['نام'] = col
    
    return name_cols

name_cols = identify_name_columns(df_clean)

# ----------------- انتخاب کلاس -----------------
classes = sorted(df_clean[class_column].dropna().unique())

with st.sidebar:
    st.markdown("---")
    selected_class = st.selectbox(
        "انتخاب کلاس",
        ["همه کلاس‌ها"] + list(classes),
        index=0
    )

if selected_class != "همه کلاس‌ها":
    df_filtered = df_clean[df_clean[class_column] == selected_class].copy()
else:
    df_filtered = df_clean.copy()

# ----------------- شاخص‌های کلیدی -----------------
st.subheader("📊 شاخص‌های عملکردی")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("تعداد دانش‌آموز", df_filtered.shape[0])

with col2:
    avg_score = df_filtered['میانگین نمرات'].mean()
    st.metric("میانگین کل", f"{avg_score:.2f}")

with col3:
    max_score = df_filtered['میانگین نمرات'].max()
    st.metric("بیشترین نمره", f"{max_score:.2f}")

with col4:
    min_score = df_filtered['میانگین نمرات'].min()
    st.metric("کمترین نمره", f"{min_score:.2f}")

with col5:
    std_score = df_filtered['میانگین نمرات'].std()
    st.metric("انحراف معیار", f"{std_score:.2f}")

st.markdown("---")

# ----------------- تحلیل تک‌تک دروس -----------------
st.subheader("📚 تحلیل عملکرد درسی")

# محاسبه آمار هر درس
subject_stats = []
for subject in subject_columns:
    if subject in df_filtered.columns:
        stats = {
            'درس': subject,
            'میانگین': df_filtered[subject].mean(),
            'بیشترین': df_filtered[subject].max(),
            'کمترین': df_filtered[subject].min(),
            'انحراف معیار': df_filtered[subject].std(),
            'تعداد نمره': df_filtered[subject].count()
        }
        subject_stats.append(stats)

if subject_stats:
    subject_df = pd.DataFrame(subject_stats).round(2)
    subject_df_sorted = subject_df.sort_values('میانگین', ascending=False)
    
    # نمایش تحلیل دروس
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # نمودار میانگین دروس
        fig_subjects = px.bar(
            subject_df_sorted,
            x='درس',
            y='میانگین',
            title='میانگین نمره هر درس',
            color='میانگین',
            color_continuous_scale='RdYlGn',
            text='میانگین'
        )
        fig_subjects.update_layout(
            xaxis_tickangle=-45,
            height=400
        )
        st.plotly_chart(fig_subjects, use_container_width=True)
    
    with col2:
        st.write("📊 آمار دروس:")
        st.dataframe(
            subject_df_sorted[['درس', 'میانگین', 'بیشترین', 'کمترین']],
            use_container_width=True,
            height=400
        )
else:
    st.warning("⚠️ هیچ آمار درسی برای نمایش وجود ندارد.")

# ----------------- تب‌های اصلی -----------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 توزیع نمرات", 
    "🏫 مقایسه کلاس‌ها", 
    "🥇 رتبه‌بندی", 
    "📋 داده خام",
    "⚙️ تنظیمات پیشرفته"
])

# ---------- تب ۱: توزیع نمرات ----------
with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        # هیستوگرام
        if not df_filtered.empty:
            fig_hist = px.histogram(
                df_filtered,
                x='میانگین نمرات',
                nbins=15,
                title='توزیع میانگین نمرات',
                color_discrete_sequence=['#2E86AB'],
                opacity=0.8
            )
            fig_hist.update_layout(
                xaxis_title='میانگین نمرات',
                yaxis_title='تعداد دانش‌آموزان'
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.warning("داده‌ای برای نمایش هیستوگرام وجود ندارد.")
    
    with col2:
        # نمودار جعبه‌ای
        if not df_filtered.empty and len(df_filtered) > 1:
            fig_box = px.box(
                df_filtered,
                y='میانگین نمرات',
                title='پراکندگی نمرات',
                points='all',
                color_discrete_sequence=['#A23B72']
            )
            fig_box.update_layout(height=400)
            st.plotly_chart(fig_box, use_container_width=True)
            
            # نمایش آمار توصیفی
            st.write("📊 آمار توصیفی:")
            desc_stats = df_filtered['میانگین نمرات'].describe().round(2)
            st.write(desc_stats)
        else:
            st.warning("داده کافی برای نمودار جعبه‌ای وجود ندارد.")

# ---------- تب ۲: مقایسه کلاس‌ها ----------
with tab2:
    if selected_class == "همه کلاس‌ها":
        if len(df_clean[class_column].unique()) > 1:
            # محاسبه آمار برای هر کلاس
            class_stats = df_clean.groupby(class_column)['میانگین نمرات'].agg([
                ('تعداد', 'count'),
                ('میانگین', 'mean'),
                ('انحراف معیار', 'std'),
                ('کمترین', 'min'),
                ('میانه', 'median'),
                ('بیشترین', 'max')
            ]).round(2).reset_index()
            
            class_stats = class_stats.sort_values('میانگین', ascending=False)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # نمودار مقایسه کلاس‌ها
                fig_class = px.bar(
                    class_stats,
                    x=class_column,
                    y='میانگین',
                    title='میانگین نمره هر کلاس',
                    color='میانگین',
                    text='میانگین',
                    color_continuous_scale='plasma'
                )
                st.plotly_chart(fig_class, use_container_width=True)
            
            with col2:
                # جدول آمار کلاس‌ها
                st.write("📋 آمار کلاس‌ها:")
                st.dataframe(
                    class_stats,
                    use_container_width=True,
                    hide_index=True
                )
        else:
            st.info("فقط یک کلاس در داده‌ها وجود دارد.")
    else:
        st.info(f"📌 در حال مشاهده کلاس **{selected_class}** هستید. برای مقایسه کلاس‌ها، گزینه 'همه کلاس‌ها' را انتخاب کنید.")

# ---------- تب ۳: رتبه‌بندی ----------
with tab3:
    if not df_filtered.empty:
        # آماده‌سازی داده برای رتبه‌بندی
        ranking_df = df_filtered.copy()
        
        # ایجاد نام کامل
        full_name = ""
        if name_cols['نام'] and name_cols['نام خانوادگی']:
            if name_cols['نام'] in ranking_df.columns and name_cols['نام خانوادگی'] in ranking_df.columns:
                ranking_df['نام کامل'] = ranking_df[name_cols['نام']].astype(str) + ' ' + ranking_df[name_cols['نام خانوادگی']].astype(str)
                full_name = 'نام کامل'
        elif name_cols['نام']:
            if name_cols['نام'] in ranking_df.columns:
                ranking_df['نام کامل'] = ranking_df[name_cols['نام']].astype(str)
                full_name = 'نام کامل'
        
        if not full_name:
            ranking_df['شناسه'] = 'دانش‌آموز ' + (ranking_df.index + 1).astype(str)
            full_name = 'شناسه'
        
        # مرتب‌سازی و رتبه‌بندی
        ranking_df = ranking_df.sort_values('میانگین نمرات', ascending=False)
        ranking_df['رتبه'] = range(1, len(ranking_df) + 1)
        
        # نمایش جدول رتبه‌بندی
        display_cols = ['رتبه', full_name, 'میانگین نمرات', class_column]
        
        # اضافه کردن حداکثر ۳ درس اول
        subject_display = []
        for subject in subject_columns[:3]:
            if subject in ranking_df.columns:
                subject_display.append(subject)
        
        display_cols.extend(subject_display)
        
        # حذف ستون‌های تکراری
        display_cols = list(dict.fromkeys(display_cols))
        
        st.dataframe(
            ranking_df[display_cols],
            use_container_width=True,
            height=400
        )
        
        # نمایش ۵ نفر برتر
        if len(ranking_df) >= 3:
            st.subheader("🏆 برترین‌های کلاس")
            top_count = min(5, len(ranking_df))
            top_n = ranking_df.head(top_count)
            
            fig_top = px.bar(
                top_n,
                x=full_name,
                y='میانگین نمرات',
                title=f'{top_count} دانش‌آموز برتر',
                text='میانگین نمرات',
                color='میانگین نمرات',
                color_continuous_scale='RdYlGn'
            )
            fig_top.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_top, use_container_width=True)
        else:
            st.info("تعداد دانش‌آموزان برای نمایش نمودار برترین‌ها کافی نیست.")
    else:
        st.warning("داده‌ای برای رتبه‌بندی وجود ندارد.")

# ---------- تب ۴: داده خام ----------
with tab4:
    st.write(f"📄 داده‌های خام کلاس: **{selected_class}**")
    
    if not df_filtered.empty:
        # انتخاب ستون‌های نمایش
        all_columns = list(df_filtered.columns)
        
        # ستون‌های پیش‌فرض بدون تکراری
        default_cols = []
        
        # اضافه کردن ستون کلاس
        if class_column in all_columns:
            default_cols.append(class_column)
        
        # اضافه کردن میانگین نمرات
        if 'میانگین نمرات' in all_columns:
            default_cols.append('میانگین نمرات')
        
        # اضافه کردن نام و نام خانوادگی اگر وجود دارند
        if name_cols['نام'] and name_cols['نام'] in all_columns:
            default_cols.append(name_cols['نام'])
        
        if name_cols['نام خانوادگی'] and name_cols['نام خانوادگی'] in all_columns:
            default_cols.append(name_cols['نام خانوادگی'])
        
        # اضافه کردن ۳ درس اول
        for subject in subject_columns[:3]:
            if subject in all_columns and subject not in default_cols:
                default_cols.append(subject)
        
        # حذف مقادیر None و تکراری
        default_cols = [col for col in default_cols if col is not None]
        default_cols = list(dict.fromkeys(default_cols))
        
        # فیلتر ستون‌ها
        columns_to_show = st.multiselect(
            "ستون‌ها را برای نمایش انتخاب کنید:",
            options=all_columns,
            default=default_cols
        )
        
        if columns_to_show:
            # حذف ستون‌های تکراری
            columns_to_show = list(dict.fromkeys(columns_to_show))
            
            try:
                st.dataframe(
                    df_filtered[columns_to_show],
                    use_container_width=True,
                    height=500
                )
            except Exception as e:
                st.error(f"❌ خطا در نمایش داده‌ها: {str(e)}")
                st.write("ستون‌های انتخاب شده:", columns_to_show)
                st.write("تعداد ستون‌های منحصر به فرد:", len(set(columns_to_show)))
        else:
            st.warning("لطفاً حداقل یک ستون برای نمایش انتخاب کنید.")
    else:
        st.warning("داده‌ای برای نمایش وجود ندارد.")

# ---------- تب ۵: تنظیمات پیشرفته ----------
with tab5:
    st.subheader("⚙️ تنظیمات پیشرفته تحلیل")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # آستانه نمره
        min_score_threshold = st.slider(
            "حداقل نمره برای محاسبه میانگین:",
            min_value=0,
            max_value=20,
            value=0,
            help="نمرات کمتر از این مقدار در محاسبه میانگین در نظر گرفته نمی‌شوند"
        )
        
        # وزن‌دهی دروس
        st.write("### وزن‌دهی دروس (اختیاری)")
        use_weighting = st.checkbox("فعال کردن وزن‌دهی دروس")
        
        if use_weighting:
            st.info("⚠️ این قابلیت در نسخه فعلی غیرفعال است")
    
    with col2:
        # دروس انتخابی
        st.write("### انتخاب دروس برای تحلیل")
        selected_subjects = st.multiselect(
            "دروس مورد نظر برای تحلیل:",
            options=subject_columns,
            default=subject_columns[:min(6, len(subject_columns))]
        )
        
        if selected_subjects:
            st.success(f"{len(selected_subjects)} درس انتخاب شده است")
        
        # ریست کش
        if st.button("🔄 ریست حافظه کش"):
            st.cache_data.clear()
            st.success("حافظه کش پاک شد!")
            st.rerun()

# ----------------- بخش دانلود خروجی -----------------
st.markdown("---")
st.subheader("📥 خروجی‌ها")

output_col1, output_col2, output_col3 = st.columns(3)

with output_col1:
    # دانلود داده‌های فیلتر شده
    if not df_filtered.empty:
        filtered_csv = df_filtered.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            "💾 دانلود داده‌های فیلتر شده (CSV)",
            data=filtered_csv,
            file_name=f"کارنامه_{selected_base}_{selected_class}.csv",
            mime="text/csv",
            help="دانلود تمام داده‌های کلاس انتخاب شده"
        )
    else:
        st.info("داده‌ای برای دانلود وجود ندارد.")

with output_col2:
    # دانلود آمار دروس
    if 'subject_df' in locals() and not subject_df.empty:
        subjects_csv = subject_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            "📊 دانلود آمار دروس (CSV)",
            data=subjects_csv,
            file_name=f"آمار_دروس_{selected_base}_{selected_class}.csv",
            mime="text/csv",
            help="دانلود آمار توصیفی تمام دروس"
        )
    else:
        st.info("آمار دروسی برای دانلود وجود ندارد.")

with output_col3:
    # دانلود رتبه‌بندی
    if 'ranking_df' in locals() and not ranking_df.empty:
        ranking_csv = ranking_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            "🥇 دانلود رتبه‌بندی (CSV)",
            data=ranking_csv,
            file_name=f"رتبه‌بندی_{selected_base}_{selected_class}.csv",
            mime="text/csv",
            help="دانلود رتبه‌بندی کامل دانش‌آموزان"
        )
    else:
        st.info("رتبه‌بندی برای دانلود وجود ندارد.")

# ----------------- راهنمای استفاده -----------------
with st.sidebar:
    st.markdown("---")
    with st.expander("📖 راهنمای استفاده"):
        st.markdown("""
        ### نحوه استفاده:
        
        1. **آپلود فایل**: فایل اکسل کارنامه را آپلود کنید
        2. **انتخاب شیت**: پایه/شیت مورد نظر را انتخاب کنید
        3. **انتخاب کلاس**: کلاس خاص یا همه کلاس‌ها را انتخاب کنید
        4. **تحلیل داده**: از تب‌های مختلف برای تحلیل استفاده کنید
        5. **دانلود**: نتایج را در قالب CSV دانلود کنید
        
        ### ساختار فایل مورد انتظار:
        - ستون «کلاس» برای شناسایی کلاس‌ها
        - ستون‌های «نام» و «نام خانوادگی»
        - ستون‌های دروس با نام‌های استاندارد
        - داده‌های عددی در ستون‌های دروس
        
        ### نکات:
        - فایل باید فرمت xlsx یا xls باشد
        - سیستم به صورت خودکار ستون‌ها را شناسایی می‌کند
        - برای بهترین تجربه از مرورگرهای مدرن استفاده کنید
        """)

# ----------------- پیام موفقیت -----------------
if not df_filtered.empty:
    st.success("""
    ✅ تحلیل با موفقیت انجام شد! 
    میتوانید از تب‌های مختلف برای بررسی جزئیات استفاده کنید یا نتایج را دانلود نمایید.
    """)
else:
    st.info("📊 منتظر ورود داده‌ها هستیم. لطفاً فایل کارنامه را آپلود کنید.")

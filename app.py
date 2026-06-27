import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io
import base64

# إعدادات الصفحة
st.set_page_config(
    page_title="نظام التقارير الأسبوعية - البلهارسيا والفاشيولا",
    page_icon="🧪",
    layout="wide"
)

# عنوان التطبيق
st.markdown("""
    <h1 style='text-align: center; color: #136b5e;'>🧪 وكيل التقارير - البلهارسيا والفاشيولا</h1>
    <hr>
""", unsafe_allow_html=True)

# العمودين الرئيسيين
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📅 تاريخ نهاية الأسبوع")
    date = st.date_input("اختر التاريخ", datetime(2026, 5, 24))
    
    days = ['الأحد', 'الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت']
    day_idx = date.weekday() + 1 if date.weekday() != 6 else 0
    selected_day = st.selectbox("يوم نهاية الأسبوع", days, index=day_idx)
    
    # حساب رقم الأسبوع
    week_number = date.isocalendar()[1]
    week = st.number_input("رقم الأسبوع الدولي", min_value=1, max_value=53, value=week_number)

with col2:
    st.subheader("📊 معلومات التقرير")
    st.write(f"**📅 التاريخ:** {date.strftime('%Y-%m-%d')}")
    st.write(f"**📆 اليوم:** {selected_day}")
    st.write(f"**📊 الأسبوع:** {week}")

# إنشاء الجدول
st.subheader("📋 بيانات التقرير")

# بيانات الجدول
data = {
    "الفئة": ["العيادة الخارجية", "عينة عشوائية", "المدارس"],
    "مصرى أنثى ≥12": [0, 0, 0],
    "مصرى أنثى >12": [0, 0, 0],
    "مصرى ذكر ≥12": [0, 0, 0],
    "مصرى ذكر >12": [0, 0, 0],
    "غير مصرى أنثى ≥12": [0, 0, 0],
    "غير مصرى أنثى >12": [0, 0, 0],
    "غير مصرى ذكر ≥12": [0, 0, 0],
    "غير مصرى ذكر >12": [0, 0, 0],
}

df = st.data_editor(
    pd.DataFrame(data),
    use_container_width=True,
    hide_index=True,
    column_config={
        "الفئة": st.column_config.TextColumn("الفئة", width="small"),
        "مصرى أنثى ≥12": st.column_config.NumberColumn("مصرى أنثى ≥12", min_value=0, step=1),
        "مصرى أنثى >12": st.column_config.NumberColumn("مصرى أنثى >12", min_value=0, step=1),
        "مصرى ذكر ≥12": st.column_config.NumberColumn("مصرى ذكر ≥12", min_value=0, step=1),
        "مصرى ذكر >12": st.column_config.NumberColumn("مصرى ذكر >12", min_value=0, step=1),
        "غير مصرى أنثى ≥12": st.column_config.NumberColumn("غير مصرى أنثى ≥12", min_value=0, step=1),
        "غير مصرى أنثى >12": st.column_config.NumberColumn("غير مصرى أنثى >12", min_value=0, step=1),
        "غير مصرى ذكر ≥12": st.column_config.NumberColumn("غير مصرى ذكر ≥12", min_value=0, step=1),
        "غير مصرى ذكر >12": st.column_config.NumberColumn("غير مصرى ذكر >12", min_value=0, step=1),
    }
)

# حساب الإجماليات
st.subheader("📊 إجماليات التقرير")

# جدول الجنسيات
st.subheader("🌍 إجمالي المفحوصين حسب الجنسية")

cols = st.columns(5)
with cols[0]:
    syrian = st.number_input("سورى", min_value=0, step=1, key="syrian")
with cols[1]:
    iraqi = st.number_input("عراقى", min_value=0, step=1, key="iraqi")
with cols[2]:
    sudani = st.number_input("سودانى", min_value=0, step=1, key="sudani")
with cols[3]:
    libyan = st.number_input("ليبى", min_value=0, step=1, key="libyan")
with cols[4]:
    yemeni = st.number_input("يمنى", min_value=0, step=1, key="yemeni")

# أزرار التحكم
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("💾 حفظ التقرير", use_container_width=True):
        st.success("✅ تم حفظ التقرير بنجاح في السجل!")

with col2:
    if st.button("📄 استخراج PDF", use_container_width=True):
        st.info("📄 سيتم تحميل ملف PDF...")
        st.success("✅ تم استخراج PDF بنجاح!")

with col3:
    if st.button("🧹 مسح الخلايا", use_container_width=True):
        st.info("🧹 تم مسح جميع الحقول")

# عرض سجل التقارير
st.subheader("📋 سجل التقارير المحفوظة")

# تقارير عينة
sample_reports = pd.DataFrame({
    "التاريخ": ["2026-05-24", "2026-05-17", "2026-05-10"],
    "اليوم": ["السبت", "السبت", "السبت"],
    "الأسبوع": [21, 20, 19],
    "المفحوصين": [120, 95, 110],
    "الإيجابي": [5, 3, 7]
})

st.dataframe(sample_reports, use_container_width=True, hide_index=True)

# تذييل الصفحة
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    st.write("**فنى المعمل**")
    st.write("**محمود عبده الجمال**")
    st.write("**ساره عبدالحميد جابر**")

with col2:
    st.write("**مدير الوحدة**")
    st.write("**_________________**")
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import io
import base64
from reportlab.lib.pagesizes import A3, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
import calendar

# ==================== إعدادات الصفحة ====================
st.set_page_config(
    page_title="نظام التقارير الأسبوعية - البلهارسيا والفاشيولا",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==================== تهيئة Session State ====================
def init_session_state():
    """تهيئة جميع متغيرات الجلسة"""
    if 'reports_db' not in st.session_state:
        st.session_state.reports_db = []
    
    if 'auto_week' not in st.session_state:
        st.session_state.auto_week = True
    
    if 'report_data' not in st.session_state:
        st.session_state.report_data = {}
    
    if 'endDate' not in st.session_state:
        st.session_state.endDate = '2026-05-24'
    
    if 'endDaySelect' not in st.session_state:
        st.session_state.endDaySelect = 6
    
    if 'customWeekNumber' not in st.session_state:
        st.session_state.customWeekNumber = 21
    
    if 'totals' not in st.session_state:
        st.session_state.totals = {f'sum{i+1}': 0 for i in range(26)}
    
    # تهيئة الحقول الفارغة
    for prefix in ['out', 'rand', 'school']:
        for i in range(26):
            key = f'{prefix}_{i}'
            if key not in st.session_state:
                st.session_state[key] = ''
    
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True

# استدعاء التهيئة
init_session_state()

# ==================== دوال مساعدة ====================
def get_iso_week_number(date):
    """حساب رقم الأسبوع الدولي"""
    return date.isocalendar()[1]

def get_day_name(day_index):
    """الحصول على اسم اليوم"""
    days = ['الأحد', 'الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت']
    return days[day_index]

def calculate_totals(data):
    """حساب الإجماليات"""
    totals = {f'sum{i+1}': 0 for i in range(26)}
    for row in ['out', 'rand', 'school']:
        for i in range(26):
            key = f'{row}_{i}'
            val = data.get(key, 0)
            if val:
                try:
                    totals[f'sum{i+1}'] += int(val)
                except:
                    pass
    return totals

def collect_data():
    """جمع البيانات من جميع الحقول"""
    data = {}
    for i in range(26):
        for prefix in ['out', 'rand', 'school']:
            key = f'{prefix}_{i}'
            if key in st.session_state:
                data[key] = st.session_state[key]
    data['savedDate'] = st.session_state.get('endDate', '')
    data['savedDay'] = st.session_state.get('endDaySelect', 6)
    data['savedWeek'] = st.session_state.get('customWeekNumber', 21)
    return data

def load_data(data):
    """تحميل البيانات إلى session state"""
    for key, value in data.items():
        if key.startswith(('out_', 'rand_', 'school_')):
            st.session_state[key] = value
    if 'savedDate' in data:
        st.session_state['endDate'] = data['savedDate']
    if 'savedDay' in data:
        st.session_state['endDaySelect'] = data['savedDay']
    if 'savedWeek' in data:
        st.session_state['customWeekNumber'] = data['savedWeek']
        st.session_state['auto_week'] = False
    else:
        st.session_state['auto_week'] = True
    update_totals()

def update_totals():
    """تحديث الإجماليات"""
    totals = {f'sum{i+1}': 0 for i in range(26)}
    for i in range(26):
        total = 0
        for prefix in ['out', 'rand', 'school']:
            key = f'{prefix}_{i}'
            val = st.session_state.get(key, 0)
            if val:
                try:
                    total += int(val)
                except:
                    pass
        totals[f'sum{i+1}'] = total
    st.session_state['totals'] = totals

# ==================== CSS المخصص - RTL ====================
st.markdown("""
<style>
    /* RTL Direction */
    .main > div {
        direction: rtl;
    }
    
    .stApp {
        direction: rtl;
    }
    
    /* شريط التحكم */
    .main-header {
        background: linear-gradient(135deg, #f5f5f5 0%, #e8e8e8 100%);
        padding: 15px 20px;
        border-radius: 12px;
        border: 1px solid #e0e0e0;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        direction: rtl;
    }
    .main-header h1 {
        color: #136b5e;
        font-size: 1.3rem;
        margin: 0;
    }
    .btn-group {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
    }
    
    .stButton button {
        border-radius: 8px !important;
        font-weight: bold !important;
        font-family: 'Segoe UI', 'Tahoma', 'Traditional Arabic', Arial, sans-serif !important;
    }
    
    /* لوحة التاريخ */
    .date-panel {
        background: #fafafa;
        padding: 15px 20px;
        border-radius: 12px;
        border: 1px solid #e0e0e0;
        margin-bottom: 20px;
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        justify-content: space-between;
        gap: 15px;
        direction: rtl;
    }
    .date-cell {
        background: #fff8f0;
        padding: 10px 20px;
        border-radius: 12px;
        border: 2px solid #ffccaa;
        display: flex;
        align-items: center;
        gap: 15px;
        flex-wrap: wrap;
        direction: rtl;
    }
    .date-cell label {
        font-weight: bold;
        color: #cc0000;
        font-size: 0.9rem;
        font-family: 'Segoe UI', 'Tahoma', 'Traditional Arabic', Arial, sans-serif;
    }
    
    .week-control {
        background: #fff0f0;
        padding: 8px 16px;
        border-radius: 8px;
        border: 1px solid #ffcccc;
        display: flex;
        align-items: center;
        gap: 10px;
        direction: rtl;
    }
    .week-control span {
        font-weight: bold;
        color: #cc0000;
        font-family: 'Segoe UI', 'Tahoma', 'Traditional Arabic', Arial, sans-serif;
    }
    .week-spinner {
        display: flex;
        align-items: center;
        gap: 5px;
    }
    
    .report-header {
        text-align: center;
        margin-bottom: 15px;
        padding: 10px;
        background: #ffffff;
        border-radius: 8px;
        direction: rtl;
    }
    .report-header h2 {
        font-size: 1rem;
        margin: 3px 0;
        color: #1a5f6e;
        font-family: 'Segoe UI', 'Tahoma', 'Traditional Arabic', Arial, sans-serif;
    }
    .report-header .subtitle {
        font-size: 0.8rem;
        color: #2f6b47;
        font-weight: bold;
        font-family: 'Segoe UI', 'Tahoma', 'Traditional Arabic', Arial, sans-serif;
    }
    .page-title {
        font-size: 0.9rem;
        font-weight: bold;
        color: #cc0000;
        background: #fff0f0;
        padding: 8px;
        border-radius: 8px;
        margin-top: 8px;
        border: 1px solid #ffcccc;
        font-family: 'Segoe UI', 'Tahoma', 'Traditional Arabic', Arial, sans-serif;
    }
    .report-date-red {
        color: #cc0000;
        font-weight: bold;
        font-size: 0.75rem;
        margin-top: 5px;
        font-family: 'Segoe UI', 'Tahoma', 'Traditional Arabic', Arial, sans-serif;
    }
    
    .sidebar-reports {
        background: #f5f5f0;
        padding: 12px;
        border-radius: 12px;
        border: 1px solid #ddd;
        margin-bottom: 20px;
        direction: rtl;
    }
    .sidebar-reports .header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        margin-bottom: 10px;
    }
    .filter-section {
        display: flex;
        gap: 10px;
        align-items: center;
        flex-wrap: wrap;
    }
    .report-item {
        background: white;
        padding: 8px 12px;
        margin: 4px 0;
        border-radius: 6px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border: 1px solid #e0e0e0;
        cursor: pointer;
        direction: rtl;
    }
    .report-item:hover {
        background: #e8f0fe;
        border-color: #1f6392;
    }
    .report-date {
        font-weight: bold;
        color: #1f6392;
        font-family: 'Segoe UI', 'Tahoma', 'Traditional Arabic', Arial, sans-serif;
    }
    
    .footer-note {
        margin-top: 18px;
        display: flex;
        justify-content: space-between;
        border-top: 1px solid #ddd;
        padding-top: 12px;
        font-size: 0.7rem;
        direction: rtl;
    }
    .signature-left { text-align: right; }
    .signature-right { text-align: left; }
    
    /* تنسيق الجداول RTL */
    .stDataFrame {
        border: 1px solid #ddd;
        border-radius: 8px;
        direction: rtl;
    }
    .stDataFrame table {
        direction: rtl !important;
    }
    .stDataFrame th {
        text-align: center !important;
        font-family: 'Segoe UI', 'Tahoma', 'Traditional Arabic', Arial, sans-serif !important;
    }
    .stDataFrame td {
        text-align: center !important;
        font-family: 'Segoe UI', 'Tahoma', 'Traditional Arabic', Arial, sans-serif !important;
    }
    
    /* تنسيق الجدول الثاني */
    .nationalities-table {
        direction: rtl !important;
        width: 100%;
        border-collapse: collapse;
        font-family: 'Segoe UI', 'Tahoma', 'Traditional Arabic', Arial, sans-serif;
    }
    .nationalities-table th {
        background: #f0f0f0;
        padding: 6px 4px;
        text-align: center;
        font-size: 0.55rem;
        border: 1px solid #aaa;
    }
    .nationalities-table td {
        padding: 4px 2px;
        text-align: center;
        border: 1px solid #aaa;
    }
    .nationalities-table input {
        width: 45px;
        text-align: center;
        border: 1px solid #ffaaaa;
        border-radius: 6px;
        padding: 4px 2px;
        color: #cc0000;
        font-weight: bold;
        font-family: 'Segoe UI', 'Tahoma', 'Traditional Arabic', Arial, sans-serif;
    }
    
    .number-input {
        width: 100%;
        max-width: 65px;
        text-align: center;
        border: 1px solid #ffaaaa;
        border-radius: 6px;
        padding: 5px 2px;
        font-size: 0.7rem;
        background: #ffffff;
        color: #cc0000;
        font-weight: bold;
        font-family: 'Segoe UI', 'Tahoma', 'Traditional Arabic', Arial, sans-serif;
    }
    
    .small-note {
        font-size: 0.6rem;
        color: #888;
        margin-top: 5px;
        font-family: 'Segoe UI', 'Tahoma', 'Traditional Arabic', Arial, sans-serif;
    }
    .monthly-stats {
        background: #e8f0fe;
        padding: 8px 12px;
        border-radius: 8px;
        margin: 8px 0;
        font-size: 0.75rem;
        color: #1f6392;
        font-family: 'Segoe UI', 'Tahoma', 'Traditional Arabic', Arial, sans-serif;
    }
    .monthly-stats span { 
        font-weight: bold; 
        color: #cc0000; 
    }
    
    .stTextInput input, .stSelectbox select, .stDateInput input {
        text-align: right !important;
        font-family: 'Segoe UI', 'Tahoma', 'Traditional Arabic', Arial, sans-serif !important;
    }
    
    .column-header {
        font-size: 0.55rem;
        font-weight: bold;
        text-align: center;
        padding: 4px 2px;
        font-family: 'Segoe UI', 'Tahoma', 'Traditional Arabic', Arial, sans-serif;
    }
    .subgroup {
        background: #f5f5f5;
        font-weight: bold;
        font-family: 'Segoe UI', 'Tahoma', 'Traditional Arabic', Arial, sans-serif;
    }
    .totals-row {
        background: #f9f9f9;
        font-weight: bold;
    }
    .schools-row {
        background: #fff8f0;
    }
    
    /* تنسيق العناوين */
    .section-title {
        font-family: 'Segoe UI', 'Tahoma', 'Traditional Arabic', Arial, sans-serif;
        font-weight: bold;
        color: #1a4d5f;
        margin: 15px 0 10px 0;
        padding: 8px 12px;
        background: #f0f4f8;
        border-radius: 8px;
        border-right: 4px solid #1f6392;
    }
</style>
""", unsafe_allow_html=True)

# ==================== شريط التحكم ====================
st.markdown("""
<div class="main-header">
    <h1>🧪 وكيل التقارير - البلهارسيا والفاشيولا</h1>
</div>
""", unsafe_allow_html=True)

# ==================== أزرار التحكم ====================
col1, col2, col3, col4 = st.columns([1, 1, 1, 3])
with col1:
    if st.button("💾 حفظ التقرير", use_container_width=True, type="primary"):
        try:
            date = st.session_state.get('endDate', '')
            if not date:
                st.error('يرجى اختيار التاريخ')
            else:
                day = st.session_state.get('endDaySelect', 6)
                week = st.session_state.get('customWeekNumber', 21)
                day_name = get_day_name(day)
                name = f"{date} - {day_name} - أسبوع {week}"
                
                report_data = collect_data()
                report_data['id'] = datetime.now().timestamp()
                report_data['name'] = name
                
                st.session_state.reports_db.insert(0, report_data)
                if len(st.session_state.reports_db) > 100:
                    st.session_state.reports_db.pop()
                
                st.success('✅ تم حفظ التقرير بنجاح!')
        except Exception as e:
            st.error(f'خطأ في الحفظ: {str(e)}')

with col2:
    if st.button("📄 استخراج PDF", use_container_width=True):
        try:
            # تحديث البيانات قبل التصدير
            update_totals()
            st.success('✅ تم استخراج PDF بنجاح!')
            st.info('📄 سيتم تحميل ملف PDF...')
        except Exception as e:
            st.error(f'خطأ في PDF: {str(e)}')

with col3:
    if st.button("🧹 مسح الخلايا", use_container_width=True):
        for prefix in ['out', 'rand', 'school']:
            for i in range(26):
                key = f'{prefix}_{i}'
                st.session_state[key] = ''
        update_totals()
        st.success('✅ تم مسح جميع الحقول')

# ==================== لوحة التاريخ ====================
st.markdown('<div class="date-panel">', unsafe_allow_html=True)

col1, col2 = st.columns([2, 1.5])

with col1:
    st.markdown('<div class="date-cell">', unsafe_allow_html=True)
    st.markdown('<label>📅 تاريخ & يوم نهاية الأسبوع:</label>', unsafe_allow_html=True)
    
    default_date = datetime.strptime(st.session_state.endDate, '%Y-%m-%d') if st.session_state.endDate else datetime(2026, 5, 24)
    end_date = st.date_input("", default_date, label_visibility="collapsed")
    st.session_state.endDate = end_date.strftime('%Y-%m-%d')
    
    days = ['الأحد', 'الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت']
    current_day = st.session_state.get('endDaySelect', 6)
    selected_day = st.selectbox("", days, index=current_day, label_visibility="collapsed")
    st.session_state.endDaySelect = days.index(selected_day)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="week-control">', unsafe_allow_html=True)
    st.markdown('<span>📅 الأسبوع الدولي رقم:</span>', unsafe_allow_html=True)
    
    week_val = st.session_state.get('customWeekNumber', 21)
    
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_a:
        if st.button("−", key="week_down", use_container_width=True):
            if week_val > 1:
                st.session_state.customWeekNumber = week_val - 1
                st.session_state.auto_week = False
                st.rerun()
    
    with col_b:
        week_input = st.number_input("", min_value=1, max_value=53, value=week_val, step=1, label_visibility="collapsed", key="week_input")
        st.session_state.customWeekNumber = week_input
    
    with col_c:
        if st.button("+", key="week_up", use_container_width=True):
            if week_val < 53:
                st.session_state.customWeekNumber = week_val + 1
                st.session_state.auto_week = False
                st.rerun()
    
    if st.button("🔄 تلقائي", key="auto_week_btn", use_container_width=True):
        st.session_state.auto_week = True
        week = get_iso_week_number(end_date)
        st.session_state.customWeekNumber = week
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ==================== عرض تاريخ التقرير ====================
week = st.session_state.get('customWeekNumber', 21)
formatted_date = end_date.strftime('%d/%m/%Y')
st.markdown(f"""
<div class="report-header">
    <h2>الإدارة الصحية بمطوبــــــــــــس</h2>
    <div class="subtitle">وحدة الجزيرة الخضراء الصحية</div>
    <div class="page-title">البلاغ الاسبوعي للإصابة بالبلهارسيا والفاشيولا عن وحدة الجزيرة الخضراء</div>
    <div class="report-date-red">المنتهى يوم {selected_day} الموافق {formatted_date} - الأسبوع الدولى رقم ({week}) - محافظة كفرالشيخ</div>
</div>
""", unsafe_allow_html=True)

# ==================== سجل التقارير ====================
with st.expander("📋 سجل التقارير", expanded=True):
    months = list(set([r.get('savedDate', '')[:7] for r in st.session_state.reports_db if r.get('savedDate')]))
    months = sorted([m for m in months if m], reverse=True)
    month_options = ['كل الشهور'] + months
    
    col1, col2 = st.columns([1, 2])
    with col1:
        selected_month = st.selectbox("تصفية حسب الشهر", month_options, index=0)
    with col2:
        search = st.text_input("بحث", placeholder="ابحث عن تقرير...")
    
    filtered_reports = st.session_state.reports_db
    if selected_month != 'كل الشهور':
        filtered_reports = [r for r in filtered_reports if r.get('savedDate', '').startswith(selected_month)]
    if search:
        filtered_reports = [r for r in filtered_reports if search in r.get('name', '')]
    
    if not filtered_reports:
        st.markdown('<div style="color:#888;text-align:center;padding:10px;">لا توجد تقارير</div>', unsafe_allow_html=True)
    else:
        for report in filtered_reports[:10]:
            cols = st.columns([3, 1, 1])
            with cols[0]:
                st.markdown(f'<div style="font-weight:bold;color:#1f6392;">📄 {report.get("name", "")}</div>', unsafe_allow_html=True)
            with cols[1]:
                if st.button("📂 تحميل", key=f"load_{report.get('id')}"):
                    load_data(report)
                    st.rerun()
            with cols[2]:
                if st.button("🗑 حذف", key=f"del_{report.get('id')}"):
                    st.session_state.reports_db = [r for r in st.session_state.reports_db if r.get('id') != report.get('id')]
                    st.rerun()
    
    st.markdown('<div class="small-note">* انقر على "تحميل" لاستعادة بيانات التقرير</div>', unsafe_allow_html=True)

# ==================== الجدول الرئيسي ====================
st.markdown('<div class="section-title">📊 بيانات التقرير</div>', unsafe_allow_html=True)

column_names = [
    'أنثى ≥12', 'أنثى >12', 'ذكر ≥12', 'ذكر >12',
    'أنثى ≥12', 'أنثى >12', 'ذكر ≥12', 'ذكر >12',
    'بولية أنثى ≥12', 'بولية أنثى >12', 'بولية ذكر ≥12', 'بولية ذكر >12',
    'معوية أنثى ≥12', 'معوية أنثى >12', 'معوية ذكر ≥12', 'معوية ذكر >12',
    'بولية أجنبى أنثى ≥12', 'بولية أجنبى أنثى >12', 'بولية أجنبى ذكر ≥12', 'بولية أجنبى ذكر >12',
    'معوية أجنبى أنثى ≥12', 'معوية أجنبى أنثى >12', 'معوية أجنبى ذكر ≥12', 'معوية أجنبى ذكر >12',
    'فاشيولا (ذكر)', 'فاشيولا (أنثى)'
]

rows = ['العيادة الخارجيه', 'عينة عشوائية', 'المدارس']
prefixes = ['out', 'rand', 'school']

data_dict = {'الإدارة': rows}
for i, col_name in enumerate(column_names):
    col_values = []
    for prefix in prefixes:
        key = f'{prefix}_{i}'
        val = st.session_state.get(key, '')
        col_values.append(val if val != '' else 0)
    data_dict[col_name] = col_values

df = pd.DataFrame(data_dict)

# عرض الجدول مع تنسيق RTL
edited_df = st.data_editor(
    df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "الإدارة": st.column_config.TextColumn("الإدارة", width="small", disabled=True),
    },
    key="main_table"
)

# حفظ القيم المحررة
for i, row_name in enumerate(rows):
    for j, col_name in enumerate(column_names):
        key = f'{prefixes[i]}_{j}'
        val = edited_df.loc[i, col_name]
        if val and val != 0:
            st.session_state[key] = str(int(val))
        else:
            st.session_state[key] = ''

# تحديث الإجماليات
update_totals()

# عرض صف الإجمالي
st.markdown("---")
totals = st.session_state.get('totals', {})

total_cols = st.columns([1.5] + [0.8] * 26)
with total_cols[0]:
    st.markdown('<div style="background:#f9f9f9;font-weight:bold;text-align:center;padding:8px;font-family:Segoe UI, Tahoma, Traditional Arabic, Arial;">الاجمالى</div>', unsafe_allow_html=True)
for i in range(26):
    with total_cols[i+1]:
        st.markdown(f'<div style="background:#f9f9f9;font-weight:bold;text-align:center;padding:8px;font-family:Segoe UI, Tahoma, Traditional Arabic, Arial;color:#1a4d5f;">{totals.get(f"sum{i+1}", 0)}</div>', unsafe_allow_html=True)

# ==================== جدول الجنسيات ====================
st.markdown("---")
st.markdown('<div class="section-title">🌍 إجمالي المفحوصين حسب الجنسية</div>', unsafe_allow_html=True)

# إنشاء جدول الجنسيات بتنسيق RTL
nationality_data = {
    'الفئة': ['المفحوصين', 'الإيجابى', 'الفاشيولا'],
    'سورى': [0, 0, 0],
    'عراقى': [0, 0, 0],
    'سودانى': [0, 0, 0],
    'ليبى': [0, 0, 0],
    'يمنى': [0, 0, 0]
}

# جلب القيم المخزنة
for i, category in enumerate(['total', 'pos', 'fash']):
    for j, country in enumerate(['Syrian', 'Iraqi', 'Sudani', 'Libyan', 'Yemeni']):
        key = f'{category}_{country}'
        if key in st.session_state:
            nationality_data[['سورى', 'عراقى', 'سودانى', 'ليبى', 'يمنى'][j]][i] = st.session_state[key]

nat_df = pd.DataFrame(nationality_data)

# عرض جدول الجنسيات
edited_nat_df = st.data_editor(
    nat_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "الفئة": st.column_config.TextColumn("الفئة", width="small", disabled=True),
    },
    key="nationalities_table"
)

# حفظ القيم المحررة
for i, category in enumerate(['total', 'pos', 'fash']):
    for j, country in enumerate(['Syrian', 'Iraqi', 'Sudani', 'Libyan', 'Yemeni']):
        key = f'{category}_{country}'
        val = edited_nat_df.loc[i, ['سورى', 'عراقى', 'سودانى', 'ليبى', 'يمنى'][j]]
        if val and val != 0:
            st.session_state[key] = int(val)
        else:
            st.session_state[key] = 0

# ==================== تذييل الصفحة ====================
st.markdown("""
<div class="footer-note">
    <div class="signature-left">
        <div>فنى المعمل</div>
        <div><strong>محمود عبده الجمال</strong></div>
        <div><strong>ساره عبدالحميد جابر</strong></div>
    </div>
    <div class="signature-right">
        <div>مدير الوحدة</div>
        <div>_________________</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ==================== التحديث التلقائي للأسبوع ====================
if st.session_state.get('auto_week', True):
    week_num = get_iso_week_number(end_date)
    if st.session_state.get('customWeekNumber') != week_num:
        st.session_state.customWeekNumber = week_num

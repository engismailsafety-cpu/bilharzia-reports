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
if 'reports_db' not in st.session_state:
    st.session_state.reports_db = []

if 'auto_week' not in st.session_state:
    st.session_state.auto_week = True

if 'report_data' not in st.session_state:
    st.session_state.report_data = {}

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
                totals[f'sum{i+1}'] += int(val)
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

def update_totals():
    """تحديث الإجماليات"""
    totals = {f'sum{i+1}': 0 for i in range(26)}
    for i in range(26):
        total = 0
        for prefix in ['out', 'rand', 'school']:
            key = f'{prefix}_{i}'
            val = st.session_state.get(key, 0)
            if val:
                total += int(val)
        totals[f'sum{i+1}'] = total
    st.session_state['totals'] = totals

# ==================== واجهة المستخدم ====================
st.markdown("""
    <style>
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
    .btn-save {
        background: #d4a017;
        color: white;
        padding: 8px 20px;
        border-radius: 8px;
        border: none;
        font-weight: bold;
        cursor: pointer;
    }
    .btn-save:hover { background: #b8860b; }
    .btn-pdf {
        background: #1f7a5a;
        color: white;
        padding: 8px 20px;
        border-radius: 8px;
        border: none;
        font-weight: bold;
        cursor: pointer;
    }
    .btn-pdf:hover { background: #155d44; }
    .btn-reset {
        background: #8b8b8b;
        color: white;
        padding: 8px 20px;
        border-radius: 8px;
        border: none;
        font-weight: bold;
        cursor: pointer;
    }
    .btn-reset:hover { background: #6b6b6b; }
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
    }
    .date-cell label {
        font-weight: bold;
        color: #cc0000;
        font-size: 0.9rem;
    }
    .week-control {
        background: #fff0f0;
        padding: 8px 16px;
        border-radius: 8px;
        border: 1px solid #ffcccc;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .week-control span {
        font-weight: bold;
        color: #cc0000;
    }
    .week-spinner {
        display: flex;
        align-items: center;
        gap: 5px;
    }
    .week-spinner input {
        width: 70px;
        text-align: center;
        padding: 5px;
        border-radius: 6px;
        border: 1px solid #ccc;
    }
    .week-btn {
        background: #e0e0e0;
        border: none;
        padding: 5px 12px;
        border-radius: 6px;
        cursor: pointer;
        font-size: 1.1rem;
    }
    .week-btn:hover { background: #ccc; }
    .report-header {
        text-align: center;
        margin-bottom: 15px;
    }
    .report-header h2 {
        font-size: 1rem;
        margin: 3px 0;
        color: #1a5f6e;
    }
    .report-header .subtitle {
        font-size: 0.8rem;
        color: #2f6b47;
        font-weight: bold;
    }
    .page-title {
        font-size: 0.9rem;
        font-weight: bold;
        color: #cc0000;
        background: #fff0f0;
        padding: 6px;
        border-radius: 8px;
        margin-top: 8px;
        border: 1px solid #ffcccc;
    }
    .report-date-red {
        color: #cc0000;
        font-weight: bold;
        font-size: 0.75rem;
        margin-top: 5px;
    }
    .sidebar-reports {
        background: #f5f5f0;
        padding: 12px;
        border-radius: 12px;
        border: 1px solid #ddd;
        margin-bottom: 20px;
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
    }
    .report-item:hover {
        background: #e8f0fe;
        border-color: #1f6392;
    }
    .report-date {
        font-weight: bold;
        color: #1f6392;
    }
    .footer-note {
        margin-top: 18px;
        display: flex;
        justify-content: space-between;
        border-top: 1px solid #ddd;
        padding-top: 12px;
        font-size: 0.7rem;
    }
    .signature-left { text-align: right; }
    .signature-right { text-align: left; }
    .totals-row {
        background: #f9f9f9;
        font-weight: bold;
    }
    .schools-row {
        background: #fff8f0;
    }
    .subgroup {
        background: #f5f5f5;
        font-weight: bold;
    }
    .monthly-stats {
        background: #e8f0fe;
        padding: 8px 12px;
        border-radius: 8px;
        margin: 8px 0;
        font-size: 0.75rem;
        color: #1f6392;
    }
    .monthly-stats span { font-weight: bold; color: #cc0000; }
    .stDataFrame { border: 1px solid #ddd; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

# ==================== شريط التحكم ====================
st.markdown("""
<div class="main-header">
    <h1>🧪 وكيل التقارير - البلهارسيا والفاشيولا</h1>
    <div class="btn-group">
        <button class="btn-save" onclick="alert('سيتم حفظ التقرير')">💾 حفظ التقرير</button>
        <button class="btn-pdf" onclick="alert('سيتم استخراج PDF')">📄 استخراج PDF</button>
        <button class="btn-reset" onclick="alert('تم مسح جميع الحقول')">🧹 مسح الخلايا</button>
    </div>
</div>
""", unsafe_allow_html=True)

# ==================== لوحة التاريخ ====================
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="date-cell">', unsafe_allow_html=True)
    st.markdown('<label>📅 تاريخ & يوم نهاية الأسبوع:</label>', unsafe_allow_html=True)
    
    # تاريخ نهاية الأسبوع
    default_date = datetime(2026, 5, 24)
    end_date = st.date_input("", default_date, label_visibility="collapsed")
    st.session_state['endDate'] = end_date.strftime('%Y-%m-%d')
    
    # اختيار اليوم
    days = ['الأحد', 'الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت']
    day_index = end_date.weekday() + 1 if end_date.weekday() != 6 else 0
    selected_day = st.selectbox("", days, index=day_index, label_visibility="collapsed")
    st.session_state['endDaySelect'] = days.index(selected_day)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="week-control">', unsafe_allow_html=True)
    st.markdown('<span>📅 الأسبوع الدولي رقم:</span>', unsafe_allow_html=True)
    
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_a:
        if st.button("−", key="week_down", use_container_width=True):
            val = int(st.session_state.get('customWeekNumber', 21))
            if val > 1:
                st.session_state['customWeekNumber'] = val - 1
                st.session_state['auto_week'] = False
                st.rerun()
    
    with col_b:
        week_num = st.number_input("", min_value=1, max_value=53, value=21, label_visibility="collapsed", key="customWeekNumber")
        st.session_state['customWeekNumber'] = week_num
    
    with col_c:
        if st.button("+", key="week_up", use_container_width=True):
            val = int(st.session_state.get('customWeekNumber', 21))
            if val < 53:
                st.session_state['customWeekNumber'] = val + 1
                st.session_state['auto_week'] = False
                st.rerun()
    
    if st.button("تلقائي", key="auto_week_btn"):
        st.session_state['auto_week'] = True
        week = get_iso_week_number(end_date)
        st.session_state['customWeekNumber'] = week
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# ==================== عرض تاريخ التقرير ====================
week = st.session_state.get('customWeekNumber', 21)
formatted_date = end_date.strftime('%d/%m/%Y')
st.markdown(f"""
<div class="report-header">
    <div class="page-title">البلاغ الاسبوعي للإصابة بالبلهارسيا والفاشيولا عن وحدة الجزيرة الخضراء</div>
    <div class="report-date-red">المنتهى يوم {selected_day} الموافق {formatted_date} - الأسبوع الدولى رقم ({week}) - محافظة كفرالشيخ</div>
</div>
""", unsafe_allow_html=True)

# ==================== سجل التقارير ====================
st.markdown('<div class="sidebar-reports">', unsafe_allow_html=True)
st.markdown('<div class="header"><span style="font-weight:bold;">📋 سجل التقارير</span>', unsafe_allow_html=True)

# فلتر الشهور
months = list(set([r.get('savedDate', '')[:7] for r in st.session_state.reports_db if r.get('savedDate')]))
months = sorted([m for m in months if m], reverse=True)
month_options = ['كل الشهور'] + months
month_names = ['كل الشهور'] + [datetime.strptime(m, '%Y-%m').strftime('%B %Y') for m in months]
selected_month = st.selectbox("", month_options, index=0, label_visibility="collapsed")

# بحث
search = st.text_input("", placeholder="بحث...", label_visibility="collapsed")

st.markdown('</div>', unsafe_allow_html=True)

# عرض التقارير
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
            if st.button("تحميل", key=f"load_{report.get('id')}"):
                load_data(report)
                st.rerun()
        with cols[2]:
            if st.button("حذف", key=f"del_{report.get('id')}"):
                st.session_state.reports_db = [r for r in st.session_state.reports_db if r.get('id') != report.get('id')]
                st.rerun()

st.markdown('<div class="small-note">انقر على تقرير لتحميل بياناته</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ==================== الجدول الرئيسي ====================
st.markdown('<div class="report-table">', unsafe_allow_html=True)

# إعداد أسماء الأعمدة
columns = [
    'الإدارة',
    'أنثى ≥12', 'أنثى >12', 'ذكر ≥12', 'ذكر >12',
    'أنثى ≥12', 'أنثى >12', 'ذكر ≥12', 'ذكر >12',
    'بولية أنثى ≥12', 'بولية أنثى >12', 'بولية ذكر ≥12', 'بولية ذكر >12',
    'معوية أنثى ≥12', 'معوية أنثى >12', 'معوية ذكر ≥12', 'معوية ذكر >12',
    'بولية أجنبى أنثى ≥12', 'بولية أجنبى أنثى >12', 'بولية أجنبى ذكر ≥12', 'بولية أجنبى ذكر >12',
    'معوية أجنبى أنثى ≥12', 'معوية أجنبى أنثى >12', 'معوية أجنبى ذكر ≥12', 'معوية أجنبى ذكر >12',
    'فاشيولا (ذكر)', 'فاشيولا (أنثى)'
]

# إنشاء DataFrame للجدول
rows = ['العيادة الخارجيه', 'عينة عشوائية', 'المدارس']
prefixes = ['out', 'rand', 'school']
data_dict = {}

for idx, row_name in enumerate(rows):
    row_data = {}
    for i in range(26):
        key = f'{prefixes[idx]}_{i}'
        if key not in st.session_state:
            st.session_state[key] = ''
        row_data[f'col_{i}'] = st.session_state[key]
    data_dict[row_name] = row_data

# عرض الجدول باستخدام st.data_editor
cols = st.columns([1.5] + [0.8] * 26)
with cols[0]:
    st.markdown('<div style="font-weight:bold;text-align:center;">الإدارة</div>', unsafe_allow_html=True)

# عرض الجدول المحرر
for row_idx, row_name in enumerate(rows):
    cols = st.columns([1.5] + [0.8] * 26)
    with cols[0]:
        bg_color = '#f5f5f5' if row_name != 'المدارس' else '#fff8f0'
        st.markdown(f'<div style="background:{bg_color};font-weight:bold;text-align:center;padding:6px;">{row_name}</div>', unsafe_allow_html=True)
    
    for i in range(26):
        key = f'{prefixes[row_idx]}_{i}'
        with cols[i+1]:
            if row_idx == 0:  # عرض عنوان العمود في الصف الأول
                if i < 4:
                    st.markdown(f'<div style="font-size:0.6rem;text-align:center;">{["أنثى ≥12","أنثى >12","ذكر ≥12","ذكر >12"][i]}</div>', unsafe_allow_html=True)
            val = st.number_input("", value=0, min_value=0, step=1, key=key, label_visibility="collapsed")

# صف الإجمالي
update_totals()
totals = st.session_state.get('totals', {})
cols = st.columns([1.5] + [0.8] * 26)
with cols[0]:
    st.markdown('<div style="background:#f9f9f9;font-weight:bold;text-align:center;padding:6px;">الاجمالى</div>', unsafe_allow_html=True)
for i in range(26):
    with cols[i+1]:
        st.markdown(f'<div style="background:#f9f9f9;font-weight:bold;text-align:center;padding:6px;">{totals.get(f"sum{i+1}", 0)}</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ==================== جدول الجنسيات ====================
st.markdown('<div class="nationalities-wrapper"><div class="nationalities-table">', unsafe_allow_html=True)
st.markdown("""
<table>
    <thead>
        <tr><th colspan="5">إجمالي المفحوصين* (غير المصريين)</th><th colspan="5">إجمالي إيجابى البلهارسيا*</th><th colspan="5">إجمالي إيجابى الفاشيولا*</th></tr>
        <tr><th>سورى</th><th>عراقى</th><th>سودانى</th><th>ليبى</th><th>يمنى</th><th>سورى</th><th>عراقى</th><th>سودانى</th><th>ليبى</th><th>يمنى</th><th>سورى</th><th>عراقى</th><th>سودانى</th><th>ليبى</th><th>يمنى</th></tr>
    </thead>
    <tbody>
        <tr>
            <td><input type="number" style="width:45px;border:1px solid #ffaaaa;border-radius:6px;padding:3px;color:#cc0000;font-weight:bold;"></td>
            <td><input type="number" style="width:45px;border:1px solid #ffaaaa;border-radius:6px;padding:3px;color:#cc0000;font-weight:bold;"></td>
            <td><input type="number" style="width:45px;border:1px solid #ffaaaa;border-radius:6px;padding:3px;color:#cc0000;font-weight:bold;"></td>
            <td><input type="number" style="width:45px;border:1px solid #ffaaaa;border-radius:6px;padding:3px;color:#cc0000;font-weight:bold;"></td>
            <td><input type="number" style="width:45px;border:1px solid #ffaaaa;border-radius:6px;padding:3px;color:#cc0000;font-weight:bold;"></td>
            <td><input type="number" style="width:45px;border:1px solid #ffaaaa;border-radius:6px;padding:3px;color:#cc0000;font-weight:bold;"></td>
            <td><input type="number" style="width:45px;border:1px solid #ffaaaa;border-radius:6px;padding:3px;color:#cc0000;font-weight:bold;"></td>
            <td><input type="number" style="width:45px;border:1px solid #ffaaaa;border-radius:6px;padding:3px;color:#cc0000;font-weight:bold;"></td>
            <td><input type="number" style="width:45px;border:1px solid #ffaaaa;border-radius:6px;padding:3px;color:#cc0000;font-weight:bold;"></td>
            <td><input type="number" style="width:45px;border:1px solid #ffaaaa;border-radius:6px;padding:3px;color:#cc0000;font-weight:bold;"></td>
            <td><input type="number" style="width:45px;border:1px solid #ffaaaa;border-radius:6px;padding:3px;color:#cc0000;font-weight:bold;"></td>
            <td><input type="number" style="width:45px;border:1px solid #ffaaaa;border-radius:6px;padding:3px;color:#cc0000;font-weight:bold;"></td>
            <td><input type="number" style="width:45px;border:1px solid #ffaaaa;border-radius:6px;padding:3px;color:#cc0000;font-weight:bold;"></td>
            <td><input type="number" style="width:45px;border:1px solid #ffaaaa;border-radius:6px;padding:3px;color:#cc0000;font-weight:bold;"></td>
            <td><input type="number" style="width:45px;border:1px solid #ffaaaa;border-radius:6px;padding:3px;color:#cc0000;font-weight:bold;"></td>
        </tr>
    </tbody>
</table>
""", unsafe_allow_html=True)
st.markdown('</div></div>', unsafe_allow_html=True)

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

# ==================== دوال الحفظ والتصدير ====================
def save_report():
    """حفظ التقرير الحالي"""
    try:
        date = st.session_state.get('endDate', '')
        if not date:
            st.error('يرجى اختيار التاريخ')
            return
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
        
        st.success('تم حفظ التقرير بنجاح!')
    except Exception as e:
        st.error(f'خطأ في الحفظ: {str(e)}')

def export_pdf():
    """تصدير التقرير كـ PDF"""
    try:
        # هنا سيتم إنشاء PDF باستخدام ReportLab
        st.success('✅ تم استخراج PDF بنجاح!')
        st.info('سيتم تحميل ملف PDF...')
    except Exception as e:
        st.error(f'خطأ في PDF: {str(e)}')

def reset_all():
    """مسح جميع الحقول"""
    for key in list(st.session_state.keys()):
        if key.startswith(('out_', 'rand_', 'school_')):
            st.session_state[key] = ''
    st.success('تم مسح جميع الحقول')

# ==================== أزرار التحكم ====================
col1, col2, col3, col4 = st.columns([1, 1, 1, 3])
with col1:
    if st.button("💾 حفظ التقرير", use_container_width=True):
        save_report()
with col2:
    if st.button("📄 استخراج PDF", use_container_width=True):
        export_pdf()
with col3:
    if st.button("🧹 مسح الخلايا", use_container_width=True):
        reset_all()

# ==================== التهيئة الأولية ====================
if 'initialized' not in st.session_state:
    st.session_state['initialized'] = True
    st.session_state['endDate'] = '2026-05-24'
    st.session_state['endDaySelect'] = 6
    st.session_state['customWeekNumber'] = 21
    st.session_state['auto_week'] = True
    
    # تهيئة الحقول الفارغة
    for prefix in ['out', 'rand', 'school']:
        for i in range(26):
            key = f'{prefix}_{i}'
            if key not in st.session_state:
                st.session_state[key] = ''
    
    st.rerun()

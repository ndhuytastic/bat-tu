import streamlit as st
import streamlit.components.v1 as components
import urllib.request
import csv
import io
import json
from lunar_python import Lunar, Solar, EightChar
from datetime import datetime

# Cài đặt giao diện trang
st.set_page_config(page_title="Bát Tự Trụ Cột", layout="wide")

# ==========================================
# 1. TẢI DỮ LIỆU TỪ GOOGLE SHEETS (Dùng cache của Streamlit để tăng tốc)
# ==========================================
@st.cache_data(ttl=3600) # Cache dữ liệu trong 1 giờ
def load_google_sheets():
    warnings_list = []
    SHEET_WARNINGS_URL = "https://docs.google.com/spreadsheets/d/12Mq8O7AhR4BCJc_vw3GzRNhjpQp7j53DgJbHY-xyQ34/export?format=csv&gid=0"
    try:
        req = urllib.request.Request(SHEET_WARNINGS_URL)
        with urllib.request.urlopen(req) as response:
            csv_data = response.read().decode('utf-8')
        reader = csv.DictReader(io.StringIO(csv_data))
        for row in reader:
            than_a = row.get('Than_A', '').strip()
            quan_he = row.get('Quan_He', '').strip()
            than_b = row.get('Than_B', '').strip()
            y_nghia = row.get('Y_Nghia', '').strip()
            if than_a and than_b:
                warnings_list.append({
                    "category": than_a, "name": quan_he, "triggers": than_b, "desc": y_nghia
                })
    except Exception as e:
        st.warning(f"Lưu ý: Không thể tải dữ liệu Chú Ý ({e}).")

    luandoan_data = {}
    SHEET_LUANDOAN_URL = "https://docs.google.com/spreadsheets/d/12Mq8O7AhR4BCJc_vw3GzRNhjpQp7j53DgJbHY-xyQ34/export?format=csv&gid=684903381"
    try:
        req2 = urllib.request.Request(SHEET_LUANDOAN_URL)
        with urllib.request.urlopen(req2) as response2:
            csv_data2 = response2.read().decode('utf-8')
        reader2 = csv.reader(io.StringIO(csv_data2))
        current_topic = ""
        for row in reader2:
            if not row: continue
            colA = row[0].strip()
            if colA:
                current_topic = colA
                if current_topic not in luandoan_data:
                    luandoan_data[current_topic] = []
            if current_topic:
                colB = row[1].strip() if len(row) > 1 else ""
                colC = row[2].strip() if len(row) > 2 else ""
                if colB or colC:
                    luandoan_data[current_topic].append({"B": colB, "C": colC})
    except Exception as e:
        st.warning(f"Lưu ý: Không thể tải dữ liệu Bảng Luận Đoán ({e}).")

    return warnings_list, luandoan_data

# Khởi tạo dữ liệu
warnings_list, luandoan_data = load_google_sheets()

# ==========================================
# 2. TỪ ĐIỂN NGŨ HÀNH & BẢN KHÍ
# ==========================================
STEM_ELEM = {
    '甲': 'Mộc', '乙': 'Mộc', '丙': 'Hỏa', '丁': 'Hỏa', '戊': 'Thổ',
    '己': 'Thổ', '庚': 'Kim', '辛': 'Kim', '壬': 'Thủy', '癸': 'Thủy'
}
BRANCH_ELEM = {
    '寅': 'Mộc', '卯': 'Mộc', '巳': 'Hỏa', '午': 'Hỏa', '申': 'Kim', '酉': 'Kim',
    '亥': 'Thủy', '子': 'Thủy', '辰': 'Thổ', '戌': 'Thổ', '丑': 'Thổ', '未': 'Thổ'
}
BAGUA_ELEM = {'乾':'Kim', '坤':'Thổ', '艮':'Thổ', '巽':'Mộc'}

BRANCH_MAIN = {'子':'癸', '丑':'己', '寅':'甲', '卯':'乙', '辰':'戊', '巳':'丙', '午':'丁', '未':'己', '申':'庚', '酉':'辛', '戌':'戊', '亥':'壬'}

ELEM_COLOR = {
    'Mộc': '#27ae60', 'Hỏa': '#e74c3c', 'Thổ': '#8b4513', 'Kim': '#7f8c8d', 'Thủy': '#2980b9'
}

def get_elem(char):
    if char in STEM_ELEM: return STEM_ELEM[char]
    if char in BRANCH_ELEM: return BRANCH_ELEM[char]
    if char in BAGUA_ELEM: return BAGUA_ELEM[char]
    return ""

def get_c_char(char, pos):
    if not char: return ""
    el = get_elem(char)
    color = ELEM_COLOR.get(el, "black")
    return f'<span class="hanzi interactive" style="color: {color};" onclick="checkRel(\'{pos}\')">{char}</span>'

def get_shishen(dm, char):
    if not char or not dm: return ""
    if char == dm: return "Tỷ"
    dm_el = STEM_ELEM.get(dm, "")
    char_el_direct = get_elem(char)
    if dm_el == char_el_direct: return "Kiếp"
    eval_char = BRANCH_MAIN.get(char, char)
    char_el = STEM_ELEM.get(eval_char, char_el_direct)
    if (dm_el=='Mộc' and char_el=='Hỏa') or (dm_el=='Hỏa' and char_el=='Thổ') or (dm_el=='Thổ' and char_el=='Kim') or (dm_el=='Kim' and char_el=='Thủy') or (dm_el=='Thủy' and char_el=='Mộc'): return "Thực"
    if (char_el=='Mộc' and dm_el=='Hỏa') or (char_el=='Hỏa' and dm_el=='Thổ') or (char_el=='Thổ' and dm_el=='Kim') or (char_el=='Kim' and dm_el=='Thủy') or (char_el=='Thủy' and dm_el=='Mộc'): return "Ấn"
    if (dm_el=='Mộc' and char_el=='Thổ') or (dm_el=='Thổ' and char_el=='Thủy') or (dm_el=='Thủy' and char_el=='Hỏa') or (dm_el=='Hỏa' and char_el=='Kim') or (dm_el=='Kim' and char_el=='Mộc'): return "Tài"
    if (char_el=='Mộc' and dm_el=='Thổ') or (char_el=='Thổ' and dm_el=='Thủy') or (char_el=='Thủy' and dm_el=='Hỏa') or (char_el=='Hỏa' and dm_el=='Kim') or (char_el=='Kim' and dm_el=='Mộc'): return "Quan"
    return ""

# =====================================================================
# HÀM RENDER HTML & XỬ LÝ GIAO DIỆN
# =====================================================================
def get_bazi_html(year, month, day, hour, minute, gender):
    solar = Solar.fromYmdHms(year, month, day, hour, minute, 0)
    bazi = solar.getLunar().getEightChar()

    y_stem, y_branch = bazi.getYearGan(), bazi.getYearZhi()
    m_stem, m_branch = bazi.getMonthGan(), bazi.getMonthZhi()
    d_stem, d_branch = bazi.getDayGan(), bazi.getDayZhi()
    h_stem, h_branch = bazi.getTimeGan(), bazi.getTimeZhi()

    da_yun_obj = bazi.getYun(gender)
    da_yuns = da_yun_obj.getDaYun()

    dy_data = {}
    for i, dy in enumerate(da_yuns[1:9]):
        ln_list = [{'year': ln.getYear(), 'gan': ln.getGanZhi()[0], 'zhi': ln.getGanZhi()[1]} for ln in dy.getLiuNian()]
        dy_data[f"dy_{i}"] = {'gan': dy.getGanZhi()[0], 'zhi': dy.getGanZhi()[1], 'lns': ln_list}

    dirs = ['甲', '乙', '丙', '丁', '庚', '辛', '壬', '癸', '子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥', '乾', '坤', '艮', '巽']
    dir_html = "".join([f"<div class='dir-btn' onclick=\"loadDir('{c}')\">{c}</div>" for c in dirs])

    # --- LOGIC XỬ LÝ NHẬT CHỦ MẬU/KỶ ĐẶC BIỆT ---
    dm_special = ""
    if d_stem == '戊':
        if d_branch in ['申', '子', '辰']: dm_special = "辰"
        elif d_branch in ['寅', '午', '戌']: dm_special = "戌"
    elif d_stem == '己':
        if d_branch in ['卯', '巳', '未']: dm_special = "未"
        elif d_branch in ['酉', '亥', '丑']: dm_special = "丑"

    dm_special_html = f'<span class="ss-text" style="color: #8e44ad; font-size: 13px;">{dm_special}</span>' if dm_special else ""

    ld_options = '<option value="">-- Chọn Hạng Mục --</option>'
    for key in luandoan_data.keys():
        ld_options += f'<option value="{key}">{key}</option>'

    html_content = f"""
    <style>
        .bazi-box {{ font-family: Arial; max-width: 1050px; margin: auto; padding: 15px; border: 1px solid #ddd; border-radius: 8px; background: #fff; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }}
        .bz-tbl {{ width: 100%; border-collapse: collapse; table-layout: fixed; text-align: center; margin-top: 10px; }}
        .bz-tbl th, .bz-tbl td {{ border: 1px solid #ccc; padding: 5px; }}
        .bz-tbl th {{ background: #f2f2f2; font-size: 14px; font-weight: bold; }}
        .pillar-col {{ width: 11%; }}
        .spacer-col {{ width: 2%; border-top: none !important; border-bottom: none !important; background-color: #fff !important; }}
        .main-cell {{ position: relative; height: 60px; vertical-align: middle; }}
        .hanzi {{ font-size: 28px; font-weight: bold; }}
        .dm-hl {{ background-color: #fcf3cf; border-radius: 4px; padding: 2px 5px; display: inline-block; }}
        .interactive {{ cursor: pointer; transition: 0.15s; border-radius: 4px; padding: 0 4px; display: inline-block; }}
        .interactive:hover {{ background-color: #f39c12; color: #fff !important; transform: scale(1.15); box-shadow: 0 2px 5px rgba(0,0,0,0.2); }}
        .ss-text {{ position: absolute; bottom: 3px; right: 3px; font-size: 11px; color: #7f8c8d; font-weight: bold; background: rgba(255,255,255,0.8); padding: 1px 3px; border-radius: 3px; pointer-events: none; }}

        .rel-box {{ background-color: #ffffff; padding: 15px; border: 1px solid #ddd; border-left: 5px solid #27ae60; font-size: 15px; border-radius: 4px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }}
        .rel-box ul {{ margin: 10px 0 0 10px; padding: 0; line-height: 1.6; color: #1e8449; list-style-type: none; }}

        .warn-box {{ background-color: #fdfefe; padding: 15px; border: 1px solid #ddd; border-left: 5px solid #c0392b; font-size: 15px; border-radius: 4px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); transition: 0.3s ease-in-out; }}
        .warn-box ul {{ margin: 10px 0 0 10px; padding: 0; line-height: 1.6; color: #333; list-style-type: none; }}

        .rel-item {{ margin-bottom: 5px; }}
        .warn-item {{ margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px dashed #eee; }}
        .warn-item:last-child {{ border-bottom: none; margin-bottom: 0; padding-bottom: 0; }}

        .toggle-warn-btn {{ background-color: #e74c3c; color: white; border: none; padding: 10px 15px; font-size: 15px; border-radius: 4px; cursor: pointer; font-weight: bold; transition: background 0.2s; width: 100%; text-align: left; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-top: 10px; }}
        .toggle-warn-btn:hover {{ background-color: #c0392b; }}

        .dy-btn {{ display: inline-block; padding: 5px 10px; margin: 3px; background: #e0e0e0; cursor: pointer; border-radius: 4px; font-weight:bold; font-size:13px; border: 1px solid #ccc; transition: 0.2s; }}
        .dy-btn:hover {{ background: #c0c0c0; }}
        .ln-btn {{ display: inline-block; padding: 4px; margin: 2px; background: #f0f8ff; cursor: pointer; border: 1px solid #add8e6; border-radius: 3px; font-size:12px; transition: 0.2s; }}
        .ln-btn:hover {{ background: #d0e8f0; }}
        .lm-btn {{ display: inline-block; padding: 6px; margin: 3px; background: #f5eef8; cursor: pointer; border: 1px solid #d2b4de; border-radius: 3px; font-size:14px; font-weight: bold; transition: 0.2s; }}
        .lm-btn:hover {{ background: #e8daef; }}
        .dir-btn {{ display: inline-block; padding: 4px 8px; margin: 3px; background: #fdf2e9; cursor: pointer; border: 1px solid #e67e22; border-radius: 3px; font-size:14px; font-weight: bold; transition: 0.2s; color: #d35400; }}
        .dir-btn:hover {{ background: #fae5d3; }}

        .ld-box {{ margin-top:20px; padding:15px; border:1px solid #ddd; border-left: 5px solid #2980b9; background:#f4f9fd; border-radius:4px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }}
    </style>

    <script>
        var dy_data = {json.dumps(dy_data)};
        var warnings_data = {json.dumps(warnings_list, ensure_ascii=False)};
        var ld_data = {json.dumps(luandoan_data, ensure_ascii=False)};

        var dm_stem = "{d_stem}";

        var stem_clash = {{'甲':'庚', '庚':'甲', '乙':'辛', '辛':'乙', '丙':'壬', '壬':'丙', '丁':'癸', '癸':'丁'}};
        var stem_combo = {{'甲':'己', '己':'甲', '乙':'庚', '庚':'乙', '丙':'辛', '辛':'丙', '丁':'壬', '壬':'丁', '戊':'癸', '癸':'戊'}};
        var branch_clash = {{'子':'午', '午':'子', '丑':'未', '未':'丑', '寅':'申', '申':'寅', '卯':'酉', '酉':'卯', '辰':'戌', '戌':'辰', '巳':'亥', '亥':'巳'}};
        var branch_combo6 = {{'子':'丑', '丑':'子', '寅':'亥', '亥':'寅', '卯':'戌', '戌':'卯', '辰':'酉', '酉':'辰', '巳':'申', '申':'巳', '午':'未', '未':'午'}};
        var branch_combo3 = {{
            '申':['子','辰'], '子':['申','辰'], '辰':['申','子'], '亥':['卯','未'], '卯':['亥','未'], '未':['亥','卯'],
            '寅':['午','戌'], '午':['寅','戌'], '戌':['寅','午'], '巳':['酉','丑'], '酉':['巳','丑'], '丑':['巳','酉']
        }};
        var branch_harm = {{'子':'未', '未':'子', '丑':'午', '午':'丑', '寅':'巳', '巳':'寅', '卯':'辰', '辰':'卯', '申':'亥', '亥':'申', '酉':'戌', '戌':'酉'}};
        var branch_punish = {{'卯':['子'], '子':['卯'], '丑':['戌'], '戌':['丑','未'], '未':['戌']}};

        var posLabels = {{
            'Y_GAN': 'Can Năm', 'Y_ZHI': 'Chi Năm', 'M_GAN': 'Can Tháng', 'M_ZHI': 'Chi Tháng',
            'D_GAN': 'Can Ngày', 'D_ZHI': 'Chi Ngày', 'H_GAN': 'Can Giờ', 'H_ZHI': 'Chi Giờ',
            'DY_GAN': 'Can Đại Vận', 'DY_ZHI': 'Chi Đại Vận', 'LN_GAN': 'Can Lưu Niên', 'LN_ZHI': 'Chi Lưu Niên',
            'LM_GAN': 'Can Lưu Nguyệt', 'LM_ZHI': 'Chi Lưu Nguyệt',
            'DIR_GAN': 'Can Hướng', 'DIR_ZHI': 'Chi Hướng'
        }};

        var charToViet = {{
            '甲':'Giáp', '乙':'Ất', '丙':'Bính', '丁':'Đinh', '戊':'Mậu', '己':'Kỷ', '庚':'Canh', '辛':'Tân', '壬':'Nhâm', '癸':'Quý',
            '子':'Tý', '丑':'Sửu', '寅':'Dần', '卯':'Mão', '辰':'Thìn', '巳':'Tỵ', '午':'Ngọ', '未':'Mùi', '申':'Thân', '酉':'Dậu', '戌':'Tuất', '亥':'Hợi',
            '乾':'Càn', '坤':'Khôn', '艮':'Cấn', '巽':'Tốn'
        }};

        var stems_arr = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸'];
        var month_branches_arr = ['寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥', '子', '丑'];

        var state = {{
            'Y_GAN': '{y_stem}', 'Y_ZHI': '{y_branch}', 'M_GAN': '{m_stem}', 'M_ZHI': '{m_branch}',
            'D_GAN': '{d_stem}', 'D_ZHI': '{d_branch}', 'H_GAN': '{h_stem}', 'H_ZHI': '{h_branch}',
            'DY_GAN': null, 'DY_ZHI': null, 'LN_GAN': null, 'LN_ZHI': null, 'LM_GAN': null, 'LM_ZHI': null, 'DIR_GAN': null, 'DIR_ZHI': null
        }};

        var BRANCH_M = {json.dumps(BRANCH_MAIN)};
        var S_EL = {json.dumps(STEM_ELEM)};
        var B_EL = {json.dumps(BRANCH_ELEM)};
        var BG_EL = {json.dumps(BAGUA_ELEM, ensure_ascii=False)};
        var ELEM_COLOR = {json.dumps(ELEM_COLOR)};

        function getColor(char) {{ return ELEM_COLOR[S_EL[char] || B_EL[char] || BG_EL[char] || ""] || "black"; }}
        function getColoredChar(char, pos) {{ return '<span class="hanzi interactive" style="color: ' + getColor(char) + ';" onclick="checkRel(\\'' + pos + '\\')">' + char + '</span>'; }}

        function calcSS(char) {{
            if (!char) return "";
            if(char === dm_stem) return "Tỷ";

            var dmE = S_EL[dm_stem];
            var charE_direct = S_EL[char] || B_EL[char] || BG_EL[char];
            if(dmE === charE_direct) return "Kiếp";

            var eval_char = BRANCH_M[char] ? BRANCH_M[char] : char;
            var chE = S_EL[eval_char] || charE_direct;

            if (!chE) return "";
            var prod = {{"Mộc":"Hỏa","Hỏa":"Thổ","Thổ":"Kim","Kim":"Thủy","Thủy":"Mộc"}};
            var ctrl = {{"Mộc":"Thổ","Thổ":"Thủy","Thủy":"Hỏa","Hỏa":"Kim","Kim":"Mộc"}};
            if(prod[dmE] == chE) return "Thực";
            if(prod[chE] == dmE) return "Ấn";
            if(ctrl[dmE] == chE) return "Tài";
            if(ctrl[chE] == dmE) return "Quan";
            return "";
        }}

        function toggleWarning() {{
            var content = document.getElementById('warning_content');
            var btn = document.getElementById('toggle_warning_btn');
            if (content.style.display === 'none') {{
                content.style.display = 'block';
                btn.innerHTML = '⚠️ Chú Ý ▲';
            }} else {{
                content.style.display = 'none';
                btn.innerHTML = '⚠️ Chú Ý ▼';
            }}
        }}

        // Cập nhật hiển thị Bảng luận đoán (Tĩnh)
        function updateLuandoan() {{
            var sel = document.getElementById('ld_select').value;
            var contentDiv = document.getElementById('ld_content');

            if (!sel || !ld_data[sel] || ld_data[sel].length === 0) {{
                contentDiv.style.display = 'none';
                return;
            }}

            var htmlStr = "";
            for (var i = 0; i < ld_data[sel].length; i++) {{
                var bText = ld_data[sel][i].B ? ld_data[sel][i].B.replace(/\\n/g, '<br>') : '';
                var cText = ld_data[sel][i].C ? ld_data[sel][i].C.replace(/\\n/g, '<br>') : '';

                htmlStr += '<div style="margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px dashed #eee;">';
                if (bText) {{
                    htmlStr += '<div style="font-weight:bold; font-size:15px; color:#c0392b; margin-bottom:4px;">' + bText + '</div>';
                }}
                if (cText) {{
                    htmlStr += '<div style="color:#333; line-height:1.6; font-size: 14px;">' + cText + '</div>';
                }}
                htmlStr += '</div>';
            }}

            contentDiv.innerHTML = htmlStr;
            contentDiv.style.display = 'block';
        }}

        function checkRel(posA) {{
            var charA = state[posA];
            if (!charA) return;

            var vietChar = charToViet[charA];
            var warning_groups = {{}};
            var has_warnings = false;

            if (vietChar) {{
                warnings_data.forEach(w => {{
                    if (w.triggers.includes(vietChar)) {{
                        if (!warning_groups[w.category]) {{
                            warning_groups[w.category] = [];
                        }}
                        var descHtml = w.desc ? `<br><span style="color:#333;">${{w.desc}}</span>` : "";
                        var line = `<b style="color:#c0392b;">${{w.name}}</b> <span style="font-size:13px;color:#7f8c8d;">(Yếu tố: <i>${{w.triggers}}</i>)</span>${{descHtml}}`;
                        warning_groups[w.category].push(line);
                        has_warnings = true;
                    }}
                }});
            }}

            var isNatal = ['Y_GAN', 'Y_ZHI', 'M_GAN', 'M_ZHI', 'D_GAN', 'D_ZHI', 'H_GAN', 'H_ZHI'].includes(posA);
            var isDY = ['DY_GAN', 'DY_ZHI'].includes(posA);
            var isLN = ['LN_GAN', 'LN_ZHI'].includes(posA);
            var isLM = ['LM_GAN', 'LM_ZHI'].includes(posA);
            var isDIR = ['DIR_GAN', 'DIR_ZHI'].includes(posA);

            var targets = [];
            if (isNatal) targets = ['Y_GAN', 'Y_ZHI', 'M_GAN', 'M_ZHI', 'D_GAN', 'D_ZHI', 'H_GAN', 'H_ZHI'].filter(k => k !== posA);
            else if (isDY) targets = ['Y_GAN', 'Y_ZHI', 'M_GAN', 'M_ZHI', 'D_GAN', 'D_ZHI', 'H_GAN', 'H_ZHI'];
            else if (isLN) targets = ['Y_GAN', 'Y_ZHI', 'M_GAN', 'M_ZHI', 'D_GAN', 'D_ZHI', 'H_GAN', 'H_ZHI', 'DY_GAN', 'DY_ZHI'];
            else if (isLM) targets = ['Y_GAN', 'Y_ZHI', 'M_GAN', 'M_ZHI', 'D_GAN', 'D_ZHI', 'H_GAN', 'H_ZHI', 'DY_GAN', 'DY_ZHI', 'LN_GAN', 'LN_ZHI'];
            else if (isDIR) targets = ['Y_GAN', 'Y_ZHI', 'M_GAN', 'M_ZHI', 'D_GAN', 'D_ZHI', 'H_GAN', 'H_ZHI', 'DY_GAN', 'DY_ZHI', 'LN_GAN', 'LN_ZHI', 'LM_GAN', 'LM_ZHI'];

            var typeA = posA.endsWith('_GAN') ? 'GAN' : 'ZHI';
            targets = targets.filter(k => k.endsWith('_' + typeA) && state[k]);

            var rel_lines = [];

            targets.forEach(posB => {{
                var charB = state[posB];
                var labelB = posLabels[posB];

                var relCategory = "";
                var relLabel = "";

                if (typeA === 'GAN') {{
                    if (stem_clash[charA] === charB) {{ relCategory = "Xung"; relLabel = "Xung"; }}
                    if (stem_combo[charA] === charB) {{ relCategory = "Hợp"; relLabel = "Lục Hợp"; }}
                }}
                else if (typeA === 'ZHI') {{
                    if (branch_clash[charA] === charB) {{ relCategory = "Xung"; relLabel = "Xung"; }}
                    if (branch_combo6[charA] === charB) {{ relCategory = "Hợp"; relLabel = "Lục Hợp"; }}
                    if (branch_combo3[charA] && branch_combo3[charA].includes(charB)) {{ relCategory = "Hợp"; relLabel = "Tam Hợp"; }}
                    if (branch_harm[charA] === charB) {{ relCategory = "Hại/Hình"; relLabel = "Hại"; }}
                    if (branch_punish[charA] && branch_punish[charA].includes(charB)) {{ relCategory = "Hại/Hình"; relLabel = "Hình"; }}
                }}

                if (relCategory !== "") {{
                    rel_lines.push(`<b>${{charA}}</b> - <b>${{charB}}</b> &nbsp;&nbsp; ${{relLabel}} &nbsp;&nbsp; (${{labelB}})`);
                }}
            }});

            var container = document.getElementById('interaction_container');
            var relBox = document.getElementById('rel_box');

            var warnContent = document.getElementById('warning_content');
            var warnWrapper = document.getElementById('warning_wrapper');
            var toggleWarnBtn = document.getElementById('toggle_warning_btn');

            if (rel_lines.length > 0) {{
                var relHtml = `<b>🔗 Mối Quan Hệ của "${{charA}}" (${{posLabels[posA]}}):</b>`;
                relHtml += `<ul>` + rel_lines.map(r => `<li class="rel-item">${{r}}</li>`).join('') + `</ul>`;
                relBox.innerHTML = relHtml;
                relBox.style.display = 'block';

            }} else {{
                relBox.innerHTML = `<b>🔗 Mối Quan Hệ của "${{charA}}" (${{posLabels[posA]}}):</b><br><i style="color:gray; margin-left: 20px;">Không có tương tác nào thoả mãn.</i>`;
                relBox.style.display = 'block';
            }}

            if (has_warnings) {{
                var warnHtml = "";
                for (var cat in warning_groups) {{
                    warnHtml += `<div style="margin-top: 15px; margin-bottom: 5px; padding-bottom: 3px; border-bottom: 2px solid #e74c3c; display: inline-block; font-size: 16px; font-weight: bold; color: #c0392b; text-transform: uppercase;">🔹 ${{cat}}</div>`;
                    warnHtml += `<ul>` + warning_groups[cat].map(w => `<li class="warn-item">${{w}}</li>`).join('') + `</ul>`;
                }}
                warnContent.innerHTML = warnHtml;

                warnContent.style.display = 'none';
                toggleWarnBtn.innerHTML = '⚠️ Chú Ý ▼';
                warnWrapper.style.display = 'block';
            }} else {{
                warnWrapper.style.display = 'none';
            }}

            container.style.display = 'block';
        }}

        function loadDir(char) {{
            var isStem = (S_EL[char] !== undefined);
            state.DIR_GAN = isStem ? char : null;
            state.DIR_ZHI = isStem ? null : char;

            var isBagua = (BG_EL[char] !== undefined);
            if (isBagua) {{
                state.DIR_GAN = null;
                state.DIR_ZHI = char;
            }}

            document.getElementById('dir_main_g').innerHTML = (isStem && !isBagua) ? getColoredChar(char, 'DIR_GAN') + `<span class="ss-text">${{calcSS(char)}}</span>` : '';
            document.getElementById('dir_main_z').innerHTML = (!isStem || isBagua) ? getColoredChar(char, 'DIR_ZHI') + `<span class="ss-text">${{calcSS(char)}}</span>` : '';
            document.getElementById('interaction_container').style.display = 'none';
        }}

        function loadDY(dyKey) {{
            var d = dy_data[dyKey];
            state.DY_GAN = d.gan; state.DY_ZHI = d.zhi;
            state.LN_GAN = null; state.LN_ZHI = null;
            state.LM_GAN = null; state.LM_ZHI = null;

            document.getElementById('spacer2_th').style.display = 'table-cell';
            document.getElementById('spacer2_g').style.display = 'table-cell';
            document.getElementById('spacer2_z').style.display = 'table-cell';
            ['col_dy', 'dy_main_g', 'dy_main_z'].forEach(id => document.getElementById(id).style.display = 'table-cell');
            ['col_ln', 'ln_main_g', 'ln_main_z', 'col_lm', 'lm_main_g', 'lm_main_z'].forEach(id => document.getElementById(id).style.display = 'none');

            document.getElementById('dy_title').innerHTML = 'Đại Vận';
            document.getElementById('dy_main_g').innerHTML = getColoredChar(d.gan, 'DY_GAN') + `<span class="ss-text">${{calcSS(d.gan)}}</span>`;
            document.getElementById('dy_main_z').innerHTML = getColoredChar(d.zhi, 'DY_ZHI') + `<span class="ss-text">${{calcSS(d.zhi)}}</span>`;

            var lnHtml = "<b>Chọn Lưu Niên: </b><br>";
            d.lns.forEach((ln, idx) => {{ lnHtml += `<div class="ln-btn" onclick="loadLN('${{dyKey}}', ${{idx}})">${{ln.year}}<br>${{ln.gan}}${{ln.zhi}}</div>`; }});
            document.getElementById('ln_container').innerHTML = lnHtml;
            document.getElementById('lm_container').style.display = 'none';
            document.getElementById('interaction_container').style.display = 'none';
        }}

        function loadLN(dyKey, lnIdx) {{
            var ln = dy_data[dyKey].lns[lnIdx];
            state.LN_GAN = ln.gan; state.LN_ZHI = ln.zhi;
            state.LM_GAN = null; state.LM_ZHI = null;

            ['col_ln', 'ln_main_g', 'ln_main_z'].forEach(id => document.getElementById(id).style.display = 'table-cell');
            ['col_lm', 'lm_main_g', 'lm_main_z'].forEach(id => document.getElementById(id).style.display = 'none');

            document.getElementById('ln_title').innerHTML = 'Năm ' + ln.year;
            document.getElementById('ln_main_g').innerHTML = getColoredChar(ln.gan, 'LN_GAN') + `<span class="ss-text">${{calcSS(ln.gan)}}</span>`;
            document.getElementById('ln_main_z').innerHTML = getColoredChar(ln.zhi, 'LN_ZHI') + `<span class="ss-text">${{calcSS(ln.zhi)}}</span>`;
            document.getElementById('interaction_container').style.display = 'none';

            var yearStemIdx = stems_arr.indexOf(ln.gan);
            var startStemIdx = ((yearStemIdx % 5) * 2 + 2) % 10;
            var lmHtml = "<b>Chọn Lưu Nguyệt (Tháng): </b><br>";

            for (var i = 0; i < 12; i++) {{
                var mGan = stems_arr[(startStemIdx + i) % 10];
                var mZhi = month_branches_arr[i];
                // YÊU CẦU: Bỏ chữ Tháng đi, chỉ để Can Chi
                lmHtml += `<div class="lm-btn" onclick="loadLM('${{mGan}}', '${{mZhi}}', ${{i+1}})">${{mGan}}${{mZhi}}</div>`;
            }}

            document.getElementById('lm_container').innerHTML = lmHtml;
            document.getElementById('lm_container').style.display = 'block';
        }}

        function loadLM(mGan, mZhi, monthNum) {{
            state.LM_GAN = mGan; state.LM_ZHI = mZhi;
            ['col_lm', 'lm_main_g', 'lm_main_z'].forEach(id => document.getElementById(id).style.display = 'table-cell');

            document.getElementById('lm_title').innerHTML = 'Tháng ' + monthNum;
            document.getElementById('lm_main_g').innerHTML = getColoredChar(mGan, 'LM_GAN') + `<span class="ss-text">${{calcSS(mGan)}}</span>`;
            document.getElementById('lm_main_z').innerHTML = getColoredChar(mZhi, 'LM_ZHI') + `<span class="ss-text">${{calcSS(mZhi)}}</span>`;
            document.getElementById('interaction_container').style.display = 'none';
        }}
    </script>

    <div class="bazi-box">
        <table class="bz-tbl">
            <tr>
                <th class="pillar-col">Năm</th><th class="pillar-col">Tháng</th><th class="pillar-col">Ngày</th><th class="pillar-col">Giờ</th>
                <th class="spacer-col" id="spacer1_th"></th>
                <th id="col_dy" class="pillar-col" style="display:none;"><span id="dy_title"></span></th>
                <th id="col_ln" class="pillar-col" style="display:none;"><span id="ln_title"></span></th>
                <th id="col_lm" class="pillar-col" style="display:none;"><span id="lm_title"></span></th>
                <th class="spacer-col" id="spacer2_th" style="display:none;"></th>
                <th id="col_dir" class="pillar-col">Hướng</th>
            </tr>
            <tr>
                <td class="main-cell">{get_c_char(y_stem, 'Y_GAN')}<span class="ss-text">{get_shishen(d_stem, y_stem)}</span></td>
                <td class="main-cell">{get_c_char(m_stem, 'M_GAN')}<span class="ss-text">{get_shishen(d_stem, m_stem)}</span></td>
                <td class="main-cell"><span class="dm-hl">{get_c_char(d_stem, 'D_GAN')}</span>{dm_special_html}</td>
                <td class="main-cell">{get_c_char(h_stem, 'H_GAN')}<span class="ss-text">{get_shishen(d_stem, h_stem)}</span></td>
                <td class="spacer-col" id="spacer1_g"></td>
                <td id="dy_main_g" class="main-cell" style="display:none;"></td>
                <td id="ln_main_g" class="main-cell" style="display:none;"></td>
                <td id="lm_main_g" class="main-cell" style="display:none;"></td>
                <td class="spacer-col" id="spacer2_g" style="display:none;"></td>
                <td id="dir_main_g" class="main-cell"></td>
            </tr>
            <tr>
                <td class="main-cell">{get_c_char(y_branch, 'Y_ZHI')}<span class="ss-text">{get_shishen(d_stem, y_branch)}</span></td>
                <td class="main-cell">{get_c_char(m_branch, 'M_ZHI')}<span class="ss-text">{get_shishen(d_stem, m_branch)}</span></td>
                <td class="main-cell">{get_c_char(d_branch, 'D_ZHI')}<span class="ss-text">{get_shishen(d_stem, d_branch)}</span></td>
                <td class="main-cell">{get_c_char(h_branch, 'H_ZHI')}<span class="ss-text">{get_shishen(d_stem, h_branch)}</span></td>
                <td class="spacer-col" id="spacer1_z"></td>
                <td id="dy_main_z" class="main-cell" style="display:none;"></td>
                <td id="ln_main_z" class="main-cell" style="display:none;"></td>
                <td id="lm_main_z" class="main-cell" style="display:none;"></td>
                <td class="spacer-col" id="spacer2_z" style="display:none;"></td>
                <td id="dir_main_z" class="main-cell"></td>
            </tr>
        </table>

        <!-- KHU VỰC HIỂN THỊ TƯƠNG TÁC -->
        <div id="interaction_container" style="display:none; margin-top:20px;">
            <div id="rel_box" class="rel-box"></div>

            <div id="warning_wrapper" style="margin-top:10px; display:none;">
                <button id="toggle_warning_btn" class="toggle-warn-btn" onclick="toggleWarning()">⚠️ Chú Ý ▼</button>
                <div id="warning_content" class="warn-box" style="margin-top:5px; display:none;"></div>
            </div>
        </div>

        <!-- BẢNG CHỌN LUẬN ĐOÁN TĨNH -->
        <div class="ld-box">
            <h4 style="margin-top:0; margin-bottom:10px; color:#2c3e50;">📖 Phong Thủy</h4>
            <select id="ld_select" style="padding:6px; font-size:15px; width:100%; max-width:350px; border-radius:4px; border:1px solid #ccc; cursor: pointer;" onchange="updateLuandoan()">
                {ld_options}
            </select>
            <div id="ld_content" style="margin-top:15px; display:none; background:#fff; padding:12px; border-radius:4px; border:1px solid #eee;">
            </div>
        </div>

        <h4 style="margin-top:20px; border-bottom:1px solid #ccc; padding-bottom:5px;">⏳ Chọn Đại Vận:</h4>
        <div>
    """
    for i, dy in enumerate(da_yuns[1:9]):
        dy_lbl = f"Vận {i+1}<br>{dy.getGanZhi()}"
        html_content += f"<div class='dy-btn' onclick=\"loadDY('dy_{i}')\">{dy_lbl}</div>"

    html_content += f"""
        </div>
        <div id="ln_container" style="margin-top:15px; padding:10px; border:1px dashed #0066cc; background:#f9f9f9; min-height:50px;">
            <i>(Vui lòng chọn 1 Đại vận phía trên để xem Lưu Niên tương ứng)</i>
        </div>

        <div id="lm_container" style="margin-top:15px; padding:10px; border:1px dashed #9b59b6; background:#f4ecf7; display:none;">
        </div>

        <div id="dir_container" style="margin-top:15px; padding:10px; border:1px dashed #e67e22; background:#fdf2e9;">
            <b>Chọn Hướng: </b><br>
            {dir_html}
        </div>
    </div>
    """
    return html_content

# ==========================================
# 3. GIAO DIỆN NHẬP LIỆU BẰNG STREAMLIT
# ==========================================
st.title("Phân Tích Bát Tự")

# Bố cục hàng ngang cho các tùy chọn nhập liệu
col1, col2, col3, col4, col5, col6, col7 = st.columns([1.5, 1, 1, 1, 1, 1.5, 1.5])

with col1:
    year_val = st.number_input("Năm:", value=1993, step=1)
with col2:
    month_val = st.selectbox("Tháng:", list(range(1, 13)), index=0)
with col3:
    day_val = st.selectbox("Ngày:", list(range(1, 32)), index=6)
with col4:
    hour_val = st.selectbox("Giờ:", list(range(0, 24)), index=8)
with col5:
    min_val = st.selectbox("Phút:", list(range(0, 60)), index=30)
with col6:
    gender_str = st.selectbox("Giới tính:", ["Nam", "Nữ"], index=0)
    gender_val = 1 if gender_str == "Nam" else 0
with col7:
    st.write("") # Dùng để canh nút bấm xuống cho đều
    st.write("")
    calc_button = st.button("Tính Bát Tự", type="primary", use_container_width=True)

st.divider()

# ==========================================
# 4. RENDER HTML TÍNH TOÁN RA STREAMLIT
# ==========================================

# Mặc định load khi vào app lần đầu hoặc khi bấm nút
html_string = get_bazi_html(year_val, month_val, day_val, hour_val, min_val, gender_val)

# Sử dụng chuẩn của bạn (st.components.v1.html)
# Để chiều cao height=900 và scrolling=True để đủ chỗ khi bảng thông tin xổ xuống
components.html(html_string, height=1000, scrolling=True)

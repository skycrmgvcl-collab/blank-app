import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
import base64

st.set_page_config(page_title="PPR Paid Pending Dashboard", layout="wide")

st.markdown("## 💰 Paid Pending Report (PPR) Dashboard")
st.caption("Survey Category Wise Monitoring")

# =====================================================
# SIDEBAR FILTERS
# =====================================================

st.sidebar.header("Filters")

show_shift = st.sidebar.checkbox("Connection Shifting (Non Cons)")
show_pmsy = st.sidebar.checkbox("PMSY RTS")
show_rooftop = st.sidebar.checkbox("LT Rooftop")

# =====================================================
# FILE UPLOAD
# =====================================================

file = st.file_uploader("Upload PPR Excel/CSV File", type=["xlsx","xls","csv"])


# =====================================================
# RELEASE FORM HTML
# =====================================================

def create_release_html(row):

    mobile=""

    for c in row.index:
        if "mob" in c.lower():
            mobile=row[c]

    html=f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">

<style>

body{{font-family:'Shruti','Nirmala UI';font-size:13px}}

.header{{text-align:center;font-weight:bold;font-size:16px}}

table{{width:100%;border-collapse:collapse}}

td{{border:1px solid black;padding:5px}}

</style>

</head>

<body onload="window.print()">

<div class="header">મધ્ય ગુજરાત વીજ કંપની લી.</div>
<div style="text-align:center">વિરપુર</div>

<h3 style="text-align:center">નવું કનેક્શન ચાલુ કર્યા અંગેનો રિપોર્ટ</h3>

<table>

<tr>
<td>ગ્રાહકનું નામ</td>
<td>{row.get("Name Of Applicant","")}</td>
</tr>

<tr>
<td>SR Number</td>
<td>{row.get("SR Number","")}</td>
</tr>

<tr>
<td>Load</td>
<td>{row.get("Demand Load","")} {row.get("Load Uom","")}</td>
</tr>

<tr>
<td>સરનામું</td>
<td>
{row.get("Address1","")}
{row.get("Address2","")}
{row.get("Village Or City","")}
</td>
</tr>

<tr>
<td>Tariff</td>
<td>{row.get("Tariff","")}</td>
</tr>

<tr>
<td>Survey Category</td>
<td>{row.get("Survey Category","")}</td>
</tr>

<tr>
<td>FQ Amount</td>
<td>{row.get("FQ Amount","")}</td>
</tr>

<tr>
<td>FQ Paid Date</td>
<td>{row.get("Date Of FQ Paid","")}</td>
</tr>

<tr>
<td>ટેસ્ટ રીપોર્ટ તા.</td>
<td>{row.get("Date Of TR Recv","")}</td>
</tr>

<tr>
<td>રસીદ નં</td>
<td>{row.get("TR MR No","")}</td>
</tr>

<tr>
<td>મોબાઇલ નંબર</td>
<td>{mobile}</td>
</tr>

</table>

<br><br>

<table>

<tr>
<td>ગ્રાહકની સહી</td>
<td>કર્મચારી ની સહી</td>
<td>જુ.ઇ. સહી</td>
<td>ના.ઇ. સહી</td>
</tr>

</table>

</body>
</html>
"""

    return base64.b64encode(html.encode("utf-8")).decode()


# =====================================================
# PROCESS FILE
# =====================================================

if file:

    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)

    # CLEAN COLUMNS
    df["SR Type"] = df["SR Type"].astype(str).str.strip()
    df["Name Of Scheme"] = df["Name Of Scheme"].astype(str).str.strip()
    df["Survey Category"] = df["Survey Category"].astype(str).str.strip()

    # REMOVE EXCLUDED
    df = df[df["SR Type"].str.lower() != "change of name"]
    df = df[df["Name Of Scheme"].str.lower() != "spa schemes"]

# =====================================================
# SR TYPE FILTER
# =====================================================

    selected_types=[]

    if show_shift:
        selected_types.append("Connection Shifting(Non Cons)")

    if show_pmsy:
        selected_types.append("PMSY RTS")

    if show_rooftop:
        selected_types.append("LT Rooftop")

    if selected_types:
        df=df[df["SR Type"].isin(selected_types)]

# =====================================================
# SCHEME FILTER
# =====================================================

    scheme_list=sorted(df["Name Of Scheme"].dropna().unique())

    scheme_filter=st.sidebar.selectbox(
        "Name Of Scheme",
        ["All"]+scheme_list
    )

    if scheme_filter!="All":
        df=df[df["Name Of Scheme"]==scheme_filter]

# =====================================================
# SURVEY CATEGORY FILTER
# =====================================================

    survey_list=sorted(df["Survey Category"].dropna().unique())

    survey_filter=st.selectbox(
        "Select Survey Category",
        ["All"]+survey_list
    )

    if survey_filter!="All":
        df=df[df["Survey Category"]==survey_filter]

# =====================================================
# SERIAL NUMBER
# =====================================================

    df.insert(0,"Sr No",range(1,len(df)+1))

# =====================================================
# GENERATE PRINT DATA
# =====================================================

    def generate_print(row):

        if pd.notna(row.get("Date Of TR Recv")) and pd.notna(row.get("TR MR No")):
            return create_release_html(row)

        return ""

    df["release_html"]=df.apply(generate_print,axis=1)

    df.insert(1,"Print","")

    st.metric("Total Records",len(df))

# =====================================================
# PRINT ICON RENDERER
# =====================================================

    renderer=JsCode("""

class Renderer{

init(params){

this.eGui=document.createElement('span');

this.eGui.innerHTML='🖨';

this.eGui.style.cursor='pointer';

this.eGui.addEventListener('click',()=>{

const b64=params.data.release_html;

if(b64=="") return;

const win=window.open("","_blank");

const bytes=Uint8Array.from(atob(b64),c=>c.charCodeAt(0));
const html=new TextDecoder("utf-8").decode(bytes);

win.document.write(html);
win.document.close();

});

}

getGui(){return this.eGui;}

}

""")

# =====================================================
# AGGRID
# =====================================================

    gb=GridOptionsBuilder.from_dataframe(df)

    gb.configure_default_column(
        filter=True,
        sortable=True,
        resizable=True,
        flex=1,
        minWidth=120
    )

    gb.configure_column("Print",cellRenderer=renderer,width=70)

    gb.configure_column("release_html",hide=True)

    AgGrid(
        df,
        gridOptions=gb.build(),
        allow_unsafe_jscode=True,
        fit_columns_on_grid_load=True,
        height=650
    )

else:

    st.info("Upload PPR file to begin")

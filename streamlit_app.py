import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
import io

st.set_page_config(page_title="PPR Paid Pending Dashboard", layout="wide")

st.title("💰 Paid Pending Report (PPR) Dashboard")

# ---------------------------------------------------------
# SIDEBAR FILTER
# ---------------------------------------------------------

st.sidebar.header("Filters")

show_shift = st.sidebar.checkbox("Connection Shifting (Non Cons)")
show_pmsy = st.sidebar.checkbox("PMSY RTS")
show_rooftop = st.sidebar.checkbox("LT Rooftop")

# ---------------------------------------------------------
# FILE UPLOAD
# ---------------------------------------------------------

file = st.file_uploader("Upload PPR Excel/CSV File", type=["xlsx","xls","csv"])


# ---------------------------------------------------------
# PDF CREATION FUNCTION
# ---------------------------------------------------------

def create_pdf(rec):

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(buffer, pagesize=A4)

    mobile = ""

    for col in rec.index:
        if "mob" in col.lower():
            mobile = rec[col]

    address = f"{rec.get('Address1','')} {rec.get('Address2','')} {rec.get('Village Or City','')}"

    data = [

        ["મધ્ય ગુજરાત વીજ કંપની લી.", ""],
        ["વિરપુર", ""],

        ["ગ્રાહકનું નામ", rec.get("Name Of Applicant","")],
        ["SR Number", rec.get("SR Number","")],
        ["Load (KW)", rec.get("Demand Load","")],

        ["સરનામું", address],

        ["Tariff", rec.get("Tariff","")],
        ["Mobile", mobile],

        ["Survey Category", rec.get("Survey Category","")],

        ["FQ Amount", rec.get("FQ Amount","")],
        ["FQ Paid", rec.get("Date Of FQ Paid","")],

        ["Test Report Date", rec.get("Date Of TR Recv","")],
        ["Receipt No", rec.get("TR MR No","")],

        ["ગ્રાહકની સહી", "કર્મચારી ની સહી"],
        ["જુ.ઇ. સહી", "ના.ઇ. સહી"]

    ]

    table = Table(data, colWidths=[90*mm,100*mm])

    table.setStyle(TableStyle([
        ("GRID",(0,0),(-1,-1),0.5,colors.black),
        ("BOX",(0,0),(-1,-1),1,colors.black)
    ]))

    doc.build([table])

    buffer.seek(0)

    return buffer


# ---------------------------------------------------------
# MAIN PROCESS
# ---------------------------------------------------------

if file:

    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)

    df["SR Type"] = df["SR Type"].astype(str).str.strip()
    df["Name Of Scheme"] = df["Name Of Scheme"].astype(str).str.strip()

    df = df[df["SR Type"].str.lower() != "change of name"]
    df = df[df["Name Of Scheme"].str.lower() != "spa schemes"]

# ---------------------------------------------------------
# SERIAL NUMBER
# ---------------------------------------------------------

    df.insert(0,"Sr. No.",range(1,len(df)+1))

# ---------------------------------------------------------
# PRINT ICON COLUMN
# ---------------------------------------------------------

    def print_icon(row):

        if pd.notna(row.get("Date Of TR Recv")) and pd.notna(row.get("TR MR No")):
            return "🖨"
        return ""

    df.insert(1,"Print",df.apply(print_icon,axis=1))

    st.metric("Total Records",len(df))

# ---------------------------------------------------------
# AGGRID CONFIG
# ---------------------------------------------------------

    cellstyle = JsCode("""
    function(params) {
        if (params.value == "🖨") {
            return {'cursor':'pointer','font-size':'18px'}
        }
    }
    """)

    gb = GridOptionsBuilder.from_dataframe(df)

    gb.configure_default_column(
        filter=True,
        sortable=True,
        resizable=True,
        minWidth=120
    )

    gb.configure_column("Sr. No.", width=80)

    gb.configure_column(
        "Print",
        width=80,
        cellStyle=cellstyle
    )

    gb.configure_selection("single")

    grid = AgGrid(

        df,

        gridOptions=gb.build(),

        update_mode=GridUpdateMode.SELECTION_CHANGED,

        fit_columns_on_grid_load=True,

        height=600,

        allow_unsafe_jscode=True
    )

# ---------------------------------------------------------
# GET SELECTED ROW
# ---------------------------------------------------------

    selected = grid["selected_rows"]

    if selected is not None and len(selected) > 0:

        rec = pd.Series(selected[0])

        if pd.notna(rec.get("Date Of TR Recv")) and pd.notna(rec.get("TR MR No")):

            st.success(f"Selected SR : {rec['SR Number']}")

            pdf = create_pdf(rec)

            st.download_button(

                "📄 Download Connection Release Form",

                pdf,

                file_name=f"Connection_{rec['SR Number']}.pdf",

                mime="application/pdf"

            )

        else:

            st.warning("TR Receive Date or TR MR No not available")

else:

    st.info("Upload PPR file to begin")

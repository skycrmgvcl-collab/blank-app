import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
import io

st.set_page_config(page_title="PPR Paid Pending Dashboard", layout="wide")

st.title("💰 Paid Pending Report (PPR) Dashboard")

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

st.sidebar.header("Filters")

show_shift = st.sidebar.checkbox("Connection Shifting (Non Cons)")
show_pmsy = st.sidebar.checkbox("PMSY RTS")
show_rooftop = st.sidebar.checkbox("LT Rooftop")

# --------------------------------------------------
# FILE UPLOAD
# --------------------------------------------------

file = st.file_uploader("Upload PPR Excel/CSV File", type=["xlsx","xls","csv"])


# --------------------------------------------------
# PDF GENERATION
# --------------------------------------------------

def create_pdf(rec):

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20,
        leftMargin=20,
        topMargin=20,
        bottomMargin=20
    )

    mobile = ""

    for col in rec.index:
        if "mob" in col.lower():
            mobile = rec[col]

    address = f"{rec.get('Address1','')} {rec.get('Address2','')} {rec.get('Village Or City','')}"

    data = [

        ["મધ્ય ગુજરાત વીજ કંપની લી.", ""],
        ["વિરપુર", ""],

        ["પ્રતિ શ્રી", ""],
        ["નાયબ ઇજનેરશ્રી (સં અને નિ)", ""],

        ["તારીખ", rec.get("Date Of Release Conn","")],
        ["ગ્રાહક નં", rec.get("Consumer No","")],

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

        ["", ""],

        ["ગ્રાહકની સહી", "કર્મચારી ની સહી"],
        ["જુ.ઇ. સહી", "ના.ઇ. સહી"]

    ]

    table = Table(data, colWidths=[90*mm,100*mm])

    table.setStyle(TableStyle([

        ("GRID",(0,0),(-1,-1),0.5,colors.black),
        ("BOX",(0,0),(-1,-1),1,colors.black)

    ]))

    elements = [table]

    doc.build(elements)

    buffer.seek(0)

    return buffer


# --------------------------------------------------
# MAIN PROCESS
# --------------------------------------------------

if file:

    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)

    df["SR Type"] = df["SR Type"].astype(str).str.strip()
    df["Name Of Scheme"] = df["Name Of Scheme"].astype(str).str.strip()
    df["Survey Category"] = df["Survey Category"].astype(str).str.strip()

    df = df[df["SR Type"].str.lower() != "change of name"]
    df = df[df["Name Of Scheme"].str.lower() != "spa schemes"]

# --------------------------------------------------
# SR TYPE FILTER
# --------------------------------------------------

    selected_types = []

    if show_shift:
        selected_types.append("Connection Shifting(Non Cons)")

    if show_pmsy:
        selected_types.append("PMSY RTS")

    if show_rooftop:
        selected_types.append("LT Rooftop")

    if selected_types:
        df = df[df["SR Type"].isin(selected_types)]

# --------------------------------------------------
# SCHEME FILTER
# --------------------------------------------------

    scheme_list = sorted(df["Name Of Scheme"].dropna().unique())

    scheme_filter = st.sidebar.selectbox(
        "Name Of Scheme",
        ["All"] + scheme_list
    )

    if scheme_filter != "All":
        df = df[df["Name Of Scheme"] == scheme_filter]

# --------------------------------------------------
# SURVEY CATEGORY FILTER
# --------------------------------------------------

    survey_list = sorted(df["Survey Category"].dropna().unique())

    survey_filter = st.selectbox(
        "Select Survey Category",
        ["All"] + survey_list
    )

    if survey_filter != "All":
        df = df[df["Survey Category"] == survey_filter]

# --------------------------------------------------
# SERIAL NUMBER
# --------------------------------------------------

    df.insert(0,"Sr. No.",range(1,len(df)+1))

# --------------------------------------------------
# PRINT COLUMN (SECOND COLUMN)
# --------------------------------------------------

    def check_print(row):

        if pd.notna(row.get("Date Of TR Recv")) and pd.notna(row.get("TR MR No")):
            return "🖨"
        else:
            return ""

    df.insert(1,"Print",df.apply(check_print,axis=1))

    st.metric("Total Records",len(df))

# --------------------------------------------------
# AGGRID
# --------------------------------------------------

    gb = GridOptionsBuilder.from_dataframe(df)

    gb.configure_default_column(
        filter=True,
        sortable=True,
        resizable=True,
        minWidth=120
    )

    gb.configure_column("Sr. No.",width=80)
    gb.configure_column("Print",width=70)

    gb.configure_selection("single")

    grid = AgGrid(

        df,

        gridOptions=gb.build(),

        update_mode=GridUpdateMode.SELECTION_CHANGED,

        fit_columns_on_grid_load=True,

        height=600

    )

# --------------------------------------------------
# GET SELECTED ROW
# --------------------------------------------------

    selected = grid["selected_rows"]

    if selected is not None and len(selected) > 0:

        rec = pd.Series(selected[0])

        if pd.notna(rec.get("Date Of TR Recv")) and pd.notna(rec.get("TR MR No")):

            pdf = create_pdf(rec)

            st.download_button(

                "📄 Download Connection Release Form PDF",

                pdf,

                file_name=f"Connection_{rec['SR Number']}.pdf",

                mime="application/pdf"

            )

        else:

            st.warning("TR Receive Date or TR MR No not available")

else:

    st.info("Upload PPR file to begin")

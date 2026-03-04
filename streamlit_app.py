import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib import colors
import io

st.set_page_config(page_title="PPR Paid Pending Dashboard", layout="wide")

st.title("💰 Paid Pending Report (PPR) Dashboard")
st.caption("Survey Category Wise Monitoring")

# -------------------------------------------------
# Sidebar Filters
# -------------------------------------------------

st.sidebar.header("Filters")

show_shift = st.sidebar.checkbox("Connection Shifting (Non Cons)")
show_pmsy = st.sidebar.checkbox("PMSY RTS")
show_rooftop = st.sidebar.checkbox("LT Rooftop")

# -------------------------------------------------
# File Upload
# -------------------------------------------------

file = st.file_uploader("Upload PPR Excel/CSV File", type=["xlsx","xls","csv"])

# -------------------------------------------------
# PDF FORM CREATION
# -------------------------------------------------

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

    styles = getSampleStyleSheet()

    mobile = ""
    if "Mobile No" in rec.index:
        mobile = rec["Mobile No"]

    address = f"{rec.get('Address1','')} {rec.get('Address2','')} {rec.get('Village Or City','')}"

    data = [

        ["મધ્ય ગુજરાત વીજ કંપની લી.", ""],
        ["વિરપુર", ""],
        ["(AN ISO 9001:2000 CERTIFIED COMPANY)", ""],

        ["પ્રતિ શ્રી", ""],
        ["નાયબ ઇજનેરશ્રી (સં અને નિ)", f"તારીખ: {rec.get('Date Of Release Conn','')}"],
        ["એમ.જી.વી.સી.એલ. - પેટા વિભાગીય કચેરી", f"ગ્રાહક નં: {rec.get('Consumer No','')}"],
        ["વિરપુર", ""],

        ["વિષય: નવું કનેક્શન ચાલુ કર્યા અંગેનો રિપોર્ટ", ""],

        ["૧ ગ્રાહકનું નામ", rec.get("Name Of Applicant","")],
        ["૨ SR No", rec.get("SR Number","")],
        ["લોડ (KW)", rec.get("Demand Load","")],

        ["સરનામું", address],
        ["Tariff", rec.get("Tariff","")],
        ["Mob.No", mobile],

        ["Survey Cat.", rec.get("Survey Category","")],
        ["FQ Amt", rec.get("FQ Amount","")],
        ["FQ Paid", rec.get("Date Of FQ Paid","")],

        ["પૈસા ભર્યાની રસીદ નં", rec.get("TR MR No","")],
        ["ટેસ્ટ રીપોર્ટ તા.", rec.get("Date Of TR Recv","")],

        ["", ""],

        ["ગ્રાહકની સહી", "કર્મચારી ની સહી"],
        ["જુ.ઇ. સહી", "ના.ઇ. સહી"]

    ]

    table = Table(data, colWidths=[90*mm, 100*mm])

    table.setStyle(TableStyle([

        ("BOX",(0,0),(-1,-1),1,colors.black),
        ("GRID",(0,0),(-1,-1),0.5,colors.grey),

        ("FONTNAME",(0,0),(-1,-1),"Helvetica"),
        ("FONTSIZE",(0,0),(-1,-1),10),

    ]))

    elements = []

    elements.append(table)

    doc.build(elements)

    buffer.seek(0)

    return buffer


# -------------------------------------------------
# Main Logic
# -------------------------------------------------

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

    selected_types = []

    if show_shift:
        selected_types.append("Connection Shifting(Non Cons)")
    if show_pmsy:
        selected_types.append("PMSY RTS")
    if show_rooftop:
        selected_types.append("LT Rooftop")

    if selected_types:
        df = df[df["SR Type"].isin(selected_types)]

    scheme_list = sorted(df["Name Of Scheme"].dropna().unique())

    scheme_filter = st.sidebar.selectbox(
        "Name Of Scheme",
        ["All"] + scheme_list
    )

    if scheme_filter != "All":
        df = df[df["Name Of Scheme"] == scheme_filter]

    survey_list = sorted(df["Survey Category"].dropna().unique())

    survey_filter = st.selectbox(
        "Select Survey Category",
        ["All"] + survey_list
    )

    if survey_filter != "All":
        df = df[df["Survey Category"] == survey_filter]

    df.insert(0,"Sr. No.",range(1,len(df)+1))

    st.metric("Total Records",len(df))

# -------------------------------------------------
# Add Print Column
# -------------------------------------------------

    def check_print(row):

        if pd.notna(row.get("Date Of TR Recv")) and pd.notna(row.get("TR MR No")):
            return "🖨"
        else:
            return ""

    df["Print"] = df.apply(check_print,axis=1)

# -------------------------------------------------
# Grid Configuration
# -------------------------------------------------

    gb = GridOptionsBuilder.from_dataframe(df)

    gb.configure_default_column(
        filter=True,
        sortable=True,
        resizable=True,
        flex=1
    )

    gb.configure_selection("single")

    cell_renderer = JsCode("""
    class BtnRenderer {
        init(params) {
            this.eGui = document.createElement('button');
            this.eGui.innerHTML = '🖨';
            this.eGui.addEventListener('click', () => {
                params.api.dispatchEvent({
                    type: 'printRequested',
                    data: params.node.data
                });
            });
        }
        getGui() {
            return this.eGui;
        }
    }
    """)

    gb.configure_column("Print", cellRenderer=cell_renderer,width=70)

# -------------------------------------------------
# Show Grid
# -------------------------------------------------

    grid = AgGrid(

        df,
        gridOptions=gb.build(),
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        allow_unsafe_jscode=True,
        fit_columns_on_grid_load=True,
        height=600
    )

# -------------------------------------------------
# Row Selection → Generate PDF
# -------------------------------------------------

    selected = grid["selected_rows"]

    if selected:

        rec = pd.Series(selected[0])

        if pd.notna(rec.get("Date Of TR Recv")) and pd.notna(rec.get("TR MR No")):

            pdf = create_pdf(rec)

            st.download_button(

                "📄 Download Connection Release Form PDF",

                data=pdf,

                file_name=f"Connection_{rec['SR Number']}.pdf",

                mime="application/pdf"

            )

        else:

            st.warning("TR Receive Date or TR MR No not available")

else:

    st.info("Upload PPR file to begin")

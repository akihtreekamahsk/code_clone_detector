import io
from datetime import datetime

import streamlit as st
import matplotlib.pyplot as plt

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image
)

import backend


st.set_page_config(
    page_title="Code Clone Detector",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Code Clone Detector Application")

st.write(
    "Detect code similarity by comparing "
    "two Python source files."
)

st.divider()

# Upload Python files
col1, col2 = st.columns(2)

with col1:
    file1 = st.file_uploader(
        "Upload First Python File",
        type=["py"]
    )

with col2:
    file2 = st.file_uploader(
        "Upload Second Python File",
        type=["py"]
    )


# Generate PDF report
def create_pdf(score, name1, name2, code1, code2):

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4
    )

    styles = getSampleStyleSheet()

    story = []

    story.append(
        Paragraph(
            "Code Clone Detector Report",
            styles["Title"]
        )
    )

    story.append(Spacer(1, 15))

    story.append(
        Paragraph(
            "Generated on: "
            + datetime.now().strftime("%d-%m-%Y %H:%M"),
            styles["Normal"]
        )
    )

    story.append(Spacer(1, 15))

    story.append(
        Paragraph("File Details", styles["Heading2"])
    )

    story.append(
        Paragraph("First File: " + name1, styles["Normal"])
    )

    story.append(
        Paragraph("Second File: " + name2, styles["Normal"])
    )

    story.append(Spacer(1, 15))

    story.append(
        Paragraph(
            f"Overall Similarity: {score}%",
            styles["Heading2"]
        )
    )

    story.append(
        Paragraph(
            f"Overall Difference: {round(100-score, 2)}%",
            styles["Normal"]
        )
    )

    story.append(Spacer(1, 15))

    story.append(
        Paragraph(
            "Side-by-Side Code Comparison",
            styles["Heading2"]
        )
    )

    data = [
        [
            Paragraph("<b>First Program</b>", styles["Normal"]),
            Paragraph("<b>Second Program</b>", styles["Normal"])
        ],
        [
            Paragraph(
                "<br/>".join(code1.splitlines())[:3500],
                styles["Code"]
            ),
            Paragraph(
                "<br/>".join(code2.splitlines())[:3500],
                styles["Code"]
            )
        ]
    ]

    table = Table(
        data,
        colWidths=[250, 250]
    )

    table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 6)
        ])
    )

    story.append(table)

    story.append(Spacer(1, 15))

    story.append(
        Paragraph(
            "Note: Similarity is an estimate and "
            "is not proof of plagiarism.",
            styles["Italic"]
        )
    )

    doc.build(story)

    buffer.seek(0)

    return buffer


# Compare uploaded files
if file1 and file2:

    code1 = file1.getvalue().decode(
        "utf-8", errors="replace"
    )

    code2 = file2.getvalue().decode(
        "utf-8", errors="replace"
    )

    if st.button("Compare Files", type="primary"):

        result = backend.calculate_similarity(
            code1,
            code2
        )

        st.session_state["score"] = (
            result["similarity_score"]
        )

        st.session_state["code1"] = code1
        st.session_state["code2"] = code2

        st.session_state["name1"] = file1.name
        st.session_state["name2"] = file2.name


# Display results
if "score" in st.session_state:

    score = st.session_state["score"]

    difference = round(100 - score, 2)

    st.divider()

    st.header("Comparison Results")

    st.metric(
        "Overall Similarity",
        f"{score}%"
    )

    st.metric(
        "Overall Difference",
        f"{difference}%"
    )

    # Pie chart
    st.subheader("Similarity and Difference Chart")

    fig, ax = plt.subplots()

    ax.pie(
        [score, difference],
        labels=["Similarity", "Difference"],
        autopct="%1.1f%%",
        startangle=90
    )

    ax.axis("equal")

    st.pyplot(fig)

    plt.close(fig)

    # Side by side comparison
    st.divider()

    st.subheader("Side-by-Side Code Comparison")

    left, right = st.columns(2)

    with left:

        st.write(
            "**First File: "
            + st.session_state["name1"]
            + "**"
        )

        st.code(
            st.session_state["code1"],
            language="python"
        )

    with right:

        st.write(
            "**Second File: "
            + st.session_state["name2"]
            + "**"
        )

        st.code(
            st.session_state["code2"],
            language="python"
        )

    # PDF download
    st.divider()

    st.subheader("Download Comparison Report")

    pdf = create_pdf(
        score,
        st.session_state["name1"],
        st.session_state["name2"],
        st.session_state["code1"],
        st.session_state["code2"]
    )

    st.download_button(
        label="Download PDF Report",
        data=pdf,
        file_name="Code_Clone_Report.pdf",
        mime="application/pdf"
    )

else:

    st.info(
        "Upload two Python files and click Compare Files."
    )
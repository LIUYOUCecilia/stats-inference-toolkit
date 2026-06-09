# -*- coding: utf-8 -*-
"""
pdf_generator.py
Generates a professional-grade PDF statistical report following the AP Statistics
"State-Plan-Do-Conclude" framework. Renders LaTeX formulas using Matplotlib.
"""
import io
import datetime
from PIL import Image as PILImage

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

# -------------------------------------------------------------------------
# 1. Custom Two-Pass Canvas for Page Numbering and Headers/Footers
# -------------------------------------------------------------------------
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_elements(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_elements(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#4b5563")) # gray-600
        
        # Header (on pages after the first page)
        if self._pageNumber > 1:
            self.drawString(54, 755, "A/B Testing & Statistical Inference Report")
            self.setStrokeColor(colors.HexColor("#e5e7eb")) # gray-200
            self.setLineWidth(0.5)
            self.line(54, 748, 558, 748)
            
        # Footer (on all pages)
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 40, page_text)
        self.drawString(54, 40, "stats-inference-toolkit | Fiverr/Portfolio Edition")
        
        self.setStrokeColor(colors.HexColor("#e5e7eb")) # gray-200
        self.setLineWidth(0.5)
        self.line(54, 50, 558, 50)
        
        self.restoreState()

# -------------------------------------------------------------------------
# 2. LaTeX to ReportLab Flowable Renderer
# -------------------------------------------------------------------------
def latex_to_flowable(latex_str, scale=0.6, dpi=200):
    """
    Renders a LaTeX string into an in-memory transparent PNG using Matplotlib,
    and returns a ReportLab Image flowable. Gracefully falls back to Paragraph
    in case of any failures.
    """
    try:
        import matplotlib
        matplotlib.use('Agg')  # Force non-interactive backend
        import matplotlib.pyplot as plt
        
        # Clean up double backslashes which can happen in raw string transfers
        clean_str = latex_str.replace('\\\\', '\\')
        if not clean_str.startswith('$'):
            clean_str = f"${clean_str}$"
            
        # Render LaTeX into a matplotlib figure
        fig, ax = plt.subplots(figsize=(8, 0.8))
        ax.axis('off')
        
        # Using Helvetica-like sans-serif font for math equations for a modern clean look
        matplotlib.rcParams['mathtext.fontset'] = 'dejavusans'
        
        ax.text(0.5, 0.5, clean_str, fontsize=12, ha='center', va='center', color='#1e3a8a')
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=dpi, bbox_inches='tight', transparent=True, pad_inches=0.05)
        plt.close(fig)
        buf.seek(0)
        
        # Get dimensions with Pillow to scale correctly in ReportLab
        img = PILImage.open(buf)
        width, height = img.size
        
        width_pt = (width / dpi) * 72 * scale
        height_pt = (height / dpi) * 72 * scale
        
        buf.seek(0)
        return RLImage(buf, width=width_pt, height=height_pt)
    except Exception as e:
        # Graceful text fallback if matplotlib fails
        styles = getSampleStyleSheet()
        fallback_style = ParagraphStyle(
            'MathFallback',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=10,
            textColor=colors.HexColor("#1e3a8a"),
            leftIndent=20
        )
        return Paragraph(f"Formula Fallback: {latex_str}", fallback_style)

# -------------------------------------------------------------------------
# 3. PDF Generator Function
# -------------------------------------------------------------------------
def generate_report(test_results, assumptions_results=None, output_filename="ab_test_report.pdf"):
    """
    Orchestrates the creation of the PDF report using the State-Plan-Do-Conclude format.
    """
    # Setup document template with 0.75-inch (54 pt) margins
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    story = []
    
    # Define Color Palette
    primary_color = colors.HexColor("#1e3a8a")    # Deep Navy
    secondary_color = colors.HexColor("#0d9488")  # Teal
    dark_neutral = colors.HexColor("#1f2937")     # Slate Gray
    light_neutral = colors.HexColor("#f9fafb")    # Off-white
    border_color = colors.HexColor("#e5e7eb")     # Light gray
    accent_green = colors.HexColor("#10b981")     # Emerald Green
    accent_red = colors.HexColor("#ef4444")       # Coral Red

    # Setup Typography Styles
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'ReportTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=22, leading=26, textColor=primary_color, spaceAfter=8
    )
    subtitle_style = ParagraphStyle(
        'ReportSub', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=14, textColor=colors.HexColor("#4b5563"), spaceAfter=18
    )
    h1_style = ParagraphStyle(
        'SectionHeading', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=14, leading=18, textColor=primary_color, spaceBefore=12, spaceAfter=8, keepWithNext=True
    )
    h2_style = ParagraphStyle(
        'SubSectionHeading', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=11, leading=15, textColor=secondary_color, spaceBefore=8, spaceAfter=4, keepWithNext=True
    )
    body_style = ParagraphStyle(
        'BodyTextCustom', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=14, textColor=dark_neutral, spaceAfter=8
    )
    bullet_style = ParagraphStyle(
        'BulletCustom', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=14, textColor=dark_neutral, leftIndent=15, spaceAfter=4
    )
    callout_bold_style = ParagraphStyle(
        'CalloutBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, leading=14, textColor=primary_color
    )
    callout_body_style = ParagraphStyle(
        'CalloutBody', parent=styles['Normal'], fontName='Helvetica', fontSize=9.5, leading=13.5, textColor=dark_neutral
    )

    # Helper function for drawing horizontal rules
    def get_divider():
        t = Table([[""]], colWidths=[504], rowHeights=[2])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), primary_color),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
        ]))
        return t

    # Helper function for Callout Boxes
    def make_callout(bold_text, text, bg_color="#f0f9ff", border_color="#bae6fd"):
        content = [
            Paragraph(bold_text, callout_bold_style),
            Spacer(1, 4),
            Paragraph(text, callout_body_style)
        ]
        t = Table([[content]], colWidths=[504])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor(bg_color)),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor(border_color)),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 12),
            ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ]))
        return t

    # -------------------------------------------------------------------------
    # Title Block
    # -------------------------------------------------------------------------
    story.append(Paragraph("Statistical Inference & Hypothesis Testing Report", title_style))
    date_str = datetime.date.today().strftime("%B %d, %Y")
    story.append(Paragraph(f"<b>Analyst:</b> Portfolio Toolkit | <b>Date:</b> {date_str} | <b>Framework:</b> AP Statistics Standard", subtitle_style))
    story.append(get_divider())
    story.append(Spacer(1, 15))

    # -------------------------------------------------------------------------
    # PART 1: STATE
    # -------------------------------------------------------------------------
    story.append(Paragraph("1. State", h1_style))
    story.append(Paragraph("Define the hypotheses and significance level to evaluate the claims of the A/B test.", body_style))
    
    formulas = test_results.get("formulas", {})
    
    # Create hypothesis info
    h_latex = formulas.get("hypothesis", "")
    hyp_img = latex_to_flowable(h_latex)
    
    story.append(Paragraph(f"<b>Significance Level (&alpha;):</b> {test_results.get('alpha', 0.05)}", body_style))
    story.append(Paragraph("<b>Hypotheses (Symbols):</b>", body_style))
    story.append(hyp_img)
    story.append(Spacer(1, 6))
    
    # Hypothesis in words
    test_name = test_results.get("test_name", "")
    if "Proportion" in test_name:
        words = "<b>Null Hypothesis (H<sub>0</sub>):</b> There is no difference in the conversion rates between Group A and Group B (p<sub>A</sub> = p<sub>B</sub>).<br/>" \
                "<b>Alternative Hypothesis (H<sub>a</sub>):</b> There is a statistically significant difference in the conversion rates between Group A and Group B (p<sub>A</sub> &ne; p<sub>B</sub>)."
    elif "T-Test" in test_name:
        words = "<b>Null Hypothesis (H<sub>0</sub>):</b> There is no difference in the means of the metrics between Group A and Group B (&mu;<sub>A</sub> = &mu;<sub>B</sub>).<br/>" \
                "<b>Alternative Hypothesis (H<sub>a</sub>):</b> There is a statistically significant difference in the means of the metrics between Group A and Group B (&mu;<sub>A</sub> &ne; &mu;<sub>B</sub>)."
    elif "Chi-Square" in test_name:
        words = "<b>Null Hypothesis (H<sub>0</sub>):</b> The categorical variables are independent; the distribution of responses is similar across groups.<br/>" \
                "<b>Alternative Hypothesis (H<sub>a</sub>):</b> The categorical variables are dependent; the distribution of responses is significantly different across groups."
    else:
        words = "<b>Null Hypothesis (H<sub>0</sub>):</b> The distributions of both groups are identical.<br/>" \
                "<b>Alternative Hypothesis (H<sub>a</sub>):</b> There is a systematic difference in values between the two groups."
                
    story.append(Paragraph(words, body_style))
    story.append(Spacer(1, 12))

    # -------------------------------------------------------------------------
    # PART 2: PLAN
    # -------------------------------------------------------------------------
    story.append(Paragraph("2. Plan", h1_style))
    story.append(Paragraph(f"Identify the appropriate statistical procedure and verify its mathematical assumptions.", body_style))
    story.append(Paragraph(f"<b>Recommended Procedure:</b> {test_results.get('test_name')}", body_style))
    
    # Determine assumptions & check conditions
    conditions_summary = []
    conditions_met = True
    
    if "Proportion" in test_name:
        # Success-Failure condition check
        g_a = test_results.get("group_a", {})
        g_b = test_results.get("group_b", {})
        
        suc_a, n_a = g_a.get("successes", 0), g_a.get("n", 1)
        suc_b, n_b = g_b.get("successes", 0), g_b.get("n", 1)
        fail_a = n_a - suc_a
        fail_b = n_b - suc_b
        
        cond_a_ok = (suc_a >= 10) and (fail_a >= 10)
        cond_b_ok = (suc_b >= 10) and (fail_b >= 10)
        
        sf_text = f"Group A successes ({suc_a}) & failures ({fail_a}) &ge; 10? {'<b>Yes</b>' if cond_a_ok else '<b>No</b>'}. " \
                  f"Group B successes ({suc_b}) & failures ({fail_b}) &ge; 10? {'<b>Yes</b>' if cond_b_ok else '<b>No</b>'}."
        
        conditions_summary.append(("Randomness", "Assuming samples are collected via independent random selection."))
        conditions_summary.append(("Independence", "Samples represent less than 10% of their respective target populations."))
        conditions_summary.append(("Success-Failure Condition", sf_text))
        
        conditions_met = cond_a_ok and cond_b_ok
        
    elif "T-Test" in test_name or "Mann-Whitney" in test_name:
        # Normality and variance diagnostics
        conditions_summary.append(("Randomness", "Assuming independent random sampling/assignment of groups."))
        conditions_summary.append(("Independence", "Samples are mutually independent and represent < 10% of population."))
        
        if assumptions_results:
            norm_a = assumptions_results["group_a_normality"]
            norm_b = assumptions_results["group_b_normality"]
            homo = assumptions_results["variance_equality"]
            
            norm_text = f"Group A Normality (p = {norm_a['p_value']:.4f}, {'Passed' if norm_a['shapiro_normal'] else 'Failed'}). " \
                        f"Group B Normality (p = {norm_b['p_value']:.4f}, {'Passed' if norm_b['shapiro_normal'] else 'Failed'})."
            
            if norm_a["normal"] and norm_b["normal"]:
                norm_text += " Normality met."
            else:
                norm_text += " Normality met via CLT (Sample sizes >= 30)." if (norm_a["normal"] and norm_b["normal"]) else " Normality assumptions NOT fully met."
                
            conditions_summary.append(("Normality (Shapiro-Wilk)", norm_text))
            
            var_text = f"Levene's Test for equal variance: p = {homo['p_value']:.4f} ({'Equal variances assumed' if homo['equal_var'] else 'Unequal variances assumed'})."
            conditions_summary.append(("Equal Variance (Levene's)", var_text))
            
            conditions_met = norm_a["normal"] and norm_b["normal"]
        else:
            conditions_summary.append(("Normality check", "Shapiro-Wilk normality diagnostics skipped."))
            conditions_summary.append(("Variance check", "Levene's homogeneity diagnostics skipped."))
            
    elif "Chi-Square" in test_name:
        conditions_summary.append(("Randomness", "Categorical frequencies collected from random sampling."))
        conditions_summary.append(("Independence", "Observations represent mutually exclusive categorical responses."))
        
        # Expected Cell Counts check (all expected counts >= 5)
        expected = test_results.get("expected", [])
        expected_flat = [val for row in expected for val in row]
        exp_ok = all(val >= 5 for val in expected_flat)
        min_exp = min(expected_flat) if expected_flat else 0
        
        ec_text = f"All expected cell counts &ge; 5? {'<b>Yes</b>' if exp_ok else '<b>No</b>'} (Minimum expected cell count = {min_exp:.2f})."
        conditions_summary.append(("Large Sample (Expected counts)", ec_text))
        
        conditions_met = exp_ok

    # Build standard table of conditions
    cond_data = [["Assumption / Condition Checked", "Status & Diagnostic Details"]]
    for title, detail in conditions_summary:
        cond_data.append([
            Paragraph(f"<b>{title}</b>", body_style),
            Paragraph(detail, body_style)
        ])
        
    cond_table = Table(cond_data, colWidths=[150, 354])
    cond_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), secondary_color),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ('BACKGROUND', (0,1), (-1,-1), light_neutral),
    ]))
    
    story.append(cond_table)
    story.append(Spacer(1, 8))
    
    # Diagnostic Callout Box
    if conditions_met:
        story.append(make_callout(
            " CONDITIONS MET",
            f"All mathematical conditions for the {test_name} are satisfied. Parametric results are highly reliable.",
            bg_color="#ecfdf5", border_color="#a7f3d0"
        ))
    else:
        rec_test = assumptions_results.get("recommended_test", "Non-parametric alternative") if assumptions_results else "a non-parametric test"
        story.append(make_callout(
            " ASSUMPTION VIOLATION ENCOUNTERED",
            f"Some statistical conditions are violated. The tool automatically routed/recommends using {rec_test} to ensure robust inference.",
            bg_color="#fffbef", border_color="#fef3c7"
        ))
    story.append(Spacer(1, 12))

    # -------------------------------------------------------------------------
    # PART 3: DO
    # -------------------------------------------------------------------------
    story.append(Paragraph("3. Do", h1_style))
    story.append(Paragraph("Calculate sample metrics, standard error, test statistic, and the resulting p-value.", body_style))
    
    # Summary stats table
    story.append(Paragraph("<b>Sample Descriptive Statistics:</b>", h2_style))
    
    if "Proportion" in test_name:
        stats_data = [
            ["Group", "Sample Size (n)", "Successes (x)", "Conversion Rate (p̂)"],
            ["Group A", f"{g_a['n']}", f"{g_a['successes']}", f"{g_a['rate']:.4%}"],
            ["Group B", f"{g_b['n']}", f"{g_b['successes']}", f"{g_b['rate']:.4%}"]
        ]
        stats_table = Table(stats_data, colWidths=[120, 128, 128, 128])
    elif "T-Test" in test_name:
        g_a = test_results.get("group_a", {})
        g_b = test_results.get("group_b", {})
        stats_data = [
            ["Group", "Sample Size (n)", "Sample Mean (x̄)", "Standard Deviation (s)", "Variance (s²)"],
            ["Group A", f"{g_a['n']}", f"{g_a['mean']:.4f}", f"{g_a['std_dev']:.4f}", f"{g_a['variance']:.4f}"],
            ["Group B", f"{g_b['n']}", f"{g_b['mean']:.4f}", f"{g_b['std_dev']:.4f}", f"{g_b['variance']:.4f}"]
        ]
        stats_table = Table(stats_data, colWidths=[100, 101, 101, 101, 101])
    elif "Chi-Square" in test_name:
        obs = test_results.get("observed", [])
        exp = test_results.get("expected", [])
        
        # Build flat observed vs expected metrics table
        stats_data = [["Cell Index (Row, Col)", "Observed Count (O)", "Expected Count (E)", "Residual Contribution (O-E)²/E"]]
        for i in range(len(obs)):
            for j in range(len(obs[i])):
                o_val = obs[i][j]
                e_val = exp[i][j]
                contrib = ((o_val - e_val)**2 / e_val) if e_val > 0 else 0
                stats_data.append([
                    f"Row {i+1}, Col {j+1}",
                    f"{o_val}",
                    f"{e_val:.2f}",
                    f"{contrib:.4f}"
                ])
        stats_table = Table(stats_data, colWidths=[150, 118, 118, 118])
    else: # Mann-Whitney
        g_a = test_results.get("group_a", {})
        g_b = test_results.get("group_b", {})
        stats_data = [
            ["Group", "Sample Size (n)", "Median Value"],
            ["Group A", f"{g_a['n']}", f"{g_a['median']:.4f}"],
            ["Group B", f"{g_b['n']}", f"{g_b['median']:.4f}"]
        ]
        stats_table = Table(stats_data, colWidths=[150, 177, 177])

    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, light_neutral]),
    ]))
    
    story.append(stats_table)
    story.append(Spacer(1, 10))
    
    # Math Calculations & Formulas
    story.append(Paragraph("<b>Calculations & Mathematical Formulations:</b>", h2_style))
    
    # Add step-by-step formula images
    for name, f_str in formulas.items():
        if name != "hypothesis":
            story.append(Paragraph(f"• <i>{name.replace('_', ' ').title()}</i>:", body_style))
            story.append(latex_to_flowable(f_str))
            story.append(Spacer(1, 4))
            
    story.append(Spacer(1, 6))

    # Core statistics results table
    res_data = [
        ["Statistical Parameter", "Value"],
        [f"Test Statistic ({'Z' if 'Z-Test' in test_name else 't' if 'T-Test' in test_name else 'U' if 'Mann-Whitney' in test_name else 'χ²'})", f"{test_results.get('statistic', 0.0):.5f}"],
        ["p-value", f"{test_results.get('p_value', 1.0):.5e}" if test_results.get('p_value', 1.0) < 0.0001 else f"{test_results.get('p_value', 1.0):.5f}"]
    ]
    
    if "degrees_of_freedom" in test_results:
        res_data.append(["Degrees of Freedom (df)", f"{test_results.get('degrees_of_freedom'):.2f}" if isinstance(test_results.get('degrees_of_freedom'), float) else f"{test_results.get('degrees_of_freedom')}"])
        
    if "ci_lower" in test_results:
        ci_text = f"({test_results.get('ci_lower'):.4f}, {test_results.get('ci_upper'):.4f})"
        res_data.append([f"{(1-test_results.get('alpha', 0.05))*100:.0f}% Confidence Interval", ci_text])
        
    res_table = Table(res_data, colWidths=[250, 254])
    res_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), secondary_color),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ('BACKGROUND', (0,1), (-1,-1), light_neutral),
    ]))
    
    story.append(res_table)
    story.append(Spacer(1, 15))

    # -------------------------------------------------------------------------
    # PART 4: CONCLUDE
    # -------------------------------------------------------------------------
    story.append(Paragraph("4. Conclude", h1_style))
    story.append(Paragraph("State the final decision and offer a business interpretation based on the statistical results.", body_style))
    
    p_val = test_results.get("p_value", 1.0)
    alpha = test_results.get("alpha", 0.05)
    reject = test_results.get("reject_h0", False)
    
    decision_text = f"Compare p-value to &alpha;: {p_val:.5f} {'<' if reject else '>='} {alpha}. "
    if reject:
        decision_text += "Since the p-value is less than the significance level, we <b>reject the null hypothesis (H<sub>0</sub>)</b>. " \
                         "There is strong evidence supporting a statistically significant difference between the two variations."
        conclude_box_title = " DECISION: REJECT NULL HYPOTHESIS"
        conclude_box_color = "#fef2f2" # Light Red
        conclude_box_border = "#fecaca"
    else:
        decision_text += "Since the p-value is greater than or equal to the significance level, we <b>fail to reject the null hypothesis (H<sub>0</sub>)</b>. " \
                         "There is insufficient evidence to conclude there is a significant difference between the variations."
        conclude_box_title = " DECISION: FAIL TO REJECT NULL HYPOTHESIS"
        conclude_box_color = "#f3f4f6" # Light Gray
        conclude_box_border = "#e5e7eb"

    # Business impact description
    if "Proportion" in test_name:
        diff_rate = test_results.get("difference", 0.0)
        if reject:
            better_group = "Group B" if diff_rate > 0 else "Group A"
            impact_text = f"<b>Business Action Recommendation:</b> The conversion rate difference of {abs(diff_rate):.2%} is statistically significant. " \
                          f"Deploy <b>{better_group}</b> to production, as it is expected to generate a permanent uplift in performance."
        else:
            impact_text = "<b>Business Action Recommendation:</b> The observed difference in conversion rates could be due to random chance. " \
                          "Maintain the current control group (Group A) or extend the experiment to gather more data before implementing changes."
    elif "T-Test" in test_name or "Mann-Whitney" in test_name:
        diff_mean = test_results.get("difference", 0.0)
        if reject:
            better_group = "Group B" if diff_mean > 0 else "Group A"
            impact_text = f"<b>Business Action Recommendation:</b> The metric difference of {diff_mean:.4f} is statistically significant. " \
                          f"Variation <b>{better_group}</b> outperforms the other and should be adopted to maximize efficiency/revenue."
        else:
            impact_text = "<b>Business Action Recommendation:</b> There is no statistically detectable difference in performance. " \
                          "The variations perform identically on average. We recommend choosing the option that has lower maintenance costs or better UX."
    else:
        if reject:
            impact_text = "<b>Business Action Recommendation:</b> The frequencies are dependent. A significant association exists. " \
                          "The user segments show distinct preference profiles across variants. Tailor features/marketing to specific segments."
        else:
            impact_text = "<b>Business Action Recommendation:</b> No significant association was detected. " \
                          "User distributions are statistically homogeneous across groups. Standardize the layout/offering."

    story.append(Paragraph(decision_text, body_style))
    story.append(Spacer(1, 8))
    story.append(make_callout(
        conclude_box_title,
        impact_text,
        bg_color=conclude_box_color,
        border_color=conclude_box_border
    ))
    
    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)

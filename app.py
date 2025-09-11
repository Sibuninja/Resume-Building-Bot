# Import necessary libraries
from flask import Flask, render_template, request, jsonify, session, send_file
import groq
import json
from fpdf import FPDF
from dotenv import load_dotenv
import os
import re
import datetime
import subprocess, shlex, traceback
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import html
import datetime


# Load .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback_secret")

# Use Groq API key from .env
client = groq.Client(api_key=os.getenv("GROQ_API_KEY"))


def rr_escape(text: str) -> str:
    if text is None:
        return ""
    s = str(text)
    return html.escape(s).replace('\n', '<br/>')

questions = [
    "Hi there! I'm ResumeBot. Let's build your resume! What is your name?",
    "Great! What is your email?",
    "Now, tell me about your education. What is your course?",
    "Which college did you study at for this course?",
    "What year did you complete it?",
    "Would you like to add another education detail? (yes/no)",
    "Now, let's talk about your skills. Enter a main skill:",
    "Here are 10 related sub-skills. Select the ones you have (comma-separated):",
    "Would you like to add another main skill? (yes/no)",
    "Do you have any certifications? (yes/no)",
    "Enter the certificate name:",
    "Enter the certificate ID:",
    "Where did you get this certification from?",
    "Would you like to add another certification? (yes/no)",
    "Tell me about your projects. What is the project name?",
    "Provide a brief description of the project:",
    "Enter the project repository link:",
    "Would you like to add another project? (yes/no)",
    "All done! Generating your resume now..."
]
resume_examples = """
    Example Resume 1:
    
    ------------------------------
    Name: John Doe
    Email: johndoe@example.com
    Phone: +91 9876543210
    LinkedIn: linkedin.com/in/johndoe
    GitHub: github.com/johndoe
    ------------------------------

    **About Me**  
    A passionate software developer skilled in Python, Django, and full-stack web development. I enjoy building scalable applications and solving real-world problems through technology.

    **Education**  
    - Bachelor of Computer Applications, XYZ University (2022-2025)  

    **Skills**  
    - Programming: Python, Java, C++  
    - Web Development: HTML, CSS, JavaScript, Django  
    - Tools: Git, Docker, Postman  

    **Certifications**  
    - Google Cybersecurity Certificate (ID: GCS12345)  
    - CompTIA Security+ (ID: XYZ12345)  

    **Projects**  
    - **AI Resume Generator** - Built a chatbot-powered resume builder using Flask and Groq API.  
    - **E-commerce Website** - Developed a full-stack e-commerce site with Django.  

    ------------------------------
    
    Example Resume 2:
    
    ------------------------------
    Name: Jane Smith  
    Email: janesmith@example.com  
    Phone: +91 8765432109  
    LinkedIn: linkedin.com/in/janesmith  
    GitHub: github.com/janesmith  
    ------------------------------

    **About Me**  
    Data Science enthusiast with a strong foundation in machine learning, deep learning, and data visualization. Passionate about leveraging AI for impactful solutions.

    **Education**  
    - Master of Data Science, ABC University (2020-2022)  

    **Skills**  
    - Data Science: Machine Learning, Deep Learning, NLP  
    - Programming: Python, R, SQL  
    - Tools: TensorFlow, Scikit-Learn, Power BI  

    **Certifications**  
    - Microsoft AI Engineer Certificate (ID: AIENG456)  
    - AWS Certified Data Analyst (ID: AWSDA789)  

    **Projects**  
    - **Chatbot for Customer Support** - Created an NLP-based chatbot to handle queries.  
    - **Stock Price Prediction** - Used ML models to predict stock prices.  

    ------------------------------
    """
@app.route('/')
def index():
    session.clear()  
    session['step'] = 0
    session['data'] = {
        "name": "",
        "email": "",
        "education": [],
        "skills": [],
        "certifications": [],
        "projects": []
    }
    return render_template('chatbot.html')

@app.route('/chat', methods=['POST'])
def chat():
    raw_input = request.json.get('message', '')
    if raw_input is None:
        raw_input = ""
    raw_input = raw_input.strip()
    user_input = raw_input.lower()   # use only for yes/no decisions

    step = session.get('step', 0)
    data = session.get('data', {})

    if not user_input:
        return jsonify({"question": "Please enter a valid response."})

    if step == 0:
        data['name'] = user_input
    elif step == 1:
        data['email'] = user_input
    elif step == 2:
        data['education'].append({"course": user_input})
    elif step == 3:
        data['education'][-1]['college'] = user_input
    elif step == 4:
        data['education'][-1]['year'] = user_input
    elif step == 5:  
        if user_input == 'no':
            session['step'] = 6
            return jsonify({"question": questions[6]})  
        else:
            session['step'] = 2  
            return jsonify({"question": questions[2]})

    elif step == 6:  
        data['skills'].append({"mainskill": user_input})

        
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": f"Generate a list of 10 related sub-skills for {user_input}. Return only a comma-separated list."},
                {"role": "user", "content": user_input}
            ]
        )
        
        subskills_raw = response.choices[0].message.content.strip()
        subskills = subskills_raw.split(", ")

        session['step'] = 7  
        return jsonify({"question": "Here are 10 related sub-skills. Select the ones you have (comma-separated):", "subskills": subskills})

    elif step == 7:  
        data['skills'][-1]['subskills'] = user_input.split(',')
        session['step'] = 8
        return jsonify({"question": "Would you like to add another main skill? (yes/no)"})

    elif step == 8:  
        if user_input == 'yes':
            session['step'] = 6  
            return jsonify({"question": "Enter another main skill:"})
        else:
            session['step'] = 9  
            return jsonify({"question": questions[9]})

    elif step == 9:  
        if user_input == 'yes':
            session['step'] = 10
            return jsonify({"question": questions[10]})  
        else:
            session['step'] = 14  
            return jsonify({"question": questions[14]})

    elif step == 10:  
        data['certifications'].append({"name": user_input})  
        session['step'] = 11
        return jsonify({"question": questions[11]})

    elif step == 11:  
        if not data['certifications']:  
            return jsonify({"question": "Error: Please enter the certificate name first."})
        data['certifications'][-1]['id'] = user_input
        session['step'] = 12
        return jsonify({"question": questions[12]})

    elif step == 12:  
        if not data['certifications']: 
            return jsonify({"question": "Error: Please enter the certificate name first."})
        data['certifications'][-1]['source'] = user_input
        session['step'] = 13
        return jsonify({"question": questions[13]})

    elif step == 13:  
        if user_input == 'no':
            session['step'] = 14
            return jsonify({"question": questions[14]})  
        else:
            session['step'] = 10  
            return jsonify({"question": questions[10]})
    elif step == 14:  
        data['projects'].append({"name": user_input})  
        session['step'] = 15
        return jsonify({"question": questions[15]})

    elif step == 15:  
        if not data['projects']:  
            return jsonify({"question": "Error: Please enter the project name first."})
        data['projects'][-1]['description'] = user_input
        session['step'] = 16
        return jsonify({"question": questions[16]})

    elif step == 16:  
        if not data['projects']:  
            return jsonify({"question": "Error: Please enter the project name first."})
        data['projects'][-1]['technologies'] = user_input.split(", ")
        session['step'] = 17
        return jsonify({"question": questions[17]})

    elif step == 17: 
        if user_input == 'no':
            session['step'] = 18  
            return jsonify({"question": questions[18]})  
        else:
            session['step'] = 14  
            return jsonify({"question": questions[14]})

    session['step'] += 1
    session['data'] = data
    return jsonify({"question": questions[session['step']]})



def latex_escape(text: str) -> str:
    if text is None: return ""
    s = str(text)
    s = s.replace("\\", r"\textbackslash{}")
    # escape common latex specials
    for a,b in [('&', r'\&'),('%', r'\%'),('$', r'\$'),('#', r'\#'),('_', r'\_'),
                ('{', r'\{'),('}', r'\}'),('~', r'\textasciitilde{}'),('^', r'\^{}'),
                ('<', r'\textless{}'),('>', r'\textgreater{}')]:
        s = s.replace(a,b)
    return s

def build_latex_from_data(data: dict) -> str:
    # Gather fields (use original casing when available)
    name = latex_escape(data.get('name','')).upper()
    email = latex_escape(data.get('email',''))
    phone = latex_escape(data.get('phone',''))
    linkedin = latex_escape(data.get('linkedin',''))
    github = latex_escape(data.get('github',''))
    location = latex_escape(data.get('location',''))

    # professional summary: build a short automated summary or allow model-generated summary stored in data
    prof_summary = latex_escape(data.get('professional_summary', ''))
    if not prof_summary:
        parts = []
        if data.get('education'):
            e = data['education'][0]
            if e.get('course'): parts.append(f"{e.get('course')} graduate")
            if e.get('college'): parts.append(f"from {e.get('college')}")
        if data.get('skills'):
            tops = [s.get('mainskill','') for s in data.get('skills',[])][:3]
            tops = [t for t in tops if t]
            if tops: parts.append("Skills: " + ", ".join(tops))
        if data.get('projects'):
            pnames = [p.get('name','') for p in data.get('projects',[])][:2]
            if pnames: parts.append("Projects: " + ", ".join(pnames))
        prof_summary = latex_escape(" . ".join(parts) or "Computer Science graduate with practical experience in software and AI projects.")

    # Build skills table rows
    skills_rows = []
    for s in data.get('skills', []):
        ms = latex_escape(s.get('mainskill',''))
        subs = s.get('subskills') or []
        subs_str = ", ".join([latex_escape(x) for x in subs])
        if ms:
            skills_rows.append((ms, subs_str))

    # Education
    edu_lines = []
    for e in data.get('education', []):
        ct = latex_escape(e.get('course',''))
        clg = latex_escape(e.get('college',''))
        yr = latex_escape(e.get('year',''))
        edu_lines.append((ct, clg, yr))

    # Projects
    project_blocks = []
    for p in data.get('projects', []):
        pname = latex_escape(p.get('name',''))
        pdesc = latex_escape(p.get('description','') or "")
        repo = latex_escape(p.get('repository','') or "")
        techs = p.get('technologies') or []
        techs_str = ", ".join([latex_escape(t) for t in techs]) if techs else ""
        project_blocks.append({'name':pname,'desc':pdesc,'repo':repo,'techs':techs_str})

    # Certifications
    certs = []
    for c in data.get('certifications', []):
        cname = latex_escape(c.get('name',''))
        cid = latex_escape(c.get('id',''))
        src = latex_escape(c.get('source',''))
        certs.append((cname,cid,src))

    # Build contact lines (use tel/mail/link if present)
    contact_parts = []
    if location: contact_parts.append(location)
    if phone: contact_parts.append(r"\href{tel:+%s}{%s}" % (re.sub(r'\D','', phone), phone))
    if email: contact_parts.append(r"\href{mailto:%s}{%s}" % (email, email))
    contact_line = " \\quad | \\quad ".join(contact_parts)

    links = []
    if linkedin: links.append(r"\href{%s}{LinkedIn}" % linkedin)
    if github: links.append(r"\href{%s}{GitHub}" % github)
    links_line = " \\quad | \\quad ".join(links)

    # LaTeX template (clean, professional)
    # NOTE: percent signs in template are left as-is because we're building with concatenation (no % formatting)
    latex = r"""\documentclass[letterpaper,10pt]{article}
\usepackage[dvipsnames]{xcolor}
\usepackage[hidelinks]{hyperref}
\usepackage{tabularx}
\usepackage{geometry}
\usepackage{titlesec}
\usepackage{enumitem}
\usepackage{fancyhdr}
\usepackage[default]{lato}
\usepackage{parskip}
\usepackage{multicol}
\hypersetup{colorlinks=true,urlcolor=blue}
\geometry{left=0.6in, top=0.5in, right=0.6in, bottom=0.5in}
\pagestyle{fancy}
\fancyhf{}
\renewcommand{\headrulewidth}{0pt}
\titleformat{\section}{\large\bfseries\color{MidnightBlue}\uppercase}{}{0em}{}[\titlerule]
\titlespacing{\section}{0pt}{6pt}{3pt}
\setlength{\parskip}{0pt}
\setlength{\itemsep}{2pt}
\newcommand{\resumeItem}[1]{\item #1}
\newcommand{\resumeListStart}{\begin{itemize}[leftmargin=*,noitemsep,topsep=0pt]}
\newcommand{\resumeListEnd}{\end{itemize}}
\begin{document}
"""
    # Header
    latex += "\\begin{center}\n"
    latex += "  {\\LARGE \\textbf{" + name + "}} \\\\\n"
    if contact_line:
        latex += "  " + contact_line + " \\\\\n"
    if links_line:
        latex += "  " + links_line + " \n"
    latex += "\\end{center}\n\n"

    # Summary
    latex += "\\section*{PROFESSIONAL SUMMARY}\n" + prof_summary + "\n\n"

    # Core skills with tabularx
    latex += "\\section*{CORE SKILLS}\n\\begin{tabularx}{\\textwidth}{@{} l X @{} }\n"
    # default content (you can replace with dynamic categories if preferred)
    latex += "  \\textbf{Languages:} & Python, C++, Java, JavaScript, HTML/CSS \\\\\n"
    latex += "  \\textbf{Frameworks:} & Hugging Face, TensorFlow, PyTorch, React Native, OpenCV \\\\\n"
    latex += "  \\textbf{Tools:} & Git, Docker, VS Code, Firebase, Streamlit, Gradio, Postman \\\\\n"
    latex += "\\end{tabularx}\n\n"

    # Projects
    if project_blocks:
        latex += "\\section*{KEY PROJECTS}\n"
        for p in project_blocks:
            repo_text = f" \\href{{{p['repo']}}}{{[Repo]}}" if p['repo'] else ""
            latex += "\\textbf{" + p['name'] + "}" + repo_text + " \\\\\n"
            if p['techs']: latex += "\\textit{" + p['techs'] + "}\\\\\n"
            if p['desc']:
                latex += "\\resumeListStart\n"
                latex += f"  \\resumeItem{{{p['desc']}}}\n"
                latex += "\\resumeListEnd\n\n"

    # Education
    if edu_lines:
        latex += "\\section*{EDUCATION}\n"
        for ct, clg, yr in edu_lines:
            latex += "\\textbf{" + ct + "} \\hfill " + yr + " \\\\\n"
            if clg:
                latex += clg + " \\\\\n"
        latex += "\n"

    # Certifications
    if certs:
        latex += "\\section*{CERTIFICATIONS}\n\\resumeListStart\n"
        for cname, cid, src in certs:
            line = cname
            if cid: line += " (ID: " + cid + ")"
            if src and src.startswith("http"):
                line += f" \\href{{{src}}}{{[Cert]}}"
            latex += f"  \\resumeItem{{{line}}}\n"
        latex += "\\resumeListEnd\n\n"

    latex += "\\end{document}\n"
    return latex

# GENERATE route replacement
@app.route('/generate')
def generate_resume():
    data = session.get('data', {})
    if not data:
        return "No resume data found in session. Start the chat to build your resume.", 400

    static_dir = os.path.join(app.root_path, 'static')
    os.makedirs(static_dir, exist_ok=True)
    user_name = data.get("name", "resume").strip().replace(" ", "_")
    ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    pdf_name = f"{user_name}_Resume_{ts}.pdf"
    pdf_path = os.path.join(static_dir, pdf_name)


    # Document setup
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=0.6*inch,
        rightMargin=0.6*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )

    styles = getSampleStyleSheet()
    # Custom styles
    header_style = ParagraphStyle(
        "Header",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        alignment=1,  # center
        spaceAfter=6,
    )
    contact_style = ParagraphStyle(
        "Contact",
        parent=styles["Normal"],
        fontSize=9,
        alignment=1,  # center
        textColor=colors.grey,
        spaceAfter=10
    )
    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=colors.HexColor('#0b5394'),  # navy-ish
        spaceBefore=10,
        spaceAfter=6,
        leading=14,
        leftIndent=0
    )
    normal = ParagraphStyle(
        "NormalText",
        parent=styles["Normal"],
        fontSize=10,
        leading=12,
    )
    bullet_style = ParagraphStyle(
        "Bullet",
        parent=styles["Normal"],
        fontSize=10,
        leftIndent=12,
        bulletIndent=6,
        leading=12,
    )

    story = []

    # Header: Name
    name = rr_escape(data.get('name', '')).upper()
    story.append(Paragraph(name, header_style))

    # Contact line
    contact_items = []
    if data.get('location'):
        contact_items.append(rr_escape(data.get('location')))
    if data.get('phone'):
        contact_items.append(rr_escape(data.get('phone')))
    if data.get('email'):
        contact_items.append(rr_escape(data.get('email')))
    contact_line = " \u2022 ".join(contact_items)  # bullet as separator
    if contact_line:
        story.append(Paragraph(contact_line, contact_style))

    # Links line (LinkedIn / GitHub) - displayed as plain text for compatibility
    links = []
    if data.get('linkedin'):
        links.append("LinkedIn: " + rr_escape(data.get('linkedin')))
    if data.get('github'):
        links.append("GitHub: " + rr_escape(data.get('github')))
    if links:
        story.append(Paragraph(" \u2022 ".join(links), contact_style))

    story.append(Spacer(1, 8))

    # Professional summary
    prof = data.get('professional_summary') or ""
    if not prof:
        # Auto-generate short summary from fields if not present
        parts = []
        if data.get('education'):
            e = data['education'][0]
            if e.get('course'):
                parts.append(f"{e.get('course')} graduate")
            if e.get('college'):
                parts.append(f"from {e.get('college')}")
        if data.get('skills'):
            tops = [s.get('mainskill','') for s in data.get('skills', [])][:3]
            tops = [t for t in tops if t]
            if tops:
                parts.append("Skills: " + ", ".join(tops))
        if data.get('projects'):
            pnames = [p.get('name','') for p in data.get('projects', [])][:2]
            pnames = [p for p in pnames if p]
            if pnames:
                parts.append("Projects: " + ", ".join(pnames))
        prof = ". ".join(parts) if parts else "Computer Science graduate with practical experience in software development and AI projects."
    story.append(Paragraph("<b>PROFESSIONAL SUMMARY</b>", section_heading))
    story.append(Paragraph(rr_escape(prof), normal))

    # Core skills (table style) - display mainskill: subskills
    story.append(Spacer(1, 6))
    story.append(Paragraph("<b>CORE SKILLS</b>", section_heading))
    skills = data.get('skills', [])
    if skills:
        table_data = []
        for sk in skills:
            ms = rr_escape(sk.get('mainskill',''))
            subs = sk.get('subskills') or []
            subs_str = rr_escape(", ".join(subs))
            table_data.append([Paragraph(f"<b>{ms}</b>", normal), Paragraph(subs_str, normal)])
        table = Table(table_data, colWidths=[1.6*inch, None], hAlign='LEFT')
        table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(table)
    else:
        story.append(Paragraph("No skills provided.", normal))

    # Projects
    projects = data.get('projects', [])
    if projects:
        story.append(Spacer(1, 6))
        story.append(Paragraph("<b>KEY PROJECTS</b>", section_heading))
        for p in projects:
            pname = rr_escape(p.get('name',''))
            ptech = ", ".join(p.get('technologies') or [])
            pdesc = rr_escape(p.get('description',''))
            hdr = pname + (f" — {rr_escape(ptech)}" if ptech else "")
            story.append(Paragraph(f"<b>{hdr}</b>", normal))
            if pdesc:
                # bullet-ish paragraph
                story.append(Paragraph(pdesc, bullet_style))
            # small spacer between projects
            story.append(Spacer(1,4))

    # Education
    edu = data.get('education', [])
    if edu:
        story.append(Spacer(1, 6))
        story.append(Paragraph("<b>EDUCATION</b>", section_heading))
        for e in edu:
            ct = rr_escape(e.get('course',''))
            clg = rr_escape(e.get('college',''))
            yr = rr_escape(e.get('year',''))
            left = f"<b>{ct}</b>"
            right = yr
            # render course + year then college beneath
            story.append(Paragraph(left + (f" \u2014 {right}" if right else ""), normal))
            if clg:
                story.append(Paragraph(clg, normal))
            story.append(Spacer(1,4))

    # Certifications
    certs = data.get('certifications', [])
    if certs:
        story.append(Spacer(1,6))
        story.append(Paragraph("<b>CERTIFICATIONS</b>", section_heading))
        for c in certs:
            cname = rr_escape(c.get('name',''))
            cid = rr_escape(c.get('id',''))
            src = rr_escape(c.get('source',''))
            line = cname
            if cid:
                line += f" (ID: {cid})"
            if src:
                line += f" — {src}"
            story.append(Paragraph(line, normal))
            story.append(Spacer(1,2))

    # finalize PDF
    try:
        doc.build(story)
    except Exception as e:
        print("ReportLab build error:", e)
        traceback.print_exc()
        return "Error generating PDF on server.", 500

    return send_file(pdf_path, as_attachment=True, download_name=pdf_name)


if __name__ == '__main__':
    app.run(debug=True)

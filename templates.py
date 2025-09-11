# templates.py
# Three resume templates (modern, classic, ATS-friendly).
# Each function accepts `data` dictionary and returns an HTML string.

import html


def _esc(v):
    """Safe HTML escape for values (handle None)."""
    if v is None:
        return ""
    return html.escape(str(v))


def _build_education_html(data):
    items = []
    for e in data.get("education", []):
        course = _esc(e.get("course", ""))
        college = _esc(e.get("college", ""))
        year = _esc(e.get("year", ""))
        if course or college or year:
            line = "<div class='edu-item'>"
            if course:
                line += f"<b>{course}</b>"
            if college:
                if course:
                    line += " — "
                line += f"{college}"
            if year:
                line += f" <span class='yr'>{year}</span>"
            line += "</div>"
            items.append(line)
    return "\n".join(items) if items else "<div>No education details provided.</div>"


def _build_skills_html(data):
    pills = []
    for s in data.get("skills", []):
        mainskill = _esc(s.get("mainskill", ""))
        subs = s.get("subskills", []) or []
        subs_text = ", ".join(_esc(x) for x in subs if x)
        if mainskill:
            pills.append(f"<div class='skill-pill'><b>{mainskill}</b>: {subs_text}</div>")
    return "\n".join(pills) if pills else "<div>No skills provided.</div>"


def _build_projects_html(data):
    blocks = []
    for p in data.get("projects", []):
        name = _esc(p.get("name", ""))
        desc = _esc(p.get("description", ""))
        repo = p.get("repository", "") or ""
        techs = p.get("technologies") or []
        techs_text = ", ".join(_esc(t) for t in techs if t)
        if name or desc:
            b = "<div class='project-item'>"
            if name:
                b += f"<div class='proj-name'><b>{name}</b>"
                if repo:
                    href = _esc(repo)
                    b += f" &nbsp;<a class='proj-link' href='{href}' target='_blank'>[Repo]</a>"
                b += "</div>"
            if techs_text:
                b += f"<div class='proj-tech'><em>{techs_text}</em></div>"
            if desc:
                b += f"<div class='proj-desc'>{desc}</div>"
            b += "</div>"
            blocks.append(b)
    return "\n".join(blocks) if blocks else "<div>No projects provided.</div>"


def _build_certs_html(data):
    items = []
    for c in data.get("certifications", []):
        name = _esc(c.get("name", ""))
        cid = _esc(c.get("id", ""))
        src = c.get("source", "") or ""
        line = "<div class='cert-item'>"
        if name:
            line += f"{name}"
        if cid:
            line += f" (ID: {cid})"
        if src:
            href = _esc(src)
            # display link if it looks like a URL
            if src.startswith("http"):
                line += f" &nbsp;<a href='{href}' target='_blank'>[Certificate]</a>"
            else:
                line += f" — {_esc(src)}"
        line += "</div>"
        items.append(line)
    return "\n".join(items) if items else "<div>No certifications listed.</div>"


# -------------------------
# Modern Template (HTML)
# -------------------------
def modern_template(data):
    """Return a modern HTML resume. data: dict"""
    name = _esc(data.get("name", "Your Name"))
    email = _esc(data.get("email", ""))
    phone = _esc(data.get("phone", ""))
    linkedin = _esc(data.get("linkedin", ""))
    github = _esc(data.get("github", ""))
    location = _esc(data.get("location", ""))

    contact_parts = [p for p in [location, phone, email] if p]
    contact_line = " &nbsp;•&nbsp; ".join(contact_parts)

    link_parts = []
    if linkedin:
        link_parts.append(f"<a href='{linkedin}' target='_blank'>LinkedIn</a>")
    if github:
        link_parts.append(f"<a href='{github}' target='_blank'>GitHub</a>")
    links_line = " &nbsp;•&nbsp; ".join(link_parts)

    prof = _esc(data.get("professional_summary", ""))

    education_html = _build_education_html(data)
    skills_html = _build_skills_html(data)
    projects_html = _build_projects_html(data)
    certs_html = _build_certs_html(data)

    css = (
        "<style>"
        "body { font-family: Arial, sans-serif; margin: 36px; color:#222; }"
        ".header { text-align:center; margin-bottom:6px; }"
        "h1 { color:#2E86C1; margin:0; font-size:26px; }"
        ".contact { color:#666; font-size:11px; margin-top:6px; }"
        ".links { color:#0b5394; font-size:11px; margin-top:4px; }"
        ".section { margin-top:18px; }"
        "h2 { color:#117A65; font-size:13px; margin-bottom:6px; border-bottom:1px solid #eaeaea; padding-bottom:6px; }"
        ".skill-pill { display:inline-block; background:#f0f6fb; color:#0b5394; padding:6px 10px; border-radius:12px; margin:4px; font-size:11px; }"
        ".project-item, .edu-item, .cert-item { margin-bottom:8px; }"
        ".proj-name { font-weight:bold; }"
        ".proj-link { color:#0b5394; text-decoration:none; font-size:11px; }"
        ".proj-tech { font-style:italic; color:#444; font-size:11px; margin-top:2px; }"
        ".proj-desc { margin-top:4px; }"
        ".yr { float:right; color:#444; }"
        "a { color:#0b5394; text-decoration:none; }"
        "</style>"
    )

    html_out = (
        "<!doctype html><html><head><meta charset='utf-8'/>"
        + css
        + "</head><body>"
        + "<div class='header'>"
        + f"<h1>{name}</h1>"
        + (f"<div class='contact'>{contact_line}</div>" if contact_line else "")
        + (f"<div class='links'>{links_line}</div>" if links_line else "")
        + "</div>"
        + (f"<div class='section'><h2>Professional Summary</h2><div>{prof}</div></div>" if prof else "")
        + "<div class='section'><h2>Core Skills</h2>"
        + f"{skills_html}</div>"
        + "<div class='section'><h2>Key Projects</h2>"
        + f"{projects_html}</div>"
        + "<div class='section'><h2>Education</h2>"
        + f"{education_html}</div>"
        + "<div class='section'><h2>Certifications</h2>"
        + f"{certs_html}</div>"
        + "</body></html>"
    )
    return html_out


# -------------------------
# Classic Template (HTML)
# -------------------------
def classic_template(data):
    """Return a classic (serif) HTML resume."""
    name = _esc(data.get("name", "Your Name"))
    email = _esc(data.get("email", ""))
    phone = _esc(data.get("phone", ""))
    location = _esc(data.get("location", ""))

    education_html = _build_education_html(data)
    projects_html = _build_projects_html(data)
    certs_html = _build_certs_html(data)
    skills_html = _build_skills_html(data)

    css = (
        "<style>"
        "body { font-family: Georgia, 'Times New Roman', serif; margin: 40px; color:#111; }"
        "h1 { margin:0; font-size:26px; }"
        ".meta { font-size:12px; color:#333; margin-top:6px; }"
        "h2 { font-size:13px; margin-top:20px; margin-bottom:8px; border-bottom:1px solid #ccc; padding-bottom:6px; }"
        ".section { margin-top:12px; }"
        "a { color:#0b5394; text-decoration:none; }"
        "</style>"
    )

    contact_line = " • ".join([x for x in [location, phone, email] if x])

    html_out = (
        "<!doctype html><html><head><meta charset='utf-8'/>"
        + css
        + "</head><body>"
        + f"<h1>{name}</h1>"
        + (f"<div class='meta'>{contact_line}</div>" if contact_line else "")
        + "<div class='section'><h2>Education</h2>" + education_html + "</div>"
        + "<div class='section'><h2>Work / Projects</h2>" + projects_html + "</div>"
        + "<div class='section'><h2>Skills</h2>" + skills_html + "</div>"
        + "<div class='section'><h2>Certifications</h2>" + certs_html + "</div>"
        + "</body></html>"
    )
    return html_out


# -------------------------
# ATS-Friendly Template (plain)
# -------------------------
def ats_template(data):
    """Return simple, ATS-friendly plain HTML (preformatted)."""
    lines = []
    name = _esc(data.get("name", "")).upper()
    if name:
        lines.append(name)
        lines.append("")  # blank line

    if data.get("email"):
        lines.append(f"Email: {_esc(data.get('email'))}")
    if data.get("phone"):
        lines.append(f"Phone: {_esc(data.get('phone'))}")
    if data.get("location"):
        lines.append(f"Location: {_esc(data.get('location'))}")

    lines.append("")  # spacer
    prof = _esc(data.get("professional_summary", ""))
    if prof:
        lines.append("SUMMARY")
        lines.append(prof)
        lines.append("")

    # Skills
    skills = data.get("skills", [])
    if skills:
        lines.append("SKILLS")
        for s in skills:
            ms = _esc(s.get("mainskill", ""))
            subs = s.get("subskills") or []
            subs_text = ", ".join(_esc(x) for x in subs if x)
            if ms:
                lines.append(f"{ms}: {subs_text}")
        lines.append("")

    # Projects
    projects = data.get("projects", [])
    if projects:
        lines.append("PROJECTS")
        for p in projects:
            pname = _esc(p.get("name", ""))
            desc = _esc(p.get("description", ""))
            repo = p.get("repository", "") or ""
            line = pname + (" — " + desc if desc else "")
            if repo:
                line += " (Repo: " + _esc(repo) + ")"
            lines.append(line)
        lines.append("")

    # Education
    education = data.get("education", [])
    if education:
        lines.append("EDUCATION")
        for e in education:
            course = _esc(e.get("course", ""))
            college = _esc(e.get("college", ""))
            year = _esc(e.get("year", ""))
            lines.append(f"{course} — {college} ({year})")
        lines.append("")

    # Certifications
    certs = data.get("certifications", [])
    if certs:
        lines.append("CERTIFICATIONS")
        for c in certs:
            namec = _esc(c.get("name", ""))
            cid = _esc(c.get("id", ""))
            src = c.get("source", "") or ""
            line = namec
            if cid:
                line += f" (ID: {cid})"
            if src:
                line += f" — { _esc(src) }"
            lines.append(line)
        lines.append("")

    # Wrap in <pre> to preserve spacing (still valid HTML for pdf conversion)
    html_out = "<!doctype html><html><head><meta charset='utf-8'/><style>pre{font-family:monospace; font-size:10px; white-space:pre-wrap;}</style></head><body><pre>"
    html_out += "\n".join(lines)
    html_out += "</pre></body></html>"
    return html_out


# Usage hint (comment):
# In app.py:
# from templates import modern_template, classic_template, ats_template
# html_content = modern_template(data)   # choose the function you want
# then convert `html_content` -> PDF using pdfkit or WeasyPrint.

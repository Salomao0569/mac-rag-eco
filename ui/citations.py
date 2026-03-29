"""Renderização de citações [[LABEL; details | LABEL2; details2]] → badges HTML."""

import re
import html as html_lib


def _classify_icon(label: str) -> str:
    upper = label.upper()
    if any(k in upper for k in ("PMID", "PUBMED")):
        return "📙"
    if any(k in upper for k in ("HTTP", "WWW", "ANVISA", "FDA", "BULA")):
        return "📘"
    return "📗"


def render_citations(text: str) -> str:
    """Converte marcação [[...]] em badges HTML com tooltip estilo OpenEvidence."""

    def _replace(match):
        content = match.group(1)
        refs = [r.strip() for r in content.split("|")]

        parsed = []
        for ref in refs:
            parts = ref.split(";", 1)
            label = parts[0].strip()
            detail = parts[1].strip() if len(parts) > 1 else ""
            icon = _classify_icon(label)
            parsed.append((icon, label, detail))

        primary_icon, primary_label = parsed[0][0], html_lib.escape(parsed[0][1])
        if len(parsed) > 1:
            badge_text = f"{primary_icon} {primary_label} + {len(parsed) - 1}"
        else:
            badge_text = f"{primary_icon} {primary_label}"

        tooltip_lines = []
        for icon, label, detail in parsed:
            escaped = html_lib.escape(f"{label} · {detail}" if detail else label)
            tooltip_lines.append(f'<span class="cite-line">{icon} {escaped}</span>')

        tooltip_html = "".join(tooltip_lines)

        plain_title = " | ".join(
            f"{icon} {label} · {detail}" if detail else f"{icon} {label}"
            for icon, label, detail in parsed
        )
        escaped_title = html_lib.escape(plain_title)

        return (
            f'<span class="cite-badge" title="{escaped_title}">{badge_text}'
            f'<span class="cite-tooltip" style="display:none !important;">{tooltip_html}</span>'
            f"</span>"
        )

    return re.sub(r"\[\[(.*?)\]\]", _replace, text)

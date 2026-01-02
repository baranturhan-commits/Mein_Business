from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as ReportLabImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from datetime import datetime

def create_payroll_pdf(mandant_config, employee_data, payroll_data, mandant_path):
    """
    Erstellt eine Lohnabrechnung als PDF.
    
    Args:
        mandant_config (dict): Firmenkonfiguration (Name, Adresse, Logo).
        employee_data (dict): Mitarbeiterdaten (Name, Adresse, Steuerklasse, SV-Nr).
        payroll_data (dict): Abrechnungsdaten (Monat, Jahr, Brutto, Abzüge, Netto).
        mandant_path (Path): Pfad zum Mandantenverzeichnis (für Speicherort & Logo).
        
    Returns:
        str: Dateiname des erstellten PDFs.
    """
    
    # 1. Setup
    month_year = f"{payroll_data.get('monat', '')}-{payroll_data.get('jahr', '')}"
    # Sanitized filename parts
    nachname = employee_data.get('nachname', 'Mitarbeiter').strip()
    vorname = employee_data.get('vorname', '').strip()
    filename = f"Lohn_{nachname}_{vorname}_{month_year}.pdf"
    
    # Ordner "Lohnabrechnungen" im Mandanten-Ordner erstellen
    save_dir = os.path.join(mandant_path, 'Lohnabrechnungen')
    os.makedirs(save_dir, exist_ok=True)
    
    filepath = os.path.join(save_dir, filename)
    
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom Styles
    styles.add(ParagraphStyle(name='Small', parent=styles['Normal'], fontSize=8, leading=10))
    styles.add(ParagraphStyle(name='Bold', parent=styles['Normal'], fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle(name='DocTitle', parent=styles['Heading1'], alignment=1, spaceAfter=20))
    
    # --- HEADER (Logo rechts, Absender links) ---
    logo_path = None
    if mandant_config.get("logo"):
        p_logo = os.path.join(mandant_path, mandant_config["logo"])
        if os.path.exists(p_logo):
            logo_path = p_logo

    if logo_path:
        im = ReportLabImage(logo_path, width=5*cm, height=2.5*cm, kind='proportional')
        im.hAlign = 'RIGHT'
        logo_table = Table([[im]], colWidths=[17*cm])
        logo_table.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'RIGHT')]))
        story.append(logo_table)
        story.append(Spacer(1, 0.5*cm))
        
    # Absenderzeile (klein)
    firma = mandant_config.get('firma', 'Musterfirma')
    adresse = mandant_config.get('adresse', {})
    sender_line = f"{firma} • {adresse.get('strasse', '')} • {adresse.get('ort', '')}"
    story.append(Paragraph(sender_line, styles['Small']))
    story.append(Spacer(1, 0.5*cm))
    
    # Empfängerfeld
    emp_name = f"{employee_data.get('vorname', '')} {employee_data.get('nachname', '')}"
    emp_strasse = employee_data.get('strasse', '')
    emp_ort = employee_data.get('ort', '')
    
    recipient = f"{emp_name}<br/>{emp_strasse}<br/>{emp_ort}"
    story.append(Paragraph(recipient, styles['Normal']))
    story.append(Spacer(1, 1.5*cm))
    
    # Titel
    month_name = payroll_data.get('monat_name', payroll_data.get('monat', ''))
    story.append(Paragraph(f"Verdienstabrechnung {month_name} {payroll_data.get('jahr', '')}", styles['DocTitle']))
    
    # Metadaten Tabelle (Personal-Nr, Geb.Datum, Eintritt, StKl, SV-Nr)
    meta_data = [
        ['Pers.Nr', 'Geburtsdatum', 'Eintritt', 'Steuerklasse', 'SV-Nummer'],
        [
            employee_data.get('personalnummer', '-'),
            employee_data.get('geburtsdatum', '-'),
            employee_data.get('eintritt', '-'),
            employee_data.get('steuerklasse', '-'),
            employee_data.get('sv_nummer', '-')
        ]
    ]
    
    t_meta = Table(meta_data, colWidths=[3*cm, 3.5*cm, 3*cm, 3*cm, 4.5*cm])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 1*cm))
    
    # --- ABRECHNUNGSTABELLE ---
    # Struktur: Beschreibung | Wert / Prozentsatz | Betrag
    
    # 1. Brutto
    data = [['Bezeichnung', 'Faktor', 'Betrag (EUR)']]
    
    amount_brutto = payroll_data.get('brutto')
    if not amount_brutto:
        amount_brutto = 0
    brutto_lohn = float(amount_brutto)

    # Optional: Aufschlüsselung wenn Details da sind (z.B. Stunden * Satz)
    # Hier simpel:
    data.append(['Festbezug / Gehalt', '', f"{brutto_lohn:.2f}"])
    
    amount_bonus = payroll_data.get('bonus')
    if amount_bonus and float(amount_bonus) > 0:
        val = float(amount_bonus)
        data.append(['Einmalzahlung / Bonus', '', f"{val:.2f}"])
        brutto_lohn += val
        
    data.append(['Gesamtbrutto', '', f"{brutto_lohn:.2f}"])
    data.append(['', '', '']) # Leerzeile
    
    # 2. Abzüge
    netto = brutto_lohn
    taxes = payroll_data.get('abzuege', {})
    
    total_deductions = 0.0
    
    # Loop over taxes dict (e.g. {'Lohnsteuer': 100, 'RV': 50})
    for tax_name, amount in taxes.items():
        if amount:
            try:
                val = float(amount)
            except ValueError:
                val = 0.0
                
            if val > 0:
                data.append([tax_name, '', f"- {val:.2f}"])
                total_deductions += val
            
    netto -= total_deductions
    
    data.append(['', '', ''])
    data.append(['Nettoredienst', '', f"{netto:.2f}"])
    
    # Style Table
    t_main = Table(data, colWidths=[10*cm, 3*cm, 4*cm])
    t_main.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,0), 1, colors.black), # Header Line
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (2,0), (-1,-1), 'RIGHT'), # Amounts Right
        ('LINEABOVE', (0,-1), (-1,-1), 1, colors.black), # Netto Line Top
        ('LINEBELOW', (0,-1), (-1,-1), 1, colors.black), # Netto Line Bottom
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'), # Netto Bold
        ('ROWBACKGROUNDS', (0,2), (-1,2), [colors.whitesmoke]), # Brutto Row Highlight
    ]))
    
    story.append(t_main)
    story.append(Spacer(1, 1.5*cm))
    
    # Auszahlungsinfo
    payout_text = f"Der Betrag von <b>{netto:.2f} EUR</b> wird auf das Konto {employee_data.get('iban', '')} überwiesen."
    story.append(Paragraph(payout_text, styles['Normal']))
    
    # Build
    doc.build(story)
    return filename

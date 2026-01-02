"""
Abnahmeprotokoll-Generator
Erstellt PDF-Abnahmeprotokolle für Baustellen
"""

import os
import datetime
import json
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as ReportLabImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from pathlib import Path

def get_and_increment_delivery_counter(mandant_path):
    """Generiert und inkrementiert Protokoll-Nummer"""
    counter_file = Path(mandant_path) / "delivery_counter.json"
    current_year = datetime.date.today().year
    
    if counter_file.exists():
        with open(counter_file, 'r') as f:
            data = json.load(f)
    else:
        data = {}
    
    year_key = str(current_year)
    if year_key not in data or data.get('year') != year_key:
        data = {'year': year_key, 'counter': 0}
    
    data['counter'] += 1
    nummer = f"PROT-{current_year}-{data['counter']:03d}"
    
    with open(counter_file, 'w') as f:
        json.dump(data, f, indent=4)
    
    return nummer

def create_delivery_pdf(mandant_path, mandant_config, kunde_name, positionen, output_path, nummer, angebot_nr=None):
    """
    Erstellt Abnahmeprotokoll-PDF
    Ignoriert 'positionen', da Tabelle leer sein soll.
    """
    
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=2*cm,
        rightMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # Title Style (Blue)
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#0056b3'), # Blue
        spaceAfter=30,
        alignment=1 # Client requested center
    )
    
    # Label Style (Bold)
    label_style = ParagraphStyle(
        'Label',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        spaceAfter=2
    )

    # Value Style (Gray Box bg handled in table)
    value_style = ParagraphStyle(
        'Value',
        parent=styles['Normal'],
        fontSize=10,
        leading=12
    )

    # --- HEADER BEREICH (Logo rechts, Absender links) ---
    # Logo Check
    logo_path = None
    if mandant_config.get("logo"):
        p_logo = os.path.join(mandant_path, mandant_config["logo"])
        if os.path.exists(p_logo):
            logo_path = p_logo

    if logo_path:
        # Logo Placement using Table to align right
        im = ReportLabImage(logo_path, width=5*cm, height=2.5*cm, kind='proportional')
        im.hAlign = 'RIGHT'
        logo_table = Table([[im]], colWidths=[17*cm])
        logo_table.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'RIGHT')]))
        story.append(logo_table)
        story.append(Spacer(1, 0.5*cm))
    else:
        # Fallback: Just Firma Name if no logo, similar to Invoice generic
        firma = mandant_config.get('firma', 'Firma')
        story.append(Paragraph(f"<b>{firma}</b>", styles['Normal']))
        story.append(Spacer(1, 1*cm))

    # 1. Title
    story.append(Paragraph("ABNAHMEPROTOKOLL", title_style))
    story.append(Spacer(1, 1*cm))
    
    # 2. Key Information Block (Table for layout)
    # Mandant Info (Auftragnehmer)
    mn_name = mandant_config.get('firma', '')
    
    # Data for Info Table
    # Row 1: Projekt
    # Row 2: Auftraggeber (Kunde)
    # Row 3: Auftragnehmer (Mandant)
    # Row 4: Teilnehmer
    
    # Color for Input Fields
    bg_color = colors.HexColor('#e0e0e0') # Light Gray
    
    info_data = [
        [Paragraph("Projekt", label_style), Paragraph("", value_style)], # Empty Project
        [Paragraph("Auftraggeber", label_style), Paragraph(kunde_name, value_style)],
        [Paragraph("Auftragnehmer", label_style), Paragraph(mn_name, value_style)],
        [Paragraph("Teilnehmer", label_style), Paragraph("", value_style)],
    ]
    
    info_table = Table(info_data, colWidths=[4*cm, 12*cm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (1,0), (1,-1), bg_color), # Gray BG for values
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    
    story.append(info_table)
    story.append(Spacer(1, 1*cm))
    
    # 3. Checkboxes (Art der Abnahme)
    # Using characters for empty boxes if easy, or small table
    # □ = \xE2\x96\xA1 (utf-8) but reportlab default fonts might not support it well.
    # Using simple [ ] text or drawing rectangle. Let's use simple table.
    
    check_data = [
        [
            Paragraph("Art der Abnahme:", label_style),
            "Gesamtabnahme  [   ]",
            "Teilabnahme  [   ]"
        ]
    ]
    check_table = Table(check_data, colWidths=[4*cm, 6*cm, 6*cm])
    check_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (1,0), (2,0), 'CENTER'),
    ]))
    story.append(check_table)
    story.append(Spacer(1, 0.5*cm))
    
    # 4. Datum
    datum_today = datetime.date.today().strftime("%d.%m.%Y")
    date_data = [
        [
            Paragraph("Datum:", label_style),
            Paragraph(datum_today, value_style), # In Gray box
            Paragraph("von", label_style),
            Paragraph("", value_style), # Gray box
            Paragraph("bis", label_style),
            Paragraph("", value_style), # Gray box
            Paragraph("Uhr", label_style)
        ]
    ]
    date_table = Table(date_data, colWidths=[2*cm, 3*cm, 1*cm, 2*cm, 1*cm, 2*cm, 1.5*cm])
    date_table.setStyle(TableStyle([
        ('BACKGROUND', (1,0), (1,0), bg_color),
        ('BACKGROUND', (3,0), (3,0), bg_color),
        ('BACKGROUND', (5,0), (5,0), bg_color),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (1,0), (5,0), 'CENTER'),
    ]))
    story.append(date_table)
    story.append(Spacer(1, 1*cm))
    
    # 5. Main Table (Empty for handwriting)
    # Cols: Gewerk, Beschreibung, ok, nok, Bemerkung
    # Header Style: Dark Gray, White Text
    
    header = ["Gewerk", "Beschreibung (Mängel / Restarbeiten)", "ok", "nok", "Bemerkung"]
    
    # Generate ~15 empty rows
    main_data = [header]
    for i in range(15):
        main_data.append([str(i+1), "", "", "", ""]) # Using index as Gewerk placeholder? Or just empty? Image shows empty. 
        # Actually image shows numbered rows 1..15 on the left outside? 
        # Let's put numbers in first col for Reference
    
    main_table = Table(main_data, colWidths=[1.5*cm, 8*cm, 1.5*cm, 1.5*cm, 4.5*cm])
    main_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#555555')), # Dark Gray
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 1, colors.white), # White grid like image
        
        # Body rows BG - Alternating gray/white? Image looks fully light gray.
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#e8e8e8')),
        ('GRID', (0,0), (-1,-1), 1, colors.white),
        ('MINROWHEIGHT', (0,1), (-1,-1), 20),
    ]))
    
    story.append(main_table)
    story.append(Spacer(1, 2*cm))
    
    # 6. Footer (Signatures)
    sig_data = [
        ["_____________________________", "_____________________________"],
        ["Ort, Datum, Unterschrift Auftragnehmer", "Ort, Datum, Unterschrift Auftraggeber"]
    ]
    sig_table = Table(sig_data, colWidths=[8*cm, 8*cm])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (1,0), (1,1), 2*cm), # Gap
    ]))
    
    story.append(sig_table)
    
    doc.build(story)
    return True

if __name__ == '__main__':
    # Test
    config = {'firma': 'Elektro Meister'}
    create_delivery_pdf('.', config, 'Musterkunde', [], 'test_protocol.pdf', 'PROT-TEST')
    print("Test PDF created")

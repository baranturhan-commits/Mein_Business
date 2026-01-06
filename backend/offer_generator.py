"""
Angebots-Generator - Basiert auf invoice.py
Erstellt PDF-Angebote mit Preislisten-Integration
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

def get_and_increment_offer_counter(mandant_path, mandant_config=None):
    """Generiert und inkrementiert Angebots-Nummer mit Mandantennummer"""
    counter_file = Path(mandant_path) / "offer_counter.json"
    current_year = datetime.date.today().year
    
    # Get Mandantennummer from config
    mandanten_nr = "000"
    if mandant_config:
        mandanten_nr = mandant_config.get('mandantennummer', '000')
    else:
        # Try to load from config file
        config_file = Path(mandant_path) / "mandant_config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                    mandanten_nr = cfg.get('mandantennummer', '000')
            except:
                pass
    
    if counter_file.exists():
        with open(counter_file, 'r') as f:
            data = json.load(f)
    else:
        data = {}
    
    year_key = str(current_year)
    if year_key not in data or data.get('year') != year_key:
        data = {'year': year_key, 'counter': 0}
    
    data['counter'] += 1
    # Format: ANG-[MandantenNr]-[Jahr]-[Counter]
    nummer = f"ANG-{mandanten_nr}-{current_year}-{data['counter']:03d}"
    
    with open(counter_file, 'w') as f:
        json.dump(data, f, indent=4)
    
    return nummer

def create_offer_pdf(mandant_path, mandant_config, kunde_name, positionen, output_path, nummer):
    """
    Erstellt Angebots-PDF
    
    positionen: [{'bezeichnung': str, 'menge': float, 'einheit': str, 'einzelpreis': float}]
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
    
    # Title Style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=30,
        alignment=0
    )
    
    # Header
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
        story.append(Spacer(1, 1*cm))

    # Absender Block
    firma = mandant_config.get('firma', 'Firma')
    adresse = mandant_config.get('adresse', {})
    firmen_block = f"{firma}<br/>{adresse.get('strasse', '')}<br/>{adresse.get('ort', '')}"
    
    story.append(Paragraph(firmen_block, styles['Normal']))
    story.append(Spacer(1, 1.5*cm))
    
    # Title
    story.append(Paragraph(f"<b>ANGEBOT {nummer}</b>", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    # Kunde & Datum
    story.append(Paragraph(f"<b>An:</b> {kunde_name}", styles['Normal']))
    datum = datetime.date.today().strftime("%d.%m.%Y")
    story.append(Paragraph(f"<b>Datum:</b> {datum}", styles['Normal']))
    story.append(Spacer(1, 1*cm))
    
    # Positionen-Tabelle
    table_data = [['Pos', 'Beschreibung', 'Menge', 'Einzel', 'Gesamt']]
    
    netto_gesamt = 0
    for idx, pos in enumerate(positionen, 1):
        menge = float(pos.get('menge', 0))
        preis = float(pos.get('einzelpreis', 0))
        gesamt = menge * preis
        netto_gesamt += gesamt
        
        table_data.append([
            str(idx),
            pos.get('bezeichnung', ''),
            f"{menge} {pos.get('einheit', 'Stk')}",
            f"{preis:.2f}€",
            f"{gesamt:.2f}€"
        ])
    
    # Styles for Table
    style_right = ParagraphStyle('Right', parent=styles['Normal'], alignment=2) # 2 = TA_RIGHT

    # Summen
    mwst = netto_gesamt * 0.19
    brutto = netto_gesamt + mwst
    
    table_data.append(['', '', '', 'Netto:', f"{netto_gesamt:.2f}€"])
    table_data.append(['', '', '', 'MwSt 19%:', f"{mwst:.2f}€"])
    
    # Use Paragraph to interpret <b> tags
    table_data.append([
        '', '', '', 
        Paragraph('<b>Brutto:</b>', style_right), 
        Paragraph(f"<b>{brutto:.2f}€</b>", style_right)
    ])
    
    table = Table(table_data, colWidths=[1.5*cm, 8*cm, 3*cm, 2.5*cm, 2.5*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('ALIGN', (3,0), (-1,-1), 'RIGHT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('GRID', (0,0), (-1,-4), 1, colors.black),
        ('LINEBELOW', (0,-3), (-1,-3), 1, colors.black),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
    ]))
    
    story.append(table)
    story.append(Spacer(1, 1*cm))
    
    # Footer
    story.append(Paragraph("<i>Vielen Dank für Ihre Anfrage!</i>", styles['Normal']))
    story.append(Paragraph(f"<i>Angebot gültig bis: {(datetime.date.today() + datetime.timedelta(days=30)).strftime('%d.%m.%Y')}</i>", styles['Normal']))
    
    doc.build(story)
    
    return brutto, netto_gesamt

if __name__ == '__main__':
    # Test
    test_positionen = [
        {'bezeichnung': 'Beratungsstunde', 'menge': 5, 'einheit': 'Std', 'einzelpreis': 80},
        {'bezeichnung': 'Material', 'menge': 1, 'einheit': 'Pauschale', 'einzelpreis': 250}
    ]
    
    config = {
        'firma': 'Test GmbH',
        'adresse': {'strasse': 'Teststr. 1', 'ort': '12345 Berlin'}
    }
    
    create_offer_pdf('.', config, 'Testkunde', test_positionen, 'test_angebot.pdf', 'ANG-2025-001')
    print("✅ Test-PDF erstellt")

"""
Mahnung-Generator
Erstellt PDF-Mahnungen basierend auf Rechnungen
"""

import os
import datetime
import re

def clean_text(text):
    if not isinstance(text, str):
        return str(text)
    text = re.sub(r'[\x00-\x1F\x7F]', ' ', text)
    text = text.replace('\u25A0', ' ')
    return text

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as ReportLabImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

def create_dunning_pdf(mandant_path, mandant_config, original_invoice_data, output_path, dunning_level=1):
    """
    Erstellt eine Mahnung als PDF
    dunning_level: 1 = Zahlungserinnerung/1. Mahnung, 2 = 2. Mahnung, 3 = Letzte Mahnung
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
    
    # Custom Styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=20
    )
    
    # --- HEADER (Logo/Firma) ---
    logo_path = None
    if mandant_config.get("logo"):
        p_logo = os.path.join(mandant_path, mandant_config["logo"])
        if os.path.exists(p_logo):
            logo_path = p_logo

    if logo_path:
        im = ReportLabImage(logo_path, width=5*cm, height=2.5*cm, kind='proportional')
        im.hAlign = 'RIGHT'
        story.append(im)
    else:
        # Fallback Firma Name
        firma = mandant_config.get('firma', 'Ihre Firma')
        story.append(Paragraph(f"<b>{firma}</b>", styles['Normal']))
    
    story.append(Spacer(1, 1*cm))
    
    # --- ABSENDER & EMPFÄNGER ---
    # Absenderzeile (klein)
    firma = mandant_config.get('firma', '')
    strasse = mandant_config.get('adresse', {}).get('strasse', '')
    ort = mandant_config.get('adresse', {}).get('ort', '')
    sender_line = f"{firma} | {strasse} | {ort}"
    
    story.append(Paragraph(f"<font size=8>{sender_line}</font>", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))
    
    # Empfänger (Kunde) aus Original Invoice Data
    kunde_name = original_invoice_data.get('kunde', 'Kunde')
    # Wir haben evtl. keine Adresse im Invoice Data Objekt, wenn es aus der Liste kommt.
    # Versuchen wir es generisch zu halten.
    story.append(Paragraph(f"<b>{kunde_name}</b>", styles['Normal']))
    # Hier könnte man die Adresse aus der DB holen wenn verfügbar
    story.append(Spacer(1, 2*cm))
    
    # --- INFOS (Datum, Rechnungsnummer) ---
    today = datetime.date.today().strftime("%d.%m.%Y")
    inv_num = original_invoice_data.get('nummer', '')
    inv_date = original_invoice_data.get('datum', '')
    
    # Text je nach Mahnstufe
    if dunning_level == 1:
        title = "Zahlungserinnerung"
        intro = f"fällig am: sofort"
    elif dunning_level == 2:
        title = "2. Mahnung"
        intro = "fällig am: sofort"
    else:
        title = "Letzte Mahnung"
        intro = "fällig am: sofort"

    # Info Block rechtsbündig
    p_infos = []
    p_infos.append(['Datum:', today])
    p_infos.append(['Rechnungs-Nr.:', inv_num])
    p_infos.append(['Rechnungsdatum:', inv_date])
    # p_infos.append(['Kundennummer:', '...']) 

    t_infos = Table(p_infos, colWidths=[4*cm, 4*cm])
    t_infos.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
    ]))
    # Trick um Tabelle rechtsbündig zu machen: In eine weitere Tabelle packen oder Flowable anpassen
    # Einfachheitshalber: Links lassen oder wir nutzen einen Table mit leerer linker Spalte
    story.append(t_infos)
    story.append(Spacer(1, 1*cm))
    
    # --- TITEL ---
    story.append(Paragraph(f"<b>{title}</b>", title_style))
    
    # --- TEXT ---
    msg = ""
    # Format currency
    betrag = original_invoice_data.get('betrag', 0.0)
    try:
        if isinstance(betrag, str):
            betrag = float(betrag.replace('.','').replace(',','.'))
    except:
        betrag = 0.0
    
    # Add Mahngebühr logic here if needed for total display
    total = betrag
    fees = 0.0
    fee_text = ""
    if dunning_level > 1:
        fees = 2.50 * (dunning_level - 1)
        total += fees
        fee_text = f" (inkl. {fees:.2f} € Mahngebühr)"

    betrag_str = f"{total:.2f} €".replace('.', ',')

    if dunning_level == 1:
        msg = f"""Sehr geehrte Damen und Herren,<br/><br/>
leider konnten wir bis heute keinen Zahlungseingang für die unten genannte Rechnung feststellen.<br/>
Sicherlich handelt es sich hierbei nur um ein Versehen.<br/><br/>
Bitte überweisen Sie den offenen Betrag von <b>{betrag_str}</b>{fee_text} in den nächsten Tagen."""
    elif dunning_level == 2:
        msg = f"""Sehr geehrte Damen und Herren,<br/><br/>
auf unsere Zahlungserinnerung haben Sie bisher leider nicht reagiert.<br/>
Wir bitten Sie nachdrücklich, den fälligen Betrag von <b>{betrag_str}</b>{fee_text} umgehend zu begleichen."""
    
    msg = clean_text(msg)
    story.append(Paragraph(msg, styles['Normal']))
    story.append(Spacer(1, 1*cm))
    
    # Reference to Invoice
    inv_num = original_invoice_data.get('nummer', '')
    inv_date = original_invoice_data.get('datum', '')
    
    ref_text = f"<b>Bezug: Rechnung Nr. {inv_num} vom {inv_date}</b>"
    story.append(Paragraph(ref_text, styles['Normal']))
    story.append(Spacer(1, 2*cm))
    
    # Note about attachment
    note = "Eine Kopie der ursprünglichen Rechnung liegt diesem Schreiben bei."
    story.append(Paragraph(note, styles['Italic'])) # Use standard Italic style if available or just Normal
    story.append(Spacer(1, 1*cm))
    
    # --- FUSSZEILE (Bankverbindung) ---
    msg_end = "Bitte geben Sie bei der Überweisung unbedingt die Rechnungsnummer an."
    story.append(Paragraph(msg_end, styles['Normal']))
    story.append(Spacer(1, 1*cm))
    
    bank = mandant_config.get('bank', {})
    bank_info = f"""
    <b>Bankverbindung:</b><br/>
    {bank.get('name', '')}<br/>
    IBAN: {bank.get('iban', '')}<br/>
    BIC: {bank.get('bic', '')}
    """
    story.append(Paragraph(bank_info, styles['Normal']))
    
    doc.build(story)
    return True

if __name__ == '__main__':
    # Test
    pass

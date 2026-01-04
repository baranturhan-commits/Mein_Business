import os
import sys
import json
import datetime
import locale
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as ReportLabImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

# Set Locale for currency
try:
    locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'de_DE')
    except: pass

def generate_report(mandant_path, month, year, einnahmen, ausgaben, output_path, mandant_config):
    """
    Generates a PDF Monthly Report
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom Styles
    style_title = ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.HexColor('#2c3e50'), # Dark Blue
        alignment=1 # Center
    )
    
    style_h2 = ParagraphStyle(
        'ReportH2',
        parent=styles['Heading2'],
        fontSize=16,
        spaceBefore=20,
        spaceAfter=10,
        textColor=colors.HexColor('#34495e')
    )

    style_kpi_label = ParagraphStyle(
        'KPILabel',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.gray,
        alignment=1
    )
    
    style_kpi_value = ParagraphStyle(
        'KPIValue',
        parent=styles['Heading2'],
        fontSize=18,
        spaceAfter=10,
        alignment=1
    )

    # --- 1. HEADER (Logo + Company Info) ---
    logo_path = None
    if mandant_config.get('logo'):
        check_path = os.path.join(mandant_path, mandant_config['logo'])
        if os.path.exists(check_path):
            logo_path = check_path
            
    # Header Table
    header_data = []
    
    # Company Info Text
    info_text = f"""
    <b>{mandant_config.get('firma', 'Meine Firma')}</b><br/>
    {mandant_config.get('adresse', {}).get('strasse', '')}<br/>
    {mandant_config.get('adresse', {}).get('ort', '')}
    """
    
    col_widths = [10*cm, 7*cm]
    
    if logo_path:
        img = ReportLabImage(logo_path, width=5*cm, height=2.5*cm)
        img.hAlign = 'RIGHT'
        header_data = [[Paragraph(info_text, styles['Normal']), img]]
    else:
        header_data = [[Paragraph(info_text, styles['Normal']), '']]
        
    t = Table(header_data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
    ]))
    story.append(t)
    story.append(Spacer(1, 1*cm))
    
    # --- 2. TITLE ---
    month_name = datetime.date(year, month, 1).strftime('%B %Y')
    story.append(Paragraph(f"Monatsabschluss: {month_name}", style_title))
    story.append(Spacer(1, 1*cm))
    
    # --- 3. KPI SUMMARY ---
    # Calc Totals
    total_in = sum(float(str(x.get('Betrag_Netto','0')).replace(',','.')) for x in einnahmen)
    total_out = sum(float(str(x.get('Betrag_Netto','0')).replace(',','.')) for x in ausgaben)
    profit = total_in - total_out
    
    kpi_data = [[
        Paragraph("Einnahmen (Netto)", style_kpi_label),
        Paragraph("Ausgaben (Netto)", style_kpi_label),
        Paragraph("Gewinn (Netto)", style_kpi_label)
    ], [
        Paragraph(f"<b>{format_currency(total_in)}</b>", style_kpi_value),
        Paragraph(f"<b>{format_currency(total_out)}</b>", style_kpi_value),
        Paragraph(f"<font color='{'green' if profit >= 0 else 'red'}'><b>{format_currency(profit)}</b></font>", style_kpi_value)
    ]]
    
    kpi_table = Table(kpi_data, colWidths=[5*cm, 5*cm, 5*cm])
    kpi_table.setStyle(TableStyle([
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOX', (0,0), (-1,-1), 1, colors.lightgrey),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
        ('PADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 1.5*cm))
    
    # --- 4. DETAILS TABLES ---
    
    # Einnahmen
    story.append(Paragraph("Einnahmen Details", style_h2))
    if einnahmen:
        t_data = [['Datum', 'Kunde / Re-Nr.', 'Beschreibung', 'Betrag']]
        for e in einnahmen:
            desc = e.get('Beschreibung') or "Rechnung " + str(e.get('Rechnungsnummer',''))
            t_data.append([
                e.get('Datum',''),
                str(e.get('Kunde','')) + "\n" + str(e.get('Rechnungsnummer','')),
                Paragraph(desc, styles['Normal']),
                format_currency(e.get('Betrag_Netto',0))
            ])
            
        t_in = Table(t_data, colWidths=[2.5*cm, 4*cm, 7.5*cm, 3*cm])
        t_in.setStyle(get_table_style(colors.HexColor('#e8f5e9'))) # Light Green
        story.append(t_in)
    else:
        story.append(Paragraph("Keine Einnahmen in diesem Zeitraum.", styles['Normal']))
        
    story.append(Spacer(1, 1*cm))
    
    # Ausgaben
    story.append(Paragraph("Ausgaben Details", style_h2))
    if ausgaben:
        t_data = [['Datum', 'Kategorie', 'Beschreibung', 'Betrag']]
        for a in ausgaben:
            t_data.append([
                a.get('Datum',''),
                a.get('Kategorie',''),
                Paragraph(str(a.get('Beschreibung','')), styles['Normal']),
                format_currency(a.get('Betrag_Netto',0))
            ])
            
        t_out = Table(t_data, colWidths=[2.5*cm, 4*cm, 7.5*cm, 3*cm])
        t_out.setStyle(get_table_style(colors.HexColor('#fce4ec'))) # Light Pink
        story.append(t_out)
    else:
        story.append(Paragraph("Keine Ausgaben in diesem Zeitraum.", styles['Normal']))
        
    # --- FOOTER ---
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph(f"Erstellt am {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}", style_kpi_label))

    doc.build(story)
    return True

def format_currency(val):
    try:
        f = float(str(val).replace(',','.'))
        return "{:,.2f} €".format(f).replace(',', 'X').replace('.', ',').replace('X', '.')
    except:
        return "0,00 €"

def get_table_style(header_bg):
    return TableStyle([
        ('BACKGROUND', (0,0), (-1,0), header_bg),
        ('TEXTCOLOR', (0,0), (-1,0), colors.black),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('ALIGN', (-1,0), (-1,-1), 'RIGHT'), # Amount right aligned
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ])

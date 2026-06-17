"""
Wartungsprotokoll PDF-Generator
Erstellt professionelle Wartungsprotokolle als PDF mit ReportLab.
"""

import json
from pathlib import Path
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT


def lade_mandant_config(mandant_dir: Path) -> dict:
    """Lädt die Mandanten-Konfiguration aus mandant_config.json."""
    config_path = mandant_dir / 'mandant_config.json'
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def checkbox_symbol(checked: bool) -> str:
    """Gibt das visuelle Symbol für eine Checkbox zurück."""
    return "☑" if checked else "☐"


def erstelle_wartungsprotokoll_pdf(
    output_path: str,
    mandant_dir: Path,
    protokoll_data: dict
) -> bool:
    """
    Erstellt ein Wartungsprotokoll als PDF.

    Args:
        output_path: Pfad zur Ausgabe-PDF-Datei
        mandant_dir: Pfad zum Mandanten-Ordner
        protokoll_data: Dictionary mit den Protokoll-Daten

    Returns:
        True wenn erfolgreich, False bei Fehler
    """
    try:
        # Mandanten-Konfiguration laden
        config = lade_mandant_config(mandant_dir)
        firmenname = config.get('firma', config.get('firmenname', 'Unbekannt'))
        adresse = config.get('adresse', {})
        strasse = adresse.get('strasse', '')
        ort = adresse.get('ort', '')

        # Logo-Pfad aus Konfiguration
        logo_path = config.get('logo_path') or config.get('logo')
        logo_full_path = None
        if logo_path:
            candidate = mandant_dir / logo_path
            if candidate.exists():
                logo_full_path = str(candidate)

        # Protokoll-Felder extrahieren
        datum = protokoll_data.get('datum', datetime.now().strftime('%d.%m.%Y'))
        techniker = protokoll_data.get('techniker', '')
        kunde = protokoll_data.get('kunde', '')
        anlage = protokoll_data.get('anlage', '')
        druck_ok = bool(protokoll_data.get('druck_ok', False))
        dichtheit_ok = bool(protokoll_data.get('dichtheit_ok', False))
        filter_ok = bool(protokoll_data.get('filter_ok', False))
        sicherheitsventil_ok = bool(protokoll_data.get('sicherheitsventil_ok', False))
        befund = protokoll_data.get('befund', '')
        naechste_wartung = protokoll_data.get('naechste_wartung', '')

        # PDF-Dokument erstellen
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm
        )

        # Stile definieren
        styles = getSampleStyleSheet()

        stil_titel = ParagraphStyle(
            'Titel',
            parent=styles['Title'],
            fontSize=18,
            textColor=colors.HexColor('#1a1a2e'),
            spaceAfter=4 * mm,
            alignment=TA_LEFT
        )
        stil_untertitel = ParagraphStyle(
            'Untertitel',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#555555'),
            spaceAfter=2 * mm,
            alignment=TA_LEFT
        )
        stil_abschnitt = ParagraphStyle(
            'Abschnitt',
            parent=styles['Normal'],
            fontSize=11,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#1a1a2e'),
            spaceBefore=4 * mm,
            spaceAfter=2 * mm
        )
        stil_normal = ParagraphStyle(
            'Normal_Custom',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#333333'),
            spaceAfter=1 * mm
        )
        stil_checkbox = ParagraphStyle(
            'Checkbox',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#333333'),
            spaceAfter=2 * mm
        )
        stil_freitext = ParagraphStyle(
            'Freitext',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#333333'),
            spaceAfter=2 * mm,
            leading=14
        )

        # Inhalt zusammenstellen
        inhalt = []

        # --- Kopfzeile mit Logo und Firmenname ---
        kopf_data = []
        firmen_text = [
            Paragraph(f"<b>{firmenname}</b>", stil_titel),
            Paragraph(strasse, stil_untertitel),
            Paragraph(ort, stil_untertitel),
        ]

        if logo_full_path:
            from reportlab.platypus import Image as RLImage
            try:
                logo_img = RLImage(logo_full_path, width=35 * mm, height=20 * mm, kind='proportional')
                kopf_data = [[firmen_text, logo_img]]
            except Exception:
                kopf_data = [[firmen_text, '']]
        else:
            kopf_data = [[firmen_text, '']]

        kopf_tabelle = Table(kopf_data, colWidths=[120 * mm, 50 * mm])
        kopf_tabelle.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))
        inhalt.append(kopf_tabelle)
        inhalt.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#1a1a2e'), spaceAfter=5 * mm))

        # --- Dokumenttitel ---
        inhalt.append(Paragraph("🔧 Wartungsprotokoll", ParagraphStyle(
            'DokTitel',
            parent=styles['Normal'],
            fontSize=20,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#1a1a2e'),
            spaceAfter=6 * mm,
            alignment=TA_CENTER
        )))

        # --- Stammdaten-Tabelle ---
        inhalt.append(Paragraph("Allgemeine Informationen", stil_abschnitt))

        stamm_data = [
            ['Datum der Wartung:', datum,        'Techniker:', techniker],
            ['Kunde / Auftraggeber:', kunde,     'Anlage / Gerät:', anlage],
        ]

        stamm_tabelle = Table(stamm_data, colWidths=[45 * mm, 60 * mm, 35 * mm, 30 * mm])
        stamm_tabelle.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#333333')),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f4f6fb')),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.HexColor('#f4f6fb'), colors.white]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        inhalt.append(stamm_tabelle)
        inhalt.append(Spacer(1, 5 * mm))

        # --- Prüfpunkte / Checkboxen ---
        inhalt.append(Paragraph("Durchgeführte Prüfungen", stil_abschnitt))

        pruef_data = [
            [checkbox_symbol(druck_ok),              'Druck geprüft',
             checkbox_symbol(dichtheit_ok),          'Dichtheit geprüft'],
            [checkbox_symbol(filter_ok),             'Filter gereinigt',
             checkbox_symbol(sicherheitsventil_ok),  'Sicherheitsventil geprüft'],
        ]

        pruef_tabelle = Table(pruef_data, colWidths=[12 * mm, 70 * mm, 12 * mm, 76 * mm])
        pruef_tabelle.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTNAME', (3, 0), (3, -1), 'Helvetica'),
            ('FONTSIZE', (1, 0), (1, -1), 10),
            ('FONTSIZE', (3, 0), (3, -1), 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#333333')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.HexColor('#f9f9f9'), colors.white]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        inhalt.append(pruef_tabelle)
        inhalt.append(Spacer(1, 5 * mm))

        # --- Befund / Freitext ---
        inhalt.append(Paragraph("Befund / Feststellungen", stil_abschnitt))

        befund_text = befund if befund else "Keine besonderen Feststellungen."
        befund_tabelle = Table(
            [[Paragraph(befund_text, stil_freitext)]],
            colWidths=[170 * mm]
        )
        befund_tabelle.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fafafa')),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('MINROWHEIGHT', (0, 0), (-1, -1), 25 * mm),
        ]))
        inhalt.append(befund_tabelle)
        inhalt.append(Spacer(1, 5 * mm))

        # --- Nächste Wartung ---
        inhalt.append(Paragraph("Nächste Wartung", stil_abschnitt))

        naechste_text = naechste_wartung if naechste_wartung else '—'
        naechste_tabelle = Table(
            [['Nächste Wartung fällig am:', naechste_text]],
            colWidths=[70 * mm, 100 * mm]
        )
        naechste_tabelle.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#333333')),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fff8e1')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('PADDING', (0, 0), (-1, -1), 7),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        inhalt.append(naechste_tabelle)
        inhalt.append(Spacer(1, 12 * mm))

        # --- Unterschriftenzeile ---
        inhalt.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cccccc'), spaceAfter=3 * mm))

        unterschrift_data = [
            ['___________________________', '___________________________'],
            ['Datum, Unterschrift Techniker', 'Datum, Unterschrift Kunde'],
        ]
        unterschrift_tabelle = Table(unterschrift_data, colWidths=[85 * mm, 85 * mm])
        unterschrift_tabelle.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#666666')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 1), (-1, 1), 2),
        ]))
        inhalt.append(unterschrift_tabelle)

        # PDF generieren
        doc.build(inhalt)
        return True

    except Exception as e:
        print(f"Fehler beim Erstellen des Wartungsprotokolls: {e}")
        return False

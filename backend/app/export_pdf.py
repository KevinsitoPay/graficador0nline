from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from datetime import datetime
import os


def generar_pdf(brackets_data: list, unpaired_data: list, output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=20,
        alignment=1
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.HexColor('#1a1a2e')
    )
    
    story = []
    
    story.append(Paragraph("Sistema de Emparejamiento - Taekwondo", title_style))
    story.append(Paragraph(f"Fecha de generación: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    total_comp = sum(len(b.get('competidores', [])) for b in brackets_data)
    total_brackets = len(brackets_data)
    sin_rival = len(unpaired_data)
    
    story.append(Paragraph("Resumen General", heading_style))
    story.append(Paragraph(f"Total competidores emparejados: {total_comp}", styles['Normal']))
    story.append(Paragraph(f"Total brackets generados: {total_brackets}", styles['Normal']))
    story.append(Paragraph(f"Competidores sin rival: {sin_rival}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("Brackets por Bloque", heading_style))
    
    bloques_orden = [
        "Adultos Grupo 1", "Adultos Grupo 2", "Infantil Azul", "Infantil Verde",
        "Infantil Amarilla", "Infantil Blanca", "Pre-Taekwondo", "Infantil Marrón",
        "Infantil Roja", "Infantil Negra"
    ]
    
    brackets_por_bloque = {}
    for b in brackets_data:
        bloque = b.get('competidores', [{}])[0].get('bloque', 'Unknown')
        if bloque not in brackets_por_bloque:
            brackets_por_bloque[bloque] = []
        brackets_por_bloque[bloque].append(b)
    
    for bloque in bloques_orden:
        if bloque not in brackets_por_bloque:
            continue
        
        story.append(Paragraph(f"Bloque: {bloque}", styles['Heading3']))
        
        for bracket in brackets_por_bloque[bloque]:
            comps = bracket.get('competidores', [])
            
            data = [['#', 'Nombre', 'Edad', 'Peso', 'Cinta', 'Doyang']]
            for c in comps:
                data.append([
                    str(c.get('numero_competidor', '')),
                    f"{c.get('nombre', '')} {c.get('apellido', '')}",
                    str(c.get('edad', '')),
                    f"{c.get('peso_kg', '')} kg",
                    c.get('cinta_block', ''),
                    c.get('doyang', '')
                ])
            
            table = Table(data, colWidths=[1.5*cm, 4*cm, 1.5*cm, 2*cm, 2.5*cm, 2.5*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            ]))
            
            score = bracket.get('score', 0)
            score_color = 'green' if score >= 70 else 'orange' if score >= 50 else 'red'
            story.append(Paragraph(f"Bracket #{bracket.get('numero', '')} - Score: {score}%", styles['Normal']))
            story.append(table)
            story.append(Spacer(1, 15))
    
    if unpaired_data:
        story.append(PageBreak())
        story.append(Paragraph("Competidores Sin Rival", heading_style))
        
        data = [['Nombre', 'Bloque', 'Edad', 'Peso', 'Cinta', 'Doyang', 'Razón']]
        for u in unpaired_data:
            comp = u.get('competidor', {})
            data.append([
                f"{comp.get('nombre', '')} {comp.get('apellido', '')}",
                comp.get('bloque', ''),
                str(comp.get('edad', '')),
                f"{comp.get('peso_kg', '')} kg",
                comp.get('cinta_block', ''),
                comp.get('doyang', ''),
                u.get('razon', '')
            ])
        
        table = Table(data, colWidths=[3.5*cm, 2.5*cm, 1.5*cm, 1.5*cm, 2*cm, 2*cm, 3*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8b0000')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ffe6e6')]),
        ]))
        story.append(table)
    
    doc.build(story)
    return output_path
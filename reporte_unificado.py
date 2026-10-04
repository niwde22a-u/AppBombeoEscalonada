import os
import sys
import openpyxl
from openpyxl.chart import LineChart, Reference
from openpyxl.chart.series import Series

# BLINDAJE PARA ANDROID: Redirigir la ruta de configuración para evitar el error de ZIP
os.environ["MATPLOTLIBDATA"] = os.getcwd()

import matplotlib
matplotlib.use('Agg') # Forzar motor silencioso de dibujo sin interfaz
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def redibujar_plano_mecanico(prof_total, diam_pozo, prof_bomba, lista_filtros, nivel_estatico, nivel_dinamico):
    fig, ax = plt.subplots(figsize=(5, 9))
    ax.set_ylim(prof_total + 10, -5)
    ax.set_xlim(-diam_pozo, diam_pozo)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.set_ylabel("Profundidad (metros)", fontsize=11, fontweight='bold')
    ax.set_xticks([]) 
    
    ax.axhline(0, color='brown', lw=3)
    radio = diam_pozo / 2
    ax.plot([-radio, -radio], [0, prof_total], color='black', lw=2.5)
    ax.plot([radio, radio], [0, prof_total], color='black', lw=2.5)
    ax.plot([-radio, radio], [prof_total, prof_total], color='black', lw=2.5) 
    
    texto_filtros = "Filtros:\n"
    for inicio, fin in lista_filtros:
        ax.plot([-radio, -radio], [inicio, fin], color='darkorange', lw=4, linestyle='--')
        ax.plot([radio, radio], [inicio, fin], color='darkorange', lw=4, linestyle='--')
        texto_filtros += f"• {inicio}m a {fin}m\n"
    
    r_tub = radio * 0.25
    ax.plot([-r_tub, -r_tub], [0, prof_bomba], color='blue', lw=2)
    ax.plot([r_tub, r_tub], [0, prof_bomba], color='blue', lw=2)
    
    ancho_bomba = radio * 1.2
    alto_bomba = prof_total * 0.05
    bomba = patches.Rectangle((-ancho_bomba/2, prof_bomba - alto_bomba), ancho_bomba, alto_bomba, 
                              edgecolor='black', facecolor='darkblue', zorder=5)
    ax.add_patch(bomba)
    
    ax.axhline(nivel_estatico, color='cyan', linestyle=':', lw=2)
    ax.axhline(nivel_dinamico, color='blue', linestyle='-.', lw=2)
    
    ax.text(0, -2, f"Ø Pozo: {diam_pozo}\"", ha='center', va='bottom', fontweight='bold')
    ax.text(ancho_bomba, prof_bomba - (alto_bomba/2), f"Bomba a {prof_bomba}m", va='center', fontweight='bold', color='darkblue')
    ax.text(radio + 0.5, prof_total / 2, texto_filtros.strip(), va='center', color='darkorange', fontweight='bold')
    ax.text(0, prof_total + 4, f"Profundidad Total: {prof_total}m", ha='center', fontweight='bold')
    ax.text(-radio - 0.5, nivel_estatico, f"N. Estático: {nivel_estatico}m", ha='right', color='darkcyan')
    ax.text(-radio - 0.5, nivel_dinamico, f"N. Dinámico: {nivel_dinamico}m", ha='right', color='blue')

    plt.title("PERFIL CONSTRUCTIVO DEL POZO", fontsize=12, fontweight='bold', pad=15)
    plt.tight_layout()
    plt.savefig("plano_pozo.png", dpi=200)
    plt.close()

def generar_reporte_unificado(id_val, diam_val, prof_val, bomba_val, caudal_q1, caudal_q2, caudal_q3, filtros_raw, n_estatico, n_dinamico_max, lecturas_campo):
    lista_filtros = []
    texto_excel_filtros = ""
    try:
        tramos = filtros_raw.replace(" ", "").split(",")
        for t in tramos:
            if "-" in t:
                ini, fin = t.split("-")
                lista_filtros.append((int(ini), int(fin)))
                texto_excel_filtros += f"[{ini}-{fin}m] "
    except Exception:
        lista_filtros = [(int(prof_val * 0.7), int(prof_val * 0.9))]
        texto_excel_filtros = "Ajuste Automático"
    redibujar_plano_mecanico(prof_val, diam_val, bomba_val, lista_filtros, n_estatico, n_dinamico_max)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Prueba de Bombeo Escalonada"

    ws['A1'] = "REPORTE TÉCNICO DE PRUEBA DE BOMBEO ESCALONADA"
    ws['A1'].font = openpyxl.styles.Font(bold=True, size=14, color="003366")
    
    ws['A3'] = "Parámetro Constructivo"
    ws['B3'] = "Valor Registrado"
    
    datos_pozo = [
        ("ID del Pozo Profundo", id_val),
        ("Diámetro del Pozo (pulgadas)", diam_val),
        ("Profundidad Total (metros)", prof_val),
        ("Sectores con Filtros", texto_excel_filtros.strip()),  
        ("Profundidad de la Bomba (metros)", bomba_val),
        ("Diámetro Tubo Expulsión (pulgadas)", 3),
        ("Nivel Estático Inicial (NE - m)", n_estatico),
        ("Nivel Dinámico Máximo (ND - m)", n_dinamico_max),
        ("Caudal Escalón 1 (Q1 - L/s)", caudal_q1),
        ("Caudal Escalón 2 (Q2 - L/s)", caudal_q2),
        ("Caudal Escalón 3 (Q3 - L/s)", caudal_q3),
    ]
    
    for fila, (param, val) in enumerate(datos_pozo, start=4):
        ws.cell(row=fila, column=1, value=param)
        ws.cell(row=fila, column=2, value=val)

    inicio_tabla_campo = 17
    ws.cell(row=inicio_tabla_campo, column=1, value="Tiempo (min)")
    ws.cell(row=inicio_tabla_campo, column=2, value="ND (m)")
    ws.cell(row=inicio_tabla_campo, column=3, value="Abatimiento (m)")
    ws.cell(row=inicio_tabla_campo, column=4, value="Escalón")
    
    font_bold = openpyxl.styles.Font(bold=True, color="FFFFFF")
    fill_header = openpyxl.styles.PatternFill(start_color="003366", end_color="003366", fill_type="solid")
    
    for col in range(1, 5):
        ws.cell(row=3, column=col).font = font_bold
        ws.cell(row=3, column=col).fill = fill_header
        ws.cell(row=inicio_tabla_campo, column=col).font = font_bold
        ws.cell(row=inicio_tabla_campo, column=col).fill = fill_header

    datos_finales = lecturas_campo if lecturas_campo else [(1, n_estatico + 1, 1, 1)]
    
    for idx, (tiempo, n_dinamico, abatimiento, esc_id) in enumerate(datos_finales):
        row_num = inicio_tabla_campo + 1 + idx
        ws.cell(row=row_num, column=1, value=tiempo)
        ws.cell(row=row_num, column=2, value=n_dinamico)
        ws.cell(row=row_num, column=3, value=abatimiento)
        ws.cell(row=row_num, column=4, value=f"Escalón {esc_id}")

    chart = LineChart()
    chart.title = "Curvas de Abatimiento Escalonadas"
    chart.y_axis.title = "Abatimiento (m)"
    chart.x_axis.title = "Tiempo Transcurrido (min)"
    chart.width = 18
    chart.height = 12
    chart.y_axis.scaling.orientation = "maxMin"
    chart.x_axis.scaling.logBase = 10

    valores_de_abatimiento = Reference(ws, min_col=3, min_row=inicio_tabla_campo, max_row=inicio_tabla_campo + len(datos_finales))
    categorias_de_tiempo = Reference(ws, min_col=1, min_row=inicio_tabla_campo + 1, max_row=inicio_tabla_campo + len(datos_finales))
    
    # Integración directa compatible y estable
    chart.add_data(valores_de_abatimiento, titles_from_data=True)
    chart.set_categories(categorias_de_tiempo)

    ws.add_chart(chart, "F3")

    try:
        img = openpyxl.drawing.image.Image('plano_pozo.png')
        img.width = 300
        img.height = 540
        ws.add_image(img, "P3")
    except FileNotFoundError:
        pass

    ws.column_dimensions['A'].width = 18
    ws.column_dimensions['B'].width = 18
    ws.column_dimensions['C'].width = 18
    ws.column_dimensions['D'].width = 18

    nombre_archivo = f"reporte_{id_val}_completo.xlsx"
    wb.save(nombre_archivo)

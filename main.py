import flet as ft
import time
import threading
from reporte_unificado import generar_reporte_unificado
from reporte_pdf import generar_informe_pdf

def main(page: ft.Page):
    page.title = "App Hidrogeológica Móvil - Multi-Modo"
    page.scroll = ft.ScrollMode.AUTO
    
    # Listas en memoria
    lista_completa_mediciones = []
    lista_aux_nd = []
    
    tiempo_inicio = 0  
    cronometro_corriendo = False

    # --- COMPONENTES PESTAÑA 1 (DISEÑO CONSTRUCTIVO) ---
    id_pozo = ft.TextField(label="ID del Pozo", value="PP-01", width=300)
    diam_pozo = ft.TextField(label="Diámetro del Pozo (pulgadas)", value="10", width=300)
    prof_total = ft.TextField(label="Profundidad Total (metros)", value="100", width=300)
    prof_bomba = ft.TextField(label="Profundidad de la Bomba (metros)", value="60", width=300)
    filtros = ft.TextField(label="Tramos de Filtros (m)", value="40-50, 70-85", helper_text="Ej: 40-50, 70-85", width=300)
    caudal_q1 = ft.TextField(label="Caudal Escalón 1 (Q1 - L/s)", value="5", width=300)
    caudal_q2 = ft.TextField(label="Caudal Escalón 2 (Q2 - L/s)", value="10", width=300)
    caudal_q3 = ft.TextField(label="Caudal Escalón 3 (Q3 - L/s)", value="15", width=300)
    nivel_estatico = ft.TextField(label="Nivel Estático Inicial (NE - metros)", value="20.0", width=300)

    # --- COMPONENTES PESTAÑA 2 (MONITOREO Y CAPTURA) ---
    txt_reloj = ft.Text("00:00:00", size=36, weight=ft.FontWeight.BOLD, color="blue")
    
    # NUEVO: Selector de Modo (Tiempo Real vs Manual)
    def conmutar_modo(e):
        if switch_modo.value: # Si está activado (Modo Manual)
            panel_cronometro.visible = False
            input_tiempo.disabled = False
            input_tiempo.value = ""
            input_tiempo.hint_text = "ej: 30"
            detener_prueba(None) # Pausa el reloj si estaba corriendo
        else: # Si está desactivado (Modo Cronómetro)
            panel_cronometro.visible = True
            input_tiempo.disabled = True
            input_tiempo.value = "Auto"
        page.update()

    switch_modo = ft.Switch(
        label="Modo Llenado Manual (Apuntes Pasados)", 
        value=False, 
        on_change=conmutar_modo
    )

    selector_escalon = ft.Dropdown(
        label="Escalón Activo",
        value="1",
        options=[
            ft.dropdown.Option("1", "Escalón 1 (Q1)"),
            ft.dropdown.Option("2", "Escalón 2 (Q2)"),
            ft.dropdown.Option("3", "Escalón 3 (Q3)"),
        ],
        width=150
    )
    
    # Casillas de entrada de datos
    input_tiempo = ft.TextField(label="Tiempo (min)", value="Auto", disabled=True, width=110)
    input_nivel_dinamico = ft.TextField(label="Nivel Dinámico (ND - m)", hint_text="ej: 21.50", width=160)
    
    tabla_datos = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Tiempo (min)")),
            ft.DataColumn(ft.Text("Nivel Dinámico (m)")),
            ft.DataColumn(ft.Text("Abatimiento Calc (m)")),
            ft.DataColumn(ft.Text("Escalón")), 
            ft.DataColumn(ft.Text("Acción")),
        ],
        rows=[]
    )

    estado_txt = ft.Text("", size=16, color="green", weight=ft.FontWeight.BOLD)

    # Hilos del Reloj
    def actualizar_reloj_loop():
        nonlocal tiempo_inicio, cronometro_corriendo
        while cronometro_corriendo:
            segundos_transcurridos = int(time.time() - tiempo_inicio)
            horas = segundos_transcurridos // 3600
            minutos = (segundos_transcurridos % 3600) // 60
            segundos = segundos_transcurridos % 60
            txt_reloj.value = f"{horas:02d}:{minutos:02d}:{segundos:02d}"
            page.update()
            time.sleep(1)

    def iniciar_prueba(e):
        nonlocal tiempo_inicio, cronometro_corriendo
        if not cronometro_corriendo:
            tiempo_inicio = time.time()
            cronometro_corriendo = True
            btn_play.disabled = True
            btn_stop.disabled = False
            estado_txt.value = "▶️ Cronómetro en marcha para prueba en vivo."
            estado_txt.color = "green"
            hilo = threading.Thread(target=actualizar_reloj_loop, daemon=True)
            hilo.start()
            page.update()

    def detener_prueba(e):
        nonlocal cronometro_corriendo
        cronometro_corriendo = False
        btn_play.disabled = False
        btn_stop.disabled = True
        txt_reloj.value = "00:00:00"
        page.update()

    def eliminar_fila(e, registro, fila_visual, nd_valor):
        lista_completa_mediciones.remove(registro)
        lista_aux_nd.remove(nd_valor)
        tabla_datos.rows.remove(fila_visual)
        estado_txt.value = "Lectura eliminada de la memoria."
        estado_txt.color = "orange"
        page.update()

    # LÓGICA DE AGREGAR MEDICIONES INTEGRADA (HÍBRIDA)
    def agregar_lectura(e):
        nonlocal tiempo_inicio, cronometro_corriendo
        try:
            ne = float(nivel_estatico.value)
            nd = float(input_nivel_dinamico.value)
            esc_id = int(selector_escalon.value)
            abatimiento_calculado = round(nd - ne, 2)
            
            if abatimiento_calculado < 0:
                estado_txt.value = "⚠️ Error: El Nivel Dinámico no puede ser menor al Estático."
                estado_txt.color = "red"
                page.update()
                return

            # DETERMINAR EL TIEMPO SEGÚN EL MODO SELECCIONADO
            if switch_modo.value: # Modo Llenado Manual
                if not input_tiempo.value:
                    estado_txt.value = "⚠️ Por favor, digita el tiempo en minutos."
                    estado_txt.color = "red"
                    page.update()
                    return
                t_minutos = float(input_tiempo.value)
            else: # Modo Cronómetro en Vivo
                if not cronometro_corriendo and len(lista_completa_mediciones) == 0:
                    estado_txt.value = "⚠️ Inicia el cronómetro primero para registrar en vivo."
                    estado_txt.color = "red"
                    page.update()
                    return
                segundos_totales = time.time() - tiempo_inicio if cronometro_corriendo else 0
                t_minutos = round(segundos_totales / 60.0, 2)
                if t_minutos == 0:
                    t_minutos = 0.01

            nueva_tripleta = (t_minutos, nd, abatimiento_calculado, esc_id)
            lista_completa_mediciones.append(nueva_tripleta)
            lista_aux_nd.append(nd)
            
            nueva_fila_data = ft.DataRow(cells=[])
            nueva_fila_data.cells = [
                ft.DataCell(ft.Text(str(t_minutos))),
                ft.DataCell(ft.Text(str(nd))),
                ft.DataCell(ft.Text(str(abatimiento_calculado))),
                ft.DataCell(ft.Text(f"E{esc_id}")), 
                ft.DataCell(
                    ft.IconButton(
                        icon=ft.icons.DELETE_OUTLINE, icon_color="red",
                        on_click=lambda e, trip=nueva_tripleta, fila=nueva_fila_data, nd_val=nd: eliminar_fila(e, trip, fila, nd_val)
                    )
                ),
            ]
            
            tabla_datos.rows.append(nueva_fila_data)
            input_nivel_dinamico.value = ""
            if switch_modo.value:
                input_tiempo.value = "" # Limpia el casillero de tiempo para la libreta pasados
            
            estado_txt.value = f"✅ Registrado: {t_minutos} min | ND: {nd} m | Abatimiento: {abatimiento_calculado} m"
            estado_txt.color = "blue"
            page.update()
            
        except ValueError:
            estado_txt.value = "⚠️ Digita números válidos en los campos de entrada."
            estado_txt.color = "red"
            page.update()

    def despachar_reporte(e):
        try:
            estado_txt.value = "Generando archivos técnicos consolidados..."
            estado_txt.color = "orange"
            page.update()
            
            ne_val = float(nivel_estatico.value)
            nd_max_val = max(lista_aux_nd) if lista_aux_nd else (ne_val + 25)
            
            # Exportar a Excel
            generar_reporte_unificado(
                id_val=str(id_pozo.value), diam_val=int(diam_pozo.value),
                prof_val=int(prof_total.value), bomba_val=int(prof_bomba.value),
                caudal_q1=int(caudal_q1.value), caudal_q2=int(caudal_q2.value), caudal_q3=int(caudal_q3.value), 
                filtros_raw=str(filtros.value), n_estatico=ne_val, n_dinamico_max=nd_max_val,
                lecturas_campo=lista_completa_mediciones
            )
            
            # Exportar a PDF
            generar_informe_pdf(
                id_val=str(id_pozo.value), diam_val=int(diam_pozo.value),
                prof_val=int(prof_total.value), bomba_val=int(prof_bomba.value),
                q1=int(caudal_q1.value), q2=int(caudal_q2.value), q3=int(caudal_q3.value),
                filtros_raw=str(filtros.value), n_estatico=ne_val, n_dinamico_max=nd_max_val,
                lecturas_campo=lista_completa_mediciones
            )
            
            estado_txt.value = "¡Éxito! Archivos Excel y PDF generados correctamente."
            estado_txt.color = "green"
            page.update()
        except Exception as ex:
            estado_txt.value = f"⚠️ Error de guardado: Asegúrate de cerrar los archivos previos."
            estado_txt.color = "red"
            page.update()

    # =========================================================================
    # NAVEGACIÓN POR PESTAÑAS Y CONTROL DE VISTAS (LAYOUT INFERIOR)
    # =========================================================================
    def cambiar_pestana(e):
        index = e.control.selected_index
        vista_diseno.visible = (index == 0)
        vista_campo.visible = (index == 1)
        page.update()

    # Contenedor de la Pestaña 1: Estructura, filtros y los 3 caudales escalonados
    vista_diseno = ft.Column(
        controls=[
            ft.Text("Estructura del Pozo Profundo", size=18, weight=ft.FontWeight.BOLD),
            id_pozo, diam_pozo, prof_total, prof_bomba, filtros, nivel_estatico,
            ft.Divider(),
            ft.Text("Configuración de Caudales Escalonados", size=14, weight=ft.FontWeight.BOLD, color="blue"),
            caudal_q1, caudal_q2, caudal_q3
        ],
        visible=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )

    # Botones de control físico y panel del Cronómetro Digital
    btn_play = ft.IconButton(icon=ft.icons.PLAY_ARROW, icon_color="green", icon_size=32, on_click=iniciar_prueba)
    btn_stop = ft.IconButton(icon=ft.icons.PAUSE, icon_color="orange", icon_size=32, disabled=True, on_click=detener_prueba)
    panel_cronometro = ft.Row([btn_play, btn_stop], alignment=ft.MainAxisAlignment.CENTER)

    # Contenedor de la Pestaña 2: Conmutador de modo, entradas de datos y tabla dinámica
    vista_campo = ft.Column(
        controls=[
            ft.Text("Panel de Captura de Datos", size=18, weight=ft.FontWeight.BOLD),
            switch_modo, 
            ft.Container(height=5),
            panel_cronometro, 
            txt_reloj,
            ft.Divider(),
            ft.Row([selector_escalon, input_tiempo, input_nivel_dinamico], alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(height=5),
            ft.ElevatedButton("Registrar Medición", icon=ft.icons.SAVE, on_click=agregar_lectura),
            ft.Divider(),
            tabla_datos
        ],
        visible=False, horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )

    # Barra inferior táctil estilo nativo móvil (Diseño Pozo / Captura Datos)
    page.navigation_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationDestination(icon=ft.icons.BUILD, label="Diseño Pozo"),
            ft.NavigationDestination(icon=ft.icons.TIMELAPSE, label="Captura Datos"),
        ],
        on_change=cambiar_pestana
    )

    # Ensamble final del lienzo general de la aplicación con botón maestro de exportación
    page.add(
        ft.Column([
            ft.Text("Módulo de Prueba de Bombeo", size=22, weight=ft.FontWeight.BOLD, color="blue"),
            ft.Container(height=10),
            vista_diseno,
            vista_campo,
            ft.Container(height=15),
            ft.ElevatedButton("Exportar Reporte Técnico", icon=ft.icons.DOCUMENT_SCANNER, on_click=despachar_reporte),
            estado_txt
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )

# Inicialización absoluta del entorno móvil Flet
if __name__ == "__main__":
    ft.app(target=main)

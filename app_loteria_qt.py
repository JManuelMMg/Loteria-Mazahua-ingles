"""Interfaz Qt para Lotería Mazahua; datos y medios permanecen en SQLite."""
from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import time
import queue
from uuid import uuid4

from PySide6.QtCore import (
    Qt, QEasingCurve, QSize, QTimer, QSettings,
)
from PySide6.QtGui import QPixmap, QIcon, QPainter, QColor, QFont
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QPushButton,
    QStackedWidget, QVBoxLayout, QWidget, QAbstractItemView,
    QGraphicsDropShadowEffect, QScrollArea,
)
from ffpyplayer.player import MediaPlayer

from base_datos import (
    IDIOMAS, RUTA_BD, cargar_medio, conectar, crear_carta, crear_esquema,
    eliminar_carta, guardar_textos, importar_archivos, importar_audios_ingles,
    obtener_carta, obtener_medio, resumen, emparejar_lectura, reasignar_uid,
    obtener_checksum,
)

from lector_rfid import LectorRFID, listar_puertos, comando_grabar


# ==============================================================================
# ESTILOS
# ==============================================================================

ESTILO_CLARO = """
QMainWindow, #main { background-color: #F9FAFB; }
* { font-family: 'Segoe UI', sans-serif; color: #111827; }

/* Barra lateral gris pizarra neutro (NO café) */
#nav {
    background: #111827;
    min-width: 260px; max-width: 260px; border-right: 1px solid #1F2937;
}
#brandMark, #navLabel { color: #FBBF24; font-size: 11px; font-weight: 800; letter-spacing: 2px; }
#brandTitle { color: #FFFFFF; font-family: Georgia, serif; font-size: 28px; font-weight: 900; }
#brandText, #navFoot { color: #9CA3AF; font-size: 13px; }

QPushButton#navButton {
    color: #E5E7EB; text-align: left; background: transparent; border: 0;
    border-radius: 12px; padding: 12px 16px; font-size: 15px; font-weight: 600;
}
QPushButton#navButton:hover { color: #FFFFFF; background: rgba(251,191,36,0.12); }
QPushButton#navButton:checked {
    color: #FBBF24; background: rgba(251,191,36,0.18);
    border-left: 4px solid #FBBF24; font-weight: 700;
}

/* Textos */
#eyebrow { color: #6B7280; font-size: 12px; font-weight: 800; letter-spacing: 2px; }
#title { font-family: Georgia, serif; font-size: 34px; font-weight: 900; color: #111827; }
#sub { color: #6B7280; font-size: 15px; }

/* Tarjetas blancas limpias con sombra suave */
#card, #editor, #player {
    background: #FFFFFF; border-radius: 20px;
    border: 1px solid #E5E7EB;
}
#preview {
    background: #F3F4F6;
    border-radius: 24px;
    border: 2px solid #FBBF24;
}

#wordCard {
    background: #FFFFFF;
    border: 2px solid #E5E7EB;
    border-radius: 16px;
}
#wordCard:hover { border-color: #FBBF24; background: #FFFBEB; }
#lang { font-size: 12px; font-weight: 900; letter-spacing: 1.5px; }
#word { font-family: Georgia, serif; font-size: 24px; font-weight: 800; color: #111827; }

#play { color: white; border: 0; border-radius: 24px; font-size: 16px; font-weight: 800; min-width: 48px; min-height: 48px; }

/* Inputs */
#search, #field {
    background: #FFFFFF; border: 2px solid #D1D5DB; border-radius: 12px;
    padding: 10px 14px; font-size: 15px; color: #111827;
}
#search:focus, #field:focus { border-color: #FBBF24; background: #FFFBEB; }

/* Lista */
#list { background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 16px; padding: 8px; }
#list::item {
    padding: 12px; border-radius: 12px; margin: 4px;
    background: #F9FAFB; border: 2px solid transparent; color: #111827;
}
#list::item:hover { border-color: #FBBF24; background: #FFFBEB; }
#list::item:selected {
    background: #FBBF24; color: #111827; border: 2px solid #FBBF24; font-weight: 700;
}

/* Botones */
#action {
    background: #111827; color: white; border: 0;
    border-radius: 12px; padding: 12px 18px; font-weight: 800; font-size: 14px;
}
#action:hover { background: #1F2937; }

#soft {
    background: #F3F4F6; border: 0; border-radius: 12px;
    padding: 10px 15px; font-weight: 700; color: #111827;
}
#soft:hover { background: #E5E7EB; }

#danger {
    background: #FEF2F2; color: #B91C1C; border: 1px solid #FECACA;
    border-radius: 12px; padding: 10px 14px; font-weight: 700;
}
#danger:hover { background: #FEE2E2; }

/* Config */
#configCard { background: #FFFFFF; border-radius: 20px; padding: 6px; border: 1px solid #E5E7EB; }
#configTitle { font-family: Georgia, serif; font-size: 20px; font-weight: 900; color: #111827; }

/* Estados */
#statusGood { color: #15803D; font-weight: 800; font-size: 14px; }
#statusMuted { color: #6B7280; font-size: 14px; }

/* Scroll general */
QScrollBar:vertical { background: #F3F4F6; width: 12px; border-radius: 6px; }
QScrollBar::handle:vertical { background: #D1D5DB; border-radius: 6px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #9CA3AF; }

/* Scroll menú */
#navScroll { background: transparent; border: 0; }
#navContent { background: transparent; }
#navScroll QScrollBar:vertical { background: transparent; width: 8px; margin: 4px; }
#navScroll QScrollBar::handle:vertical { background: rgba(251,191,36,0.55); border-radius: 4px; min-height: 30px; }
#navScroll QScrollBar::handle:vertical:hover { background: #FBBF24; }
#navScroll QScrollBar::add-line:vertical,
#navScroll QScrollBar::sub-line:vertical { height: 0; }

#navLogo { margin: 8px 0; }
"""

ESTILO_OSCURO = """
QMainWindow, #main { background-color: #121212; }
* { font-family: 'Segoe UI', sans-serif; color: #ECEFF1; }

#nav { background: #000000; min-width: 260px; max-width: 260px; border-right: 1px solid #333; }
#brandMark, #navLabel { color: #FFD700; font-size: 11px; font-weight: 800; letter-spacing: 2px; }
#brandTitle { color: #FFFFFF; font-family: Georgia, serif; font-size: 28px; font-weight: 900; }
#brandText, #navFoot { color: #90A4AE; font-size: 13px; }

QPushButton#navButton {
    color: #B0BEC5; text-align: left; background: transparent; border: 0;
    border-radius: 12px; padding: 12px 16px; font-size: 15px; font-weight: 600;
}
QPushButton#navButton:hover { color: #FFFFFF; background: rgba(255,215,0,0.2); }
QPushButton#navButton:checked {
    color: #FFD700; background: rgba(255,215,0,0.28);
    border-left: 4px solid #FFD700; font-weight: 700;
}

#eyebrow { color: #B0BEC5; font-size: 12px; font-weight: 800; letter-spacing: 2px; }
#title { font-family: Georgia, serif; font-size: 34px; font-weight: 900; color: #FFFFFF; }
#sub { color: #90A4AE; font-size: 15px; }

#card, #editor, #player { background: #1E1E1E; border-radius: 24px; border: 1px solid #333333; }
#preview {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #263238, stop:1 #1C2833);
    border-radius: 32px; border: 3px solid #FFD700;
}

#wordCard { background: #1E1E1E; border: 2px solid #333333; border-radius: 20px; }
#wordCard:hover { border: 3px solid #FFD700; background: #263238; }
#lang { font-size: 12px; font-weight: 900; letter-spacing: 1.5px; color: #FFD700; }
#word { font-family: Georgia, serif; font-size: 24px; font-weight: 800; color: #FFFFFF; }

#play { color: #121212; border: 0; border-radius: 24px; font-size: 16px; font-weight: 800; min-width: 48px; min-height: 48px; }

#search, #field {
    background: #263238; border: 2px solid #37474F; border-radius: 12px;
    padding: 10px 14px; font-size: 15px; color: #ECEFF1;
}
#search:focus, #field:focus { border: 3px solid #FFD700; background: #37474F; }

#list { background: #121212; border: 0; border-radius: 24px; padding: 10px; }
#list::item {
    padding: 12px; border-radius: 14px; margin: 4px;
    background: #1E1E1E; border: 2px solid transparent; color: #ECEFF1;
}
#list::item:hover { border: 2px solid #FFD700; background: #263238; }
#list::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FFD700, stop:1 #FFAB00);
    color: #000000; border: 2px solid #FFD700; font-weight: 700;
}

#action {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FFD700, stop:1 #FFAB00);
    color: #000000; border: 0; border-radius: 12px; padding: 12px 18px; font-weight: 800; font-size: 14px;
}
#action:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FFAB00, stop:1 #FFC107); }

#soft {
    background: #263238; border: 0; border-radius: 12px; padding: 10px 15px; font-weight: 700; color: #ECEFF1;
}
#soft:hover { background: #37474F; }

#danger { background: #3E2723; color: #FF8A80; border: 2px solid #5D4037; border-radius: 12px; padding: 10px 14px; font-weight: 700; }
#danger:hover { background: #5D4037; }

#configCard { background: #1E1E1E; border-radius: 24px; padding: 6px; border: 1px solid #333333; }
#configTitle { font-family: Georgia, serif; font-size: 20px; font-weight: 900; color: #FFFFFF; }

#statusGood { color: #66BB6A; font-weight: 800; font-size: 14px; }
#statusMuted { color: #90A4AE; font-size: 14px; }

QScrollBar:vertical { background: #121212; width: 12px; border-radius: 6px; }
QScrollBar::handle:vertical { background: #FFD700; border-radius: 6px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #FFAB00; }

#navScroll { background: transparent; border: 0; }
#navContent { background: transparent; }
#navScroll QScrollBar:vertical { background: transparent; width: 8px; margin: 4px; }
#navScroll QScrollBar::handle:vertical { background: rgba(255,215,0,0.55); border-radius: 4px; min-height: 30px; }
#navScroll QScrollBar::handle:vertical:hover { background: #FFD700; }
#navScroll QScrollBar::add-line:vertical,
#navScroll QScrollBar::sub-line:vertical { height: 0; }

#navLogo { margin: 8px 0; }
"""

ESTILO_DIALOGO_CLARO = """
QDialog { background-color: #FFFFFF; color: #111827; }
QLabel { color: #111827; }
QPushButton {
    background: #F3F4F6; border: 1px solid #D1D5DB; border-radius: 8px;
    padding: 8px 16px; color: #111827; font-weight: 600;
}
QPushButton:hover { background: #E5E7EB; }
QPushButton:default { background: #FBBF24; border: 1px solid #F59E0B; color: #111827; }
"""

ESTILO_DIALOGO_OSCURO = """
QDialog { background-color: #1E1E1E; color: #ECEFF1; }
QLabel { color: #ECEFF1; }
QPushButton {
    background: #263238; border: 1px solid #37474F; border-radius: 8px;
    padding: 8px 16px; color: #ECEFF1; font-weight: 600;
}
QPushButton:hover { background: #37474F; }
QPushButton:default { background: #FFD700; border: 1px solid #FFAB00; color: #000000; }
"""

ESTILO = ESTILO_CLARO

COLORES_IDIOMA = {"español": "#e67e22", "mazahua": "#27ae60", "inglés": "#2980b9"}


class VentanaLoteria(QMainWindow):
    def __init__(self):
        super().__init__()
        self.conexion = conectar()
        crear_esquema(self.conexion)

        self.carta_actual: int | None = None
        self.reproductor: MediaPlayer | None = None
        self.archivo_audio: Path | None = None
        self.inicio_audio = 0.0
        self.idioma_audio: str | None = None
        self._audio_activo = False

        self._secuencia: list[str] = []
        self._secuencia_carta: int | None = None
        self._timer_secuencia = QTimer(self)
        self._timer_secuencia.setSingleShot(True)
        self._timer_secuencia.timeout.connect(self._siguiente_en_secuencia)

        self.lector: LectorRFID | None = None
        self.lecturas: queue.Queue = queue.Queue()

        self.reloj_audio = QTimer(self)
        self.reloj_audio.setInterval(100)
        self.reloj_audio.timeout.connect(self._vigilar_audio)

        self.reloj_lector = QTimer(self)
        self.reloj_lector.setInterval(120)
        self.reloj_lector.timeout.connect(self._revisar_lecturas)
        self.reloj_lector.start()

        self._settings = QSettings("LoteriaMazahua", "App")
        self.tema_oscuro = self._settings.value("tema_oscuro", False, type=bool)

        self.uid_a_carta = {}
        self.menu_colapsado = False
        self.tarjetas_idioma = {}

        self.setWindowTitle("Lotería Mazahua")
        self.resize(1280, 800)
        self.setMinimumSize(1000, 650)

        # 🔽 Ícono de la ventana (logo.png en la raíz)
        ruta_logo = Path(__file__).parent / "logo.ico"
        if ruta_logo.exists():
            self.setWindowIcon(QIcon(str(ruta_logo)))

        self.setStyleSheet(ESTILO_OSCURO if self.tema_oscuro else ESTILO_CLARO)
        self._crear_ui()
        self.recargar_cartas()
        self._aplicar_tema()

        # Detecta cambios hechos por otra instancia o herramienta que use la misma BD.
        self._ultimo_checksum = obtener_checksum(self.conexion)
        self._timer_sincronizacion = QTimer(self)
        self._timer_sincronizacion.setInterval(2000)
        self._timer_sincronizacion.timeout.connect(self._verificar_cambios_bd)
        self._timer_sincronizacion.start()

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------

    def estilo_dialogo(self):
        return ESTILO_DIALOGO_OSCURO if self.tema_oscuro else ESTILO_DIALOGO_CLARO

    def etiqueta(self, texto: str, nombre="", padre=None) -> QLabel:
        label = QLabel(texto, padre)
        if nombre:
            label.setObjectName(nombre)
        label.setWordWrap(True)
        return label

    def boton(self, texto, funcion, nombre="action") -> QPushButton:
        boton = QPushButton(texto)
        boton.setObjectName(nombre)
        boton.clicked.connect(funcion)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(2, 2)
        boton.setGraphicsEffect(shadow)
        return boton

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _crear_ui(self):
        raiz = QWidget(objectName="main")
        self.setCentralWidget(raiz)
        shell = QHBoxLayout(raiz)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        self.nav_widget = self._crear_nav()
        shell.addWidget(self.nav_widget)

        self.pantallas = QStackedWidget()
        shell.addWidget(self.pantallas, 1)
        self.pantallas.addWidget(self._pantalla_primaria())
        self.pantallas.addWidget(self._pantalla_edicion())
        self.pantallas.addWidget(self._pantalla_juego())
        self.pantallas.addWidget(self._pantalla_configuracion())

    def _crear_nav(self):
        nav = QFrame(objectName="nav")
        caja = QVBoxLayout(nav)
        caja.setContentsMargins(0, 0, 0, 0)
        caja.setSpacing(0)

        scroll = QScrollArea()
        scroll.setObjectName("navScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setFrameShape(QFrame.NoFrame)

        contenido = QWidget()
        contenido.setObjectName("navContent")
        caja_int = QVBoxLayout(contenido)
        caja_int.setContentsMargins(22, 30, 20, 26)
        caja_int.setSpacing(8)

        self.boton_menu = QPushButton("☰", contenido)
        self.boton_menu.setObjectName("navButton")
        self.boton_menu.clicked.connect(self.alternar_menu)
        self.boton_menu.setToolTip("Colapsar/Expandir menú")
        caja_int.addWidget(self.boton_menu)

        # 🔽 Logo en la barra lateral
        ruta_logo = Path(__file__).parent / "logo.png"
        if ruta_logo.exists():
            logo_label = QLabel()
            pixmap_logo = QPixmap(str(ruta_logo)).scaledToWidth(180, Qt.SmoothTransformation)
            logo_label.setPixmap(pixmap_logo)
            logo_label.setAlignment(Qt.AlignCenter)
            logo_label.setObjectName("navLogo")
            caja_int.addWidget(logo_label)
        else:
            caja_int.addWidget(self.etiqueta("PROYECTO INTEGRADOR", "brandMark"))
            caja_int.addWidget(self.etiqueta("Lotería\nMazahua", "brandTitle"))
            caja_int.addWidget(self.etiqueta("Aprende escuchando y jugando con las tarjetas.", "brandText"))

        caja_int.addSpacing(30)
        caja_int.addWidget(self.etiqueta("MODOS", "navLabel"))

        self.nav_botones = []
        for indice, texto in enumerate((
            "◉  Primaria",
            "✎  Media superior · Edición",
            "▣  Juego · Tarjetas",
            "⚙  Configuración",
        )):
            b = self.boton(texto, lambda _=False, i=indice: self.cambiar_pantalla(i), "navButton")
            b.setCheckable(True)
            self.nav_botones.append(b)
            caja_int.addWidget(b)
        self.nav_botones[0].setChecked(True)

        caja_int.addSpacing(24)
        self.boton_tema = self.boton("🌙 Tema oscuro", self.alternar_tema, "soft")
        self.boton_tema.setToolTip("Cambiar entre tema claro y oscuro")
        caja_int.addWidget(self.boton_tema)

        caja_int.addStretch()
        caja_int.addWidget(self.etiqueta(RUTA_BD.name, "navFoot"))

        scroll.setWidget(contenido)
        caja.addWidget(scroll)

        self._nav_scroll = scroll
        self._nav_contenido = contenido
        return nav

    def cabecera(self, modo, titulo, descripcion):
        cont = QWidget()
        caja = QVBoxLayout(cont)
        caja.setContentsMargins(36, 28, 36, 10)
        caja.setSpacing(4)
        caja.addWidget(self.etiqueta(modo.upper(), "eyebrow"))
        caja.addWidget(self.etiqueta(titulo, "title"))
        caja.addWidget(self.etiqueta(descripcion, "sub"))
        return cont

    def _pantalla_primaria(self):
        pagina = QWidget()
        caja = QVBoxLayout(pagina)
        caja.setContentsMargins(0, 0, 0, 24)
        caja.setSpacing(10)
        caja.addWidget(self.cabecera(
            "Modo Primaria", "Aprende jugando",
            "Arrastra las cartas · Haz clic para ver grande · Escucha los audios",
        ))

        self.lista_primaria = QListWidget(objectName="list")
        self.lista_primaria.setViewMode(QListWidget.IconMode)
        self.lista_primaria.setIconSize(QSize(180, 180))
        self.lista_primaria.setGridSize(QSize(200, 220))
        self.lista_primaria.setResizeMode(QListWidget.Adjust)
        self.lista_primaria.setMovement(QListWidget.Snap)
        self.lista_primaria.setDragDropMode(QAbstractItemView.InternalMove)
        self.lista_primaria.setDefaultDropAction(Qt.MoveAction)
        self.lista_primaria.setSelectionMode(QAbstractItemView.SingleSelection)
        self.lista_primaria.setSpacing(12)
        self.lista_primaria.itemClicked.connect(self._seleccionar_carta_primaria)
        caja.addWidget(self.lista_primaria, 1)

        lateral = QVBoxLayout()
        lateral.setSpacing(14)

        self.previa_primaria = QLabel("Selecciona una carta", objectName="preview")
        self.previa_primaria.setAlignment(Qt.AlignCenter)
        self.previa_primaria.setMinimumSize(300, 300)
        self.previa_primaria.setMaximumSize(380, 380)
        self.previa_primaria.setScaledContents(False)

        shadow_previa = QGraphicsDropShadowEffect()
        shadow_previa.setBlurRadius(20)
        shadow_previa.setColor(QColor(0, 0, 0, 20))
        shadow_previa.setOffset(4, 4)
        self.previa_primaria.setGraphicsEffect(shadow_previa)
        lateral.addWidget(self.previa_primaria)

        self.uid_label = QLabel("UID: —", objectName="sub")
        self.uid_label.setAlignment(Qt.AlignCenter)
        lateral.addWidget(self.uid_label)

        voces = QVBoxLayout()
        voces.setSpacing(12)
        self.voces = {}
        self.botones_audio_primaria = {}

        for num, idioma in enumerate(IDIOMAS, 1):
            tarjeta = QFrame(objectName="wordCard")
            fila = QHBoxLayout(tarjeta)
            fila.setContentsMargins(18, 16, 18, 16)

            shadow_tarjeta = QGraphicsDropShadowEffect()
            shadow_tarjeta.setBlurRadius(10)
            shadow_tarjeta.setColor(QColor(0, 0, 0, 20))
            shadow_tarjeta.setOffset(2, 2)
            tarjeta.setGraphicsEffect(shadow_tarjeta)

            n = self.etiqueta(str(num))
            n.setAlignment(Qt.AlignCenter)
            n.setFixedSize(38, 38)
            n.setProperty("colorIdioma", COLORES_IDIOMA[idioma])
            fila.addWidget(n)

            texto = QVBoxLayout()
            idioma_label = self.etiqueta(idioma.upper(), "lang")
            idioma_label.setStyleSheet(f"color:{COLORES_IDIOMA[idioma]};")
            texto.addWidget(idioma_label)
            palabra = self.etiqueta("—", "word")
            texto.addWidget(palabra)
            fila.addLayout(texto, 1)

            play = self.boton("▶", lambda _=False: None, "play")
            play.clicked.disconnect()
            play.clicked.connect(
                lambda _=False, i=idioma, b=play: self._toggle_audio(i, b)
            )
            play.setEnabled(False)
            fila.addWidget(play)

            self.botones_audio_primaria[idioma] = play
            self.tarjetas_idioma[idioma] = tarjeta
            voces.addWidget(tarjeta)
            self.voces[idioma] = palabra

        voces.addStretch()
        lateral.addLayout(voces)

        player = QFrame(objectName="player")
        fila_player = QHBoxLayout(player)
        fila_player.setContentsMargins(20, 14, 20, 14)

        shadow_player = QGraphicsDropShadowEffect()
        shadow_player.setBlurRadius(12)
        shadow_player.setColor(QColor(0, 0, 0, 25))
        shadow_player.setOffset(2, 2)
        player.setGraphicsEffect(shadow_player)

        self.estado_audio = self.etiqueta("●  Selecciona una carta para escuchar", "statusMuted")
        fila_player.addWidget(self.estado_audio, 1)

        self.boton_detener = self.boton("■ Detener", self.detener_audio, "soft")
        self.boton_detener.setEnabled(False)
        fila_player.addWidget(self.boton_detener)
        lateral.addWidget(player)

        cuerpo = QHBoxLayout()
        cuerpo.setContentsMargins(36, 0, 36, 0)
        cuerpo.setSpacing(28)
        cuerpo.addWidget(self.lista_primaria, 3)
        cuerpo.addLayout(lateral, 1)
        caja.addLayout(cuerpo, 1)

        return pagina

    def _pantalla_edicion(self):
        pagina = QWidget()
        caja = QVBoxLayout(pagina)
        caja.setContentsMargins(0, 0, 0, 24)
        caja.setSpacing(8)
        caja.addWidget(self.cabecera(
            "Media superior · Edición", "Editar carta",
            "Los campos se cargan desde SQLite y se guardan directamente en la base de datos.",
        ))

        cuerpo = QHBoxLayout()
        cuerpo.setContentsMargins(36, 0, 36, 0)
        cuerpo.setSpacing(24)
        caja.addLayout(cuerpo, 1)

        izquierda = QVBoxLayout()
        self.busqueda = QLineEdit()
        self.busqueda.setObjectName("search")
        self.busqueda.setPlaceholderText("Buscar carta...")
        self.busqueda.textChanged.connect(self.filtrar)
        izquierda.addWidget(self.busqueda)

        self.lista = QListWidget(objectName="list")
        self.lista.currentItemChanged.connect(self.seleccionar_lista)
        izquierda.addWidget(self.lista, 1)
        izquierda.addWidget(self.boton("+ Nueva carta", self.nueva_carta))
        cuerpo.addLayout(izquierda, 1)

        editor = QFrame(objectName="editor")
        ed = QVBoxLayout(editor)
        ed.setContentsMargins(28, 26, 28, 26)
        ed.setSpacing(16)
        cuerpo.addWidget(editor, 3)

        self.imagen_editor = QLabel("Sin imagen", objectName="preview")
        self.imagen_editor.setAlignment(Qt.AlignCenter)
        self.imagen_editor.setFixedHeight(180)
        ed.addWidget(self.imagen_editor)
        ed.addWidget(self.boton("Cambiar imagen…", lambda: self.cargar("imagen"), "soft"))

        self.campos = {}
        self.botones_audio_edicion = {}

        for idioma in IDIOMAS:
            fila = QHBoxLayout()
            etiqueta = self.etiqueta(idioma.capitalize())
            etiqueta.setFixedWidth(100)
            fila.addWidget(etiqueta)

            entrada = QLineEdit(objectName="field")
            entrada.editingFinished.connect(self.guardar)
            fila.addWidget(entrada, 1)

            fila.addWidget(self.boton(
                "Cargar audio", lambda _=False, i=idioma: self.cargar(i), "soft"
            ))

            play = self.boton("▶", lambda _=False: None, "play")
            play.clicked.disconnect()
            play.clicked.connect(
                lambda _=False, i=idioma, b=play: self._toggle_audio(i, b)
            )
            play.setEnabled(False)
            fila.addWidget(play)

            self.botones_audio_edicion[idioma] = play
            ed.addLayout(fila)
            self.campos[idioma] = entrada

        self.uid_edicion_label = QLabel("UID RFID: No asignado", objectName="sub")
        ed.addWidget(self.uid_edicion_label)

        acciones = QHBoxLayout()
        acciones.addWidget(self.boton("💾 Guardar cambios", self.guardar))
        acciones.addWidget(self.boton("🎙 Grabar tarjeta RFID", self.aviso_rfid, "soft"))
        acciones.addStretch()
        acciones.addWidget(self.boton("Eliminar", self.eliminar, "danger"))
        ed.addLayout(acciones)

        return pagina

    def _pantalla_juego(self):
        pagina = QWidget()
        caja = QVBoxLayout(pagina)
        caja.setContentsMargins(40, 40, 40, 40)
        caja.setSpacing(20)

        header = QHBoxLayout()
        header.addWidget(self.etiqueta("MODO JUEGO", "eyebrow"))
        header.addStretch()
        btn_salir = self.boton("✕ Salir del Juego", lambda: self.cambiar_pantalla(0), "danger")
        btn_salir.setMinimumSize(180, 50)
        btn_salir.setFont(QFont("Segoe UI", 14, QFont.Bold))
        header.addWidget(btn_salir)
        caja.addLayout(header)

        caja.addStretch()

        self.juego = QLabel("Acerca una tarjeta al lector", objectName="preview")
        self.juego.setAlignment(Qt.AlignCenter)
        self.juego.setMinimumSize(400, 400)
        self.juego.setMaximumSize(500, 550)
        caja.addWidget(self.juego, 0, Qt.AlignHCenter)

        self.uid_juego_label = QLabel("UID: Esperando lectura...", objectName="sub")
        self.uid_juego_label.setAlignment(Qt.AlignCenter)
        caja.addWidget(self.uid_juego_label, 0, Qt.AlignHCenter)

        caja.addStretch()
        return pagina

    def _tarjeta_configuracion(self, titulo: str, descripcion: str) -> tuple[QFrame, QVBoxLayout]:
        tarjeta = QFrame(objectName="configCard")
        caja = QVBoxLayout(tarjeta)
        caja.setContentsMargins(24, 20, 24, 20)
        caja.setSpacing(8)
        caja.addWidget(self.etiqueta(titulo, "configTitle"))
        caja.addWidget(self.etiqueta(descripcion, "sub"))
        return tarjeta, caja

    def _pantalla_configuracion(self):
        pagina = QWidget()
        caja = QVBoxLayout(pagina)
        caja.setContentsMargins(0, 0, 0, 26)
        caja.addWidget(self.cabecera(
        "Sistema", "Configuración",
        "Recursos, base de datos y conexión del lector RFID.",
        ))

        cuerpo = QVBoxLayout()
        cuerpo.setContentsMargins(36, 0, 36, 0)
        cuerpo.setSpacing(16)
        caja.addLayout(cuerpo, 1)

        recursos, fila = self._tarjeta_configuracion(
            "Recursos multimedia",
            "Importa o actualiza imágenes y audios dentro de SQLite.",
        )
        acciones = QHBoxLayout()
        acciones.addWidget(self.boton("⟳ Importar recursos", self.importar_recursos, "soft"))
        acciones.addWidget(self.boton("🇺🇸 Importar audios EN", self.importar_ingles, "soft"))
        acciones.addStretch()
        fila.addLayout(acciones)
        cuerpo.addWidget(recursos)

        lector, fila = self._tarjeta_configuracion(
            "Lector RFID",
            "Conecta el ESP32 para leer tarjetas en el modo Juego.",
        )
        fila_lector = QHBoxLayout()
        self.estado_lector = self.etiqueta("● Desconectado", "statusMuted")
        fila_lector.addWidget(self.estado_lector, 1)
        self.boton_lector = self.boton("◉ Conectar lector", self.alternar_lector)
        fila_lector.addWidget(self.boton_lector)
        fila.addLayout(fila_lector)
        cuerpo.addWidget(lector)

        base, fila = self._tarjeta_configuracion("Base de datos", RUTA_BD.name)
        self.estado_bd = self.etiqueta("", "statusMuted")
        fila.addWidget(self.estado_bd)
        cuerpo.addWidget(base)

        cuerpo.addStretch()
        return pagina

    # ------------------------------------------------------------------
    # Navegación y tema
    # ------------------------------------------------------------------

    def cambiar_pantalla(self, indice):
        self.pantallas.setCurrentIndex(indice)
        for i, boton in enumerate(self.nav_botones):
            boton.setChecked(i == indice)

        if indice == 2:
            self.nav_widget.hide()
        else:
            self.nav_widget.show()
            ancho = 80 if self.menu_colapsado else 260
            self.nav_widget.setMaximumWidth(ancho)
            self.nav_widget.setMinimumWidth(ancho)

    def alternar_menu(self):
        self.menu_colapsado = not self.menu_colapsado

        if self.menu_colapsado:
            self.nav_widget.setMaximumWidth(80)
            self.nav_widget.setMinimumWidth(80)
            simbolos = ("◉", "✎", "▣", "⚙")
            tips = ("Primaria", "Edición", "Juego", "Configuración")
            for i, btn in enumerate(self.nav_botones):
                btn.setText(simbolos[i])
                btn.setToolTip(tips[i])
                btn.setStyleSheet(
                    "QPushButton#navButton {"
                    "  color: #FBBF24;"
                    "  font-size: 22px;"
                    "  font-weight: 900;"
                    "  text-align: center;"
                    "  padding: 10px 0;"
                    "  border-radius: 12px;"
                    "}"
                    "QPushButton#navButton:hover {"
                    "  background: rgba(251,191,36,0.25);"
                    "  color: #FFFFFF;"
                    "}"
                    "QPushButton#navButton:checked {"
                    "  background: rgba(251,191,36,0.32);"
                    "  border-left: 4px solid #FBBF24;"
                    "  color: #FFFFFF;"
                    "}"
                )
            self.boton_menu.setText("☰")
            self.boton_menu.setStyleSheet(
                "QPushButton#navButton { color:#FBBF24; font-size:20px;"
                " font-weight:900; text-align:center; padding: 8px 0; }"
            )
            for widget in self._nav_contenido.findChildren(QLabel):
                if widget.objectName() in ["brandMark", "brandTitle", "brandText", "navLabel", "navFoot", "navLogo"]:
                    widget.hide()
        else:
            self.nav_widget.setMaximumWidth(260)
            self.nav_widget.setMinimumWidth(260)
            textos = (
                "◉  Primaria",
                "✎  Media superior · Edición",
                "▣  Juego · Tarjetas",
                "⚙  Configuración",
            )
            for i, btn in enumerate(self.nav_botones):
                btn.setText(textos[i])
                btn.setToolTip("")
                btn.setStyleSheet("")
            self.boton_menu.setText("☰")
            self.boton_menu.setStyleSheet("")
            for widget in self._nav_contenido.findChildren(QLabel):
                if widget.objectName() in ["brandMark", "brandTitle", "brandText", "navLabel", "navFoot", "navLogo"]:
                    widget.show()

        self._aplicar_tema()

    def alternar_tema(self):
        self.tema_oscuro = not self.tema_oscuro
        self._aplicar_tema()

    def _aplicar_tema(self):
        hoja = ESTILO_OSCURO if self.tema_oscuro else ESTILO_CLARO
        self.setStyleSheet(hoja)

        color_uid = "#E5E7EB" if self.tema_oscuro else "#6B7280"
        bg_uid = "#263238" if self.tema_oscuro else "#F3F4F6"
        color_num = "white" if not self.tema_oscuro else "#121212"
        color_play_txt = "white" if not self.tema_oscuro else "#121212"

        if hasattr(self, "uid_label"):
            self.uid_label.setStyleSheet(
                f"font-size: 13px; font-weight: 600; color: {color_uid};"
            )
        if hasattr(self, "uid_edicion_label"):
            self.uid_edicion_label.setStyleSheet(
                f"font-size: 13px; font-weight: 600; color: {color_uid}; "
                f"padding: 8px; background: {bg_uid}; border-radius: 8px;"
            )
        if hasattr(self, "uid_juego_label"):
            self.uid_juego_label.setStyleSheet(
                f"font-size: 18px; font-weight: 700; color: {color_uid}; margin-top: 10px;"
            )

        for idioma, color in COLORES_IDIOMA.items():
            estilo_play = (
                f"#play{{background:{color}; color:{color_play_txt}; border:0;"
                f"border-radius:24px; font-size:16px; font-weight:800;"
                f"min-width:48px; min-height:48px;}}"
                f"#play:disabled{{background:#9CA3AF; color:#F9FAFB;}}"
            )
            if hasattr(self, "botones_audio_primaria") and idioma in self.botones_audio_primaria:
                self.botones_audio_primaria[idioma].setStyleSheet(estilo_play)
            if hasattr(self, "botones_audio_edicion") and idioma in self.botones_audio_edicion:
                self.botones_audio_edicion[idioma].setStyleSheet(estilo_play)

        for lbl in self.findChildren(QLabel):
            color_idioma = lbl.property("colorIdioma")
            if color_idioma:
                lbl.setStyleSheet(
                    f"background:{color_idioma}; color:{color_num}; "
                    f"border-radius:12px; font-weight:800; font-size:16px;"
                )

        if self.menu_colapsado:
            self.boton_tema.setText("🌙" if not self.tema_oscuro else "☀️")
        else:
            self.boton_tema.setText("🌙 Tema oscuro" if not self.tema_oscuro else "☀️ Tema claro")

        self._settings.setValue("tema_oscuro", self.tema_oscuro)

        self._resaltar_idioma(self.idioma_audio)

        self.update()
        QApplication.processEvents()

    def _resaltar_idioma(self, idioma: str | None):
        for idi, frame in getattr(self, "tarjetas_idioma", {}).items():
            if idi == idioma:
                frame.setStyleSheet(
                    f"#wordCard {{ border: 3px solid {COLORES_IDIOMA[idi]}; "
                    f"background: rgba(251,191,36,0.15); }}"
                )
            else:
                frame.setStyleSheet("")

    # ------------------------------------------------------------------
    # Datos / listas
    # ------------------------------------------------------------------

    def recargar_cartas(self):
        self.filas = [dict(fila) for fila in resumen(self.conexion)]
        self.filtrar()
        self._actualizar_lista_primaria()
        self._actualizar_mapeo_uid()

        if hasattr(self, "estado_bd"):
            medios = self.conexion.execute("SELECT count(*) FROM medio").fetchone()[0]
            self.estado_bd.setText(
                f"{len(self.filas)} cartas · {medios} recursos multimedia · SQLite sincronizada"
            )

    def _verificar_cambios_bd(self):
        """Recarga la interfaz si la base cambió desde la última comprobación."""
        try:
            checksum_actual = obtener_checksum(self.conexion)
        except Exception as error:
            print(f"[SYNC ERROR] {error}")
            return

        if checksum_actual == self._ultimo_checksum:
            return

        carta_seleccionada = self.carta_actual
        self.recargar_cartas()
        if carta_seleccionada is not None:
            self._seleccionar_id(carta_seleccionada)
        self._ultimo_checksum = checksum_actual

    def _actualizar_mapeo_uid(self):
        self.uid_a_carta.clear()
        cursor = self.conexion.execute(
            "SELECT id, uid_rfid FROM carta WHERE uid_rfid IS NOT NULL"
        )
        for row in cursor:
            self.uid_a_carta[row["uid_rfid"]] = row["id"]

    def filtrar(self):
        texto = self.busqueda.text().casefold() if hasattr(self, "busqueda") else ""
        self.lista.blockSignals(True)
        self.lista.clear()
        for fila in self.filas:
            if texto and texto not in " ".join(
                str(fila[c] or "") for c in ("nombre", "mazahua", "ingles")
            ).casefold():
                continue
            item = QListWidgetItem(
                f"{fila['nombre'].capitalize()}\n"
                f"{fila['mazahua'] or '—'} · {fila['ingles'] or '—'}"
            )
            item.setData(Qt.UserRole, fila["id"])
            self.lista.addItem(item)
        self.lista.blockSignals(False)
        if self.lista.count():
            self.lista.setCurrentRow(0)

    def _actualizar_lista_primaria(self):
        if not hasattr(self, "lista_primaria"):
            return
        self.lista_primaria.blockSignals(True)
        self.lista_primaria.clear()
        for fila in self.filas:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, fila["id"])
            item.setText(fila["nombre"].capitalize())

            uid = fila.get("uid_rfid")
            uid_text = f"\nUID: {uid}" if uid else ""
            item.setToolTip(f"{fila['mazahua'] or '—'} · {fila['ingles'] or '—'}{uid_text}")

            medio = obtener_medio(self.conexion, fila["id"], "imagen")
            if medio:
                pixmap = QPixmap()
                pixmap.loadFromData(medio["contenido"])
                pixmap = pixmap.scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                item.setIcon(QIcon(pixmap))
            else:
                pixmap = QPixmap(180, 180)
                pixmap.fill(QColor(243, 244, 246))
                painter = QPainter(pixmap)
                painter.setPen(QColor(107, 114, 128))
                painter.drawText(pixmap.rect(), Qt.AlignCenter, "Sin imagen")
                painter.end()
                item.setIcon(QIcon(pixmap))

            self.lista_primaria.addItem(item)
        self.lista_primaria.blockSignals(False)

    # ------------------------------------------------------------------
    # Selección / edición
    # ------------------------------------------------------------------

    def _seleccionar_carta_primaria(self, item):
        carta_id = item.data(Qt.UserRole)
        if carta_id is None:
            return
        self.carta_actual = carta_id

        carta = obtener_carta(self.conexion, carta_id)
        if not carta:
            return

        self._poner_imagen(carta["id"])

        valores = {
            "español": carta["nombre"],
            "mazahua": carta["mazahua"],
            "inglés": carta["ingles"],
        }
        for idioma, valor in valores.items():
            if idioma in self.voces:
                self.voces[idioma].setText(valor or "—")

        uid_val = carta["uid_rfid"] if carta["uid_rfid"] else None
        if hasattr(self, "uid_label"):
            self.uid_label.setText(f"UID: {uid_val}" if uid_val else "UID: No asignado")

        for idioma in IDIOMAS:
            medio = obtener_medio(self.conexion, carta_id, idioma)
            if idioma in self.botones_audio_primaria:
                self.botones_audio_primaria[idioma].setEnabled(medio is not None)

    def seleccionar_lista(self, actual, _anterior=None):
        if not actual:
            return
        self.carta_actual = actual.data(Qt.UserRole)
        carta = obtener_carta(self.conexion, self.carta_actual)

        valores = {
            "español": carta["nombre"],
            "mazahua": carta["mazahua"],
            "inglés": carta["ingles"],
        }
        for idioma, valor in valores.items():
            self.campos[idioma].setText(valor or "")
            self.voces[idioma].setText(valor or "—")
            if hasattr(self, "botones_audio_edicion") and idioma in self.botones_audio_edicion:
                medio = obtener_medio(self.conexion, self.carta_actual, idioma)
                self.botones_audio_edicion[idioma].setEnabled(medio is not None)

        self._poner_imagen(carta["id"])

        uid_val = carta["uid_rfid"] if carta["uid_rfid"] else None
        if hasattr(self, "uid_edicion_label"):
            self.uid_edicion_label.setText(
                f"UID RFID: {uid_val}" if uid_val else "UID RFID: No asignado"
            )

    def _poner_imagen(self, carta_id):
        medio = obtener_medio(self.conexion, carta_id, "imagen")
        destino = [self.imagen_editor, self.previa_primaria]
        if not medio:
            for etiqueta in destino:
                etiqueta.setPixmap(QPixmap())
                etiqueta.setText("Esta carta no tiene imagen")
            return
        pixmap = QPixmap()
        pixmap.loadFromData(medio["contenido"])
        for etiqueta in destino:
            etiqueta.setText("")
            etiqueta.setPixmap(
                pixmap.scaled(etiqueta.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )

    def nueva_carta(self):
        nombre = self.busqueda.text().strip()
        if not nombre:
            msg = QMessageBox(self)
            msg.setWindowTitle("Nueva carta")
            msg.setText("Escribe la palabra en el buscador y pulsa otra vez Nueva carta.")
            msg.setStyleSheet(self.estilo_dialogo())
            msg.exec()
            self.busqueda.setFocus()
            return

        try:
            carta_id = crear_carta(self.conexion, nombre)
        except ValueError as error:
            msg = QMessageBox(self)
            msg.setWindowTitle("Nueva carta")
            msg.setText(str(error))
            msg.setStyleSheet(self.estilo_dialogo())
            msg.exec()
            return

        self.busqueda.clear()
        self.recargar_cartas()

        for i in range(self.lista.count()):
            if self.lista.item(i).data(Qt.UserRole) == carta_id:
                self.lista.setCurrentRow(i)
                break

    def guardar(self):
        if not self.carta_actual:
            return
        try:
            guardar_textos(
                self.conexion,
                self.carta_actual,
                *(self.campos[i].text() for i in IDIOMAS),
            )
        except ValueError as error:
            msg = QMessageBox(self)
            msg.setWindowTitle("No se pudo guardar")
            msg.setText(str(error))
            msg.setStyleSheet(self.estilo_dialogo())
            msg.exec()
            return
        self.recargar_cartas()
        self._seleccionar_id(self.carta_actual)

    def _seleccionar_id(self, carta_id):
        for i in range(self.lista.count()):
            if self.lista.item(i).data(Qt.UserRole) == carta_id:
                self.lista.setCurrentRow(i)
                break

        if hasattr(self, "botones_audio_edicion"):
            for idioma in IDIOMAS:
                medio = obtener_medio(self.conexion, carta_id, idioma)
                self.botones_audio_edicion[idioma].setEnabled(medio is not None)

        carta = obtener_carta(self.conexion, carta_id)
        if carta and hasattr(self, "uid_edicion_label"):
            uid_val = carta["uid_rfid"] if carta["uid_rfid"] else None
            self.uid_edicion_label.setText(
                f"UID RFID: {uid_val}" if uid_val else "UID RFID: No asignado"
            )

    def cargar(self, tipo):
        if not self.carta_actual:
            return
        filtros = (
            "Imágenes (*.png *.jpg *.jpeg *.webp);;Todos (*.*)"
            if tipo == "imagen"
            else "Audio (*.mp3 *.wav *.ogg *.m4a *.mp4);;Todos (*.*)"
        )
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Selecciona un archivo", str(Path.cwd()), filtros
        )
        if not ruta:
            return

        try:
            cargar_medio(self.conexion, self.carta_actual, tipo, ruta)
        except ValueError as error:
            msg = QMessageBox(self)
            msg.setWindowTitle("Archivo no válido")
            msg.setText(str(error))
            msg.setStyleSheet(self.estilo_dialogo())
            msg.exec()
            return

        if tipo == "imagen":
            self._poner_imagen(self.carta_actual)
        else:
            if hasattr(self, "botones_audio_edicion") and tipo in self.botones_audio_edicion:
                self.botones_audio_edicion[tipo].setEnabled(True)

        self.recargar_cartas()
        self._seleccionar_id(self.carta_actual)

    def eliminar(self):
        if not self.carta_actual:
            return
        msg = QMessageBox(self)
        msg.setWindowTitle("Eliminar carta")
        msg.setText("¿Eliminar esta carta y sus recursos?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setStyleSheet(self.estilo_dialogo())
        if msg.exec() != QMessageBox.Yes:
            return

        eliminar_carta(self.conexion, self.carta_actual)
        self.carta_actual = None
        self.recargar_cartas()

    # ------------------------------------------------------------------
    # Audio
    # ------------------------------------------------------------------

    def _toggle_audio(self, idioma: str, boton: QPushButton):
        """Play si no está sonando ese idioma; Stop si ya está sonando."""
        if self.idioma_audio == idioma and self.reproductor is not None:
            self.detener_audio()
            return
        self.reproducir(idioma)

    def reproducir(self, idioma):
        if self.carta_actual is None:
            msg = QMessageBox(self)
            msg.setWindowTitle("Audio")
            msg.setText("Primero selecciona una carta.")
            msg.setStyleSheet(self.estilo_dialogo())
            msg.exec()
            return

        medio = obtener_medio(self.conexion, self.carta_actual, idioma)
        if not medio:
            msg = QMessageBox(self)
            msg.setWindowTitle("Audio")
            msg.setText(f"Esta carta aún no tiene audio en {idioma}.")
            msg.setStyleSheet(self.estilo_dialogo())
            msg.exec()
            return

        self.detener_audio()
        time.sleep(0.05)

        carpeta = Path(tempfile.gettempdir()) / "loteria_mazahua_audio"
        carpeta.mkdir(exist_ok=True)
        self.archivo_audio = carpeta / f"{uuid4().hex}{medio['extension']}"
        self.archivo_audio.write_bytes(medio["contenido"])

        try:
            self.reproductor = MediaPlayer(
                str(self.archivo_audio),
                ff_opts={"vn": True, "loop": 0, "paused": False},
            )
            self.reproductor.set_pause(False)
            self.inicio_audio = time.monotonic()
            self.idioma_audio = idioma
            self._audio_activo = True

            self.estado_audio.setObjectName("statusGood")
            self.estado_audio.setText(
                f"● Reproduciendo {idioma.capitalize()} · pulsa Detener para cancelar"
            )
            self.estado_audio.style().unpolish(self.estado_audio)
            self.estado_audio.style().polish(self.estado_audio)
            self.boton_detener.setEnabled(True)

            if idioma in self.botones_audio_primaria:
                self.botones_audio_primaria[idioma].setText("■")
            if idioma in self.botones_audio_edicion:
                self.botones_audio_edicion[idioma].setText("■")

            self._resaltar_idioma(idioma)
            self.reloj_audio.start()
        except Exception as error:
            self.detener_audio()
            msg = QMessageBox(self)
            msg.setWindowTitle("No se pudo reproducir")
            msg.setText(str(error))
            msg.setStyleSheet(self.estilo_dialogo())
            msg.exec()

    def _reproducir_secuencia(self, carta_id: int):
        self.detener_audio()
        self._secuencia_carta = carta_id
        self._secuencia = []
        for idioma in ("mazahua", "español", "inglés"):
            if obtener_medio(self.conexion, carta_id, idioma):
                self._secuencia.append(idioma)
        if not self._secuencia:
            return
        self._siguiente_en_secuencia()

    def _siguiente_en_secuencia(self):
        if not self._secuencia:
            self.detener_audio()
            return
        idioma = self._secuencia.pop(0)
        if self._secuencia_carta is None:
            return

        carta_previa = self.carta_actual
        self.carta_actual = self._secuencia_carta
        self.reproducir(idioma)
        self.carta_actual = carta_previa

        if self._secuencia and self.reproductor is not None:
            self._timer_secuencia.start(600)

    def _vigilar_audio(self):
        if self.reproductor is None:
            self.reloj_audio.stop()
            return

        try:
            _frame, estado = self.reproductor.get_frame()
            duracion = float(self.reproductor.get_metadata().get("duration") or 0)
            terminado = estado == "eof" or (
                duracion > 0 and time.monotonic() - self.inicio_audio >= duracion + 0.2
            )

            if terminado:
                try:
                    self.reproductor.set_pause(True)
                except Exception:
                    pass
                self.detener_audio(finalizo=True)
                if self._secuencia:
                    self._timer_secuencia.start(600)
        except Exception:
            self.detener_audio(finalizo=True)

    def detener_audio(self, finalizo: bool = False):
        if not finalizo:
            self._secuencia = []
            self._secuencia_carta = None
            if hasattr(self, "_timer_secuencia"):
                self._timer_secuencia.stop()

        self.reloj_audio.stop()

        if self.reproductor is not None:
            try:
                self.reproductor.set_pause(True)
                self.reproductor.close_player()
            except Exception:
                pass
            self.reproductor = None

        if self.archivo_audio is not None:
            for _ in range(5):
                try:
                    self.archivo_audio.unlink(missing_ok=True)
                    break
                except OSError:
                    time.sleep(0.1)
            self.archivo_audio = None

        self.idioma_audio = None
        self._audio_activo = False

        if hasattr(self, "estado_audio"):
            self.estado_audio.setObjectName("statusMuted")
            self.estado_audio.setText(
                "● Audio terminado" if finalizo else "● Selecciona una carta para escuchar"
            )
            self.estado_audio.style().unpolish(self.estado_audio)
            self.estado_audio.style().polish(self.estado_audio)
        if hasattr(self, "boton_detener"):
            self.boton_detener.setEnabled(False)

        for btn in getattr(self, "botones_audio_primaria", {}).values():
            btn.setText("▶")
        for btn in getattr(self, "botones_audio_edicion", {}).values():
            btn.setText("▶")

        self._resaltar_idioma(None)

    # ------------------------------------------------------------------
    # Importar recursos
    # ------------------------------------------------------------------

    def importar_recursos(self):
        try:
            totales = importar_archivos(self.conexion)
        except Exception as error:
            msg = QMessageBox(self)
            msg.setWindowTitle("No se pudieron importar recursos")
            msg.setText(str(error))
            msg.setStyleSheet(self.estilo_dialogo())
            msg.exec()
            return
        self.recargar_cartas()
        msg = QMessageBox(self)
        msg.setWindowTitle("Recursos actualizados")
        msg.setText(" · ".join(f"{cantidad} {tipo}" for tipo, cantidad in totales.items()))
        msg.setStyleSheet(self.estilo_dialogo())
        msg.exec()

    def importar_ingles(self):
        try:
            total = importar_audios_ingles(self.conexion)
        except Exception as error:
            msg = QMessageBox(self)
            msg.setWindowTitle("No se pudieron importar los audios")
            msg.setText(str(error))
            msg.setStyleSheet(self.estilo_dialogo())
            msg.exec()
            return
        self.recargar_cartas()
        msg = QMessageBox(self)
        msg.setWindowTitle("Audios en inglés")
        msg.setText(f"Se importaron o actualizaron {total} audios.")
        msg.setStyleSheet(self.estilo_dialogo())
        msg.exec()
    # ------------------------------------------------------------------
    # RFID
    # ------------------------------------------------------------------

    def alternar_lector(self):
        if self.lector:
            self.lector.detener()
            self.lector = None
            self.estado_lector.setObjectName("statusMuted")
            self.estado_lector.setText("● Desconectado")
            self.boton_lector.setText("◉ Conectar lector")
            return

        puertos = listar_puertos()
        if not puertos:
            msg = QMessageBox(self)
            msg.setWindowTitle("Lector RFID")
            msg.setText("No se detectó ningún puerto serie. Conecta el ESP32 por USB.")
            msg.setStyleSheet(self.estilo_dialogo())
            msg.exec()
            return

        puerto = puertos[0]
        self.lector = LectorRFID(
            puerto,
            lambda lectura: self.lecturas.put({"lectura": lectura}),
            lambda error: self.lecturas.put({"error": error}),
            lambda es_error, mensaje: self.lecturas.put(
                {"estado": mensaje, "es_error": es_error}
            ),
        )
        self.lector.start()
        self.estado_lector.setObjectName("statusGood")
        self.estado_lector.setText(f"● Conectando en {puerto}")
        self.estado_lector.style().unpolish(self.estado_lector)
        self.estado_lector.style().polish(self.estado_lector)
        self.boton_lector.setText("Desconectar lector")

    def _revisar_lecturas(self):
        while not self.lecturas.empty():
            evento = self.lecturas.get()
            if "error" in evento:
                self.lector = None
                if hasattr(self, "estado_lector"):
                    self.estado_lector.setText(evento["error"])
                    self.boton_lector.setText("◉ Conectar lector")
            elif "estado" in evento:
                if hasattr(self, "estado_lector"):
                    self.estado_lector.setText(evento["estado"])
            elif "lectura" in evento:
                lectura = evento["lectura"]
                carta, estado = emparejar_lectura(
                    self.conexion,
                    lectura["uid"],
                    [lectura["espanol"], lectura["mazahua"], lectura["ingles"]],
                )
                self.recargar_cartas()
                if carta:
                    self._seleccionar_id(carta["id"])
                    self.juego.setText(
                        f"{carta['nombre'].capitalize()}\n\n"
                        f"{carta['mazahua'] or '—'} · {carta['ingles'] or '—'}\n\n"
                        f"RFID {lectura['uid']}"
                    )
                    self._poner_imagen(carta["id"])
                    if hasattr(self, "uid_juego_label"):
                        self.uid_juego_label.setText(f"UID: {lectura['uid']}")
                    self._reproducir_secuencia(carta["id"])
                if hasattr(self, "estado_lector"):
                    self.estado_lector.setText(f"● Lectura {estado}: {lectura['uid']}")

    def aviso_rfid(self):
        if self.carta_actual is None:
            msg = QMessageBox(self)
            msg.setWindowTitle("RFID")
            msg.setText("Primero selecciona una carta para grabar.")
            msg.setStyleSheet(self.estilo_dialogo())
            msg.exec()
            return

        carta = obtener_carta(self.conexion, self.carta_actual)
        if not carta:
            msg = QMessageBox(self)
            msg.setWindowTitle("RFID")
            msg.setText("No se encontró la carta seleccionada.")
            msg.setStyleSheet(self.estilo_dialogo())
            msg.exec()
            return

        if not self.lector:
            msg = QMessageBox(self)
            msg.setWindowTitle("RFID - Lector no conectado")
            msg.setText("No hay lector RFID conectado. ¿Quieres conectar uno ahora?")
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg.setStyleSheet(self.estilo_dialogo())
            respuesta = msg.exec()
            if respuesta == QMessageBox.Yes:
                self.alternar_lector()
                QTimer.singleShot(1500, lambda: self._grabar_rfid_carta(carta))
            return

        self._grabar_rfid_carta(carta)

    def _grabar_rfid_carta(self, carta):
        if not self.lector:
            msg = QMessageBox(self)
            msg.setWindowTitle("RFID")
            msg.setText("El lector no está conectado.")
            msg.setStyleSheet(self.estilo_dialogo())
            msg.exec()
            return

        espanol = carta["nombre"] or ""
        mazahua = carta["mazahua"] or ""
        ingles = carta["ingles"] or ""

        comando = comando_grabar(espanol, mazahua, ingles)
        if not self.lector.enviar(comando):
            msg = QMessageBox(self)
            msg.setWindowTitle("RFID")
            msg.setText("No se pudo enviar el comando al lector.")
            msg.setStyleSheet(self.estilo_dialogo())
            msg.exec()
            return

        self._dialogo_grabacion = QMessageBox(self)
        self._dialogo_grabacion.setWindowTitle("Grabando tarjeta RFID")
        self._dialogo_grabacion.setText(
            "Acerca una tarjeta en blanco al lector...\n\n"
            "Esperando respuesta del ESP32..."
        )
        self._dialogo_grabacion.setStandardButtons(QMessageBox.Cancel)
        self._dialogo_grabacion.button(QMessageBox.Cancel).setText("Cancelar")
        self._dialogo_grabacion.setModal(True)
        self._dialogo_grabacion.setStyleSheet(self.estilo_dialogo())

        self._timer_grabacion = QTimer(self)
        self._timer_grabacion.setInterval(200)
        self._timer_grabacion.timeout.connect(lambda: self._verificar_grabacion(carta))
        self._timer_grabacion.start()

        self._dialogo_grabacion.show()

    def _verificar_grabacion(self, carta):
        while not self.lecturas.empty():
            evento = self.lecturas.get()
            if "grabacion" in evento:
                self._timer_grabacion.stop()
                if hasattr(self, "_dialogo_grabacion"):
                    self._dialogo_grabacion.close()

                grabacion = evento["grabacion"]
                if grabacion == "ok":
                    uid = evento.get("uid", "desconocido")
                    anterior = reasignar_uid(self.conexion, carta["id"], uid)
                    extra = f" (se quitó de «{anterior}»)" if anterior else ""
                    msg = QMessageBox(self)
                    msg.setWindowTitle("RFID - Grabación exitosa")
                    msg.setText(
                        f"Tarjeta {uid} grabada y asignada a «{carta['nombre']}»{extra}.\n"
                        f"Retira la tarjeta del lector."
                    )
                    msg.setStyleSheet(self.estilo_dialogo())
                    msg.exec()
                    self.recargar_cartas()
                elif grabacion == "error":
                    motivo = evento.get("motivo", "Error desconocido")
                    msg = QMessageBox(self)
                    msg.setWindowTitle("RFID - Error")
                    msg.setText(f"No se pudo grabar: {motivo}")
                    msg.setStyleSheet(self.estilo_dialogo())
                    msg.exec()
                elif grabacion == "cancelado":
                    msg = QMessageBox(self)
                    msg.setWindowTitle("RFID")
                    msg.setText("Grabación cancelada.")
                    msg.setStyleSheet(self.estilo_dialogo())
                    msg.exec()
                return
            elif "error" in evento:
                self._timer_grabacion.stop()
                if hasattr(self, "_dialogo_grabacion"):
                    self._dialogo_grabacion.close()
                msg = QMessageBox(self)
                msg.setWindowTitle("RFID - Error")
                msg.setText(f"Error del lector: {evento['error']}")
                msg.setStyleSheet(self.estilo_dialogo())
                msg.exec()
                return
    # ------------------------------------------------------------------
    # Cierre
    # ------------------------------------------------------------------

    def closeEvent(self, event):
        if hasattr(self, "_timer_sincronizacion"):
            self._timer_sincronizacion.stop()
        if hasattr(self, "_timer_secuencia"):
            self._timer_secuencia.stop()
        self._secuencia = []
        self._secuencia_carta = None
        self.detener_audio()
        if self.lector:
            self.lector.detener()
        self.conexion.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = VentanaLoteria()
    ventana.show()
    sys.exit(app.exec())

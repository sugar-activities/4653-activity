#! /usr/bin/env python
# Conozco Uruguay
# Copyright (C) 2008,2009,2010 Gabriel Eirea
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact information:
# Gabriel Eirea geirea@gmail.com
# Ceibal Jam http://ceibaljam.org

import os
import sys
import random
import pygame
import time
import imp
import gettext
import ConfigParser

gtk_present = True
try:
    import gtk
except:
    gtk_present = False

# constantes
RADIO = 10
RADIO2 = RADIO**2
XMAPAMAX = 800
DXPANEL = 400
XCENTROPANEL = 1002
YGLOBITO = 310
DXBICHO = 218
DYBICHO = 268
XBICHO = 1200-DXBICHO
YBICHO = 900-DYBICHO
XNAVE = 800
YNAVE = 650
DXNAVE = 100
DYNAVE = 200
YTEXTO = 370
CAMINORECURSOS = "recursos"
CAMINOCOMUN = "comun"
CAMINOFUENTES = "fuentes"
CAMINODATOS = "datos"
CAMINOIMAGENES = "imagenes"
CAMINOSONIDOS = "sonidos"
ARCHIVONIVELES = "levels"
ARCHIVOEXPLORACIONES = "explorations"
COLORNOMBREDEPTO = (10,10,10)
COLORNOMBRECAPITAL = (10,10,10)
COLORNOMBRERIO = (10,10,10)
COLORNOMBRERUTA = (10,10,10)
COLORNOMBREELEVACION = (10,10,10)
COLORESTADISTICAS1 = (10, 10, 150)
COLORESTADISTICAS2 = (10, 10, 10)
COLORPREGUNTAS = (80,80,155)
COLORPANEL = (156,158,172)
COLORBARRA_P = (255, 0, 0)
COLORBARRA_A = (0, 0, 255)
TOTALAVANCE = 7
EVENTORESPUESTA = pygame.USEREVENT+1
TIEMPORESPUESTA = 2300
EVENTODESPEGUE = EVENTORESPUESTA+1
TIEMPODESPEGUE = 40
EVENTOREFRESCO = EVENTODESPEGUE+1
TIEMPOREFRESCO = 250
ESTADONORMAL = 1
ESTADOPESTANAS = 2
ESTADOFRENTE = 3
ESTADODESPEGUE = 4

# variables globales para adaptar la pantalla a distintas resoluciones
scale = 1
shift_x = 0
shift_y = 0
xo_resolution = True

clock = pygame.time.Clock()

def wait_events():
    """ Funcion para esperar por eventos de pygame sin consumir CPU """
    global clock
    clock.tick(20)
    return pygame.event.get()

class Punto():
    """Clase para objetos geograficos que se pueden definir como un punto.

    La posicion esta dada por un par de coordenadas (x,y) medida en pixels
    dentro del mapa.
    """
    
    def __init__(self,nombre,tipo,simbolo,posicion,postexto):
        global scale, shift_x, shift_y
        self.nombre = nombre
        self.tipo = int(tipo)
        self.posicion = (int(int(posicion[0])*scale+shift_x),
                         int(int(posicion[1])*scale+shift_y))
        self.postexto = (int(int(postexto[0])*scale)+self.posicion[0],
                         int(int(postexto[1])*scale)+self.posicion[1])
        self.simbolo = simbolo

    def estaAca(self,pos):
        """Devuelve un booleano indicando si esta en la coordenada pos,
        la precision viene dada por la constante global RADIO"""
        if (pos[0]-self.posicion[0])**2 + \
                (pos[1]-self.posicion[1])**2 < RADIO2:
            return True
        else:
            return False

    def dibujar(self,pantalla,flipAhora):
        """Dibuja un punto en su posicion"""
        pantalla.blit(self.simbolo, (self.posicion[0]-8, self.posicion[1]-8))
        if flipAhora:
            pygame.display.flip()

    def mostrarNombre(self,pantalla,fuente,color,flipAhora):
        """Escribe el nombre del punto en su posicion"""
        text = fuente.render(self.nombre, 1, color)
        textrect = text.get_rect()
        textrect.center = (self.postexto[0], self.postexto[1])
        pantalla.blit(text, textrect)
        if flipAhora:
            pygame.display.flip()


class Zona():
    """Clase para objetos geograficos que se pueden definir como una zona.

    La posicion esta dada por una imagen bitmap pintada con un color
    especifico, dado por la clave (valor 0 a 255 del componente rojo).
    """

    def __init__(self,mapa,nombre,claveColor,tipo,posicion,rotacion):
        self.mapa = mapa # esto hace una copia en memoria o no????
        self.nombre = nombre
        self.claveColor = int(claveColor)
        self.tipo = int(tipo)
        self.posicion = (int(int(posicion[0])*scale+shift_x),
                         int(int(posicion[1])*scale+shift_y))
        self.rotacion = int(rotacion)

    def estaAca(self,pos):
        """Devuelve True si la coordenada pos esta en la zona"""
        if pos[0] < XMAPAMAX*scale+shift_x:
            try:
                colorAca = self.mapa.get_at((int(pos[0]-shift_x),
                                             int(pos[1]-shift_y)))
            except: # probablemente click fuera de la imagen
                return False
            if colorAca[0] == self.claveColor:
                return True
            else:
                return False
        else:
            return False

    def mostrarNombre(self,pantalla,fuente,color,flipAhora):
        """Escribe el nombre de la zona en su posicion"""
        yLinea = self.posicion[1]
        lineas = self.nombre.split("\n")
        for l in lineas:
            text = fuente.render(l.strip(), 1, color)
            textrot = pygame.transform.rotate(text, self.rotacion)
            textrect = textrot.get_rect()
            textrect.center = (self.posicion[0], yLinea)
            pantalla.blit(textrot, textrect)
            yLinea = yLinea + fuente.get_height() + int(5*scale)


class Nivel():
    """Clase para definir los niveles del juego.

    Cada nivel tiene un dibujo inicial, los elementos pueden estar
    etiquetados con el nombre o no, y un conjunto de preguntas.
    """

    def __init__(self,nombre):
        self.nombre = nombre
        self.dibujoInicial = list()
        self.nombreInicial = list()
        self.preguntas = list()
        self.indicePreguntaActual = 0
        self.elementosActivos = list()

    def prepararPreguntas(self):
        """Este metodo sirve para preparar la lista de preguntas al azar."""
        random.shuffle(self.preguntas)

    def siguientePregunta(self,listaSufijos,listaPrefijos):
        """Prepara el texto de la pregunta siguiente"""
        self.preguntaActual = self.preguntas[self.indicePreguntaActual]
        self.sufijoActual = random.randint(1,len(listaSufijos))-1
        self.prefijoActual = random.randint(1,len(listaPrefijos))-1
        lineas = listaPrefijos[self.prefijoActual].split("\n")
        lineas.extend(self.preguntaActual[0].split("\n"))
        lineas.extend(listaSufijos[self.sufijoActual].split("\n"))
        self.indicePreguntaActual = self.indicePreguntaActual+1
        if self.indicePreguntaActual == len(self.preguntas):
            self.indicePreguntaActual = 0
        return lineas

    def devolverAyuda(self):
        """Devuelve la linea de ayuda"""
        self.preguntaActual = self.preguntas[self.indicePreguntaActual-1]
        return self.preguntaActual[3].split("\n")

class ConozcoUy():
    """Clase principal del juego.

    """

    def mostrarTexto(self,texto,fuente,posicion,color):
        """Muestra texto en una determinada posicion"""
        text = fuente.render(texto, 1, color)
        textrect = text.get_rect()
        textrect.center = posicion
        self.pantalla.blit(text, textrect)

    def loadInfo(self):
        """Carga las imagenes y los datos de cada pais"""
        r_path = os.path.join(self.camino_datos, self.directorio + '.py')
        a_path = os.path.abspath(r_path)
        f = None
        try:
            f = imp.load_source(self.directorio, a_path)
        except:
            print _('Cannot open %s') % self.directorio

        if f:
            lugares = []
            if hasattr(f, 'CAPITALS'):
                lugares = lugares + f.CAPITALS
            if hasattr(f, 'CITIES'):
                lugares = lugares + f.CITIES
            if hasattr(f, 'BEACHS'):
                lugares = lugares + f.BEACHS
            if hasattr(f, 'HILLS'):
                lugares = lugares + f.HILLS
            self.listaLugares = list()
            for c in lugares:
                #nombreLugar = c[0]
                nombreLugar = unicode(c[0], 'UTF-8')
                posx = c[1]
                posy = c[2]
                tipo = c[3]
                incx = c[4]
                incy = c[5]
                if tipo == 0:
                    simbolo = self.simboloCapitalN
                elif tipo == 1:
                    simbolo = self.simboloCapitalD
                elif tipo == 2:
                    simbolo = self.simboloCiudad
                elif tipo == 5:
                    simbolo = self.simboloCerro
                else:
                    simbolo = self.simboloCiudad

                nuevoLugar = Punto(nombreLugar, tipo, simbolo,
                            (posx,posy),(incx,incy))
                self.listaLugares.append(nuevoLugar)

            if hasattr(f, 'STATES'):
                self.deptos = self.cargarImagen("deptos.png")
                self.deptosLineas = self.cargarImagen("deptosLineas.png")
                self.listaDeptos = list()
                for d in f.STATES:
                    #nombreDepto = d[0]
                    nombreDepto = unicode(d[0], 'UTF-8')
                    claveColor = d[1]
                    posx = d[2]
                    posy = d[3]
                    rotacion = d[4]
                    nuevoDepto = Zona(self.deptos, nombreDepto,
                                    claveColor,1,(posx,posy),rotacion)
                    self.listaDeptos.append(nuevoDepto)

            if hasattr(f, 'CUCHILLAS'):
                self.cuchillas = self.cargarImagen("cuchillas.png")
                self.cuchillasDetectar = self.cargarImagen("cuchillasDetectar.png")
                self.listaCuchillas = list()
                for c in f.CUCHILLAS:
                    #nombreCuchilla = c[0]
                    nombreCuchilla = unicode(c[0], 'UTF-8')
                    claveColor = c[1]
                    posx = c[2]
                    posy = c[3]
                    rotacion = c[4]
                    nuevaCuchilla = Zona(self.cuchillasDetectar, nombreCuchilla,
                                    claveColor,4,(posx,posy),rotacion)
                    self.listaCuchillas.append(nuevaCuchilla)

            if hasattr(f, 'RIVERS'):
                self.rios = self.cargarImagen("rios.png")
                self.riosDetectar = self.cargarImagen("riosDetectar.png")
                self.listaRios = list()
                for r in f.RIVERS:
                    #print r[0]
                    nombreRio = unicode(r[0], 'UTF-8')
                    claveColor = r[1]
                    posx = r[2]
                    posy = r[3]
                    rotacion = r[4]
                    nuevoRio = Zona(self.riosDetectar, nombreRio,
                                    claveColor,3,(posx,posy),rotacion)
                    self.listaRios.append(nuevoRio)

            if hasattr(f, 'ROUTES'):
                self.rutas = self.cargarImagen("rutas.png")
                self.rutasDetectar = self.cargarImagen("rutasDetectar.png")
                self.listaRutas = list()
                for r in f.ROUTES:
                    #nombreRuta = r[0]
                    nombreRuta = unicode(r[0], 'UTF-8')
                    claveColor = r[1]
                    posx = r[2]
                    posy = r[3]
                    rotacion = r[4]
                    nuevaRuta = Zona(self.rutasDetectar, nombreRuta,
                                claveColor,6,(posx,posy),rotacion)
                    self.listaRutas.append(nuevaRuta)
            self.lista_estadisticas = list()
            if hasattr(f, 'STATS'):
                for e in f.STATS:
                    p1 = unicode(e[0], 'UTF-8')
                    p2 = unicode(e[1], 'UTF-8')
                    self.lista_estadisticas.append((p1, p2))


    def cargarListaDirectorios(self):
        """Carga la lista de directorios con los distintos mapas"""
        self.listaDirectorios = list()
        self.listaNombreDirectorios = list()
        listaTemp = os.listdir(CAMINORECURSOS)
        listaTemp.sort()
        for d in listaTemp:
            if not (d == 'comun'):
                r_path = os.path.join(CAMINORECURSOS, d, 'datos', d + '.py')
                a_path = os.path.abspath(r_path)
                f = None
                try:
                    f = imp.load_source(d, a_path)
                except:
                    print _('Cannot open %s') % d
                if f:
                    name = unicode(f.NAME, 'UTF-8')
                    self.listaNombreDirectorios.append(name)
                    self.listaDirectorios.append(d)

    def loadCommons(self):
                
        self.listaPrefijos = list()
        self.listaSufijos = list()
        self.listaCorrecto = list()
        self.listaMal = list()
        self.listaDespedidas = list()
        self.listaPresentacion = list()
        self.listaCreditos = list()
        

        r_path = os.path.join(CAMINORECURSOS, CAMINOCOMUN, 'datos', 'commons.py')
        a_path = os.path.abspath(r_path)
        f = None
        try:
            f = imp.load_source('commons', a_path)
        except:
            print _('Cannot open %s') % 'commons'

        if f:
            if hasattr(f, 'ACTIVITY_NAME'):
                e = f.ACTIVITY_NAME
                self.activity_name = unicode(e, 'UTF-8')
            if hasattr(f, 'PREFIX'):
                for e in f.PREFIX:
                    e1 = unicode(e, 'UTF-8')
                    self.listaPrefijos.append(e1)
            if hasattr(f, 'SUFIX'):
                for e in f.SUFIX:
                    e1 = unicode(e, 'UTF-8')
                    self.listaSufijos.append(e1)  
            if hasattr(f, 'CORRECT'):
                for e in f.CORRECT:
                    e1 = unicode(e, 'UTF-8')
                    self.listaCorrecto.append(e1)
            if hasattr(f, 'WRONG'):
                for e in f.WRONG:
                    e1 = unicode(e, 'UTF-8')
                    self.listaMal.append(e1)
            if hasattr(f, 'BYE'):
                for e in f.BYE:
                    e1 = unicode(e, 'UTF-8')
                    self.listaDespedidas.append(e1)
            if hasattr(f, 'PRESENTATION'):
                for e in f.PRESENTATION:
                    e1 = unicode(e, 'UTF-8')
                    self.listaPresentacion.append(e1)
            if hasattr(f, 'CREDITS'):
                for e in f.CREDITS:
                    e1 = unicode(e, 'UTF-8')
                    self.listaCreditos.append(e1)

        self.numeroSufijos = len(self.listaSufijos)
        self.numeroPrefijos = len(self.listaPrefijos)
        self.numeroCorrecto = len(self.listaCorrecto)
        self.numeroMal = len(self.listaMal)
        self.numeroDespedidas = len(self.listaDespedidas)


    def cargarNiveles(self):
        """Carga los niveles del archivo de configuracion"""
        self.listaNiveles = list()

        r_path = os.path.join(self.camino_datos, ARCHIVONIVELES + '.py')
        a_path = os.path.abspath(r_path)
        f = None
        try:
            f = imp.load_source(ARCHIVONIVELES, a_path)
        except:
            print _('Cannot open %s') % ARCHIVONIVELES

        if f:
            if hasattr(f, 'LEVELS'):
                for ln in f.LEVELS:
                    index = ln[0]
                    nombreNivel = unicode(ln[1], 'UTF-8')
                    nuevoNivel = Nivel(nombreNivel)

                    listaDibujos = ln[2]
                    for i in listaDibujos:
                        nuevoNivel.dibujoInicial.append(i.strip())

                    listaNombres = ln[3]
                    for i in listaNombres:
                        nuevoNivel.nombreInicial.append(i.strip())

                    listpreguntas = ln[4]

                    if (index == 1):
                        for i in listpreguntas:
                            texto = unicode(i[0], 'UTF-8')
                            tipo = i[1]
                            respuesta = unicode(i[2], 'UTF-8')
                            ayuda = unicode(i[3], 'UTF-8')
                            nuevoNivel.preguntas.append((texto, tipo, respuesta, ayuda))
                    else:

                        for i in listpreguntas:
                            respuesta = unicode(i[0], 'UTF-8')
                            ayuda = unicode(i[1], 'UTF-8')
                            if (index == 2):
                                tipo = 2
                                texto = _('the city of\n%s') % respuesta
                            elif (index == 7):
                                tipo = 1
                                texto = _('the department of\n%s') % respuesta
                            elif (index == 8):
                                tipo = 1
                                texto = _('the province of\n%s') % respuesta
                            elif (index == 9):
                                tipo = 1
                                texto = _('the district of\n%s') % respuesta
                            elif (index == 10):
                                tipo = 1
                                texto = _('the state of\n%s') % respuesta
                            elif (index == 11):
                                tipo = 1
                                texto = _('the region of\n%s') % respuesta
                            elif (index == 12):
                                tipo = 1
                                texto = _('the parish of\n%s') % respuesta
                            elif (index == 14):
                                tipo = 1
                                texto = _('the taluka of\n%s') % respuesta
                            elif (index == 6):
                                tipo = 1
                                texto = _('the municipality of\n%s') % respuesta
                            elif (index == 4):
                                tipo = 3
                                texto = _('the %s') % respuesta
                            elif (index == 15):
                                tipo = 3
                                texto = _('the %(river)s') % {'river': respuesta}
                            elif (index == 5):
                                tipo = 6
                                texto = _('the %(route)s') % {'route': respuesta}

                            nuevoNivel.preguntas.append((texto, tipo, respuesta, ayuda))

                    self.listaNiveles.append(nuevoNivel)

        self.indiceNivelActual = 0
        self.numeroNiveles = len(self.listaNiveles)


    def cargarExploraciones(self):
        """Carga los niveles de exploracion del archivo de configuracion"""
        self.listaExploraciones = list()

        r_path = os.path.join(self.camino_datos, ARCHIVOEXPLORACIONES + '.py')
        a_path = os.path.abspath(r_path)
        f = None
        try:
            f = imp.load_source(ARCHIVOEXPLORACIONES, a_path)
        except:
            print _('Cannot open %s') % ARCHIVOEXPLORACIONES

        if f:
            if hasattr(f, 'EXPLORATIONS'):
                for e in f.EXPLORATIONS:
                    #nombreNivel = e[0]
                    nombreNivel= unicode(e[0], 'UTF-8')
                    nuevoNivel = Nivel(nombreNivel)

                    listaDibujos = e[1]
                    for i in listaDibujos:
                        nuevoNivel.dibujoInicial.append(i.strip())

                    listaNombres = e[2]
                    for i in listaNombres:
                        nuevoNivel.nombreInicial.append(i.strip())

                    listaNombres = e[3]
                    for i in listaNombres:
                        nuevoNivel.elementosActivos.append(i.strip())

                    self.listaExploraciones.append(nuevoNivel)

        self.numeroExploraciones = len(self.listaExploraciones)

    def pantallaAcercaDe(self):
        """Pantalla con los datos del juego, creditos, etc"""
        global scale, shift_x, shift_y, xo_resolution
        self.pantallaTemp = pygame.Surface(
            (self.anchoPantalla,self.altoPantalla))
        self.pantallaTemp.blit(self.pantalla,(0,0))
        self.pantalla.fill((0,0,0))
        self.pantalla.blit(self.terron,
                        (int(20*scale+shift_x),
                            int(20*scale+shift_y)))
        self.mostrarTexto(_("About %s") % self.activity_name,
                        self.fuente40,
                        (int(600*scale+shift_x),
                        int(100*scale+shift_y)),
                        (255,255,255))

        yLinea = int(200*scale+shift_y)
        for linea in self.listaCreditos:
            self.mostrarTexto(linea.strip(),
                            self.fuente32,
                            (int(600*scale+shift_x),yLinea),
                            (155,155,255))
            yLinea = yLinea + int(40*scale)

        self.mostrarTexto(_("Press any key to return"),
                        self.fuente32,
                        (int(600*scale+shift_x),
                        int(800*scale+shift_y)),
                        (255,155,155))
        pygame.display.flip()
        while 1:
            if gtk_present:
                while gtk.events_pending():
                    gtk.main_iteration()

            for event in wait_events():
                if event.type == pygame.KEYDOWN or \
                        event.type == pygame.MOUSEBUTTONDOWN:
                    if self.sound:
                        self.click.play()
                    self.pantalla.blit(self.pantallaTemp,(0,0))
                    pygame.display.flip()
                    return
                elif event.type == EVENTOREFRESCO:
                    pygame.display.flip()

    def pantallaInicial(self):
        """Pantalla con el menu principal del juego"""
        global scale, shift_x, shift_y
        self.pantalla.fill((0,0,0))
        self.mostrarTexto(self.activity_name,
                        self.fuente60,
                        (int(600*scale+shift_x),
                        int(80*scale+shift_y)),
                        (255,255,255))
        self.mostrarTexto(_("You have chosen the map ")+\
                            self.listaNombreDirectorios\
                            [self.indiceDirectorioActual],
                        self.fuente40,
                        (int(600*scale+shift_x), int(140*scale+shift_y)),
                        (200,100,100))
        self.mostrarTexto(_("Play"),
                        self.fuente60,
                        (int(300*scale+shift_x), int(220*scale+shift_y)),
                        (200,100,100))
        yLista = int(300*scale+shift_y)
        for n in self.listaNiveles:
            self.pantalla.fill((20,20,20),
                            (int(10*scale+shift_x),
                                yLista-int(24*scale),
                                int(590*scale),
                                int(48*scale)))
            self.mostrarTexto(n.nombre,
                            self.fuente40,
                            (int(300*scale+shift_x), yLista),
                            (200,100,100))
            yLista += int(50*scale)
        self.mostrarTexto(_("Explore"),
                        self.fuente60,
                        (int(900*scale+shift_x), int(220*scale+shift_y)),
                        (100,100,200))
        yLista = int(300*scale+shift_y)
        for n in self.listaExploraciones:
            self.pantalla.fill((20,20,20),
                            (int(610*scale+shift_x),
                                yLista-int(24*scale),
                                int(590*scale),
                                int(48*scale)))
            self.mostrarTexto(n.nombre,
                            self.fuente40,
                            (int(900*scale+shift_x),yLista),
                            (100,100,200))
            yLista += int(50*scale)
        self.pantalla.fill((20,20,20),
                        (int(10*scale+shift_x),
                            int(801*scale+shift_y),
                            int(590*scale),int(48*scale)))
        self.mostrarTexto(_("About this game"),
                        self.fuente40,
                        (int(300*scale+shift_x),int(825*scale+shift_y)),
                        (100,200,100))
        self.pantalla.fill((20,20,20),
                        (int(610*scale+shift_x),
                            int(801*scale+shift_y),
                            int(590*scale),int(48*scale)))
        self.mostrarTexto(_("Return"),
                        self.fuente40,
                        (int(900*scale+shift_x),int(825*scale+shift_y)),
                        (100,200,100))
        pygame.display.flip()
        while 1:
            if gtk_present:
                while gtk.events_pending():
                    gtk.main_iteration()

            for event in wait_events():
                if event.type == pygame.KEYDOWN:
                    if event.key == 27: # escape: volver
                        if self.sound:
                            self.click.play()
                        self.elegir_directorio = True
                        return
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.sound:
                        self.click.play()
                    pos = event.pos
                    if pos[1] > 275*scale + shift_y: # zona de opciones
                        if pos[0] < 600*scale + shift_x: # primera columna
                            if pos[1] < 275*scale + shift_y + \
                                    len(self.listaNiveles)*50*scale: # nivel
                                self.indiceNivelActual = \
                                    int((pos[1]-int(275*scale+shift_y))//\
                                            int(50*scale))
                                self.jugar = True
                                return
                            elif pos[1] > 800*scale + shift_y and \
                                    pos[1] < 850*scale + shift_y: # acerca de
                                self.pantallaAcercaDe()
                        else: # segunda columna
                            if pos[1] < 275*scale + shift_y+\
                                    len(self.listaExploraciones)*50*scale:
                                # nivel de exploracion
                                self.indiceNivelActual = \
                                    int((pos[1]-int(275*scale+shift_y))//\
                                            int(50*scale))
                                self.jugar = False
                                return
                            elif pos[1] > 800*scale + shift_y and \
                                    pos[1] < 850*scale+shift_y: # volver
                                self.elegir_directorio = True
                                return
                elif event.type == EVENTOREFRESCO:
                    pygame.display.flip()

    def pantallaDirectorios(self):
        """Pantalla con el menu de directorios"""
        global scale, shift_x, shift_y
        self.pantalla.fill((0,0,0))
        self.mostrarTexto(self.activity_name,
                        self.fuente60,
                        (int(600*scale+shift_x),int(80*scale+shift_y)),
                        (255,255,255))
        self.mostrarTexto(_("Choose the map to use"),
                        self.fuente40,
                        (int(600*scale+shift_x),int(140*scale+shift_y)),
                        (200,100,100))
        nDirectorios = len(self.listaNombreDirectorios)
        paginaDirectorios = self.paginaDir
        while 1:
            yLista = int(200*scale+shift_y)
            self.pantalla.fill((0,0,0),
                            (int(shift_x),yLista-int(24*scale),
                                int(1200*scale),int(600*scale)))
            if paginaDirectorios == 0:
                paginaAnteriorActiva = False
            else:
                paginaAnteriorActiva = True
            paginaSiguienteActiva = False
            if paginaAnteriorActiva:
                self.pantalla.fill((20,20,20),
                                (int(10*scale+shift_x),yLista-int(24*scale),
                                    int(590*scale),int(48*scale)))
                self.mostrarTexto(unicode("<<< " + _("Previous page"), "UTF-8"),
                                self.fuente40,
                                (int(300*scale+shift_x),yLista),
                                (100,100,200))
            yLista += int(50*scale)
            indiceDir = paginaDirectorios * 20
            terminar = False
            while not terminar:
                self.pantalla.fill((20,20,20),
                                (int(10*scale+shift_x),yLista-int(24*scale),
                                    int(590*scale),int(48*scale)))
                self.mostrarTexto(self.listaNombreDirectorios[indiceDir],
                                self.fuente40,
                                (int(300*scale+shift_x),yLista),
                                (200,100,100))
                yLista += int(50*scale)
                indiceDir = indiceDir + 1
                if indiceDir == nDirectorios or \
                        indiceDir == paginaDirectorios * 20 + 10:
                    terminar = True
            if indiceDir == paginaDirectorios * 20 + 10 and \
                    not indiceDir == nDirectorios:
                nDirectoriosCol1 = 10
                yLista = int(250*scale+shift_y)
                terminar = False
                while not terminar:
                    self.pantalla.fill((20,20,20),
                                    (int(610*scale+shift_x),
                                        yLista-int(24*scale),
                                        int(590*scale),int(48*scale)))
                    self.mostrarTexto(self.listaNombreDirectorios[indiceDir],
                                    self.fuente40,
                                    (int(900*scale+shift_x),yLista),
                                    (200,100,100))
                    yLista += int(50*scale)
                    indiceDir = indiceDir + 1
                    if indiceDir == nDirectorios or \
                            indiceDir == paginaDirectorios * 20 + 20:
                        terminar = True
                if indiceDir == paginaDirectorios * 20 + 20:
                    if indiceDir < nDirectorios:
                        self.pantalla.fill((20,20,20),
                                        (int(610*scale+shift_x),
                                            yLista-int(24*scale),
                                            int(590*scale),int(48*scale)))
                        self.mostrarTexto(unicode(_("Next page") + " >>>", "UTF-8"),
                                        self.fuente40,
                                        (int(900*scale+shift_x),yLista),
                                        (100,100,200))
                        paginaSiguienteActiva = True
                    nDirectoriosCol2 = 10
                else:
                    nDirectoriosCol2 = indiceDir - paginaDirectorios * 20 - 10
            else:
                nDirectoriosCol1 = indiceDir - paginaDirectorios * 20
                nDirectoriosCol2 = 0
            self.pantalla.fill((20,20,20),
                            (int(10*scale+shift_x),int(801*scale+shift_y),
                                int(590*scale),int(48*scale)))
            self.mostrarTexto(_("About this game"),
                            self.fuente40,
                            (int(300*scale+shift_x),int(825*scale+shift_y)),
                            (100,200,100))
            self.pantalla.fill((20,20,20),
                            (int(610*scale+shift_x),int(801*scale+shift_y),
                                int(590*scale),int(48*scale)))
            self.mostrarTexto(_("Exit"),
                            self.fuente40,
                            (int(900*scale+shift_x),int(825*scale+shift_y)),
                            (100,200,100))
            pygame.display.flip()
            cambiarPagina = False
            while not cambiarPagina:
                if gtk_present:
                    while gtk.events_pending():
                        gtk.main_iteration()

                for event in wait_events():
                    if event.type == pygame.KEYDOWN:
                        if event.key == 27: # escape: salir
                            if self.sound:
                                self.click.play()
                            sys.exit()
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        if self.sound:
                            self.click.play()
                        pos = event.pos
                        if pos[1] > 175*scale+shift_y: # zona de opciones
                            if pos[0] < 600*scale+shift_x: # primera columna
                                if pos[1] < 175*scale + shift_y + \
                                        (nDirectoriosCol1+1)*50*scale: # mapa
                                    self.indiceDirectorioActual = \
                                        int((pos[1]-int(175*scale+shift_y))//\
                                                int(50*scale)) - 1 + \
                                                paginaDirectorios*20
                                    if self.indiceDirectorioActual == \
                                            paginaDirectorios*20-1 and \
                                            paginaAnteriorActiva: # pag. ant.
                                        paginaDirectorios = paginaDirectorios-1
                                        paginaSiguienteActiva = True
                                        cambiarPagina = True
                                    elif self.indiceDirectorioActual>\
                                            paginaDirectorios*20-1:
                                        self.paginaDir = paginaDirectorios
                                        return
                                elif pos[1] > 800*scale + shift_y and \
                                        pos[1] < 850*scale + shift_y: # acerca
                                    self.pantallaAcercaDe()
                            else:
                                if pos[1] < 225*scale + shift_y + \
                                        nDirectoriosCol2*50*scale or \
                                        (paginaSiguienteActiva and \
                                            pos[1]<775*scale+shift_y): # mapa
                                    self.indiceDirectorioActual = \
                                        int((pos[1]-int(225*scale+shift_y))//\
                                                int(50*scale)) + \
                                                paginaDirectorios*20 + 10
                                    if self.indiceDirectorioActual == \
                                            paginaDirectorios*20+9:
                                        pass # ignorar; espacio vacio
                                    elif self.indiceDirectorioActual == \
                                            paginaDirectorios*20+20 and \
                                            paginaSiguienteActiva: # pag. sig.
                                        paginaDirectorios = \
                                            paginaDirectorios + 1
                                        paginaAnteriorActiva = True
                                        cambiarPagina = True
                                    elif self.indiceDirectorioActual<\
                                            paginaDirectorios*20+20:
                                        self.paginaDir = paginaDirectorios
                                        return
                                elif pos[1] > 800*scale+shift_y and \
                                        pos[1] < 850*scale+shift_y: # salir
                                    sys.exit()
                    elif event.type == EVENTOREFRESCO:
                        pygame.display.flip()

    def cargarImagen(self,nombre):
        """Carga una imagen y la escala de acuerdo a la resolucion"""
        global scale, xo_resolution
        imagen = None
        archivo = os.path.join(self.camino_imagenes, nombre)
        if os.path.exists(archivo):
            if xo_resolution:
                imagen = pygame.image.load( \
                    os.path.join(self.camino_imagenes,nombre))
            else:
                imagen0 = pygame.image.load( \
                    os.path.join(self.camino_imagenes,nombre))
                imagen = pygame.transform.scale(imagen0,
                            (int(imagen0.get_width()*scale),
                            int(imagen0.get_height()*scale)))
                del imagen0
        return imagen

    def __init__(self):
        """Esta es la inicializacion del juego"""
        file_activity_info = ConfigParser.ConfigParser()
        activity_info_path = os.path.abspath('activity/activity.info')
        file_activity_info.read(activity_info_path)
        bundle_id = file_activity_info.get('Activity', 'bundle_id')
        self.activity_name = file_activity_info.get('Activity', 'name')
        path = os.path.abspath('locale')
        gettext.bindtextdomain(bundle_id, path)
        gettext.textdomain(bundle_id)
        global _
        _ = gettext.gettext


    def loadAll(self):
        global scale, shift_x, shift_y, xo_resolution
        pygame.init()
        pygame.display.init()
        # crear pantalla
        info = pygame.display.Info()
        self.anchoPantalla = info.current_w
        self.altoPantalla = info.current_h
        self.pantalla = pygame.display.get_surface()
        if not(self.pantalla):
            # prevent hide zones
            #self.anchoPantalla = self.anchoPantalla - 50
            #self.altoPantalla = self.altoPantalla - 100
            self.pantalla = pygame.display.set_mode((self.anchoPantalla,
                                               self.altoPantalla), pygame.FULLSCREEN)
        pygame.display.flip()
        if self.anchoPantalla==1200 and self.altoPantalla==900:
            xo_resolution = True
            scale = 1
            shift_x = 0
            shift_y = 0
        else:
            xo_resolution = False
            if self.anchoPantalla/1200.0<self.altoPantalla/900.0:
                scale = self.anchoPantalla/1200.0
                shift_x = 0
                shift_y = int((self.altoPantalla-scale*900)/2)
            else:
                scale = self.altoPantalla/900.0
                shift_x = int((self.anchoPantalla-scale*1200)/2)
                shift_y = 0
        # cargar imagenes generales
        self.camino_imagenes = os.path.join(CAMINORECURSOS,
                                            CAMINOCOMUN,
                                            CAMINOIMAGENES)
        self.bicho = self.cargarImagen("bicho.png")
        self.bichopestanas = self.cargarImagen("bichopestanas.png")
        self.bichofrente = self.cargarImagen("bichofrente.png")
        self.globito = self.cargarImagen("globito.png")
        self.nave = list()
        self.nave.append(self.cargarImagen("nave1.png"))
        self.nave.append(self.cargarImagen("nave2.png"))
        self.nave.append(self.cargarImagen("nave3.png"))
        self.nave.append(self.cargarImagen("nave4.png"))
        self.nave.append(self.cargarImagen("nave5.png"))
        self.nave.append(self.cargarImagen("nave6.png"))
        self.nave.append(self.cargarImagen("nave7.png"))
        self.fuego = list()
        self.fuego.append(self.cargarImagen("fuego1.png"))
        self.fuego.append(self.cargarImagen("fuego2.png"))
        self.tierra = self.cargarImagen("tierra.png")
        self.navellegando = self.cargarImagen("navellegando.png")
        self.bichotriste = self.cargarImagen("bichotriste.png")
        self.alerta = self.cargarImagen("alerta.png")
        self.alertarojo = self.cargarImagen("alertarojo.png")
        self.pedazo1 = self.cargarImagen("pedazo1.png")
        self.pedazo2 = self.cargarImagen("pedazo2.png")
        self.paracaidas = self.cargarImagen("paracaidas.png")
        self.terron = self.cargarImagen("terron.png")

        self.simboloCapitalD = self.cargarImagen("capitalD.png")
        self.simboloCapitalN = self.cargarImagen("capitalN.png")
        self.simboloCiudad = self.cargarImagen("ciudad.png")

        self.simboloCerro = self.cargarImagen("cerro.png")
        # cargar sonidos
        self.camino_sonidos = os.path.join(CAMINORECURSOS,
                                           CAMINOCOMUN,
                                           CAMINOSONIDOS)
        self.sound = True
        try:
            self.despegue = pygame.mixer.Sound(os.path.join(\
                    self.camino_sonidos,"NoiseCollector_boom2.ogg"))
            self.click = pygame.mixer.Sound(os.path.join(\
                    self.camino_sonidos,"junggle_btn117.wav"))
            self.click.set_volume(0.2)
            self.chirp = pygame.mixer.Sound(os.path.join(\
                    self.camino_sonidos,"chirp_alerta.ogg"))
        except:
            self.sound = False
        # cargar directorios
        self.cargarListaDirectorios()
        # cargar fuentes
        self.fuente60 = pygame.font.Font(os.path.join(CAMINORECURSOS,\
                                                        CAMINOCOMUN,\
                                                        CAMINOFUENTES,\
                                                        "Share-Regular.ttf"),
                                        int(60*scale))
        self.fuente40 = pygame.font.Font(os.path.join(CAMINORECURSOS,\
                                                        CAMINOCOMUN,\
                                                        CAMINOFUENTES,\
                                                        "Share-Regular.ttf"),
                                        int(34*scale))
        self.fuente9 = pygame.font.Font(os.path.join(CAMINORECURSOS,\
                                                        CAMINOCOMUN,\
                                                        CAMINOFUENTES,\
                                                        "Share-Regular.ttf"),
                                        int(20*scale))
        self.fuente32 = pygame.font.Font(None, int(30*scale))
        self.fuente24 = pygame.font.Font(None, int(24*scale))
        # cursor
        datos_cursor = (
            "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX  ",
            "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX ",
            "XXX.........................XXXX",
            "XXX..........................XXX",
            "XXX..........................XXX",
            "XXX.........................XXXX",
            "XXX.......XXXXXXXXXXXXXXXXXXXXX ",
            "XXX........XXXXXXXXXXXXXXXXXXX  ",
            "XXX.........XXX                 ",
            "XXX..........XXX                ",
            "XXX...........XXX               ",
            "XXX....X.......XXX              ",
            "XXX....XX.......XXX             ",
            "XXX....XXX.......XXX            ",
            "XXX....XXXX.......XXX           ",
            "XXX....XXXXX.......XXX          ",
            "XXX....XXXXXX.......XXX         ",
            "XXX....XXX XXX.......XXX        ",
            "XXX....XXX  XXX.......XXX       ",
            "XXX....XXX   XXX.......XXX      ",
            "XXX....XXX    XXX.......XXX     ",
            "XXX....XXX     XXX.......XXX    ",
            "XXX....XXX      XXX.......XXX   ",
            "XXX....XXX       XXX.......XXX  ",
            "XXX....XXX        XXX.......XXX ",
            "XXX....XXX         XXX.......XXX",
            "XXX....XXX          XXX......XXX",
            "XXX....XXX           XXX.....XXX",
            "XXX....XXX            XXX...XXXX",
            " XXX..XXX              XXXXXXXX ",
            "  XXXXXX                XXXXXX  ",
            "   XXXX                  XXXX   ")
        self.cursor = pygame.cursors.compile(datos_cursor)
        pygame.mouse.set_cursor((32,32), (1,1), *self.cursor)
        datos_cursor_espera = (
            "                                ",
            "                                ",
            "                                ",
            "                                ",
            "                                ",
            "                                ",
            "                                ",
            "                                ",
            "                                ",
            "                                ",
            "  XXXXXX     XXXXXX     XXXXXX  ",
            " XXXXXXXX   XXXXXXXX   XXXXXXXX ",
            "XXXX..XXXX XXXX..XXXX XXXX..XXXX",
            "XXX....XXX XXX....XXX XXX....XXX",
            "XXX....XXX XXX....XXX XXX....XXX",
            "XXX....XXX XXX....XXX XXX....XXX",
            "XXXX..XXXX XXXX..XXXX XXXX..XXXX",
            " XXXXXXXX   XXXXXXXX   XXXXXXXX ",
            "  XXXXXX     XXXXXX      XXXXX  ",
            "                                ",
            "                                ",
            "                                ",
            "                                ",
            "                                ",
            "                                ",
            "                                ",
            "                                ",
            "                                ",
            "                                ",
            "                                ",
            "                                ",
            "                                ")
        self.cursor_espera = pygame.cursors.compile(datos_cursor_espera)

    def cargarDirectorio(self):
        """Carga la informacion especifica de un directorio"""
        self.camino_imagenes = os.path.join(CAMINORECURSOS,
                                            self.directorio,
                                            CAMINOIMAGENES)
        self.camino_sonidos = os.path.join(CAMINORECURSOS,
                                            self.directorio,
                                            CAMINOSONIDOS)
        self.camino_datos = os.path.join(CAMINORECURSOS,
                                            self.directorio,
                                            CAMINODATOS)
        self.fondo = self.cargarImagen("fondo.png")
        self.bandera = self.cargarImagen("bandera.png")

        self.loadInfo()

        self.cargarNiveles()
        self.cargarExploraciones()

    def mostrarGlobito(self,lineas):
        """Muestra texto en el globito"""
        global scale, shift_x, shift_y
        self.pantalla.blit(self.globito,
                           (int(XMAPAMAX*scale+shift_x),
                            int(YGLOBITO*scale+shift_y)))
        yLinea = int(YGLOBITO*scale) + shift_y + \
            self.fuente32.get_height()*3
        for l in lineas:
            text = self.fuente32.render(l, 1, COLORPREGUNTAS)
            textrect = text.get_rect()
            textrect.center = (int(XCENTROPANEL*scale+shift_x),yLinea)
            self.pantalla.blit(text, textrect)
            yLinea = yLinea + self.fuente32.get_height() + int(10*scale)
        pygame.display.flip()

    def borrarGlobito(self):
        """ Borra el globito, lo deja en blanco"""
        global scale, shift_x, shift_y
        self.pantalla.blit(self.globito,
                           (int(XMAPAMAX*scale+shift_x),
                            int(YGLOBITO*scale+shift_y)))

    def correcto(self):
        """Muestra texto en el globito cuando la respuesta es correcta"""
        global scale, shift_x, shift_y
        self.pantalla.blit(self.nave[self.avanceNivel],
                           (int(XNAVE*scale+shift_x),
                            int(YNAVE*scale+shift_y)))
        self.correctoActual = random.randint(1,self.numeroCorrecto)-1
        self.mostrarGlobito([self.listaCorrecto[self.correctoActual]])
        self.esCorrecto = True
        pygame.time.set_timer(EVENTORESPUESTA,TIEMPORESPUESTA)
        
    def mal(self):
        """Muestra texto en el globito cuando la respuesta es incorrecta"""
        self.malActual = random.randint(1,self.numeroMal)-1
        self.mostrarGlobito([self.listaMal[self.malActual]])
        self.esCorrecto = False
        self.nRespuestasMal += 1
        pygame.time.set_timer(EVENTORESPUESTA,TIEMPORESPUESTA)

    def esCorrecta(self,nivel,pos):
        """Devuelve True si las coordenadas cliqueadas corresponden a la
        respuesta correcta
        """
        respCorrecta = nivel.preguntaActual[2]
        # primero averiguar tipo
        if nivel.preguntaActual[1] == 1: # DEPTO
            # buscar depto correcto
            for d in self.listaDeptos:
                if d.nombre == respCorrecta:
                    break
            if d.estaAca(pos):
                d.mostrarNombre(self.pantalla,
                                self.fuente32,
                                COLORNOMBREDEPTO,
                                True)
                return True
            else:
                return False
        elif nivel.preguntaActual[1] == 2: # CAPITAL o CIUDAD
            # buscar lugar correcto
            for l in self.listaLugares:
                if l.nombre == respCorrecta:
                    break
            if l.estaAca(pos):
                l.mostrarNombre(self.pantalla,
                                self.fuente24,
                                COLORNOMBRECAPITAL,
                                True)
                return True
            else:
                return False
        if nivel.preguntaActual[1] == 3: # RIO
            # buscar rio correcto
            for d in self.listaRios:
                if d.nombre == respCorrecta:
                    break
            if d.estaAca(pos):
                d.mostrarNombre(self.pantalla,
                                self.fuente24,
                                COLORNOMBRERIO,
                                True)
                return True
            else:
                return False
        if nivel.preguntaActual[1] == 4: # CUCHILLA
            # buscar cuchilla correcta
            for d in self.listaCuchillas:
                if d.nombre == respCorrecta:
                    break
            if d.estaAca(pos):
                d.mostrarNombre(self.pantalla,
                                self.fuente24,
                                COLORNOMBREELEVACION,
                                True)
                return True
            else:
                return False
        elif nivel.preguntaActual[1] == 5: # CERRO
            # buscar lugar correcto
            for l in self.listaLugares:
                if l.nombre == respCorrecta:
                    break
            if l.estaAca(pos):
                l.mostrarNombre(self.pantalla,
                                self.fuente24,
                                COLORNOMBREELEVACION,
                                True)
                return True
            else:
                return False
        if nivel.preguntaActual[1] == 6: # RUTA
            # buscar ruta correcta
            for d in self.listaRutas:
                if d.nombre == respCorrecta:
                    break
            if d.estaAca(pos):
                d.mostrarNombre(self.pantalla,
                                self.fuente24,
                                COLORNOMBRERUTA,
                                True)
                return True
            else:
                return False

    def explorarNombres(self):
        """Juego principal en modo exploro."""
        self.nivelActual = self.listaExploraciones[self.indiceNivelActual]
        # presentar nivel
        for i in self.nivelActual.dibujoInicial:
            if i.startswith("lineasDepto"):
                self.pantalla.blit(self.deptosLineas, (shift_x, shift_y))
            elif i.startswith("rios"):
                self.pantalla.blit(self.rios, (shift_x, shift_y))
            elif i.startswith("rutas"):
                self.pantalla.blit(self.rutas, (shift_x, shift_y))
            elif i.startswith("cuchillas"):
                self.pantalla.blit(self.cuchillas, (shift_x, shift_y))
            elif i.startswith("capitales"):
                for l in self.listaLugares:
                    if ((l.tipo == 0) or (l.tipo == 1)):
                        l.dibujar(self.pantalla,False)
            elif i.startswith("ciudades"):
                for l in self.listaLugares:
                    if l.tipo == 2:
                        l.dibujar(self.pantalla,False)
            elif i.startswith("cerros"):
                for l in self.listaLugares:
                    if l.tipo == 5:
                        l.dibujar(self.pantalla,False)
        for i in self.nivelActual.nombreInicial:
            if i.startswith("deptos"):
                for d in self.listaDeptos:
                    d.mostrarNombre(self.pantalla,self.fuente32,
                                    COLORNOMBREDEPTO,False)
            elif i.startswith("rios"):
                for d in self.listaRios:
                    d.mostrarNombre(self.pantalla,self.fuente24,
                                    COLORNOMBRERIO,False)
            elif i.startswith("rutas"):
                for d in self.listaRutas:
                    d.mostrarNombre(self.pantalla,self.fuente24,
                                    COLORNOMBRERUTA,False)
            elif i.startswith("cuchillas"):
                for d in self.listaCuchillas:
                    d.mostrarNombre(self.pantalla,self.fuente24,
                                    COLORNOMBREELEVACION,False)
            elif i.startswith("capitales"):
                for l in self.listaLugares:
                    if ((l.tipo == 0) or (l.tipo == 1)):
                        l.mostrarNombre(self.pantalla,self.fuente24,
                                        COLORNOMBRECAPITAL,False)
            elif i.startswith("ciudades"):
                for l in self.listaLugares:
                    if l.tipo == 2:
                        l.mostrarNombre(self.pantalla,self.fuente24,
                                        COLORNOMBRECAPITAL,False)
            elif i.startswith("cerros"):
                for l in self.listaLugares:
                    if l.tipo == 5:
                        l.mostrarNombre(self.pantalla,self.fuente24,
                                        COLORNOMBREELEVACION,False)
        # boton terminar
        self.pantalla.fill((100,20,20),(int(975*scale+shift_x),
                                        int(25*scale+shift_y),
                                        int(200*scale),
                                        int(50*scale)))
        self.mostrarTexto(_("End"),
                        self.fuente40,
                        (int(1075*scale+shift_x),
                        int(50*scale+shift_y)),
                        (255,155,155))
        pygame.display.flip()
        # boton mostrar todo
        self.pantalla.fill((100,20,20),(int(975*scale+shift_x),
                                        int(90*scale+shift_y),
                                        int(200*scale),
                                        int(50*scale)))
        self.mostrarTexto(_("Show all"),
                        self.fuente40,
                        (int(1075*scale+shift_x),
                        int(115*scale+shift_y)),
                        (255,155,155))
        pygame.display.flip()
        # lazo principal de espera por acciones del usuario
        while 1:
            if gtk_present:
                while gtk.events_pending():
                    gtk.main_iteration()

            for event in wait_events():
                if event.type == pygame.KEYDOWN:
                    if event.key == 27: # escape: salir
                        if self.sound:
                            self.click.play()
                        return
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.sound:
                        self.click.play()
                    if event.pos[0] < XMAPAMAX*scale+shift_x: # zona de mapa
                        for i in self.nivelActual.elementosActivos:
                            if i.startswith("capitales"):
                                for l in self.listaLugares:
                                    if ((l.tipo == 0) or (l.tipo == 1)) and l.estaAca(event.pos):
                                        l.mostrarNombre(self.pantalla,
                                                        self.fuente24,
                                                        COLORNOMBRECAPITAL,
                                                        True)
                                        break
                            elif i.startswith("ciudades"):
                                for l in self.listaLugares:
                                    if l.tipo == 2 and l.estaAca(event.pos):
                                        l.mostrarNombre(self.pantalla,
                                                        self.fuente24,
                                                        COLORNOMBRECAPITAL,
                                                        True)
                                        break
                            elif i.startswith("rios"):
                                for d in self.listaRios:
                                    if d.estaAca(event.pos):
                                        d.mostrarNombre(self.pantalla,
                                                        self.fuente24,
                                                        COLORNOMBRERIO,
                                                        True)
                                        break
                            elif i.startswith("rutas"):
                                for d in self.listaRutas:
                                    if d.estaAca(event.pos):
                                        d.mostrarNombre(self.pantalla,
                                                        self.fuente24,
                                                        COLORNOMBRERUTA,
                                                        True)
                                        break
                            elif i.startswith("cuchillas"):
                                for d in self.listaCuchillas:
                                    if d.estaAca(event.pos):
                                        d.mostrarNombre(self.pantalla,
                                                        self.fuente24,
                                                        COLORNOMBREELEVACION,
                                                        True)
                                        break
                            elif i.startswith("cerros"):
                                for l in self.listaLugares:
                                    if l.tipo == 5 and l.estaAca(event.pos):
                                        l.mostrarNombre(self.pantalla,
                                                        self.fuente24,
                                                        COLORNOMBREELEVACION,
                                                        True)
                                        break
                            elif i.startswith("deptos"):
                                for d in self.listaDeptos:
                                    if d.estaAca(event.pos):
                                        d.mostrarNombre(self.pantalla,
                                                        self.fuente32,
                                                        COLORNOMBREDEPTO,
                                                        True)
                                        break
                    elif event.pos[0] > 975*scale+shift_x and \
                            event.pos[0] < 1175*scale+shift_x:
                        if event.pos[1] > 25*scale+shift_y and \
                            event.pos[1] < 75*scale+shift_y: # terminar
                            return
                        elif event.pos[1] > 90*scale+shift_y and \
                            event.pos[1] < 140*scale+shift_y: # mostrar todo
                            for i in self.nivelActual.elementosActivos:
                                if i.startswith("deptos"):
                                    for d in self.listaDeptos:
                                        d.mostrarNombre(self.pantalla,self.fuente32,
                                                        COLORNOMBREDEPTO,False)
                                elif i.startswith("rios"):
                                    for d in self.listaRios:
                                        d.mostrarNombre(self.pantalla,self.fuente24,
                                                        COLORNOMBRERIO,False)
                                elif i.startswith("rutas"):
                                    for d in self.listaRutas:
                                        d.mostrarNombre(self.pantalla,self.fuente24,
                                                        COLORNOMBRERUTA,False)
                                elif i.startswith("cuchillas"):
                                    for d in self.listaCuchillas:
                                        d.mostrarNombre(self.pantalla,self.fuente24,
                                                        COLORNOMBREELEVACION,False)
                                elif i.startswith("capitales"):
                                    for l in self.listaLugares:
                                        if ((l.tipo == 0) or (l.tipo == 1)):
                                            l.mostrarNombre(self.pantalla,self.fuente24,
                                                            COLORNOMBRECAPITAL,False)
                                elif i.startswith("ciudades"):
                                    for l in self.listaLugares:
                                        if l.tipo == 2:
                                            l.mostrarNombre(self.pantalla,self.fuente24,
                                                            COLORNOMBRECAPITAL,False)
                                elif i.startswith("cerros"):
                                    for l in self.listaLugares:
                                        if l.tipo == 5:
                                            l.mostrarNombre(self.pantalla,self.fuente24,
                                                            COLORNOMBREELEVACION,False)
                            pygame.display.flip()
                elif event.type == EVENTOREFRESCO:
                    pygame.display.flip()


    def jugarNivel(self):
        """Juego principal de preguntas y respuestas"""
        self.nivelActual = self.listaNiveles[self.indiceNivelActual]
        self.avanceNivel = 0
        self.nivelActual.prepararPreguntas()
        # presentar nivel
        for i in self.nivelActual.dibujoInicial:
            if i.startswith("lineasDepto"):
                self.pantalla.blit(self.deptosLineas, (shift_x, shift_y))
            elif i.startswith("rios"):
                self.pantalla.blit(self.rios, (shift_x, shift_y))
            elif i.startswith("rutas"):
                self.pantalla.blit(self.rutas, (shift_x, shift_y))
            elif i.startswith("cuchillas"):
                self.pantalla.blit(self.cuchillas, (shift_x, shift_y))
            elif i.startswith("capitales"):
                for l in self.listaLugares:
                    if ((l.tipo == 0) or (l.tipo == 1)):
                        l.dibujar(self.pantalla,False)
            elif i.startswith("ciudades"):
                for l in self.listaLugares:
                    if l.tipo == 2:
                        l.dibujar(self.pantalla,False)
            elif i.startswith("cerros"):
                for l in self.listaLugares:
                    if l.tipo == 5:
                        l.dibujar(self.pantalla,False)
        for i in self.nivelActual.nombreInicial:
            if i.startswith("deptos"):
                for d in self.listaDeptos:
                    d.mostrarNombre(self.pantalla,self.fuente32,
                                    COLORNOMBREDEPTO,False)
            if i.startswith("rios"):
                for d in self.listaRios:
                    d.mostrarNombre(self.pantalla,self.fuente24,
                                    COLORNOMBRERIO,False)
            if i.startswith("rutas"):
                for d in self.listaRutas:
                    d.mostrarNombre(self.pantalla,self.fuente24,
                                    COLORNOMBRERUTA,False)
            if i.startswith("cuchillas"):
                for d in self.listaCuchillas:
                    d.mostrarNombre(self.pantalla,self.fuente24,
                                    COLORNOMBREELEVACION,False)
            elif i.startswith("capitales"):
                for l in self.listaLugares:
                    if l.tipo == 1:
                        l.mostrarNombre(self.pantalla,self.fuente24,
                                        COLORNOMBRECAPITAL,False)
            elif i.startswith("ciudades"):
                for l in self.listaLugares:
                    if l.tipo == 2:
                        l.mostrarNombre(self.pantalla,self.fuente24,
                                        COLORNOMBRECAPITAL,False)
            elif i.startswith("cerros"):
                for l in self.listaLugares:
                    if l.tipo == 5:
                        l.mostrarNombre(self.pantalla,self.fuente24,
                                        COLORNOMBREELEVACION,False)
        self.pantalla.fill((100,20,20),
                           (int(975*scale+shift_x),
                            int(26*scale+shift_y),
                            int(200*scale),
                            int(48*scale)))
        self.mostrarTexto("End",
                          self.fuente40,
                          (int(1075*scale+shift_x),
                           int(50*scale+shift_y)),
                          (255,155,155))
        pygame.display.flip()
        # presentar pregunta inicial
        self.lineasPregunta = self.nivelActual.siguientePregunta(\
                self.listaSufijos,self.listaPrefijos)
        self.mostrarGlobito(self.lineasPregunta)
        self.nRespuestasMal = 0
        # leer eventos y ver si la respuesta es correcta
        while 1:
            if gtk_present:
                while gtk.events_pending():
                    gtk.main_iteration()

            for event in wait_events():
                if event.type == pygame.KEYDOWN:
                    if event.key == 27: # escape: salir
                        if self.sound:
                            self.click.play()
                        pygame.time.set_timer(EVENTORESPUESTA,0)
                        pygame.time.set_timer(EVENTODESPEGUE,0)
                        return
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.sound:
                        self.click.play()
                    if self.avanceNivel < TOTALAVANCE:
                        if event.pos[0] < XMAPAMAX*scale+shift_x: # zona mapa
                            self.borrarGlobito()
                            if self.esCorrecta(self.nivelActual,
                                               event.pos):
                                self.correcto()
                            else:
                                self.mal()
                        elif event.pos[0] > 975*scale+shift_x and \
                                event.pos[0] < 1175*scale+shift_x and \
                                event.pos[1] > 25*scale+shift_y and \
                                event.pos[1] < 75*scale+shift_y: # terminar
                            return
                elif event.type == EVENTORESPUESTA:
                    pygame.time.set_timer(EVENTORESPUESTA,0)
                    if self.esCorrecto:
                        self.avanceNivel = self.avanceNivel + 1
                        if self.avanceNivel == TOTALAVANCE: # inicia despegue
                            self.lineasPregunta =  self.listaDespedidas[\
                                random.randint(1,self.numeroDespedidas)-1]\
                                .split("\n")
                            self.mostrarGlobito(self.lineasPregunta)
                            self.yNave = int(YNAVE*scale+shift_y)
                            self.fuego1 = True
                            pygame.time.set_timer(EVENTODESPEGUE,
                                                  TIEMPORESPUESTA*2)
                        else: # pregunta siguiente
                            self.lineasPregunta = \
                                self.nivelActual.siguientePregunta(\
                                self.listaSufijos,self.listaPrefijos)
                            self.mostrarGlobito(self.lineasPregunta)
                            self.nRespuestasMal = 0
                    else:
                        if self.nRespuestasMal >= 2: # ayuda
                            self.mostrarGlobito(
                                self.nivelActual.devolverAyuda())
                            self.nRespuestasMal = 0
                            pygame.time.set_timer(
                                EVENTORESPUESTA,TIEMPORESPUESTA)
                        else: # volver a preguntar
                            self.mostrarGlobito(self.lineasPregunta)
                elif event.type == EVENTODESPEGUE:
                    if self.yNave == int(YNAVE*scale+shift_y): # inicio
                        self.pantalla.fill(COLORPANEL,
                                           (int(XBICHO*scale+shift_x),
                                            int(YBICHO*scale+shift_y),
                                            int(DXBICHO*scale),
                                            int(DYBICHO*scale)))
                        self.pantalla.fill(COLORPANEL,
                                           (int(XMAPAMAX*scale+shift_x),0,
                                            int(DXPANEL*scale),
                                            int(900*scale)))
                        self.estadobicho = ESTADODESPEGUE
                        if self.sound:
                            self.despegue.play()
                    self.pantalla.fill(COLORPANEL,
                                       (int(XNAVE*scale+shift_x),
                                        self.yNave,
                                        int(DXNAVE*scale),
                                        int((DYNAVE+30)*scale)))
                    self.yNave = self.yNave-8
                    if self.yNave<1: # fin del despegue
                        pygame.time.set_timer(EVENTODESPEGUE,0)
                        return
                    else: # animacion
                        pygame.time.set_timer(EVENTODESPEGUE,TIEMPODESPEGUE)
                        self.pantalla.blit(self.nave[6],
                                           (int(XNAVE*scale+shift_x),
                                            self.yNave))
                        if self.fuego1:
                            self.pantalla.blit(self.fuego[0],
                                               (int((XNAVE+30)*scale+shift_x),
                                                self.yNave+int(DYNAVE*scale)))
                        else:
                            self.pantalla.blit(self.fuego[1],
                                               (int((XNAVE+30)*scale+shift_x),
                                                self.yNave+int(DYNAVE*scale)))
                        self.fuego1 = not self.fuego1
                        pygame.display.flip()
                elif event.type == EVENTOREFRESCO:
                    if self.estadobicho == ESTADONORMAL:
                        if random.randint(1,15) == 1:
                            self.estadobicho = ESTADOPESTANAS
                            self.pantalla.blit(self.bichopestanas,
                                               (int(XBICHO*scale+shift_x),
                                                int(YBICHO*scale+shift_y)))
                        elif random.randint(1,20) == 1:
                            self.estadobicho = ESTADOFRENTE
                            self.pantalla.blit(self.bichofrente,
                                               (int(XBICHO*scale+shift_x),
                                                int(YBICHO*scale+shift_y)))

                    elif self.estadobicho == ESTADOPESTANAS:
                        self.estadobicho = ESTADONORMAL
                        self.pantalla.blit(self.bicho,
                                           (int(XBICHO*scale+shift_x),
                                            int(YBICHO*scale+shift_y)))
                    elif self.estadobicho == ESTADOFRENTE:
                        if random.randint(1,10) == 1:
                            self.estadobicho = ESTADONORMAL
                            self.pantalla.blit(self.bicho,
                                               (int(XBICHO*scale+shift_x),
                                                int(YBICHO*scale+shift_y)))
                    elif self.estadobicho == ESTADODESPEGUE:
                        pass
                    pygame.display.flip()

    def presentacion(self):
        """Presenta una animacion inicial"""
        self.pantalla.fill((0,0,0))

        # cuadro 1: nave llegando
        self.pantalla.blit(self.tierra,(int(200*scale+shift_x),
                                        int(150*scale+shift_y)))
        self.mostrarTexto(_("Press any key to skip"),
                        self.fuente32,
                        (int(600*scale+shift_x),int(800*scale+shift_y)),
                        (255,155,155))
        pygame.display.flip()
        pygame.time.set_timer(EVENTODESPEGUE,TIEMPODESPEGUE)
        if self.sound:
            self.despegue.play()
        self.paso = 0
        terminar = False
        while 1:
            if gtk_present:
                while gtk.events_pending():
                    gtk.main_iteration()

            for event in wait_events():
                if event.type == pygame.KEYDOWN or \
                        event.type == pygame.MOUSEBUTTONDOWN:
                    if self.sound:
                        self.click.play()
                    pygame.time.set_timer(EVENTODESPEGUE,0)
                    return
                elif event.type == EVENTODESPEGUE:
                    self.paso += 1
                    if self.paso == 150:
                        pygame.time.set_timer(EVENTODESPEGUE,0)
                        terminar = True
                    else:
                        pygame.time.set_timer(EVENTODESPEGUE,TIEMPODESPEGUE)
                        self.pantalla.fill((0,0,0),
                                           (int((900-(self.paso-1)*3)*scale+\
                                                    shift_x),
                                            int((150+(self.paso-1)*1)*scale+\
                                                    shift_y),
                                            int(100*scale),int(63*scale)))
                        self.pantalla.blit(self.navellegando,
                                           (int((900-self.paso*3)*scale+\
                                                    shift_x),
                                            int((150+self.paso*1)*scale+\
                                                    shift_y)))
                        pygame.display.flip()
                elif event.type == EVENTOREFRESCO:
                    pygame.display.flip()
            if terminar:
                break
        # cuadro 2: marcianito hablando
        self.pantalla.fill((0,0,0))
        self.pantalla.blit(self.bicho,(int(600*scale+shift_x),
                                       int(450*scale+shift_y)))
        self.pantalla.blit(self.globito,
                           (int(350*scale+shift_x),int(180*scale+shift_y)))
        yLinea = int((180+self.fuente32.get_height()*3)*scale+shift_y)
        lineas = self.listaPresentacion[0].split("\n")
        for l in lineas:
            text = self.fuente32.render(l.strip(), 1, COLORPREGUNTAS)
            textrect = text.get_rect()
            textrect.center = (int(557*scale+shift_x),yLinea)
            self.pantalla.blit(text, textrect)
            yLinea = yLinea + self.fuente32.get_height()+int(10*scale)
        self.mostrarTexto("Press any key to skip",
                          self.fuente32,
                          (int(600*scale+shift_x),int(800*scale+shift_y)),
                          (255,155,155))
        pygame.display.flip()
        terminar = False
        pygame.time.set_timer(EVENTORESPUESTA,4000)
        while 1:
            for event in wait_events():
                if event.type == pygame.KEYDOWN or \
                        event.type == pygame.MOUSEBUTTONDOWN:
                    if self.sound:
                        self.click.play()
                    pygame.time.set_timer(EVENTORESPUESTA,0)
                    return
                elif event.type == EVENTORESPUESTA:
                    pygame.time.set_timer(EVENTORESPUESTA,0)
                    terminar = True
                elif event.type == EVENTOREFRESCO:
                    pygame.display.flip()
            if terminar:
                break
        # cuadro 3: alerta
        self.pantalla.fill((0,0,0))
        self.pantalla.blit(self.alerta,(int(264*scale+shift_x),
                                        int(215*scale+shift_y)))
        self.pantalla.blit(self.alertarojo,(int(459*scale+shift_x),
                                            int(297*scale+shift_y)))
        self.mostrarTexto("Press any key to skip",
                          self.fuente32,
                          (int(600*scale+shift_x),int(800*scale+shift_y)),
                          (255,155,155))
        pygame.display.flip()
        if self.sound:
            self.chirp.play()
        pygame.time.set_timer(EVENTORESPUESTA,500)
        self.paso = 0
        terminar = False
        while 1:
            if gtk_present:
                while gtk.events_pending():
                    gtk.main_iteration()

            for event in wait_events():
                if event.type == pygame.KEYDOWN or \
                        event.type == pygame.MOUSEBUTTONDOWN:
                    if self.sound:
                        self.click.play()
                    pygame.time.set_timer(EVENTORESPUESTA,0)
                    return
                elif event.type == EVENTORESPUESTA:
                    self.paso += 1
                    if self.paso == 10:
                        pygame.time.set_timer(EVENTORESPUESTA,0)
                        terminar = True
                    else:
                        pygame.time.set_timer(EVENTORESPUESTA,500)
                        if self.paso % 2 == 0:
                            self.pantalla.blit(self.alerta,
                                               (int(264*scale+shift_x),
                                                int(215*scale+shift_y)))
                            self.pantalla.blit(self.alertarojo,
                                               (int(459*scale+shift_x),
                                                int(297*scale+shift_y)))
                            if self.sound:
                                self.chirp.play()
                        else:
                            self.pantalla.blit(self.alerta,
                                               (int(264*scale+shift_x),
                                                int(215*scale+shift_y)))
                        pygame.display.flip()
                elif event.type == EVENTOREFRESCO:
                    pygame.display.flip()
            if terminar:
                break
        # cuadro 4: marcianito asustado
        self.pantalla.fill((0,0,0))
        self.pantalla.blit(self.bichotriste,(int(600*scale+shift_x),
                                             int(450*scale+shift_y)))
        self.pantalla.blit(self.globito,(int(350*scale+shift_x),
                                         int(180*scale+shift_y)))
        yLinea = int(180*scale+shift_y)+self.fuente32.get_height()*3
        lineas = self.listaPresentacion[1].split("\n")
        for l in lineas:
            text = self.fuente32.render(l.strip(), 1, COLORPREGUNTAS)
            textrect = text.get_rect()
            textrect.center = (int(557*scale+shift_x),yLinea)
            self.pantalla.blit(text, textrect)
            yLinea = yLinea + self.fuente32.get_height()+int(10*scale)
        self.mostrarTexto("Presiona cualquier tecla para saltear",
                          self.fuente32,
                          (int(600*scale+shift_x),int(800*scale+shift_y)),
                          (255,155,155))
        pygame.display.flip()
        terminar = False
        pygame.time.set_timer(EVENTORESPUESTA,4000)
        while 1:
            if gtk_present:
                while gtk.events_pending():
                    gtk.main_iteration()

            for event in wait_events():
                if event.type == pygame.KEYDOWN or \
                        event.type == pygame.MOUSEBUTTONDOWN:
                    if self.sound:
                        self.click.play()
                    pygame.time.set_timer(EVENTORESPUESTA,0)
                    return
                elif event.type == EVENTORESPUESTA:
                    pygame.time.set_timer(EVENTORESPUESTA,0)
                    terminar = True
                elif event.type == EVENTOREFRESCO:
                    pygame.display.flip()
            if terminar:
                break
        # cuadro 5: explota nave
        self.pantalla.blit(self.tierra,(int(200*scale+shift_x),
                                        int(150*scale+shift_y)))
        self.mostrarTexto("Presiona cualquier tecla para saltear",
                          self.fuente32,
                          (int(600*scale+shift_x),int(800*scale+shift_y)),
                          (255,155,155))
        pygame.display.flip()
        pygame.time.set_timer(EVENTODESPEGUE,TIEMPODESPEGUE)
        if self.sound:
            self.despegue.play()
        self.paso = 0
        terminar = False
        while 1:
            if gtk_present:
                while gtk.events_pending():
                    gtk.main_iteration()

            for event in wait_events():
                if event.type == pygame.KEYDOWN or \
                        event.type == pygame.MOUSEBUTTONDOWN:
                    if self.sound:
                        self.click.play()
                    pygame.time.set_timer(EVENTODESPEGUE,0)
                    return
                elif event.type == EVENTODESPEGUE:
                    self.paso += 1
                    if self.paso == 130:
                        pygame.time.set_timer(EVENTODESPEGUE,0)
                        terminar = True
                    else:
                        pygame.time.set_timer(EVENTODESPEGUE,TIEMPODESPEGUE)
                        self.pantalla.fill((0,0,0),
                                           (int((430-(self.paso-1)*.1)*scale+\
                                                    shift_x),
                                            int((280+(self.paso-1)*.6)*scale+\
                                                    shift_y),
                                            int(30*scale),int(35*scale)))
                        self.pantalla.blit(self.pedazo1,
                                           (int((430-self.paso*.2)*scale+\
                                                    shift_x),
                                            int((290+self.paso*1)*scale+\
                                                    shift_y)))
                        self.pantalla.blit(self.pedazo1,
                                           (int((430+self.paso*.15)*scale+\
                                                    shift_x),
                                            int((290+self.paso*.9)*scale+\
                                                    shift_y)))
                        self.pantalla.blit(self.pedazo2,
                                           (int((430+self.paso*.25)*scale+\
                                                    shift_x),
                                            int((290+self.paso*.75)*scale+\
                                                    shift_y)))
                        self.pantalla.blit(self.pedazo2,
                                           (int((430-self.paso*.15)*scale+\
                                                    shift_x),
                                            int((290+self.paso*.8)*scale+\
                                                    shift_y)))
                        self.pantalla.blit(self.paracaidas,
                                           (int((430-self.paso*.1)*scale+\
                                                    shift_x),
                                            int((280+self.paso*.6)*scale+\
                                                    shift_y)))
                        pygame.display.flip()
                elif event.type == EVENTOREFRESCO:
                    pygame.display.flip()
            if terminar:
                break
        # cuadro 6: marcianito hablando
        self.pantalla.fill((0,0,0))
        self.pantalla.blit(self.bicho,(int(600*scale+shift_x),
                                       int(450*scale+shift_y)))
        self.pantalla.blit(self.globito,(int(350*scale+shift_x),
                                         int(180*scale+shift_y)))
        yLinea = int(180*scale+shift_y)+self.fuente32.get_height()*3
        lineas = self.listaPresentacion[2].split("\n")
        for l in lineas:
            text = self.fuente32.render(l.strip(), 1, COLORPREGUNTAS)
            textrect = text.get_rect()
            textrect.center = (int(557*scale+shift_x),yLinea)
            self.pantalla.blit(text, textrect)
            yLinea = yLinea + self.fuente32.get_height()+int(10*scale)
        self.mostrarTexto(_("Press any key to skip"),
                          self.fuente32,
                          (int(600*scale+shift_x),int(800*scale+shift_y)),
                          (255,155,155))
        pygame.display.flip()
        terminar = False
        pygame.time.set_timer(EVENTORESPUESTA,6000)
        while 1:
            if gtk_present:
                while gtk.events_pending():
                    gtk.main_iteration()
            for event in wait_events():
                if event.type == pygame.KEYDOWN or \
                        event.type == pygame.MOUSEBUTTONDOWN:
                    if self.sound:
                        self.click.play()
                    pygame.time.set_timer(EVENTORESPUESTA,0)
                    return
                elif event.type == EVENTORESPUESTA:
                    pygame.time.set_timer(EVENTORESPUESTA,0)
                    terminar = True
                elif event.type == EVENTOREFRESCO:
                    pygame.display.flip()
            if terminar:
                break
        return

    def principal(self):
        """Este es el loop principal del juego"""
        global scale, shift_x, shift_y
        pygame.time.set_timer(EVENTOREFRESCO,TIEMPOREFRESCO)

        self.loadAll()

        self.loadCommons()

        #self.presentacion()

        self.paginaDir = 0
        while 1:
            self.pantallaDirectorios() # seleccion de mapa
            pygame.mouse.set_cursor((32,32), (1,1), *self.cursor_espera)
            self.directorio = self.listaDirectorios\
                [self.indiceDirectorioActual]
            self.cargarDirectorio()
            pygame.mouse.set_cursor((32,32), (1,1), *self.cursor)
            while 1:
                # pantalla inicial de juego
                self.elegir_directorio = False
                self.pantallaInicial()
                if self.elegir_directorio: # volver a seleccionar mapa
                    break
                # dibujar fondo y panel
                self.pantalla.blit(self.fondo, (shift_x, shift_y))
                self.pantalla.fill(COLORPANEL,
                                (int(XMAPAMAX*scale+shift_x),shift_y,
                                int(DXPANEL*scale),int(900*scale)))
                if self.jugar:
                    self.borrarGlobito()
                    self.pantalla.blit(self.bicho,
                                    (int(XBICHO*scale+shift_x),
                                    int(YBICHO*scale+shift_y)))
                    self.estadobicho = ESTADONORMAL
                    pygame.display.flip()
                    pygame.time.set_timer(EVENTORESPUESTA,0)
                    self.jugarNivel()
                else:
                    if self.bandera:
                        self.pantalla.blit(self.bandera,
                                        (int((XMAPAMAX+47)*scale+shift_x),
                                        int(155*scale+shift_y)))
                    yLinea = int(YTEXTO*scale) + shift_y + \
                                self.fuente9.get_height()
                    for par in self.lista_estadisticas:
                        text1 = self.fuente9.render(par[0], 1, COLORESTADISTICAS1)
                        self.pantalla.blit(text1,
                                ((XMAPAMAX+10)*scale+shift_x, yLinea))
                        text2 = self.fuente9.render(par[1], 1, COLORESTADISTICAS2)
                        self.pantalla.blit(text2,
                                ((XMAPAMAX+135)*scale+shift_x, yLinea))
                        yLinea = yLinea+self.fuente9.get_height()+int(5*scale)

                    pygame.display.flip()
                    self.explorarNombres()


def main():
    juego = ConozcoUy()
    juego.principal()


if __name__ == "__main__":
    main()

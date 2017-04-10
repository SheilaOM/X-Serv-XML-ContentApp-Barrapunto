from django.shortcuts import render
from django.http import HttpResponse
from cms_put.models import Pages
from django.views.decorators.csrf import csrf_exempt
from xml.sax.handler import ContentHandler
from xml.sax import make_parser
import sys
import urllib.request

# Create your views here.


class myContentHandler(ContentHandler):

    def __init__(self):
        self.inItem = False
        self.inContent = False
        self.theContent = ""

    def startElement(self, name, attrs):
        if name == 'item':
            self.inItem = True
        elif self.inItem:
            if name == 'title':
                self.inContent = True
            elif name == 'link':
                self.inContent = True

    def endElement(self, name):
        if name == 'item':
            self.inItem = False
        elif self.inItem:
            if name == 'title':
                self.titulo = self.theContent
                self.inContent = False
                self.theContent = ""
            elif name == 'link':
                global cont_rss
                self.link = self.theContent
                cont_rss += ("\t\t\t<li><a href='" + self.link + "'>" +
                             self.titulo + "</a></li>\n")
                self.inContent = False
                self.theContent = ""

    def characters(self, chars):
        if self.inContent:
            self.theContent = self.theContent + chars


def update(request):
    global cont_rss
    cont_rss = ""
    theParser = make_parser()
    theHandler = myContentHandler()
    theParser.setContentHandler(theHandler)

    xmlFile = urllib.request.urlopen("http://barrapunto.com/index.rss")
    theParser.parse(xmlFile)

    msg = "Contenidos de barrapunto actualizados"
    return HttpResponse(msg)


def barra(request):
    cont_rss = ""
    resp = "Las direcciones disponibles son: "
    lista_pages = Pages.objects.all()
    for page in lista_pages:
        resp += "<br>-/" + page.name + " --> " + page.page
    return HttpResponse(resp)


@csrf_exempt
def process(request, req):
    if request.method == "GET":
        global cont_rss

        try:
            page = Pages.objects.get(name=req)
            resp = ("<html>\n\t<head>\n\t\t<meta http-equiv='Content-Type'" +
                    "content='text/html; charset=utf-8'/>" +
                    "\n\t</head>\n\t<body>\n\t\t<ul>\n\t\t\t<div>" +
                    "La página solicitada es /" + page.name + " -> " +
                    page.page + "<br><br></div>\n\t\t\t<div>\n\t\t\t" +
                    "<h3>Titulares de barrapunto.com:</h3>\n" +
                    cont_rss + "\t\t\t</div>\n\t\t</ul>\n\t</body>\n</html>")
        except Pages.DoesNotExist:
            resp = "La página introducida no está en la base de datos. Créala:"
            resp += "<form action='/" + req + "' method=POST>"
            resp += "Nombre: <input type='text' name='nombre'>"
            resp += "<br>Página: <input type='text' name='page'>"
            resp += "<input type='submit' value='Enviar'></form>"
    elif request.method == "POST":
        nombre = request.POST['nombre']
        page = request.POST['page']
        pagina = Pages(name=nombre, page=page)
        pagina.save()
        resp = "Has creado la página " + nombre
    elif request.method == "PUT":
        try:
            page = Pages.objects.get(name=req)
            resp = "Ya existe una página con ese nombre"
        except Pages.DoesNotExist:
            page = request.body
            pagina = Pages(name=req, page=page)
            pagina.save()
            resp = "Has creado la página " + req
    else:
        resp = "Error. Method not supported."

    return HttpResponse(resp)

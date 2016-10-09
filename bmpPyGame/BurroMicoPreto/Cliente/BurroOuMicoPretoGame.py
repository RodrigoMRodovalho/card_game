import os
import sys
import pygame
import socket
import linecache
from datetime import datetime
import pygame.time
import time
from pygame.locals import *
import eztext
from threading import Thread, BoundedSemaphore

def carrega_imagem(nome, carta):

    if carta == 1:
        caminho = os.path.join("images/cartas_resize/", nome)
    else:
        caminho = os.path.join('images', nome)

    try:
        image = pygame.image.load(caminho)
    except pygame.error, message:
        print 'Nao foi possivel carregar a imagem: ', nome
        raise SystemExit, message
    image = image.convert()

    return image, image.get_rect()

def display(font, sentence):
    """ Displays text at the bottom of the screen, informing the player of what is going on."""

    displayFont = pygame.font.Font.render(font, sentence, 1, (255, 255, 255), (0, 0, 0))
    return displayFont

def soundLoad(name):
    """ Same idea as the imageLoad function. """

    fullName = os.path.join('sounds', name)
    try:
        sound = pygame.mixer.Sound(fullName)
    except pygame.error, message:
        print 'Cannot load sound:', name
        raise SystemExit, message
    return sound

def playClick():
    clickSound = soundLoad("click2.wav")
    clickSound.play()

def playParFormado():
    parSound = soundLoad("par.wav")
    parSound.play()

def playFimJogo():
    fimSound = soundLoad("fim_de_jogo.wav")
    fimSound.play()

def playCampeao():
    campeaoSound = soundLoad("campeao.wav")
    campeaoSound.play()

def cria_campo_texto():
    txtbx.update(events)
    # blit txtbx on the sceen
    txtbx.draw(screen)

#Funcoes conexao servidor

def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print 'EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj)

def envia_mensagem_servidor(mensagem):
    print >> sys.stderr, 'enviando ',mensagem,'  at ',datetime.now().time()
    servidor_sock.sendall(mensagem)

def log_mensagem_recebida(mensagem):
    print >> sys.stderr, 'recebido ', mensagem, '  at ', datetime.now().time()

def escolhe_nome_jogador(nome):
    global nome_jogador
    nome_jogador = nome

def configura_servidor(host,port):
    global host_ip,porta
    host_ip = host
    porta = port

def conecta_servidor():
    global servidor_sock
    try:
        # Create a TCP/IP socket
        servidor_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connect the socket to the port on the server given by the caller
        server_address = (host_ip, porta)
        print >> sys.stderr, 'connecting to %s port %s' % server_address
        servidor_sock.connect(server_address)
        print >> sys.stderr, 'connected'
        return True
    except:
        PrintException()
        return False

def desconecta_servidor():
    servidor_sock.close()

def comeca_jogo():
    global mensagem_status,s_mensagem_status,step

    s_mensagem_status.acquire()
    mensagem_status = 'Tentando entrar no jogo...'
    s_mensagem_status.release()

    mensagem = 'Oi/' + nome_jogador + '/recepcao'
    envia_mensagem_servidor(mensagem)
    while True:
        data = servidor_sock.recv(4096)
        log_mensagem_recebida(data)
        if(data == 'Ok'):
            s_mensagem_status.acquire()
            mensagem_status = 'Entrada no jogo aceita'
            s_mensagem_status.release()
            print 'Estamos no jogo :)'
            return True
        else:
            print 'Nao estamos no jogo :('
            s_mensagem_status.acquire()
            mensagem_status = 'Nao foi possivel entrar no jogo, '+data
            s_mensagem_status.release()
            step = ERRO_AO_ENTRAR_NO_JOGO
            #todo Tratar os tipos de erros Ex. Jogador com mesmo nome
            return False

def recebe_ordem():
    global ordem,recebeu_ordem,s_recebeu_ordem,mensagem_erro,mensagem_status,s_mensagem_status,nome_proximo_jogador
    while True:
        data = servidor_sock.recv(4096)
        log_mensagem_recebida(data)
        if (data == "Comecou"):
            s_mensagem_status.acquire()
            mensagem_status = 'Jogo comecou'
            s_mensagem_status.release()
        if(data == 'Jogador unico'):
            mensagem_erro = 'Nao foi possivel jogar, somente voce esta participando desse jogo'
        if(data == 'Fim_jogo'):
            s_recebeu_ordem.acquire()
            recebeu_ordem = True
            ordem = None
            s_recebeu_ordem.release()
            break
        elif ('Ordem' in data):
            s_recebeu_ordem.acquire()
            recebeu_ordem = True
            ordem = data.split('/')
            del ordem[0]
            print 'Ordem ', ordem
            if (ordem[0] == nome_jogador):
                print 'Eba!! Eu comeco a jogada!'

            jogador_indice = ordem.index(nome_jogador)

            if jogador_indice == len(ordem)-1:
                nome_proximo_jogador = ordem[0]
            else:
                nome_proximo_jogador = ordem[jogador_indice+1]
            s_recebeu_ordem.release()

            if len(ordem) != 2:

                quantidade_outros_jogadores = len(ordem) - 2
                i = 0
                t = len(ordem)
                num_cartas = int(((NUM_CARTAS*2)-1) / t)

                for o in ordem:
                    if o is nome_proximo_jogador:
                        for j in range(ordem.index(o) + 1, t):
                            if ordem[j] != o and ordem[j] != nome_jogador:
                                outros_jogadores.append([ordem[j], num_cartas, None,False])
                                i += 1


                if (quantidade_outros_jogadores != i):
                    for x in range(0, ordem.index(nome_proximo_jogador)):
                        if ordem[x] != nome_jogador and ordem[x] != nome_proximo_jogador:
                            outros_jogadores.append([ordem[x], num_cartas, None,False])


                posicao_inicial_x = 650
                offset_x = 0

                print 'quantidade outros jogadores '+str(len(outros_jogadores))

                for oj in outros_jogadores:
                    oj[2] = (posicao_inicial_x + offset_x,80)
                    offset_x += 100

                    s_outros_jogadores_sprite.acquire()
                    outros_jogadores_sprite.add(carta_outros_jogadores(oj[2]))
                    s_outros_jogadores_sprite.release()

            break

def recebe_cartas(jogador_cartas):
    global cartas,s_recebeu_cartas,recebeu_cartas

    initial_pos = 375
    offset = 65
    fileira = 28
    index = 0
    while True:
        data = servidor_sock.recv(4096)
        log_mensagem_recebida(data)
        if 'mao_carta' in data:
            jogador_cartas.add(cartaSprite(str(int(data[10:len(data)])+1),(initial_pos + offset, abs(fileira - 600))))
            cartas.append(str(int(data[10:len(data)])+1))
            initial_pos += offset
            if index == 9:
                fileira += 80
                initial_pos = 375
            if index == 19:
                fileira += 80
                initial_pos = 375
            if index == 29:
                fileira += 80
                initial_pos = 375
            if index == 39:
                fileira += 80
                initial_pos = 375
            if index == 49:
                fileira += 80
                initial_pos = 375
            index += 1

        elif data == 'Fim_mao':
            s_recebeu_cartas.acquire()
            recebeu_cartas = True
            s_recebeu_cartas.release()
            print cartas

        elif data == 'Pares?':
            break

def verifica_pares():
    global cartas
    if (len(cartas) > 0):
        for c in cartas:
            if cartas.count(c) > 1:
                return True

    return False

#Declaracao da classe do botao para comecar o jogo
class BotaoComecaJogo(pygame.sprite.Sprite):

    #inicilializacao das informacoes do botao
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = carrega_imagem("comecar_jogo.png", 0)
        self.rect.x = 500
        self.rect.y = 450

    #atualiza informacoes do botao e do jogo
    def atualiza(self,posicao_mouse_x,posicao_mouse_y,tela_atual,click):

        #verifica se o botao foi clicado
        if self.rect.collidepoint(posicao_mouse_x, posicao_mouse_y) == 1 and click == 1:

            #emite som de clique
            playClick()
            tela_atual = MOSTRA_TELA_MESA

        return tela_atual
#acaba classe BotaoComecaJogo

#Declaracao da classe do botao para comecar o jogo
class BotaoVoltarTelaInicial(pygame.sprite.Sprite):

    #inicilializacao das informacoes do botao
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = carrega_imagem("voltar_inicio.png", 0)
        self.rect.x = 500
        self.rect.y = 450

    #atualiza informacoes do botao e do jogo
    def atualiza(self,posicao_mouse_x,posicao_mouse_y,tela_atual,click):

        #verifica se o botao foi clicado
        if self.rect.collidepoint(posicao_mouse_x, posicao_mouse_y) == 1 and click == 1:

            #emite som de clique
            playClick()
            tela_atual = MOSTRA_TELA_INICIAL

        return tela_atual
#acaba classe BotaoComecaJogo

#Declaracao da classe de cartas
class cartaSprite(pygame.sprite.Sprite):
    """ Sprite that displays a specific card. """

    def __init__(self, carta, position):
        pygame.sprite.Sprite.__init__(self)
        if carta == '53':
            carta = '1'
        cardImage = carta + ".png"
        self.image, self.rect = carrega_imagem(cardImage, 1)
        self.position = position
        self.id = carta
        self.rect.x = position[0]
        self.rect.y = position[1]
        self.posicao_inicial_x = position[0]
        self.posicao_inicial_y = position[1]

    def retorna_posicao_inicial(self):
        self.rect.x = self.posicao_inicial_x
        self.rect.y = self.posicao_inicial_y

    def atualiza_posicao(self,nova_posicao):
        self.posicao_inicial_x  = nova_posicao[0]
        self.posicao_inicial_y = nova_posicao[1]
        self.rect.x = self.posicao_inicial_x
        self.rect.y = self.posicao_inicial_y

    def update(self, posicao_mouse_x, posicao_mouse_y, click,candidado_pares,selecionar):
        # verifica se o botao foi clicado

        if self.rect.collidepoint(posicao_mouse_x, posicao_mouse_y) == 1 and click == 1:
            # emite som de clique
            playClick()

            if(candidado_pares == None or len(candidado_pares) == 0):

                self.rect.x = 800
                self.rect.y = 150
                candidado_pares = []
                candidado_pares.append(self.id)

            elif (len(candidado_pares)== 1):

                self.rect.x = 880
                self.rect.y = 150
                candidado_pares.append(self.id)

        return candidado_pares

#acaba da classe de cartas

class carta_proximoSprite(pygame.sprite.Sprite):
    """ Sprite that displays a specific card. """

    def __init__(self, carta, position):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = carrega_imagem("virada_deitada_menor.png", 1)
        self.position = position
        self.id = carta
        self.rect.x = position[0]
        self.rect.y = position[1]

    def atualiza_id(self,id):
        self.id = id

    def atualiza_id_posicao(self, id, position):
        self.id = id
        self.rect.x = position[0]
        self.rect.y = position[1]

    def update(self, posicao_mouse_x, posicao_mouse_y, click,vez):
        # verifica se o botao foi clicado

        if self.rect.collidepoint(posicao_mouse_x, posicao_mouse_y) == 1 and click == 1:
            # emite som de clique
            playClick()
            if vez:
                return self.id

class carta_outros_jogadores(pygame.sprite.Sprite):

    def __init__(self,position):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = carrega_imagem("virada_cima.png", 1)
        self.position = position
        self.rect.x = position[0]
        self.rect.y = position[1]

    def pega_posicao(self):
        return self.position



nome_jogador=''
host_ip=''
porta=''
servidor_sock = None
cartas = []
ordem = []
candidado_pares = []

TELA_LARGURA = 1200
TELA_ALTURA = 700

MENSAGEM_JOGO_POSICAO_X=70
MENSAGEM_JOGO_POSICAO_Y=20
MENSAGEM_JOGO_FLUXO_POSICAO_X=750

#nome,quantidade_cartas,posicao_tela,campeao
outros_jogadores = []

pygame.font.init()
pygame.mixer.init()

textFont = pygame.font.Font(None, 28)
screen = pygame.display.set_mode((TELA_LARGURA, TELA_ALTURA))
clock = pygame.time.Clock()

# Constantes
MOSTRA_TELA_INICIAL = 0
MOSTRA_TELA_MESA = 1
CONECTA_SERVIDOR = 2
COMECA_JOGO = 3
AGUARDANDO_COMECO = 4
RECEBE_ORDEM_JOGO = 5
RECEBE_CARTAS = 6
VERIFICA_PARES = 7
MOSTRA_TELA_ERRO = 8

#Constantes fluxo de erros
ERRO_AO_ENTRAR_NO_JOGO = -1

# Variaveis
recebeu_ordem = False
mostra_jogadores_nomes = False
s_recebeu_ordem = BoundedSemaphore()
recebeu_cartas = False
s_recebeu_cartas = BoundedSemaphore()

thread_recebe_ordem_aberta = False
thread_recebe_cartas_aberta = False


mensagem_erro = ''
mensagem_status = None
s_mensagem_status = BoundedSemaphore()
mensagem_fluxo = ''
s_mensagem_fluxo = BoundedSemaphore()

jogador_cartas = pygame.sprite.LayeredUpdates()
s_jogador_cartas = BoundedSemaphore()
jogador_proximo_cartas = pygame.sprite.LayeredUpdates()
s_jogador_proximo_cartas = BoundedSemaphore()
outros_jogadores_sprite = pygame.sprite.LayeredUpdates()
s_outros_jogadores_sprite = BoundedSemaphore()
# Controla o fluxo de telas do jogo
#todo
step = MOSTRA_TELA_INICIAL
#step = MOSTRA_TELA_MESA

terminou_jogo = False
s_terminou_jogo = BoundedSemaphore()

click = 0

# 2 - Initialize the game
pygame.init()

# 3 - Load images
#player = pygame.image.load("/resources/images/dude.png")
plano_de_fundo,plano_de_fundo_Rect = carrega_imagem("table_background.jpg", 0)

botaoComecaJogo = BotaoComecaJogo()
posicao_mouse_x, posicao_mouse_y = 0, 0

txtbx = eztext.Input(x=250,y=350,maxlength=45, color=(0,0,0), prompt='Digite seu nome:  ')

botoes = pygame.sprite.Group(botaoComecaJogo)
# 4 - keep looping through

pygame.display.set_caption('Burro ou Mico Preto')

thread_estabele_conexao_servidor_aberta = False
servidor_conectado = False
s_servidor_contectado = BoundedSemaphore()

def estabelece_conexao_servidor(nome_jogador):
    global s_servidor_contectado,servidor_conectado,mensagem_erro
    escolhe_nome_jogador(nome_jogador)
    configura_servidor('192.168.0.105', 50053)
    if (conecta_servidor()):
        mensagem_erro = None
    else:
        mensagem_erro = 'Nao foi possivel conectar ao servidor'

    s_servidor_contectado.acquire()
    servidor_conectado = True
    s_servidor_contectado.release()

erro_ao_comecar_jogo = False
s_erro_ao_comecar_jogo = BoundedSemaphore()
thread_comecou_jogo_aberta = False
verificar_pares = False
s_verificar_pares = BoundedSemaphore()
par_selecionado = False
s_par_selecionado = BoundedSemaphore()
carta_selecionada = ''
s_carta_selecionada = BoundedSemaphore()

def verifica_envia_par():

    global s_verificar_pares, verificar_pares, s_par_selecionado, par_selecionado, carta_selecionada,\
        s_carta_selecionada,mensagem_status, s_mensagem_status,jogador_cartas,s_jogador_cartas

    if verifica_pares():
        envia_mensagem_servidor('Sim')
        s_mensagem_status.acquire()
        mensagem_status = 'Selecione pares'
        s_mensagem_status.release()
        while True:
            s_par_selecionado.acquire()
            if par_selecionado:
                s_carta_selecionada.acquire()
                envia_mensagem_servidor(str(int(carta_selecionada)-1))
                s_jogador_cartas.acquire()
                atualiza_posicao_baralho_jogador(jogador_cartas)
                s_jogador_cartas.release()
                s_carta_selecionada.release()
                par_selecionado = False
                s_par_selecionado.release()
                break
            else:
                s_par_selecionado.release()
        return True
    else:
        envia_mensagem_servidor('Nao')
        return False

def remove_par_baralho_adversario(nome_adversario):
    global jogador_proximo_cartas

    if nome_adversario != nome_jogador:

        if len(jogador_proximo_cartas) > 1:

            sprites_para_remover = []
            sprites_para_remover.append(jogador_proximo_cartas.get_sprite(0))
            sprites_para_remover.append(jogador_proximo_cartas.get_sprite(1))

            grupo_auxiliar = pygame.sprite.Group(sprites_para_remover[0], sprites_para_remover[1])
            s_jogador_proximo_cartas.acquire()
            jogador_proximo_cartas.remove(grupo_auxiliar)
            s_jogador_proximo_cartas.release()

            atualiza_posicao_baralho_adversario()

def remove_carta_baralho_adversario(carta_adversario_selecionada):

    for i in range(0, len(jogador_proximo_cartas)):
        aux = jogador_proximo_cartas.get_sprite(i)
        if aux.id == carta_adversario_selecionada:
            jogador_proximo_cartas.remove(aux)
            break

    atualiza_posicao_baralho_adversario()


def atualiza_posicao_baralho_jogador(jogador_cartas):

    initial_pos = 375
    offset = 65
    fileira = 28
    index = 0
    for cSprite in jogador_cartas:
        cSprite.atualiza_posicao((initial_pos + offset, abs(fileira-600)))
        initial_pos += offset
        if index == 9:
            fileira += 80
            initial_pos = 375
        if index == 19:
            fileira += 80
            initial_pos = 375
        if index == 29:
            fileira += 80
            initial_pos = 375
        if index == 39:
            fileira += 80
            initial_pos = 375
        if index == 49:
            fileira += 80
            initial_pos = 375
        index += 1

def atualiza_posicao_baralho_adversario():

    initial_pos = 100
    offset = 40
    fileira = 0

    index  = 0
    for cSprite in jogador_proximo_cartas:
        cSprite.atualiza_id_posicao(index,  (fileira + 30, initial_pos + offset))
        initial_pos += offset
        if index == 9:
            fileira += 60
            initial_pos = 100
        if index == 19:
            fileira += 60
            initial_pos = 100
        if index == 29:
            fileira += 60
            initial_pos = 100
        if index == 39:
            fileira += 60
            initial_pos = 100
        if index == 49:
            fileira += 60
            initial_pos = 100
        index += 1


NUM_CARTAS = 53
escolhe_carta_adversario = False
s_escolhe_carta_adversario = BoundedSemaphore()
quantidade_cartas_adversario = 0
s_quantidade_cartas_adversario = BoundedSemaphore()
carta_adversario_escolhida = False
carta_adversario = 0
s_carta_adversario_escolhida = BoundedSemaphore()
nome_proximo_jogador = ''
campeao = False
def comeca_jogar(jogador_cartas):

    global erro_ao_comecar_jogo,s_erro_ao_comecar_jogo,mensagem_status,s_mensagem_status,s_verificar_pares,\
        verificar_pares,s_par_selecionado,par_selecionado,carta_selecionada,s_carta_selecionada,vez,s_vez,\
        s_jogador_cartas,quantidade_cartas_adversario,carta_adversario_escolhida,s_carta_adversario_escolhida,\
        escolhe_carta_adversario,mensagem_fluxo,s_mensagem_fluxo,campeao,s_terminou_jogo,terminou_jogo

    if not comeca_jogo():
        s_erro_ao_comecar_jogo.acquire()
        s_erro_ao_comecar_jogo = True
        s_erro_ao_comecar_jogo.release()
        return

    s_mensagem_status.acquire()
    mensagem_status = 'Aguardando inicio do jogo'
    s_mensagem_status.release()
    recebe_ordem()

    s_mensagem_status.acquire()
    mensagem_status = 'Recebendo cartas'
    s_mensagem_status.release()

    s_jogador_cartas.acquire()
    recebe_cartas(jogador_cartas)
    s_jogador_cartas.release()

    monta_cartas_adversario()

    if(verifica_envia_par()):
        while True:
            data = servidor_sock.recv(4096)
            log_mensagem_recebida(data)
            if data == 'Pares?':
                if not verifica_envia_par():
                    break
            elif 'par/' in data:
                data = data.split('/')
                if len(ordem) == 2:
                    remove_par_baralho_adversario(data[1])

    s_mensagem_status.acquire()
    mensagem_status = 'Esperando todos os jogadores selecionarem seus pares'
    s_mensagem_status.release()

    if (ordem[0] == nome_jogador):
        if conecta_servidor():
            mensagem = 'Oi/' + nome_jogador + '/envio'
            envia_mensagem_servidor(mensagem)

    while True:

        data = servidor_sock.recv(4096)
        log_mensagem_recebida(data)

        if (data == ''):
            print 'error'
            break

        if data == 'cartas_ord':
            cards = ''
            for c in cartas:
                cards += str(int(c)-1) + '/'

            print 'Cartas '+cards
            cards = cards[:len(cards) - 1]
            envia_mensagem_servidor(str(cards))

        if 'quant_cartas' in data:
            data = data.split('/')

            s_quantidade_cartas_adversario.acquire()
            quantidade_cartas_adversario = int(data[1])
            s_quantidade_cartas_adversario.release()
            s_jogador_proximo_cartas.acquire()

            while len(jogador_proximo_cartas) > int (data[1]):
                jogador_proximo_cartas.remove(jogador_proximo_cartas.get_sprite(0))

            while len(jogador_proximo_cartas) < int(data[1]):
                jogador_proximo_cartas.add(carta_proximoSprite(0, (0, 0)))

            atualiza_posicao_baralho_adversario()

            s_jogador_proximo_cartas.release()
            s_escolhe_carta_adversario.acquire()
            escolhe_carta_adversario = True
            s_escolhe_carta_adversario.release()
            s_vez.acquire()
            vez = True
            s_vez.release()

            s_mensagem_status.acquire()
            mensagem_status = 'Sua Vez! Escolha uma carta do seu adversario a esquerda'
            s_mensagem_status.release()

            while True:

                s_carta_adversario_escolhida.acquire()
                if(carta_adversario_escolhida):
                    s_carta_adversario_escolhida.release()
                    break
                s_carta_adversario_escolhida.release()

            carta_adversario_escolhida = False
            remove_carta_baralho_adversario(carta_adversario)
            envia_mensagem_servidor(str(carta_adversario))

        if data == 'Pares?':
            verifica_envia_par()

        if 'par' in data:
            data = data.split('/')

            if data[1] == nome_proximo_jogador:
                 remove_par_baralho_adversario(data[1])

            if(data[1] != nome_jogador):
                s_mensagem_fluxo.acquire()
                mensagem_fluxo = 'Jogador '+ str(data[1]) + '  fez par com a carta ' +str(data[2])
                s_mensagem_fluxo.release()

            for o in outros_jogadores:
                if o[0] == data[1]:
                    o[1]-=2
                    break

            playParFormado()

        if 'vez' in data:
            data = data.split('/')
            if data[1] == nome_jogador:
                s_mensagem_status.acquire()
                mensagem_status = 'Sua Vez! Escolha uma carta do seu adversario a esquerda'
                s_mensagem_status.release()
                s_mensagem_fluxo.acquire()
                mensagem_fluxo = ''
                s_mensagem_fluxo.release()
            else:

                if not campeao:
                    s_vez.acquire()
                    vez = True
                    s_vez.release()
                    s_mensagem_status.acquire()
                    mensagem_status = 'Esperando jogada'
                    s_mensagem_status.release()
                    s_mensagem_fluxo.acquire()
                    mensagem_fluxo = 'Jogador ' + str(data[1]) + ' jogando'
                    s_mensagem_fluxo.release()


        if 'carta_escolhida' in data:
            data = data.split('/')
            for c in cartas:
                if (c == str(int(data[1])+1)):
                    cartas.remove(c)
                    break

            s_jogador_cartas.acquire()
            for i in range(0, len(jogador_cartas)):
                aux = jogador_cartas.get_sprite(i)
                if (aux.id == str(int(data[1])+1)):
                    jogador_cartas.remove(aux)
                    break

            atualiza_posicao_baralho_jogador(jogador_cartas)
            s_jogador_cartas.release()

            if len(ordem) == 2:
                s_jogador_proximo_cartas.acquire()

                jogador_proximo_cartas.add(carta_proximoSprite(0, (0, 0)))

                for i in range(0, len(jogador_proximo_cartas)):
                    aux = jogador_proximo_cartas.get_sprite(i)
                    aux.atualiza_id(i)

                atualiza_posicao_baralho_adversario()
                s_jogador_proximo_cartas.release()

        if 'escolha' in data:
            data = data.split('/')
            cartas.append(str(int(data[1])+1))
            s_jogador_cartas.acquire()
            jogador_cartas.add(cartaSprite(str(int(data[1]) + 1), (0, 0)))
            atualiza_posicao_baralho_jogador(jogador_cartas)
            s_jogador_cartas.release()

        if 'campeao' in data:
            data = data.split('/')
            if data[1] == nome_jogador:
                print 'Ganhei!!!!'
                playCampeao()
                s_mensagem_status.acquire()
                mensagem_status = 'Parabens voce ganhou!'
                s_mensagem_status.release()
                campeao = True
            else:
                s_mensagem_fluxo.acquire()
                mensagem_fluxo = 'Jogador ' + str(data[1]) + ' campeao!!'
                s_mensagem_fluxo.release()

                for o in outros_jogadores:
                    if o[0] == data[1]:
                        o[3] = True
                        break

        if 'Burro' in data:
            data = data.split('/')
            if data[1] == nome_jogador:
                print 'Perdi!!!!'
                playFimJogo()
                s_mensagem_status.acquire()
                mensagem_status = 'Que pena, voce perdeu :('
                s_mensagem_status.release()
            else:
                s_mensagem_fluxo.acquire()
                mensagem_fluxo = 'Jogador ' + str(data[1]) + ' e o burro'
                s_mensagem_fluxo.release()


        if data == 'Fim_jogo':
            print 'O jogo acabou'
            s_mensagem_fluxo.acquire()
            mensagem_fluxo = 'O jogo acabou'
            s_mensagem_fluxo.release()
            s_terminou_jogo.acquire()
            terminou_jogo = True
            s_terminou_jogo.release()
            break

monta_adversario_carta = False
s_monta_adversario_carta = BoundedSemaphore()
vez = False
s_vez = BoundedSemaphore()
botao_voltar_inicio = BotaoVoltarTelaInicial()

def monta_cartas_adversario():
    global ordem,monta_adversario_carta,s_monta_adversario_carta,jogador_proximo_cartas

    quantidade_cartas = int(((NUM_CARTAS*2)-1)/len(ordem))

    if(ordem[0] == nome_proximo_jogador):
        quantidade_cartas += 1
    else:
        for o in outros_jogadores:
            if o[0] == ordem[0]:
                o[1] += 1
                break

    initial_pos = 100
    offset = 40
    fileira = 0
    s_jogador_proximo_cartas.acquire()
    for x in range(0, quantidade_cartas):
        jogador_proximo_cartas.add(carta_proximoSprite(str(x + 1), (fileira + 30, initial_pos + offset)))
        initial_pos += offset
        if x == 9:
            fileira += 60
            initial_pos = 100
        if x == 19:
            fileira += 60
            initial_pos = 100
        if x == 29:
            fileira += 60
            initial_pos = 100
        if x == 39:
            fileira += 60
            initial_pos = 100
        if x == 49:
            fileira += 60
            initial_pos = 100

    s_jogador_proximo_cartas.release()


try:
    while 1:
        # make sure the program is running at 30 fps
        clock.tick(30)
        # 5 - clear the screen before drawing it again
        screen.fill(0)
        # 6 - draw the screen elements
        screen.blit(plano_de_fundo,plano_de_fundo_Rect)
        # 7 - update the screen

        events = pygame.event.get()

        for event in events:
            if event.type == QUIT:
                sys.exit()
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    posicao_mouse_x,posicao_mouse_y = pygame.mouse.get_pos()
                    click = 1
            elif event.type == MOUSEBUTTONUP:
                posicao_mouse_x, posicao_mouse_y = 0, 0
                click = 0

        if(step == MOSTRA_TELA_INICIAL):
            #todo resetar tudo
            displayFont = display(pygame.font.Font(None, 60), 'Bem vindo ao jogo Burro ou Mico Preto')
            screen.blit(displayFont, (200, 50))
            txtbx.update(events)
            txtbx.draw(screen)
            
            if len(botoes) == 0:
                botoes.add(botaoComecaJogo)

            step = botaoComecaJogo.atualiza(posicao_mouse_x, posicao_mouse_y, step, click)
            botoes.draw(screen)
            
        elif step != MOSTRA_TELA_ERRO:
            screen.fill(pygame.Color("black"), (MENSAGEM_JOGO_POSICAO_X+10, MENSAGEM_JOGO_POSICAO_Y, 1060, 40))

        if(step == MOSTRA_TELA_MESA):
            botoes.remove(botaoComecaJogo)
            step = CONECTA_SERVIDOR

        if(step == CONECTA_SERVIDOR):

            displayFont = display(textFont, "Conectando servidor...")
            screen.blit(displayFont, (MENSAGEM_JOGO_POSICAO_X + 10, MENSAGEM_JOGO_POSICAO_Y + 5))
            pygame.display.flip()

            if not thread_estabele_conexao_servidor_aberta:
                t = Thread(target=estabelece_conexao_servidor, args=(txtbx.value,))
                t.start()
                thread_estabele_conexao_servidor_aberta = True

            s_servidor_contectado.acquire()
            if servidor_conectado:
                if mensagem_erro is None:
                    displayFont = display(textFont, "Servidor Conectado")
                    screen.blit(displayFont, (MENSAGEM_JOGO_POSICAO_X + 10, MENSAGEM_JOGO_POSICAO_Y + 5))
                    step = COMECA_JOGO
                else:
                    desconecta_servidor()
                    botoes.remove(botaoComecaJogo)
                    botoes.add(botao_voltar_inicio)
                    step = MOSTRA_TELA_ERRO
            s_servidor_contectado.release()

        if (step == MOSTRA_TELA_ERRO):

            displayFont = display(pygame.font.Font(None, 30), mensagem_erro)
            screen.blit(displayFont, (300, 300))

            step = botao_voltar_inicio.atualiza(posicao_mouse_x, posicao_mouse_y, step, click)
            if(step == MOSTRA_TELA_INICIAL):
                botoes.remove(botao_voltar_inicio)

            botoes.draw(screen)


        if (step == ERRO_AO_ENTRAR_NO_JOGO):
            displayFont = display(textFont, "Nao foi possivel entrar no jogo, tente novamente outra hora")
            screen.blit(displayFont, (MENSAGEM_JOGO_POSICAO_X + 10, MENSAGEM_JOGO_POSICAO_Y + 5))

        if(step == COMECA_JOGO):

            displayFont = display(pygame.font.Font(None, 35), str(nome_jogador))
            screen.blit(displayFont, (750, 670))

            if mostra_jogadores_nomes:
                displayFont = display(pygame.font.Font(None, 35), nome_proximo_jogador)
                screen.blit(displayFont, (40, 670))

                s_outros_jogadores_sprite.acquire()
                if len(outros_jogadores_sprite) is not 0:
                    outros_jogadores_sprite.update()
                    outros_jogadores_sprite.draw(screen)
                s_outros_jogadores_sprite.release()

                for o in outros_jogadores:
                    displayFont = display(pygame.font.Font(None, 18), '  '+o[0]+'  ')
                    screen.blit(displayFont, (o[2][0], o[2][1]+70))

                    if o[3] :
                        displayFont = display(pygame.font.Font(None, 15), 'campeao')
                    else:
                        displayFont = display(pygame.font.Font(None, 15), '  ' + str(o[1]) + '  cartas')
                    screen.blit(displayFont, (o[2][0], o[2][1] + 85))

                s_terminou_jogo.acquire()
                if terminou_jogo:
                    step = MOSTRA_TELA_INICIAL
                s_terminou_jogo.release()

            if not thread_comecou_jogo_aberta:
                t = Thread(target=comeca_jogar, args=(jogador_cartas,))
                t.start()
                thread_comecou_jogo_aberta = True
            else:
                s_mensagem_status.acquire()
                displayFont = display(textFont, mensagem_status)
                screen.blit(displayFont, (MENSAGEM_JOGO_POSICAO_X + 10, MENSAGEM_JOGO_POSICAO_Y + 5))
                s_mensagem_status.release()

                s_mensagem_fluxo.acquire()
                displayFont = display(textFont, mensagem_fluxo)
                screen.blit(displayFont, (MENSAGEM_JOGO_FLUXO_POSICAO_X + 10, MENSAGEM_JOGO_POSICAO_Y + 5))
                s_mensagem_fluxo.release()


                s_erro_ao_comecar_jogo.acquire()
                if erro_ao_comecar_jogo :
                    step = MOSTRA_TELA_ERRO
                    mensagem_erro = mensagem_status
                s_erro_ao_comecar_jogo.release()

                s_recebeu_ordem.acquire()
                if recebeu_ordem:
                    if (ordem == None):
                        step = MOSTRA_TELA_ERRO
                        mensagem_erro = "Erro ao receber ordem dos jogadores"
                    else:
                        displayFont = display(textFont, 'Ordem dos jogadores recebida')
                        screen.blit(displayFont, (MENSAGEM_JOGO_POSICAO_X + 10, MENSAGEM_JOGO_POSICAO_Y + 5))
                        recebeu_ordem = False
                        mostra_jogadores_nomes = True
                s_recebeu_ordem.release()

                s_recebeu_cartas.acquire()
                if (recebeu_cartas):
                    displayFont = display(textFont, 'Cartas Recebidas')
                    screen.blit(displayFont, (MENSAGEM_JOGO_POSICAO_X + 10, MENSAGEM_JOGO_POSICAO_Y + 5))
                    recebeu_cartas = False
                s_recebeu_cartas.release()

                if len(jogador_cartas) is not 0:
                    for i in range(0, len(jogador_cartas)):
                        aux = jogador_cartas.get_sprite(i)
                        candidado_pares = aux.update(posicao_mouse_x, posicao_mouse_y, click, candidado_pares, True)

                    jogador_cartas.draw(screen)
                    pygame.display.flip()

                if candidado_pares != None and len(candidado_pares) == 2:
                    pygame.time.delay(300)
                    if (candidado_pares[0] != candidado_pares[1]):
                        for i in range(0, len(jogador_cartas)):
                            aux = jogador_cartas.get_sprite(i)
                            aux.retorna_posicao_inicial()
                    else:

                        sprites_para_remover = []

                        for i in range(0, len(jogador_cartas)):
                            aux = jogador_cartas.get_sprite(i)
                            if (aux.id == candidado_pares[0]):
                                sprites_para_remover.append(aux)
                                if len(sprites_para_remover) == 2:
                                    break

                        grupo_auxiliar = pygame.sprite.Group(sprites_para_remover[0], sprites_para_remover[1])
                        jogador_cartas.remove(grupo_auxiliar)

                        if candidado_pares[0] in cartas:
                            cartas.remove(candidado_pares[0])
                        if candidado_pares[0] in cartas:
                            cartas.remove(candidado_pares[1])

                        playParFormado()

                        s_par_selecionado.acquire()
                        par_selecionado = True
                        s_carta_selecionada.acquire()
                        carta_selecionada = candidado_pares[0]
                        s_carta_selecionada.release()
                        s_par_selecionado.release()

                        atualiza_posicao_baralho_jogador(jogador_cartas)

                    candidado_pares = []
                    jogador_cartas.draw(screen)
                    pygame.display.flip()

                if len(jogador_proximo_cartas) is not 0:

                    s_escolhe_carta_adversario.acquire()
                    if escolhe_carta_adversario:
                        s_jogador_proximo_cartas.acquire()
                        for i in range(0, len(jogador_proximo_cartas)):
                            aux = jogador_proximo_cartas.get_sprite(i)
                            id  = aux.update(posicao_mouse_x, posicao_mouse_y, click, vez)
                            if id is not None:
                                s_carta_adversario_escolhida.acquire()
                                carta_adversario = id
                                carta_adversario_escolhida = True
                                escolhe_carta_adversario = False
                                s_carta_adversario_escolhida.release()
                        s_jogador_proximo_cartas.release()
                    else:
                        jogador_proximo_cartas.update(posicao_mouse_x, posicao_mouse_y, click, vez)
                    s_escolhe_carta_adversario.release()
                    jogador_proximo_cartas.draw(screen)

        pygame.display.flip()

except:
    PrintException()
finally:
    desconecta_servidor()


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

#Funcao que carrega imagem do sistema de arquivos
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

#Funcao que carrega sons do sistema de arquivos
def carrega_som(nome):

    caminho = os.path.join('sounds', nome)
    try:
        sound = pygame.mixer.Sound(caminho)
    except pygame.error, message:
        print 'Nao foi possivel carregar:', nome
        raise SystemExit, message
    return sound

#Funcao que toca o som de click
def toca_som_click():
    som_click = carrega_som("click2.wav")
    som_click.play()

#Funcao que toca o som de par formado
def toca_som_par_formado():
    som_par = carrega_som("par.wav")
    som_par.play()

#Funcao que toca o som de final de jogo
def toca_som_final_jogo():
    som_final_jogo = carrega_som("fim_de_jogo.wav")
    som_final_jogo.play()

#Funcao que toca o som de campeao
def toca_som_campeao():
    som_campeao = carrega_som("campeao.wav")
    som_campeao.play()

def cria_campo_texto():
    txtbx.update(events)
    txtbx.draw(screen)

###Solucao da internet para ver todas as informacoes sobre o erro dentro do except:
def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print 'EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj)

#Funcao que envia mensagem para o servidor
def envia_mensagem_servidor(mensagem):
    print >> sys.stderr, 'enviando ',mensagem,'  as ',datetime.now().time()
    servidor_sock.sendall(mensagem)

#Imprime as mensagens recebidas
def log_mensagem_recebida(mensagem):
    print >> sys.stderr, 'recebido ', mensagem, '  at ', datetime.now().time()

#Funcao que guarda na variavel o nome do jogador
def escolhe_nome_jogador(nome):
    global nome_jogador
    nome_jogador = nome
#Funcao que guarda nas variaveis o IP e Porta do servidor
def configura_servidor(host,port):
    global host_ip,porta
    host_ip = host
    porta = port

#Funcao que conecta socket do servidor
def conecta_servidor():
    global servidor_sock
    try:
        # Cria socket para conexao
        servidor_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Configura endereco - IP e Porta
        endereco_servidor = (host_ip, porta)
        print >> sys.stderr, 'Conectando em %s port %s' % endereco_servidor
        servidor_sock.connect(endereco_servidor)
        print >> sys.stderr, 'Conectado'
        return True
    except:
        PrintException()
        return False

#Funcao que desconecta socket do servidor
def desconecta_servidor():
    servidor_sock.close()

#Funcao que manda mensagem pro servidor para tentar entrar no jogo
def comeca_jogo():
    global mensagem_status,s_mensagem_status,step

    #Configura mensagem de status
    s_mensagem_status.acquire()
    mensagem_status = 'Tentando entrar no jogo...'
    s_mensagem_status.release()

    #Envia mensagem para entrar no jogo para o servidor
    mensagem = 'Oi/' + nome_jogador + '/recepcao'
    envia_mensagem_servidor(mensagem)
    while True:
        #Pega resposta
        data = servidor_sock.recv(4096)
        #Imprime mensagem recebida no console
        log_mensagem_recebida(data)
        if(data == 'Ok'):
            #Servidor permitiu entrada no jogo
            # Configura mensagem de status
            s_mensagem_status.acquire()
            mensagem_status = 'Entrada no jogo aceita'
            s_mensagem_status.release()
            print 'Estamos no jogo :)'
            return True
        else:
            #Servidor nao permitiu a entrada no jogo
            print 'Nao estamos no jogo :('
            # Configura mensagem de status
            s_mensagem_status.acquire()
            mensagem_status = 'Nao foi possivel entrar no jogo, '+data
            s_mensagem_status.release()
            #Atualiza passo  para ERRO_AO_ENTRAR_NO_JOGO
            step = ERRO_AO_ENTRAR_NO_JOGO
            return False

#Funcao que recebe a ordem dos jogadores do servidor
def recebe_ordem():
    global ordem,recebeu_ordem,s_recebeu_ordem,mensagem_erro,mensagem_status,s_mensagem_status,nome_proximo_jogador
    while True:
        #recebe os dados
        data = servidor_sock.recv(4096)
        log_mensagem_recebida(data)
        if (data == "Comecou"):
            # Configura mensagem de status
            s_mensagem_status.acquire()
            mensagem_status = 'Jogo comecou'
            s_mensagem_status.release()
        if(data == 'Jogador unico'):
            #Recebido que so possui um jogador no jogo, entao o jogo nao vai comecar
            mensagem_erro = 'Nao foi possivel jogar, somente voce esta participando desse jogo'
        if(data == 'Fim_jogo'):
            # Fim de jogo, sem ter comecado de fato
            s_recebeu_ordem.acquire()
            #Configura que recebeu ordem, mas configura que nao recebeu a ordem
            recebeu_ordem = True
            ordem = None
            s_recebeu_ordem.release()
            break
        elif ('Ordem' in data):
            #Recebeu a ordem dos jogadores
            s_recebeu_ordem.acquire()
            recebeu_ordem = True
            ordem = data.split('/')
            del ordem[0]
            print 'Ordem ', ordem
            if (ordem[0] == nome_jogador):
                print 'Eba!! Eu comeco a jogada!'

            #pega o indice do jogador
            jogador_indice = ordem.index(nome_jogador)

            #pega o indice do proximo jogador
            if jogador_indice == len(ordem)-1:
                nome_proximo_jogador = ordem[0]
            else:
                nome_proximo_jogador = ordem[jogador_indice+1]
            s_recebeu_ordem.release()

            #Se tiverem mais de 2 jogadores, configura a variavel outros_jogadores com as informacoes
            # [nome,quantidade_cartas,(posicao_x,posicao_y),campeao]
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

                #Adiciona outros_jogadores no sprite de outros jogadores, para serem mostrados na tela
                for oj in outros_jogadores:
                    oj[2] = (posicao_inicial_x + offset_x,80)
                    offset_x += 100

                    s_outros_jogadores_sprite.acquire()
                    outros_jogadores_sprite.add(carta_outros_jogadores(oj[2]))
                    s_outros_jogadores_sprite.release()

            break

#Funcao que recebe as cartas do jogador
def recebe_cartas(jogador_cartas):
    global cartas,s_recebeu_cartas,recebeu_cartas

    inicial_pos = 375
    deslocamento = 65
    fileira = 28
    index = 0
    #Recebe as cartas do servidor e adiciona na lista de sprite as cartas e na lista de cartas com as posicoes na tela
    while True:
        data = servidor_sock.recv(4096)
        log_mensagem_recebida(data)
        if 'mao_carta' in data:
            jogador_cartas.add(cartaSprite(str(int(data[10:len(data)])+1),(inicial_pos + deslocamento, abs(fileira - 600))))
            cartas.append(str(int(data[10:len(data)])+1))
            inicial_pos += deslocamento
            if index == 9:
                fileira += 80
                inicial_pos = 375
            if index == 19:
                fileira += 80
                inicial_pos = 375
            if index == 29:
                fileira += 80
                inicial_pos = 375
            if index == 39:
                fileira += 80
                inicial_pos = 375
            if index == 49:
                fileira += 80
                inicial_pos = 375
            index += 1

        elif data == 'Fim_mao':
            s_recebeu_cartas.acquire()
            recebeu_cartas = True
            s_recebeu_cartas.release()
            print cartas

        elif data == 'Pares?':
            break

#Funcao que verifica na lista de cartas, se o jogador tem algum par
def verifica_pares():
    global cartas
    if (len(cartas) > 0):
        for c in cartas:
            if cartas.count(c) > 1:
                return True

    return False

# Funcao que realiza comunicacao com servidor
def estabelece_conexao_servidor(nome_jogador):
    global s_servidor_contectado,servidor_conectado,mensagem_erro
    # Configura o nome do jogador (digitado no campo de texto)
    escolhe_nome_jogador(nome_jogador)
    #Configura IP e Porta do Servidor
    configura_servidor('192.168.0.105', 50053)
    #Verifica se conectar com o servidor
    if (conecta_servidor()):
        mensagem_erro = None
    else:
        mensagem_erro = 'Nao foi possivel conectar ao servidor'

    #Libera a variavel que controla se conectou o servidor ou se deu erro
    s_servidor_contectado.acquire()
    servidor_conectado = True
    s_servidor_contectado.release()

#Funcao que verifica se tem pares a serem formados
def verifica_envia_par():

    global s_verificar_pares, verificar_pares, s_par_selecionado, par_selecionado, carta_selecionada,\
        s_carta_selecionada,mensagem_status, s_mensagem_status,jogador_cartas,s_jogador_cartas

    #Verifica se tem pares de cartas
    if verifica_pares():
        #envia mensagem pro servidor
        envia_mensagem_servidor('Sim')
        # Configura mensagem de status
        s_mensagem_status.acquire()
        mensagem_status = 'Selecione pares'
        s_mensagem_status.release()
        while True:
            #Verifica se o par foi selecionado na tela
            s_par_selecionado.acquire()
            if par_selecionado:
                s_carta_selecionada.acquire()
                #Com o par selecionado envia pro servdor
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
        #Envia pro servidor que nao tem mais pares
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

#Funcao que remove carta do baralho do proximo jogador
def remove_carta_baralho_adversario(carta_adversario_selecionada):

    for i in range(0, len(jogador_proximo_cartas)):
        aux = jogador_proximo_cartas.get_sprite(i)
        if aux.id == carta_adversario_selecionada:
            jogador_proximo_cartas.remove(aux)
            break

    #Atualiza posicao das cartas do proximo jogador na tela
    atualiza_posicao_baralho_adversario()

#Funcao que atualiza a posicao das cartas do jogador
def atualiza_posicao_baralho_jogador(jogador_cartas):

    #Atualiza posicao na tela das cartas
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

#Funcao que atualiza a posicao das cartas do jogador proximo jogador
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

#Funcao que roda em uma thread separada, que realiza toda interacao com servidor e seta variaveis de controle
#para atualizacao da tela
def comeca_jogar(jogador_cartas):

    global erro_ao_comecar_jogo,s_erro_ao_comecar_jogo,mensagem_status,s_mensagem_status,s_verificar_pares,\
        verificar_pares,s_par_selecionado,par_selecionado,carta_selecionada,s_carta_selecionada,vez,s_vez,\
        s_jogador_cartas,quantidade_cartas_adversario,carta_adversario_escolhida,s_carta_adversario_escolhida,\
        escolhe_carta_adversario,mensagem_fluxo,s_mensagem_fluxo,campeao,s_terminou_jogo,terminou_jogo

    #Verifica se o servidor permitiu a entrada no jogo
    if not comeca_jogo():
        s_erro_ao_comecar_jogo.acquire()
        #Marca a variavel de controle que deu erro para entrar no jogo
        s_erro_ao_comecar_jogo = True
        s_erro_ao_comecar_jogo.release()
        return

    # Configura mensagem de status
    s_mensagem_status.acquire()
    mensagem_status = 'Aguardando inicio do jogo'
    s_mensagem_status.release()

    # Recebe a ordem dos jogadores
    recebe_ordem()

    # Configura mensagem de status
    s_mensagem_status.acquire()
    mensagem_status = 'Recebendo cartas'
    s_mensagem_status.release()

    #Recebe cartas
    s_jogador_cartas.acquire()
    recebe_cartas(jogador_cartas)
    s_jogador_cartas.release()

    #Funcao que monta na tela as cartas do proximo jogador
    monta_cartas_adversario()

    #Verifica se tem pares a serem formados
    if(verifica_envia_par()):
        while True:
            #Caso ainda tenha mais pares continua verificando os pares
            data = servidor_sock.recv(4096)
            log_mensagem_recebida(data)
            if data == 'Pares?':
                if not verifica_envia_par():
                    break
            elif 'par/' in data:
                data = data.split('/')
                if len(ordem) == 2:
                    #Se tiverem so dois jogadorem, se o proximo jogador fez um par, atualiza tela retirando 2 cartas
                    #do proximo jogador
                    remove_par_baralho_adversario(data[1])

    # Configura mensagem de status
    s_mensagem_status.acquire()
    mensagem_status = 'Esperando todos os jogadores selecionarem seus pares'
    s_mensagem_status.release()

    #Verifica se jogador e o primeiro na ordem e manda mensagem pro servidor para comecar
    # a escolher cartas do proximo jogador
    if (ordem[0] == nome_jogador):
        if conecta_servidor():
            mensagem = 'Oi/' + nome_jogador + '/envio'
            envia_mensagem_servidor(mensagem)

    while True:
        #Recebe dados do servidor
        data = servidor_sock.recv(4096)
        log_mensagem_recebida(data)

        #Deu algum erro no recebimento dos dados
        if (data == ''):
            print 'error'
            step = MOSTRA_TELA_ERRO
            break

        #Recebe mensagem para enviar a ordem das cartas
        if data == 'cartas_ord':
            cards = ''
            for c in cartas:
                cards += str(int(c)-1) + '/'

            print 'Cartas '+cards
            cards = cards[:len(cards) - 1]
            envia_mensagem_servidor(str(cards))

        #Recebe mensagem para escolher uma carta no baralho do proximo jogador
        if 'quant_cartas' in data:
            data = data.split('/')

            #Recebe a quantidade de cartas que o proximo jogador tem
            s_quantidade_cartas_adversario.acquire()
            quantidade_cartas_adversario = int(data[1])
            s_quantidade_cartas_adversario.release()
            s_jogador_proximo_cartas.acquire()

            # Remove cartas caso tenha mais cartas que o proximo jogador realmente possui
            while len(jogador_proximo_cartas) > int (data[1]):
                jogador_proximo_cartas.remove(jogador_proximo_cartas.get_sprite(0))

            # Adiciona cartas caso tenha menos cartas que o proximo jogador realmente possui
            while len(jogador_proximo_cartas) < int(data[1]):
                jogador_proximo_cartas.add(carta_proximoSprite(0, (0, 0)))

            #Atualiza posicao na tela do baralho do jogar adversario
            atualiza_posicao_baralho_adversario()

            #Atualiza variaveis de controle, para avisar o jogador que tem escolher uma carta do proximo jogador
            s_jogador_proximo_cartas.release()
            s_escolhe_carta_adversario.acquire()
            escolhe_carta_adversario = True
            s_escolhe_carta_adversario.release()
            s_vez.acquire()
            vez = True
            s_vez.release()

            # Configura mensagem de status
            s_mensagem_status.acquire()
            mensagem_status = 'Sua Vez! Escolha uma carta do seu adversario a esquerda'
            s_mensagem_status.release()

            while True:
                #Verifica se o jogador escolheu uma carta do adversario
                s_carta_adversario_escolhida.acquire()
                if(carta_adversario_escolhida):
                    s_carta_adversario_escolhida.release()
                    break
                s_carta_adversario_escolhida.release()

            carta_adversario_escolhida = False

            #Remove carta do proximo jogador da tela
            remove_carta_baralho_adversario(carta_adversario)
            #Envia mensagem pro servidor com a carta selecionada
            envia_mensagem_servidor(str(carta_adversario))

        # Recebe mensagem para verificar se o jogador possui algum par
        if data == 'Pares?':
            # Verifica se tem pares a serem formados
            verifica_envia_par()

        # Recebe mensagem qua algum jogador fez um par
        if 'par' in data:
            data = data.split('/')

            #Verifica se o proximo jogador fez algum par e remove o par da tela
            if data[1] == nome_proximo_jogador:
                 remove_par_baralho_adversario(data[1])

            # Verifica se o jogador que fez par nao e o jogador principal, mostra mensagem de fluxo na tela
            if(data[1] != nome_jogador):
                # Configura mensagem de fluxo
                s_mensagem_fluxo.acquire()
                mensagem_fluxo = 'Jogador '+ str(data[1]) + '  fez par com a carta ' +str(data[2])
                s_mensagem_fluxo.release()

            #Se o par foi feito por algum jogador dos "outros jogadores" diminui a quantidade de cartas da lista
            for o in outros_jogadores:
                if o[0] == data[1]:
                    o[1]-=2
                    break

            #Emite som de par formado
            toca_som_par_formado()

        # Recebe mensagem contendo o nome do jogador da vez
        if 'vez' in data:
            data = data.split('/')

            #Se for a vez do jogador principal, mostra mensagem de status
            if data[1] == nome_jogador:
                # Configura mensagem de status
                s_mensagem_status.acquire()
                mensagem_status = 'Sua Vez! Escolha uma carta do seu adversario a esquerda'
                s_mensagem_status.release()
                # Limpa mensagem de fluxo
                s_mensagem_fluxo.acquire()
                mensagem_fluxo = ''
                s_mensagem_fluxo.release()
            else:

                #Verifica se o jogador ja foi campeao para nao receber mensagens de escolha de cartas
                if not campeao:
                    #Configura variavel de controle de vez
                    s_vez.acquire()
                    vez = True
                    s_vez.release()
                    # Configura mensagem de status
                    s_mensagem_status.acquire()
                    mensagem_status = 'Esperando jogada'
                    s_mensagem_status.release()
                    # Configura mensagem de fluxo
                    s_mensagem_fluxo.acquire()
                    mensagem_fluxo = 'Jogador ' + str(data[1]) + ' jogando'
                    s_mensagem_fluxo.release()

        # Recebe mensagem contendo a carta que algum jogador escolheu do baralho do jogador principal
        if 'carta_escolhida' in data:
            data = data.split('/')
            #Remove a carta escolhida da lista de cartas
            for c in cartas:
                if (c == str(int(data[1])+1)):
                    cartas.remove(c)
                    break

            #Remove cartas do grupo de sprites
            s_jogador_cartas.acquire()
            for i in range(0, len(jogador_cartas)):
                aux = jogador_cartas.get_sprite(i)
                if (aux.id == str(int(data[1])+1)):
                    jogador_cartas.remove(aux)
                    break

            #Atualiza posicao das cartas na tela
            atualiza_posicao_baralho_jogador(jogador_cartas)
            s_jogador_cartas.release()

            #Se so existirem dois jogadores, adiciona na tela uma carta no baralho do proximo jogador.
            if len(ordem) == 2:
                s_jogador_proximo_cartas.acquire()

                #Adiciona carta no grupo de cartas do proximo jogador
                jogador_proximo_cartas.add(carta_proximoSprite(0, (0, 0)))

                #Atualiza identicadores das cartas
                for i in range(0, len(jogador_proximo_cartas)):
                    aux = jogador_proximo_cartas.get_sprite(i)
                    aux.atualiza_id(i)

                #Atualiza posicao na tela das cartas do proximo jogador
                atualiza_posicao_baralho_adversario()
                s_jogador_proximo_cartas.release()

        # Recebe mensagem contendo a carta que que o jogador principal selecionou no baralho do proximo jogador
        if 'escolha' in data:
            data = data.split('/')
            #Adiciona na lista de cartas a carta recebida
            cartas.append(str(int(data[1])+1))
            #Adiciona uma carta no grupo de cartas do jogador principal
            s_jogador_cartas.acquire()
            jogador_cartas.add(cartaSprite(str(int(data[1]) + 1), (0, 0)))
            #Atualiza a posicao das cartas do baralho do jogador principal
            atualiza_posicao_baralho_jogador(jogador_cartas)
            s_jogador_cartas.release()

        # Recebe mensagem contendo o nome do jogador que foi campeao
        if 'campeao' in data:
            data = data.split('/')
            if data[1] == nome_jogador:
                print 'Ganhei!!!!'
                #Toca som de campeao
                toca_som_campeao()
                # Configura mensagem de status
                s_mensagem_status.acquire()
                mensagem_status = 'Parabens voce ganhou!'
                s_mensagem_status.release()
                campeao = True
            else:
                # Configura mensagem de fluxo
                s_mensagem_fluxo.acquire()
                mensagem_fluxo = 'Jogador ' + str(data[1]) + ' campeao!!'
                s_mensagem_fluxo.release()

                #Se o campeao estiver na lista de "outros jogadores" atualiza a variavel de campeao
                for o in outros_jogadores:
                    if o[0] == data[1]:
                        o[3] = True
                        break

        # Recebe mensagem contendo o nome do jogador que e o burro
        if 'Burro' in data:
            data = data.split('/')
            #Se o burro for o jogador principal
            if data[1] == nome_jogador:
                print 'Perdi!!!!'
                #Toca musica que perdeu
                toca_som_final_jogo()
                # Configura mensagem de status
                s_mensagem_status.acquire()
                mensagem_status = 'Que pena, voce perdeu :('
                s_mensagem_status.release()
            else:
                s_mensagem_fluxo.acquire()
                mensagem_fluxo = 'Jogador ' + str(data[1]) + ' e o burro'
                s_mensagem_fluxo.release()

        # Recebe mensagem de final de jogo
        if data == 'Fim_jogo':
            print 'O jogo acabou'
            # Configura mensagem de status
            s_mensagem_fluxo.acquire()
            mensagem_fluxo = 'O jogo acabou'
            s_mensagem_fluxo.release()
            s_terminou_jogo.acquire()
            #Configura variavel de termino de jogo
            terminou_jogo = True
            s_terminou_jogo.release()
            break

#Funcao que monta as cartas do proximo jogador com suas posicoes na tela e colocam no grup de sprite jogador_proximo_cartas
def monta_cartas_adversario():
    global ordem,monta_adversario_carta,s_monta_adversario_carta,jogador_proximo_cartas

    quantidade_cartas = int(((NUM_CARTAS*2)-1)/len(ordem))

    #Calcula a quantidade inicial do proximo jogador
    if(ordem[0] == nome_proximo_jogador):
        quantidade_cartas += 1
    else:
        for o in outros_jogadores:
            if o[0] == ordem[0]:
                o[1] += 1
                break

    #Adiciona no grupo de sprite jogador_proximo_cartas com as cartas do proximo jogador e suas posicoes na tela
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
            toca_som_click()
            # configura para seguir o fluxo pra tela de mesa
            tela_atual = MOSTRA_TELA_MESA

        return tela_atual

#Declaracao da classe do botao para voltar para tela de inicio
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
            toca_som_click()
            #configura para seguir o fluxo pra tela inicial
            tela_atual = MOSTRA_TELA_INICIAL

        return tela_atual

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
            toca_som_click()

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
            toca_som_click()
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

#Variaveis para guarda informacoes do jogador e do servidor
nome_jogador=''
host_ip=''
porta=''
#Variavel pra guardar o nome do jogador
nome_proximo_jogador = ''
# Declaracao do socket de conexao com servidor
servidor_sock = None
#Variavel para guardar as cartas do jogador
cartas = []
#Variavel para guardar a ordem dos jogadores
ordem = []
#Variavel para guardar as cartas candidatas a pares
candidado_pares = []

#Constantes de largura e altura da janela do jogo
TELA_LARGURA = 1200
TELA_ALTURA = 700

#Constante para posicao na tela das mensagens de status e de fluxo
MENSAGEM_JOGO_POSICAO_X=70
MENSAGEM_JOGO_POSICAO_Y=20
MENSAGEM_JOGO_FLUXO_POSICAO_X=750

# Variaveis com informacoes dos outros jogadores (outros jogadores nao inclui o jogador principal, nem o proximo jogador)
# nome,quantidade_cartas,posicao_tela,campeao
outros_jogadores = []

# Constantes de fluxo
MOSTRA_TELA_INICIAL = 0
MOSTRA_TELA_MESA = 1
CONECTA_SERVIDOR = 2
COMECA_JOGO = 3
MOSTRA_TELA_ERRO = 4
ERRO_AO_ENTRAR_NO_JOGO = -1

#Variaveis para controlar fluxo do jogo, usadas como controle para uma thread identificar uma acao para outra thread
recebeu_ordem = False
mostra_jogadores_nomes = False
s_recebeu_ordem = BoundedSemaphore()
recebeu_cartas = False
s_recebeu_cartas = BoundedSemaphore()
verificar_pares = False
s_verificar_pares = BoundedSemaphore()
par_selecionado = False
s_par_selecionado = BoundedSemaphore()
carta_selecionada = ''
s_carta_selecionada = BoundedSemaphore()
escolhe_carta_adversario = False
s_escolhe_carta_adversario = BoundedSemaphore()
carta_adversario_escolhida = False
carta_adversario = 0
s_carta_adversario_escolhida = BoundedSemaphore()
monta_adversario_carta = False
s_monta_adversario_carta = BoundedSemaphore()
vez = False
s_vez = BoundedSemaphore()

#Variavel controla se threads ja foram abertas ou nao
thread_comecou_jogo_aberta = False

quantidade_cartas_adversario = 0
s_quantidade_cartas_adversario = BoundedSemaphore()

#Variaveis para guardar as mensagem a serem mostradas na tela
mensagem_erro = ''
mensagem_status = None
s_mensagem_status = BoundedSemaphore()
mensagem_fluxo = ''
s_mensagem_fluxo = BoundedSemaphore()

#Declara os grupos de sprites
# grupo de sprite das cartas dos jogadores
jogador_cartas = pygame.sprite.LayeredUpdates()
s_jogador_cartas = BoundedSemaphore()
#grupo de sprite das cartas do proximo jogador
jogador_proximo_cartas = pygame.sprite.LayeredUpdates()
s_jogador_proximo_cartas = BoundedSemaphore()
#grupo de sprite das cartas dos outros jogadores
outros_jogadores_sprite = pygame.sprite.LayeredUpdates()
s_outros_jogadores_sprite = BoundedSemaphore()

# Variavel guarda o passo atual do jogo, inicia com a tela inicial
step = MOSTRA_TELA_INICIAL

#Variavel que guarda se o jogo terminou
terminou_jogo = False
s_terminou_jogo = BoundedSemaphore()

#Variavel que controla se o evento de click foi disparado
click = 0

# Inicializacao do jogo
pygame.init()
pygame.font.init()
pygame.mixer.init()

#Inicializa fonte
textFont = pygame.font.Font(None, 28)
#Configura tamanho da tela
screen = pygame.display.set_mode((TELA_LARGURA, TELA_ALTURA))
#Configura clock para controlar a quantidade de fps do jogo
clock = pygame.time.Clock()
#Carrega a imagem do plano de fundo
plano_de_fundo,plano_de_fundo_Rect = carrega_imagem("table_background.jpg", 0)

# Inicializacao do botao usado para comecar o jogo
botaoComecaJogo = BotaoComecaJogo()
# Criacao do grupo de sprites e adiciona o botao de comecar jogo
botoes = pygame.sprite.Group(botaoComecaJogo)
# Inicializacao do botao usado para voltar para tela inicial
botao_voltar_inicio = BotaoVoltarTelaInicial()

# Variaveis usadas para pegar a posicao do mouse e usada identificar se algum elemento foi clicado
posicao_mouse_x, posicao_mouse_y = 0, 0

#Inicializao do campo de texto
txtbx = eztext.Input(x=250,y=350,maxlength=45, color=(0,0,0), prompt='Digite seu nome:  ')

#Configuracao do titulo da janela do jogo
pygame.display.set_caption('Burro ou Mico Preto')

#Variaveis para controlar conexao com servidor
thread_estabele_conexao_servidor_aberta = False
servidor_conectado = False
s_servidor_contectado = BoundedSemaphore()

#Variaveis para controlar fluxo de erros
erro_ao_comecar_jogo = False
s_erro_ao_comecar_jogo = BoundedSemaphore()

#Declacarao do numero de cartas
NUM_CARTAS = 53

#Controla se o jogador ja foi campeao
campeao = False

#Loop do pygame
try:
    while 1:
        # Garantindo que o jogo vai rodar com 30 frames por segundo, usado para o jogo ter a mesma velocidade
        # em todos os computadores
        clock.tick(30)
        # Apaga a tela, antes de desenhar de novo
        screen.fill(0)
        # 6 - Desenha a imagem de fundo
        screen.blit(plano_de_fundo, plano_de_fundo_Rect)

        events = pygame.event.get()

        # controle de eventos do pygame, pegamos eventos de click dentro do loop
        for event in events:
            if event.type == QUIT:
                sys.exit()
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    posicao_mouse_x, posicao_mouse_y = pygame.mouse.get_pos()
                    click = 1
            elif event.type == MOUSEBUTTONUP:
                posicao_mouse_x, posicao_mouse_y = 0, 0
                click = 0

        if (step == MOSTRA_TELA_INICIAL):
            #Desenha a primeira tela, texto com nome do jogo, campo de texto, botao para comecar
            displayFont = display(pygame.font.Font(None, 60), 'Bem vindo ao jogo Burro ou Mico Preto')
            screen.blit(displayFont, (200, 50))
            txtbx.update(events)
            txtbx.draw(screen)

            if len(botoes) == 0:
                botoes.add(botaoComecaJogo)

            #Se o botao for clicado , step recebe MOSTRA_TELA_MESA
            step = botaoComecaJogo.atualiza(posicao_mouse_x, posicao_mouse_y, step, click)
            #Desenha o botao
            botoes.draw(screen)

        elif step != MOSTRA_TELA_ERRO:
            #Na tela de erro nao mostra a barra preta no topo, para mostrar mensagens
            screen.fill(pygame.Color("black"), (MENSAGEM_JOGO_POSICAO_X + 10, MENSAGEM_JOGO_POSICAO_Y, 1060, 40))

        if (step == MOSTRA_TELA_MESA):
            #Retira o botao de comecar jogo
            botoes.remove(botaoComecaJogo)
            # Muda para o proximo passo para conectar com servidor
            step = CONECTA_SERVIDOR

        if (step == CONECTA_SERVIDOR):

            #Mostra mensagem na barra preta no topo
            displayFont = display(textFont, "Conectando servidor...")
            screen.blit(displayFont, (MENSAGEM_JOGO_POSICAO_X + 10, MENSAGEM_JOGO_POSICAO_Y + 5))
            #atualiza tela
            pygame.display.flip()

            #Se a thread para estabelecer conexao com servidor ainda nao foi aberta, abre, passando o valor digitado
            #no campo de texto
            if not thread_estabele_conexao_servidor_aberta:
                t = Thread(target=estabelece_conexao_servidor, args=(txtbx.value,))
                t.start()
                # Marca que a thread ja foi aberta
                thread_estabele_conexao_servidor_aberta = True

            s_servidor_contectado.acquire()
            if servidor_conectado:
                # Variavel foi liberada - Verifica se conectou com sucesso ou se deu erro
                if mensagem_erro is None:
                    #Servidor conectado
                    #Mostra mensagem
                    displayFont = display(textFont, "Servidor Conectado")
                    screen.blit(displayFont, (MENSAGEM_JOGO_POSICAO_X + 10, MENSAGEM_JOGO_POSICAO_Y + 5))
                    #Configura o proximo passo COMECA_JOGO
                    step = COMECA_JOGO
                else:
                    #Deu erro ao conectar servidor , desconecta socket
                    desconecta_servidor()
                    #Remove botao de comecar jogo
                    botoes.remove(botaoComecaJogo)
                    #Adiciona botao para voltar para tela de inicio
                    botoes.add(botao_voltar_inicio)
                    #Configura o proximo
                    step = MOSTRA_TELA_ERRO
            s_servidor_contectado.release()

        if (step == MOSTRA_TELA_ERRO):
            #Mostra tela de erro
            #Mostra mensagem de erro
            displayFont = display(pygame.font.Font(None, 30), mensagem_erro)
            screen.blit(displayFont, (300, 300))

            # Se o botao for clicado , step recebe MOSTRA_TELA_INICIAL
            step = botao_voltar_inicio.atualiza(posicao_mouse_x, posicao_mouse_y, step, click)
            if (step == MOSTRA_TELA_INICIAL):
                #Remove o botao de voltar
                botoes.remove(botao_voltar_inicio)

            #Desenha os botoes
            botoes.draw(screen)

        if (step == ERRO_AO_ENTRAR_NO_JOGO):
            #Mostra mensagem de erro ao entrar no jogo
            displayFont = display(textFont, "Nao foi possivel entrar no jogo, tente novamente outra hora")
            screen.blit(displayFont, (MENSAGEM_JOGO_POSICAO_X + 10, MENSAGEM_JOGO_POSICAO_Y + 5))

        if (step == COMECA_JOGO):
            # Passo onde comeco jogo

            #Mostra o nome do jogador embaixo das suas cartas
            displayFont = display(pygame.font.Font(None, 35), str(nome_jogador))
            screen.blit(displayFont, (750, 670))

            #Se ja recebeu a ordem dos jogadores do servidor
            if mostra_jogadores_nomes:
                #Mostra o nome do proximo jogador
                displayFont = display(pygame.font.Font(None, 35), nome_proximo_jogador)
                screen.blit(displayFont, (40, 670))

                #Mostra informacoes dos outros jogadores , sem ser o jogador principal e o proximo
                s_outros_jogadores_sprite.acquire()
                if len(outros_jogadores_sprite) is not 0:
                    outros_jogadores_sprite.update()
                    outros_jogadores_sprite.draw(screen)
                s_outros_jogadores_sprite.release()

                #Mostra o nome dos outros jogadores
                for o in outros_jogadores:
                    displayFont = display(pygame.font.Font(None, 18), '  ' + o[0] + '  ')
                    screen.blit(displayFont, (o[2][0], o[2][1] + 70))

                    #Mostra a quantidade de cartas ou a mensagem se ja foi campeao
                    if o[3]:
                        displayFont = display(pygame.font.Font(None, 15), 'campeao')
                    else:
                        displayFont = display(pygame.font.Font(None, 15), '  ' + str(o[1]) + '  cartas')
                    screen.blit(displayFont, (o[2][0], o[2][1] + 85))

                #Se o jogo terminou - volta para tela inicial
                s_terminou_jogo.acquire()
                if terminou_jogo:
                    step = MOSTRA_TELA_INICIAL
                s_terminou_jogo.release()

            #Verifica se a thread para comecar a jogar, ja foi aberta
            if not thread_comecou_jogo_aberta:
                #Abre a thread para comecar a jogar, passando o grupo de cartas do jogador como parametro
                t = Thread(target=comeca_jogar, args=(jogador_cartas,))
                t.start()
                #Marca que a thread ja foi aberta
                thread_comecou_jogo_aberta = True
            else:
                #Mostra mensagem de status de acordo com o jogo - Topo esquerdo
                s_mensagem_status.acquire()
                displayFont = display(textFont, mensagem_status)
                screen.blit(displayFont, (MENSAGEM_JOGO_POSICAO_X + 10, MENSAGEM_JOGO_POSICAO_Y + 5))
                s_mensagem_status.release()

                # Mostra mensagem de fluxo de acordo com o jogo - Topo direita
                s_mensagem_fluxo.acquire()
                displayFont = display(textFont, mensagem_fluxo)
                screen.blit(displayFont, (MENSAGEM_JOGO_FLUXO_POSICAO_X + 10, MENSAGEM_JOGO_POSICAO_Y + 5))
                s_mensagem_fluxo.release()

                #Caso tenha tido problema para comecar o jogo - mostra mensagem de erro e volta para tela inicial.
                s_erro_ao_comecar_jogo.acquire()
                if erro_ao_comecar_jogo:
                    step = MOSTRA_TELA_ERRO
                    mensagem_erro = mensagem_status
                s_erro_ao_comecar_jogo.release()

                #Verifica se recebeu a ordem dos jogadores do jogo
                s_recebeu_ordem.acquire()
                if recebeu_ordem:
                    if (ordem == None):
                        # Teve algum erro para pegar a ordem
                        step = MOSTRA_TELA_ERRO
                        mensagem_erro = "Erro ao receber ordem dos jogadores"
                    else:
                        #Mostra mensagem de sucesso
                        displayFont = display(textFont, 'Ordem dos jogadores recebida')
                        screen.blit(displayFont, (MENSAGEM_JOGO_POSICAO_X + 10, MENSAGEM_JOGO_POSICAO_Y + 5))
                        #Marca que ja recebeu a ordem
                        recebeu_ordem = False
                        #Marca que ja pode mostrar o nome dos jogadores
                        mostra_jogadores_nomes = True
                s_recebeu_ordem.release()

                #Verifica se ja recebeu as cartas do servidor
                s_recebeu_cartas.acquire()
                if (recebeu_cartas):
                    #Mostra mensagem que recebeu as cartas
                    displayFont = display(textFont, 'Cartas Recebidas')
                    screen.blit(displayFont, (MENSAGEM_JOGO_POSICAO_X + 10, MENSAGEM_JOGO_POSICAO_Y + 5))
                    recebeu_cartas = False
                s_recebeu_cartas.release()

                #Mostra as cartas do jogador e verifica se ela foi clicada, se foi clicada ela muda de posicao na tela
                #e entra como candidata a ser um par formado
                if len(jogador_cartas) is not 0:
                    # Pega resposta do click de todas as cartas
                    for i in range(0, len(jogador_cartas)):
                        aux = jogador_cartas.get_sprite(i)
                        candidado_pares = aux.update(posicao_mouse_x, posicao_mouse_y, click, candidado_pares, True)

                    #Desenha as cartas
                    jogador_cartas.draw(screen)
                    pygame.display.flip()

                #Verifica se duas cartas foram selecionadas como candidatas
                if candidado_pares != None and len(candidado_pares) == 2:
                    pygame.time.delay(300)
                    #Verifica se as candidatas formam mesmo um par
                    # se nao formarem, voltam para posicao inicial
                    #se formarem as cartas sao removidas

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

                        #Toca som de par formado
                        toca_som_par_formado()

                        #Configura variavel de controle, para avisa a outra thread que o par foi selecionado
                        s_par_selecionado.acquire()
                        par_selecionado = True
                        s_carta_selecionada.acquire()
                        #configura variavel com o valor do par selecionado
                        carta_selecionada = candidado_pares[0]
                        s_carta_selecionada.release()
                        s_par_selecionado.release()

                        #Atualiza posicao das cartas
                        atualiza_posicao_baralho_jogador(jogador_cartas)

                    #Limpa os pares candidados
                    candidado_pares = []
                    #Desenha cartas na tela
                    jogador_cartas.draw(screen)
                    pygame.display.flip()

                #Verifica se o proximo jogador tem cartas
                if len(jogador_proximo_cartas) is not 0:

                    #Verifica se o jogador deve escolher alguma carta no baralho do proximo jogador
                    s_escolhe_carta_adversario.acquire()
                    if escolhe_carta_adversario:
                        s_jogador_proximo_cartas.acquire()
                        # Verifica qual vai ser a carta selecionada
                        for i in range(0, len(jogador_proximo_cartas)):
                            aux = jogador_proximo_cartas.get_sprite(i)
                            #se uma carta for selecionada, id recebe o indice da carta selecionada
                            id = aux.update(posicao_mouse_x, posicao_mouse_y, click, vez)
                            if id is not None:
                                #Marca a variavel de controle para outra thread saber que a carta do adversario
                                # foi escolhida
                                s_carta_adversario_escolhida.acquire()
                                #Configura a variavel com o id da carta selecionada
                                carta_adversario = id
                                carta_adversario_escolhida = True
                                escolhe_carta_adversario = False
                                s_carta_adversario_escolhida.release()
                        s_jogador_proximo_cartas.release()
                    else:
                        #Mostra cartas na tela, sem verificar click
                        jogador_proximo_cartas.update(posicao_mouse_x, posicao_mouse_y, click, vez)
                    s_escolhe_carta_adversario.release()
                    jogador_proximo_cartas.draw(screen)

        #Atualiza tela
        pygame.display.flip()

#Caso de um erro, mostra mensagem
except:
    PrintException()
#Por final, desconecta serviddor
finally:
    desconecta_servidor()

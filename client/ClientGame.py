import socket
import sys
import time
import linecache
from random import randrange, seed
from datetime import datetime

nome_jogador=''
host_ip=''
porta=''
servidor_sock = None
cartas = []
ordem = []

#server_address = ('192.168.0.105', 50053)


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
    # Create a TCP/IP socket
    servidor_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Connect the socket to the port on the server given by the caller
    server_address = (host_ip, porta)
    print >> sys.stderr, 'connecting to %s port %s' % server_address
    servidor_sock.connect(server_address)
    print >> sys.stderr, 'connected'

def desconecta_servidor():
    servidor_sock.close()

def comeca_jogo():
    mensagem = 'Oi/' + nome_jogador + '/recepcao'
    envia_mensagem_servidor(mensagem)
    while True:
        data = servidor_sock.recv(4096)
        log_mensagem_recebida(data)
        if(data == 'Ok'):
            print 'Estamos no jogo :)'
            break;
        else:
            print 'Nao estamos no jogo :('
            #todo Tratar os tipos de erros Ex. Jogador com mesmo nome
            break

def recebe_ordem():
    global  ordem
    while True:
        data = servidor_sock.recv(4096)
        log_mensagem_recebida(data)
        if(data == "Comecou"):
            print 'Jogo Comecou'
        elif ('Ordem' in data):
            ordem = data.split('/')
            del ordem[0]
            print 'Ordem ', ordem
            if(ordem[0] == nome_jogador):
                print 'Eba!! Eu comeco a jogada!'
            break

def recebe_cartas():
    global cartas
    while True:
        data = servidor_sock.recv(4096)
        log_mensagem_recebida(data)
        if 'mao_carta' in data:
            cartas.append(data[10:len(data)])

        elif data == 'Fim_mao':
            print cartas

        elif data == 'Pares?':
            break

def verifica_pares():
    if (len(cartas) > 0):
        control = True
        for c in cartas:
            if cartas.count(c) > 1:
                while c in cartas:
                    cartas.remove(c)
                return c

        if (control):
            return None
    else:
        return None

def envia_pares():

    par = verifica_pares()
    if(par != None):
        envia_mensagem_servidor('Sim')
        time.sleep(3)
        envia_mensagem_servidor(par)
        return True
    else:
        envia_mensagem_servidor('Nao')
        return False

def pares():

    if(envia_pares()):
        while True:
            data = servidor_sock.recv(4096)
            log_mensagem_recebida(data)
            if data == 'Pares?':
                if not (envia_pares()):
                    break

    print 'sobraram %d cartas' % len(cartas)


try:

    escolhe_nome_jogador(sys.argv[1])
    configura_servidor('192.168.0.105', 50053)
    conecta_servidor()
    comeca_jogo()
    recebe_ordem()
    recebe_cartas()
    pares()

    if (ordem[0] == nome_jogador):
        conecta_servidor()
        mensagem = 'Oi/' + nome_jogador + '/envio'
        envia_mensagem_servidor(mensagem)

    while True:

        data = servidor_sock.recv(4096)
        log_mensagem_recebida(data)

        if(data == ''):
            print 'error'
            break

        if data == 'cartas_ord':
            cards = ''
            for c in cartas:
                cards += str(c)+'/'

            cards = cards[:len(cards)-1]
            envia_mensagem_servidor(str(cards))

        if 'quant_cartas' in data:
            data = data.split('/')
            carta_escolhida = randrange(int(data[1]))
            if(carta_escolhida <= data[1]):
                envia_mensagem_servidor(str(carta_escolhida))
            else:
                print 'erro na geracao de numero aleatorio'
                break

        if data == 'Pares?':
            envia_pares()

        if 'vez' in data:
            data = data.split('/')
            if data[1] == nome_jogador:
                print 'Eba! Minha vez!'

        if 'carta_escolhida' in data:
            data = data.split('/')
            for c in cartas:
                if (c == data[1]):
                    cartas.remove(c)
                    break

        if 'escolha' in data:
            data = data.split('/')
            cartas.append(data[1])


        if 'campeao' in data:
            data = data.split('/')
            if data[1] == nome_jogador:
                print 'Ganhei!!!!'

        if 'Burro' in data:
            data = data.split('/')
            if data[1] == nome_jogador:
                print 'Perdi!!!!'

        if data == 'Fim_jogo':
            print 'O jogo acabou'
            break

except:
    PrintException()

finally:
    desconecta_servidor()

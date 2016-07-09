import socket
import sys
import time
import linecache

nome_jogador=''
host_ip=''
porta=''
servidor_sock = None
cartas = []

#server_address = ('192.168.0.105', 50053)


def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print 'EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj)

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
    print >> sys.stderr, 'sending "%s"' % mensagem
    servidor_sock.sendall(mensagem)
    while True:
        data = servidor_sock.recv(4096)
        print >> sys.stderr, 'recebido ',data
        if(data == 'Ok'):
            print 'Estamos no jogo :)'
            break;
        else:
            print 'Nao estamos no jogo :('
            #todo Tratar os tipos de erros Ex. Jogador com mesmo nome
            break

def recebe_cartas():
    global cartas
    while True:
        data = servidor_sock.recv(4096)
        print >> sys.stderr, 'recebido ', data
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
        print 'enviando Sim'
        servidor_sock.sendall('Sim')
        time.sleep(1)
        print 'enviando carta ', par
        servidor_sock.sendall(par)
        return True
    else:
        print 'enviando Nao'
        servidor_sock.sendall('Nao')
        return False

def pares():

    if(envia_pares()):
        while True:
            data = servidor_sock.recv(4096)
            print >> sys.stderr, 'recebido ', data
            if data == 'Pares?':
                if not (envia_pares()):
                    break

    print 'sobraram %d cartas' % len(cartas)

try:

    escolhe_nome_jogador(sys.argv[1])
    configura_servidor('192.168.0.105', 50053)
    conecta_servidor()
    comeca_jogo()
    recebe_cartas()
    pares()

except:
    PrintException()

finally:
    desconecta_servidor()

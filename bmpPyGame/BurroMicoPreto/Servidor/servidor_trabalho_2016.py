# -*- coding: cp1252 -*-
# Echo server program
import socket
from threading import Thread, BoundedSemaphore
from random import randrange, seed
import time, sys
import linecache


#Constantes:
TEMPO_INIT = 20
NUM_CARTAS = 53 ##13 pares + 1 burro
MAX_PLAYERS = 5
PORT = 50053              # Arbitrary non-privileged port
TS= 1
seed()


###Solução da internet para ver todas as informações sobre o erro dentro do except:
def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print 'EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj)


def conta_tempo():
	global tempo, init, jogadores, envios,envios1,vez, s_vez, organizacao,	cartas_dadas, fim,s_jogadores, s_envios, s_envios1, s_fim , s_init, s_tempo, s_cartas
	s_init.acquire()
	s_tempo.acquire()
	print "Estou começando um novo jogo e init=", init, "e tempo =", tempo
	s_tempo.release()
	s_init.release()
	try: #Vou liberar todos os semáforos que possam estar bloqueados
		s_jogadores.release()
	except:
		pass
	try:
		s_envios.release()
	except:
		pass
	try:
		s_envios1.release()
	except:
		pass
	try:
		s_vez.release()
	except:
		pass
	try:
		s_init.release()
	except:
		pass
	try:
		s_fim.release()
	except:
		pass
	try:
		s_tempo.release()
	except:
		pass
	try:
		s_cartas.release()
	except:
		pass
	
	s_cartas.acquire()
	cartas_dadas=False
	s_cartas.release()
	s_fim.acquire()
	fim = False
	s_fim.release()
	while init and tempo == None:
		time.sleep(1)
	s_tempo.acquire()
	print 'tempo = ', tempo
	s_tempo.release()
	time.sleep(TEMPO_INIT)
	s_init.acquire()
	init = False
	s_init.release()
	s_jogadores.acquire()
	#Checa se recebeu o envio e a recepção de todos os jogadores
	##Copia o dicionário para nao mudar o seu conteúdo durante o for
	temp = {}
	for jogador in jogadores:
		temp[jogador] = jogadores[jogador][:]
	for jogador in temp:
		if jogadores[jogador][0]==None:
			print "Jogador ", jogador, "com entrada irregular", 'jogadores=', jogadores
			del jogadores[jogador]
		#<RR>
		#elif jogadores[jogador][1]==None:
		#	print "Jogador ", jogador, "com entrada irregular", 'jogadores=', jogadores
		#	del jogadores[jogador]
        #</RR>
	if len(jogadores)<2:
		print "tenho menos que 2 jogadores", jogadores
		for jogador in jogadores:
			s_envios.acquire()
			s_envios1.acquire()
			envios.append(jogadores[jogador][0])
			envios1.append(jogadores[jogador][1])		
			s_envios1.release()
			s_envios.release()

		# <RR>
		#Correcao #1
		if len(jogadores)==1:
		# </RR>
			temp = jogadores.keys()[0]
			temp = jogadores[temp]
			temp[0].sendall("Jogador unico")
		time.sleep(TS)
		s_jogadores.release()
		print 't1'
		termina_jogo()
		return


			
	lista = "Ordem/"
	print "jogadores = ", jogadores
	for jogador in jogadores:
		jogadores[jogador][0].sendall("Comecou")
		time.sleep(TS)
		s_envios.acquire()
		s_envios1.acquire()
		envios.append(jogadores[jogador][0])
		envios1.append(jogadores[jogador][1])
		s_envios1.release()
		s_envios.release()
		s_organizacao.acquire()	
		print '5 org =', organizacao	
		organizacao.append(jogador)
		print '6 org =', organizacao
		s_organizacao.release()
		lista += jogador + '/'	
	lista = lista[:-1]
	for jogador in jogadores:
		jogadores[jogador][0].sendall(lista) ###Envia a ordem de jogadas e o nome de todos os jogadores
		time.sleep(TS)
	s_jogadores.release()	
	sorteia_cartas(jogadores)
	s_cartas.acquire()
	cartas_dadas=True
	s_cartas.release()
	s_vez.acquire()
	vez = 0
	s_vez.release()
	s_tempo.acquire()
	tempo = None
	s_tempo.release()

def pares_iniciais(jogadores, jog):
	global fim
	if not fim:
		s_jogadores.acquire()
		# <RR> Correcao
		sock = jogadores[jog][0]
		# </RR>

		cartas = jogadores[jog][2]
		s_jogadores.release()
		try:	
			sock.send("Pares?")
			data = sock.recv(4096)
			while 'Sim' in data:
				data = sock.recv(4096)
				if not data:
					raise Exception, 'Não mandou informação sobre pares'
				if data in cartas:
					print "Jogador ", jog, 'fez um par com a carta',data
					del cartas[cartas.index(data)]
					if data in cartas:
						del cartas[cartas.index(data)]
						realiza_envio('par/'+jog+'/'+data)
					else:
						raise Exception, jog+' tentando tirar par que não tem '
				else:
					raise Exception, jog+' tentando tirar par que não tem da carta '+data
				sock.send("Pares?")
				data = sock.recv(4096)
			if 'Nao' not in data:
				raise Exception, "Não recebi o Não que indica o fim dos pares"
				print 't2'
				termina_jogo()
			else:
				print "Recebi o Não do jogador", jog
		except:
			
			print "Erro nos pares iniciais"
			PrintException()
			print 't3'
			termina_jogo()		

def sorteia_cartas(jogadores):
	s_jogadores.acquire()
	jog = jogadores.keys()
	s_jogadores.release()
	i=0
	baralho1 = range(NUM_CARTAS)
	baralho2 = range(NUM_CARTAS-1)
	baralho = baralho1 + baralho2
	try:
		while len(baralho)>0:
			sorteio = randrange(len(baralho))
			s_jogadores.acquire()
			# <RR> Correcao
			jogadores[jog[i]][0].sendall('mao_carta/'+str(baralho[sorteio]))
			# </RR>
			time.sleep(TS)
			jogadores[jog[i]][2].append(str(baralho[sorteio])) #Guardo que mandei essa carta para esse cliente
			s_jogadores.release()

			del baralho[sorteio]
			s_jogadores.acquire()
			i = (i + 1)%len(jogadores)
			s_jogadores.release()
			
		s_jogadores.acquire()
		for jog in jogadores:
			# <RR>
			jogadores[jog][0].sendall('Fim_mao')
			# </RR>
			print "Mandei fim_mao para ", jog
		s_jogadores.release()
		time.sleep(TS)

	except:
		print "Deu erro ao distribuir as cartas"
		print 'i = ', i, 'jog = ', jog, 'jogadores = ', jogadores
		print 'sorteio =', sorteio, 'baralho =', baralho
		PrintException()
		print 't4'
		termina_jogo()
		return
	s_jogadores.acquire()
	t3 = range(len(jogadores))
	s_jogadores.release()
	i=0
	s_jogadores.acquire()
	for jog in jogadores:
		t3[i] = Thread(target=pares_iniciais, args = (jogadores, jog))
		t3[i].start()
		i = i+1
	s_jogadores.release()
	for i in range(len(t3)):
		t3[i].join()	
	
		

		
		
def realiza_envio(string):
	global envios, s_envios
	s_envios.acquire()
	for i in envios:
		try:
			i.sendall(string)
		except:
			print "Perdeu conexão com um dos jogadores. i = ",i
			PrintException()
			s_envios.release()
			print 't5'
			termina_jogo()
			exit()
	s_envios.release()
	time.sleep(TS)

def termina_jogo():
	global envios, envios1, jogadores, organizacao, init, vez, s_vez, tempo, fim, s_jogadores, s_envios, s_envios1, s_fim  , s_init
	s_termina.acquire() #Só um termina de cada vez!
	if len(jogadores) !=0:
		s_envios.acquire()
		print "Vai terminar o jogo", envios
		s_envios.release()
		s_fim.acquire()
		fim = True
		s_fim.release()
		s_envios.acquire()
		for i in envios:
			try:
				i.sendall("Fim_jogo")
				i.close()
			except:
				pass
		s_envios.release()
		s_envios1.acquire()
		for i in envios1:
			try:
				print "Fechei envios 1"
				i.settimeout(1)
				i.close()
			except:
				pass
		s_envios1.release()

		print "Terminou e vai começar nova partida"
		time.sleep(TS)
		s_jogadores.acquire()
		jogadores = {}
		s_jogadores.release()
		s_vez.acquire()
		vez = None
		s_vez.release()
		s_organizacao.acquire()
		print '7 org =', organizacao
		organizacao = []
		print '8 org =', organizacao
		s_organizacao.release()
		s_envios.acquire()
		envios = []
		s_envios.release()
		s_envios1.acquire()
		envios1=[]
		s_envios1.release()
		s_init.acquire()
		init = True
		s_init.release()
		s_tempo.acquire()
		tempo = None
		s_tempo.release()
		s_cartas.acquire()
		cartas_dadas=False
		s_cartas.release()
		t = Thread(target = conta_tempo, args=())
		t.start()
		
	s_termina.release()	
	return


def envia_todos(*args):
	if len(args) == 2:
		if args[0] == 'vez':
			realiza_envio("vez/"+str(args[1]))
		elif args[0] == 'mais um campeao':
			realiza_envio("campeao/"+str(args[1]))
		elif args[0] == "Burro":
			realiza_envio("Burro/"+str(args[1]))
	elif len(args) == 3:
		realiza_envio("par/"+str(jogador)+"/"+str(selecao))

def pergunta_ordem(con2, jogadores, oponente):
	
	con2.sendall('cartas_ord')
	time.sleep(TS)
	data = con2.recv(4096)
	if not data:
		print 't6'
		termina_jogo()
		return
	sucess = False
	tentativas = 0
	while not sucess:
		sucess = True
		#print "Data =", data
		data = data.split('/') #c1/c2/.../cn -->cartas colocadas dessa forma
		if len(data)!= len(jogadores[oponente][2]): ##Mandou cartas erradas
			sucess = False
			tentativas+=1
			print "Jogador ", oponente , 'mandou as cartas erradas'
			con2.sendall('cartas_ord')
			data = con2.recv(4096)
			if not data:
				print 't7'
				termina_jogo()
				return
			else:
				
				tentativas+=1
				s_jogadores.acquire()
				for i in range(len(jogadores[oponente][2])):
					if jogadores[oponente][2][i] not in data:
						print "Jogador ", oponente , 'mandou cartas faltando'
						sucess = False
				s_jogadores.release()
				if sucess == False:
					con2.sendall('cartas_ord')
					data = con2.recv(4096)
					if not data:
						print 't8'
						termina_jogo()
						return
				if tentativas == 5:
					raise Exception , oponente + ' se recusa a mandar as cartas'

						


		
def envia(jogador):
	global vez, s_vez #Diz qual é o jogador atual
	global jogadores
	global organizacao, init, fim,s_fim , s_init, s_organizacao
	print "Jogador ", jogador, "criou a envia"
			
	try:
		s_jogadores.acquire()
		con = jogadores[jogador][1] #Pega conexão para enviar dados
		s_jogadores.release()
		while cartas_dadas==False:
			time.sleep(1)
		if cartas_dadas==True: ###O jogo comecou
			while not fim: #Enquanto o jogo não chegar ao fim
				#print init, vez, organizacao, jogador
				s_vez.acquire()
				s_organizacao.acquire()

				if vez != None and vez < len(organizacao) and organizacao[vez] == jogador and len(jogadores)>=2: #Eh a vez desse jogador
					s_organizacao.release()
					s_vez.release()
					print 'É a vez do ', jogador
					s_organizacao.acquire()
					oponente = organizacao[(organizacao.index(jogador)+1)%len(organizacao)]
					s_organizacao.release()
					s_jogadores.acquire()
					numero = len(jogadores[oponente][2])#Número de cartas do próximo jogador
					con2 = jogadores[oponente][0]
					pergunta = Thread(target=pergunta_ordem, args=(con2, jogadores, oponente))
					s_jogadores.release()
					pergunta.start()
					#<RR>
					con.sendall('quant_cartas/'+str(numero))
					#</RR>
					time.sleep(TS)
					carta = con.recv(4096)
					if not carta:
						print 't9'
						termina_jogo()
						return
					else:
						try:
							tentativas = 0
							sucesso = False
							while not sucesso and not fim:
								carta = int(carta)
								s_jogadores.acquire()
								if carta > len(jogadores[oponente][2])-1 or carta<0:
									con.sendall("Posição inválida")
									tentativas +=1
									carta = con.recv(4096)
									if not carta:
										s.release()
										print 't10'
										termina_jogo()

										return
								else:
									sucesso = True
								if tentativas == 5:
									raise Exception, jogador+' não enviou um pedido de carta válido'
								s_jogadores.release()

							pergunta.join()
							s_jogadores.acquire()
							con2.sendall('carta_escolhida/'+str(jogadores[oponente][2][int(carta)]))#Envio para o jogador a carta do oponente

							time.sleep(TS)
							jogadores[jogador][2].append(jogadores[oponente][2][int(carta)]) #Adiciono a carta na mão do jogado

							con.sendall('escolha/'+jogadores[oponente][2][int(carta)])
							time.sleep(TS)
							del jogadores[oponente][2][int(carta)] #Tiro a carta da mão do oponente
							if len(jogadores[oponente][2])==0: ##Oponente ficou sem cartas
								envia_todos('mais um campeao', oponente)
								del jogadores[oponente]
								s_vez.acquire()
								s_organizacao.acquire()
								print '1 org =', organizacao
								del organizacao[(vez+1)%len(organizacao)]
								print '2 org =', organizacao
								s_organizacao.release()
								s_vez.release()
							s_jogadores.release()	

							pares_iniciais(jogadores, jogador)

							s_jogadores.acquire()
							if len(jogadores[jogador][2])==0:
								s_jogadores.release()
								envia_todos('mais um campeao', jogador)
								s_jogadores.acquire()
								del jogadores[jogador]
								s_vez.acquire()
								s_organizacao.acquire()
								print '3 org =', organizacao
								del organizacao[vez]
								print '4 org =', organizacao
								s_organizacao.release()
								s_vez.release()
							if len(jogadores)==1:
								s_jogadores.release()
								for i in jogadores:
									envia_todos('Burro', i)
								print 't11'
								termina_jogo()
								return
							s_jogadores.release()
							s_vez.acquire()
							s_organizacao.acquire()
							print "Antes: vez = ", vez, 'organizacao=', organizacao
							vez = (vez +1) %len(organizacao)
							print "vez vale", vez,'e organizacao vale', organizacao
							envia_todos("vez", organizacao[vez])
							#<RR>
							jogador = organizacao[vez]
							con = jogadores[jogador][0]
							# </RR>
							s_organizacao.release()
							s_vez.release()
								
										
						
						
						except:
							try:
								con.send ("Você não enviou a posição da carta")
							except:
								print "O jogo já acabou!"
							PrintException()
							print 't12'
							termina_jogo()
							time.sleep(TS)
				else:
					s_organizacao.release()
					s_vez.release()
		

	except:
		PrintException()
		print 't14'
		termina_jogo()
		
			
			
	
				
		


def aceita(conn):
	global jogadores, tempo, init, end_game,s_jogadores, s_fim , s_init
	#<RR>
	#s_init.acquire()
	#if init :
		#s_init.release()
	if True:
	#</RR> todo corrigir esse pedaco, receber o pedido /envio, depois de ter comecado, problema na variavel init
		data = conn.recv(4096) #Recebe os dados 
		valores = data.split('/') #Oi/Nome_usuario/envio_ou_recepcao
		print 'valores=',valores
		if len(jogadores) > MAX_PLAYERS:
			if valores[1] not in jogadores:
				print "Já tem jogadores demais"
				conn.sendall("Espere proximo jogo")
				time.sleep(TS)
				conn.close()
				return

		if len(valores) != 3 or valores[0] != 'Oi' or (valores[2] != 'recepcao' and valores[2] != 'envio'):
			print 'data vale ', data
			conn.sendall("Pacote mal formado")
			time.sleep(TS)
		#<RR>
		elif valores[1] in jogadores and jogadores[valores[1]][0] != None and jogadores[valores[1]][0]!=None and valores[2] == 'recepcao': ###Jogador já existe e está confgurado
		#</RR>
			print "recebi ", data , 'e jogadores=', jogadores, 'por isso escolha outro usuário'
			conn.sendall("Escolha outro nome de usuário")
			time.sleep(TS)
			aceita(conn)
			return
					
		else:
			if valores[1] not in jogadores:
				print "Coloquei ", valores[1]
				jogadores[valores[1]]=[None,None, []]
			s_tempo.acquire()
			tempo = TEMPO_INIT
			print "!!!!!!!Setei o tempo como o aceita para ", tempo
			s_tempo.release()
			conn.sendall("Ok")
			time.sleep(TS)
			print "valores[2]=",valores[2]
			if valores[2] == 'recepcao':
				print "Coloquei a recepcao de ", valores[1]
				jogadores[valores[1]][0] = conn
				return

			else:
				#<RR>
				s_envios.acquire()
				envios.remove(jogadores[valores[1]][0])
				s_envios.release()
				jogadores[valores[1]][0] = conn
				#</RR>
				jogadores[valores[1]][1] = conn
				# <RR>
				envios.append(conn)
				# </RR>
				print "Coloquei o envio de ", valores[1]
				t = Thread(target= envia, args = (valores[1],))
				t.start()
				return

	else:
		s_init.release()
		data = conn.recv(4096)
		data = data.split('/')
		conn.send(data[1]+', o jogo já começou. Espere a próxima partida.')
		conn.close()


# <RR>
HOST = '192.168.0.105'                 # Symbolic name meaning all available interfaces
# </RR>
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #IPv4,tipo de socket
# <RR>
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# </RR>
s.bind((HOST, PORT)) #liga o socket com IP e porta
jogadores = {}
s_jogadores = BoundedSemaphore()
organizacao = []
s_organizacao = BoundedSemaphore()
envios = []
s_envios = BoundedSemaphore()
envios1 = []
s_envios1 = BoundedSemaphore()
init = True
s_init = BoundedSemaphore()
vez = None
s_vez = BoundedSemaphore()
tempo = None
s_tempo = BoundedSemaphore()
fim = False
s_fim = BoundedSemaphore()
cartas_dadas=False
s_cartas = BoundedSemaphore()
s_termina = BoundedSemaphore()
t = Thread(target = conta_tempo, args = ())
t.start()


while(1):
	s.listen(1) #espera chegar pacotes na porta especificada
	conn, addr = s.accept()#Aceita uma conexão
	print "Aceitou mais uma"
	t = Thread(target=aceita, args=(conn,))
	t.start()
	

